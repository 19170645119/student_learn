"""题库生成Agent - RAG检索增强"""
from core.llm_service import chat as llm_chat
from core.rag import build_chapter_rag
import json

SYSTEM_PROMPT = """你是一个专业的课程题库设计专家。请根据提供的知识库内容，生成练习题。

要求生成5道题，包含以下类型：
- 1道单选题（4个选项）
- 1道判断题
- 1道填空题
- 1道简答题
- 1道综合应用题

题目必须严格基于知识库内容，不要超纲。输出JSON格式。
"""

async def generate_quiz(chapter_title: str, chapter_content: str = "", chapter_id: int = None, profile: dict = None, memory_entries: list = None) -> dict:
    rag_content = chapter_content
    if chapter_id:
        full = await build_chapter_rag(chapter_id)
        if full:
            rag_content = full

    user_prompt = f"请为以下章节内容生成练习题：\n\n章节：{chapter_title}\n\n知识库内容：\n{rag_content}"
    if profile:
        user_prompt += f"\n学生水平：{profile.get('knowledge_base','中等')}，请调整题目难度。"

    if memory_entries:
        mem_text = "\n???????" + "?".join([f"{m['key']}={m['value']}" for m in memory_entries])
        user_prompt += mem_text

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
        return {"title": f"{chapter_title} - 练习题", "questions": []}
