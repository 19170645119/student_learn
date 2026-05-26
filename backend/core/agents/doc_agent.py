"""文档生成Agent - RAG检索增强"""
from core.openai_service import chat as llm_chat, chat_stream as llm_chat_stream
from core.rag import build_chapter_rag, build_rag_context


SYSTEM_PROMPT = """你是一位资深的课程讲师。请根据提供的知识内容，生成一份结构清晰、内容详实的课程讲解文档。

要求：
1. 使用Markdown格式，包含标题层级、列表、代码块等
2. 内容覆盖：概念引入 → 核心原理 → 关键方法 → 应用场景 → 小结
3. 适当使用LaTeX数学公式（用包裹）
4. 语言通俗易懂，适合大学生阅读
5. 总字数控制在2000-4000字
6. 严格基于提供的知识内容，不要编造事实；如果内容有限，基于有限内容尽力展开

输出纯Markdown文本。
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
            if rag_content:
                rag_content += "\n\n" + extra_rag
            else:
                rag_content = extra_rag

    if not rag_content.strip():
        rag_content = f"关于「{chapter_title}」的基础知识介绍。"

    user_prompt = f"请为以下主题生成课程讲解文档：\n\n主题：{chapter_title}\n\n参考内容：\n{rag_content}"

    if profile:
        style_hint = (
            f"\n学生画像：知识基础={profile.get('knowledge_base', '')}，"
            f"认知风格={profile.get('cognitive_style', '')}，请据此调整讲解深度和风格。"
        )
        user_prompt += style_hint

    return [
        {"role": "system", "content": SYSTEM_PROMPT},
        {"role": "user", "content": user_prompt},
    ]


async def generate_doc(
    chapter_title: str,
    chapter_content: str = "",
    chapter_id: int = None,
    profile: dict = None,
    user_query: str = None,
) -> str:
    messages = await _build_messages(chapter_title, chapter_content, chapter_id, profile, user_query)
    return await llm_chat(messages)


async def generate_doc_stream(
    chapter_title: str,
    chapter_content: str = "",
    chapter_id: int = None,
    profile: dict = None,
    user_query: str = None,
):
    messages = await _build_messages(chapter_title, chapter_content, chapter_id, profile, user_query)
    async for chunk in llm_chat_stream(messages):
        yield chunk