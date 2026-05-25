"""思维导图生成Agent - RAG检索增强"""
import base64
from core.llm_service import chat as llm_chat
from core.rag import build_chapter_rag

SYSTEM_PROMPT = """你是一个知识可视化专家。请根据提供的知识库内容，生成一份Mermaid格式的思维导图(mindmap)。

要求：
1. 使用Mermaid mindmap语法
2. 以章节标题为根节点
3. 分支覆盖：核心概念 → 关键算法 → 应用场景 → 重要公式
4. 层级不超过4层，保持可读性
5. 严格基于知识库内容

只输出Mermaid代码。
"""

async def generate_mindmap(chapter_title: str, chapter_content: str = "", chapter_id: int = None, profile: dict = None, memory_entries: list = None):
    rag_content = chapter_content
    if chapter_id:
        full = await build_chapter_rag(chapter_id)
        if full:
            rag_content = full

    user_prompt = f"请为以下章节内容生成Mermaid思维导图：\n\n章节：{chapter_title}\n知识库内容：{rag_content}"
    if profile:
        hints = []
        if profile.get('cognitive_style'): hints.append(f"学生认知风格={profile['cognitive_style']}")
        if profile.get('knowledge_base'): hints.append(f"学生水平={profile['knowledge_base']}")
        if hints: user_prompt += f"\n学生信息：{'; '.join(hints)}。请调整导图的层次深度。"

    messages = [
        {"role": "system", "content": SYSTEM_PROMPT},
        {"role": "user", "content": user_prompt}
    ]
    mermaid_code = await llm_chat(messages)
    # 生成 Mermaid.ink 图片URL
    code_bytes = mermaid_code.encode('utf-8')
    encoded = base64.urlsafe_b64encode(code_bytes).decode()
    return {
        "content": mermaid_code,
        "extra_data": {
            "mermaid": mermaid_code,
            "image_url": f"https://mermaid.ink/img/{encoded}",
            "svg_url": f"https://mermaid.ink/svg/{encoded}"
        }
    }
