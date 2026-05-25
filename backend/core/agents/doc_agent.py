"""文档生成Agent - RAG检索增强"""
from core.llm_service import chat as llm_chat
from core.rag import build_chapter_rag
import json

SYSTEM_PROMPT = """你是一位资深的人工智能课程讲师。请根据提供的知识库内容，生成一份结构清晰、内容详实的课程讲解文档。

要求：
1. 使用Markdown格式，包含标题层级、列表、代码块等
2. 内容覆盖：概念引入 → 核心原理 → 关键算法/方法 → 应用场景 → 小结
3. 适当使用LaTeX数学公式（用$$包裹）
4. 语言通俗易懂，适合大学生阅读
5. 总字数控制在2000-4000字
6. 严格基于提供的知识库内容，不要编造事实

输出纯Markdown文本。
"""

async def generate_doc(chapter_title: str, chapter_content: str = "", chapter_id: int = None, profile: dict = None, memory_entries: list = None) -> str:
    # RAG检索：获取章节完整内容
    rag_content = chapter_content
    if chapter_id:
        full = await build_chapter_rag(chapter_id)
        if full:
            rag_content = full

    user_prompt = f"请为以下章节生成课程讲解文档：\n\n章节标题：{chapter_title}\n\n知识库内容：\n{rag_content}"

    if profile:
        style_hint = f"\n学生画像：知识基础={profile.get('knowledge_base','')}，认知风格={profile.get('cognitive_style','')}，请据此调整讲解深度和风格。"
        user_prompt += style_hint

    if memory_entries:
        mem_text = "\n???????" + "?".join([f"{m['key']}={m['value']}" for m in memory_entries])
        user_prompt += mem_text

    messages = [
        {"role": "system", "content": SYSTEM_PROMPT},
        {"role": "user", "content": user_prompt}
    ]
    return await llm_chat(messages)
