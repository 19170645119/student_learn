"""
RAG 检索增强服务 - 从知识库检索相关内容注入 Prompt
"""
from sqlalchemy import select, text
from models.learning_path import KnowledgeNode
from models import AsyncSessionFactory


async def search_knowledge(query: str, top_k: int = 5) -> list[dict]:
    """
    关键词检索知识库，返回 top_k 条最相关结果
    策略：MySQL LIKE 匹配 title + content
    """
    if not query.strip():
        return []

    keywords = query.strip().split()
    async with AsyncSessionFactory() as session:
        async with session.begin():
            result = await session.execute(
                select(KnowledgeNode)
            )
            all_nodes = result.scalars().all()

    # 计算相关度分数（简单的关键词命中计数）
    scored = []
    for node in all_nodes:
        score = 0
        title_lower = node.title.lower()
        content_lower = (node.content or "").lower()
        query_lower = query.lower()

        for kw in keywords:
            kw_lower = kw.lower()
            if kw_lower in title_lower:
                score += 3  # 标题命中权重高
            if kw_lower in content_lower:
                score += 1  # 内容命中权重低

        # 额外：完整查询匹配加分
        if query_lower in title_lower:
            score += 5
        if query_lower in content_lower:
            score += 2

        if score > 0:
            scored.append({
                "id": node.id,
                "title": node.title,
                "content": node.content or "",
                "node_type": node.node_type,
                "level": node.level if hasattr(node, 'level') else "",
                "parent_id": node.parent_id,
                "score": score,
            })

    scored.sort(key=lambda x: x["score"], reverse=True)
    return scored[:top_k]


async def build_rag_context(query: str, top_k: int = 5) -> str:
    """
    构建 RAG 上下文文本，可拼入 System Prompt
    """
    results = await search_knowledge(query, top_k)
    if not results:
        return ""

    context_parts = ["【知识库相关内容】"]
    for i, r in enumerate(results, 1):
        context_parts.append(f"{i}. [{r['title']}] {r['content'][:300]}")
    return "\n".join(context_parts)


async def search_by_chapter(chapter_id: int) -> dict | None:
    """获取指定章节及其子节点"""
    async with AsyncSessionFactory() as session:
        async with session.begin():
            chapter = await session.scalar(
                select(KnowledgeNode).filter(KnowledgeNode.id == chapter_id)
            )
            if not chapter:
                return None

            children = await session.execute(
                select(KnowledgeNode).filter(KnowledgeNode.parent_id == chapter_id)
                .order_by(KnowledgeNode.order_num)
            )
            children_list = children.scalars().all()

            return {
                "id": chapter.id,
                "title": chapter.title,
                "content": chapter.content or "",
                "children": [
                    {"title": c.title, "content": c.content or ""}
                    for c in children_list
                ]
            }


async def build_chapter_rag(chapter_id: int) -> str:
    """构建章节完整的 RAG 上下文（章节 + 所有子节点）"""
    chapter = await search_by_chapter(chapter_id)
    if not chapter:
        return ""

    parts = [f"# {chapter['title']}\n{chapter['content']}"]
    if chapter["children"]:
        parts.append("\n## 子章节")
        for c in chapter["children"]:
            parts.append(f"### {c['title']}\n{c['content']}")
    return "\n\n".join(parts)
