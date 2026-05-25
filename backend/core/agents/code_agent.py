"""代码案例生成Agent - RAG检索增强"""
from core.llm_service import chat as llm_chat
from core.rag import build_chapter_rag

SYSTEM_PROMPT = """你是一个AI编程教育专家。请根据提供的知识库内容，生成一段完整的Python实操代码案例。

要求：
1. 代码可完整运行，包含必要的import
2. 添加详细的注释说明
3. 包含示例数据和运行结果展示
4. 严格基于知识库中的算法和概念
5. 代码难度根据学生水平调整

输出Python代码。
"""

async def generate_code(chapter_title: str, chapter_content: str = "", chapter_id: int = None, profile: dict = None, memory_entries: list = None) -> str:
    rag_content = chapter_content
    if chapter_id:
        full = await build_chapter_rag(chapter_id)
        if full:
            rag_content = full

    user_prompt = f"请为以下章节内容生成Python实操代码案例：\n\n章节：{chapter_title}\n\n知识库内容：\n{rag_content}"
    if profile:
        user_prompt += f"\n学生水平：{profile.get('knowledge_base','中等')}，请调整代码难度。"

    if memory_entries:
        mem_text = "\n???????" + "?".join([f"{m['key']}={m['value']}" for m in memory_entries])
        user_prompt += mem_text

    messages = [
        {"role": "system", "content": SYSTEM_PROMPT},
        {"role": "user", "content": user_prompt}
    ]
    return await llm_chat(messages)
