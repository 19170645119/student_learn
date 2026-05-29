"""PPT生成Agent - RAG检索增强，输出结构化幻灯片JSON"""
from core.openai_service import chat as llm_chat, chat_stream as llm_chat_stream
from core.rag import build_chapter_rag, build_rag_context
import json


SYSTEM_PROMPT = """你是一位资深教学课件设计师。请根据提供的知识内容，生成一份结构化的教学PPT幻灯片。

要求：
1. 输出严格JSON格式，不要任何额外文字
2. 幻灯片8-12页，包含：封面→目录→核心概念→详细讲解→对比分析→图表展示→案例→小结
3. 每页要点3-5条，每条控制在20字以内，简洁有力
4. 适当使用表格对比、Mermaid图表增强理解
5. speaker_notes是为演讲者准备的备注，50-100字，解释本页核心
6. key_point是本页最核心的一句话总结
7. 严格基于提供的知识内容，不要编造

JSON结构：
{
  "title": "PPT标题",
  "slides": [
    {
      "page": 1,
      "title": "页面标题",
      "layout": "title_slide|title_content|two_column|table|diagram|summary",
      "bullets": ["要点1", "要点2"],
      "table": null 或 {"headers": ["列1","列2"], "rows": [["值1","值2"]]},
      "diagram": null 或 "Mermaid语法字符串",
      "key_point": "本页核心要点",
      "speaker_notes": "演讲者备注文字"
    }
  ]
}

layout说明：
- title_slide: 封面页，bullets作为副标题
- title_content: 标题+要点列表，最常用
- two_column: 左右对比，bullets前一半左列后一半右列
- table: 表格数据，填table字段
- diagram: Mermaid图表，填diagram字段，bullets可选
- summary: 小结页，bullets是本课核心要点总结
"""


async def _build_messages(
    chapter_title: str,
    chapter_content: str = "",
    chapter_id: int = None,
    profile: dict = None,
    user_query: str = None,
) -> list:
    rag_content = chapter_content

    if chapter_id:
        full = await build_chapter_rag(chapter_id)
        if full:
            rag_content = full

    if user_query:
        extra_rag = await build_rag_context(user_query, top_k=5)
        if extra_rag:
            rag_content = rag_content + "\n\n" + extra_rag if rag_content else extra_rag

    if not rag_content.strip():
        rag_content = f"关于""{chapter_title}""的基础知识介绍。"

    user_prompt = f"请为以下主题生成教学PPT幻灯片：\n\n主题：{chapter_title}\n\n参考内容：\n{rag_content}"

    if profile:
        style_hint = (
            f"\n学生画像：知识基础={profile.get('knowledge_base', '')}，"
            f"认知风格={profile.get('cognitive_style', '')}，请据此调整讲解深度。"
        )
        user_prompt += style_hint

    return [
        {"role": "system", "content": SYSTEM_PROMPT},
        {"role": "user", "content": user_prompt},
    ]


async def generate_ppt(
    chapter_title: str,
    chapter_content: str = "",
    chapter_id: int = None,
    profile: dict = None,
    user_query: str = None,
    extra: dict = None,
) -> str:
    """非流式生成PPT JSON"""
    messages = await _build_messages(chapter_title, chapter_content, chapter_id, profile, user_query)
    result = await llm_chat(messages)

    # 尝试从结果中提取JSON
    if "{" in result and "}" in result:
        json_start = result.index("{")
        json_end = result.rindex("}") + 1
        json_str = result[json_start:json_end]
        try:
            data = json.loads(json_str)
            # 验证基本结构
            if "slides" in data:
                return json.dumps(data, ensure_ascii=False)
        except json.JSONDecodeError:
            pass

    # 如果解析失败，返回原始结果
    return result


async def generate_ppt_stream(
    chapter_title: str,
    chapter_content: str = "",
    chapter_id: int = None,
    profile: dict = None,
    user_query: str = None,
    extra: dict = None,
):
    """流式生成PPT JSON"""
    messages = await _build_messages(chapter_title, chapter_content, chapter_id, profile, user_query)
    full_text = ""
    async for chunk in llm_chat_stream(messages):
        if chunk.get("done"):
            full_text = chunk.get("full_text", full_text)
            break
        yield {"type": "token", "text": chunk.get("text", "")}

    # 提取JSON
    content = full_text
    if "{" in full_text and "}" in full_text:
        json_start = full_text.index("{")
        json_end = full_text.rindex("}") + 1
        content = full_text[json_start:json_end]
        try:
            data = json.loads(content)
            content = json.dumps(data, ensure_ascii=False)
        except json.JSONDecodeError:
            pass

    yield {"type": "done", "content": content}
