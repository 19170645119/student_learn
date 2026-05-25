"""教学视频脚本生成Agent - RAG检索增强"""
from core.llm_service import chat as llm_chat
from core.rag import build_chapter_rag
import json

SYSTEM_PROMPT = """你是一个教学视频制作专家。请根据提供的知识库内容，生成一份5-8分钟的教学视频脚本。

要求：
1. 包含开场白 → 核心内容讲解(3-4个要点) → 总结回顾
2. 每个场景标注：场景时长、画面描述、旁白文字、字幕
3. 建议配合的动画/图表类型
4. 严格基于知识库内容
5. 语言生动，适合视频讲解风格

输出JSON格式。
"""

async def generate_video_script(chapter_title: str, chapter_content: str = "", chapter_id: int = None, profile: dict = None, memory_entries: list = None) -> dict:
    rag_content = chapter_content
    if chapter_id:
        full = await build_chapter_rag(chapter_id)
        if full:
            rag_content = full

    user_prompt = f"请为以下章节内容生成教学视频脚本：\n\n章节：{chapter_title}\n知识库内容：{rag_content}"
    if profile:
        hints = []
        if profile.get('cognitive_style'): hints.append(f"学生偏好{profile['cognitive_style']}")
        if profile.get('knowledge_base'): hints.append(f"水平{profile['knowledge_base']}")
        if hints: user_prompt += f"\n学生信息：{'; '.join(hints)}。请调整视频的讲解深度和呈现风格。"

    messages = [
        {"role": "system", "content": SYSTEM_PROMPT},
        {"role": "user", "content": user_prompt}
    ]
    response = await llm_chat(messages)

    try:
        if "```json" in response:
            json_str = response.split("```json")[1].split("```")[0]
        elif "```" in response:
            json_str = response.split("```")[1].split("```")[0]
        else:
            json_str = response
        return json.loads(json_str)
    except (json.JSONDecodeError, IndexError):
        return {"title": f"{chapter_title} - 教学视频", "scenes": []}
