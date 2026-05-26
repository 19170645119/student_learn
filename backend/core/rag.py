"""
RAG 检索增强服务 - 从知识库检索相关内容注入 Prompt
"""
from sqlalchemy import select, text
from models.learning_path import KnowledgeNode
from models import AsyncSessionFactory

# 中文常见停用词 / 意图词
_STOP_WORDS = {
    "我", "想", "要", "学", "学习", "了解", "生成", "帮我", "请", "一个", "一下",
    "相关", "关于", "什么是", "怎么", "如何", "帮忙", "的", "了", "吗", "呢", "吧",
    "谢谢", "可以", "能不能", "为什么", "告诉我", "介绍", "解释",
}


def _extract_keywords(query: str) -> list:
    """从中文查询中提取有效关键词"""
    query = query.strip()
    keywords = []

    # 方法1: 按空格/标点分割
    import re
    parts = re.split(r'[，,。；;！!？?\s]+', query)
    for part in parts:
        part = part.strip()
        if part and part not in _STOP_WORDS:
            keywords.append(part)

    # 方法2: 如果没分割出有效关键词，移除停用词后取剩余部分
    if not keywords:
        remaining = query
        for sw in sorted(_STOP_WORDS, key=len, reverse=True):
            remaining = remaining.replace(sw, " ")
        remaining_parts = [p.strip() for p in remaining.split() if len(p.strip()) >= 2]
        keywords.extend(remaining_parts)

    # 方法3: 兜底 — 取 query 中最长连续非停用词子串
    if not keywords and len(query) >= 2:
        # 从 query 中逐个字符扫描，取汉字/字母连续段
        segments = re.findall(r'[\u4e00-\u9fff\w]{2,}', query)
        for seg in segments:
            if seg not in _STOP_WORDS:
                keywords.append(seg)

    # 去重
    seen = set()
    result = []
    for kw in keywords:
        if kw.lower() not in seen:
            seen.add(kw.lower())
            result.append(kw)
    return result


async def search_knowledge(query: str, top_k: int = 5) -> list[dict]:
    """
    关键词检索知识库，返回 top_k 条最相关结果
    策略：MySQL LIKE 匹配 title + content + 反向匹配
    """
    if not query.strip():
        return []

    keywords = _extract_keywords(query)
    query_lower = query.lower()

    async with AsyncSessionFactory() as session:
        async with session.begin():
            result = await session.execute(
                select(KnowledgeNode)
            )
            all_nodes = result.scalars().all()

    scored = []
    for node in all_nodes:
        score = 0
        title_lower = node.title.lower()
        content_lower = (node.content or "").lower()

        # 关键词正向匹配: kw 在 title 或 content 中
        for kw in keywords:
            kw_lower = kw.lower()
            if kw_lower in title_lower:
                score += 3
            if kw_lower in content_lower:
                score += 1

        # 完整查询正向匹配
        if query_lower in title_lower:
            score += 5
        if query_lower in content_lower:
            score += 2

        # ★ 反向匹配: 节点标题的关键部分是否出现在 query 中
        #   提取节点标题中的关键词（按空格/标点分割）
        title_parts = [p.strip().lower() for p in title_lower.replace("、", ",").replace("，", ",").split(",") if p.strip()]
        for part in title_parts:
            if len(part) >= 2 and part in query_lower:
                score += 4
                break  # 一个节点只计一次反向匹配

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
