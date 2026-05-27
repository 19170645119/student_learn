"""思维导图生成Agent - RAG检索增强，输出Mermaid语法"""
from core.openai_service import chat as llm_chat, chat_stream as llm_chat_stream
from core.rag import build_chapter_rag, build_rag_context


SYSTEM_PROMPT = """你是一位知识体系架构师。请根据提供的知识内容，生成一份结构清晰的Mermaid mindmap思维导图。

要求：
1. 仅输出 Mermaid mindmap 语法代码，不要包裹在代码块中，不要前后说明文字
2. 根节点用 root((主题)) 格式
3. 分支层级2-3层，每个分支3-6个子节点
4. 使用形状变体丰富层次：第1层((云朵)), 第2层[矩形], 第3层普通文字
5. 内容覆盖：核心概念、关键方法、典型应用、重要原理
6. 每个节点尽量控制在10个字以内
7. 严格基于提供的知识内容，不要编造

输出示例：
mindmap
  root((机器学习))
    [监督学习]
      线性回归
      决策树
      支持向量机
    [无监督学习]
      K-Means聚类
      主成分分析
    [强化学习]
      Q-Learning
      策略梯度


【画像驱动模式】
当没有具体章节内容，但有学生画像时，根据画像信息生成综合学习规划思维导图：
- 根节点为学生的学习方向总结
- 第一层分支：兴趣领域、知识短板、学习目标、基础知识
- 第二层展开具体方向和建议
- 参考画像数据生成个性化内容
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
        if profile and any(profile.values()):
            profile_parts = []
            if profile.get('interest_direction'): profile_parts.append(f"兴趣方向：{profile['interest_direction']}")
            if profile.get('error_prone'): profile_parts.append(f"知识短板：{profile['error_prone']}")
            if profile.get('learning_goal'): profile_parts.append(f"学习目标：{profile['learning_goal']}")
            if profile.get('knowledge_base'): profile_parts.append(f"知识基础：{profile['knowledge_base']}")
            if profile.get('cognitive_style'): profile_parts.append(f"认知风格：{profile['cognitive_style']}")
            if profile.get('learning_pace'): profile_parts.append(f"学习节奏：{profile['learning_pace']}")
            rag_content = "学生画像信息：\n" + "\n".join(profile_parts)
        else:
            rag_content = f"关于「{chapter_title}」的基础知识介绍。"

    user_prompt = f"\u8bf7\u4e3a\u4ee5\u4e0b\u4e3b\u9898\u751f\u6210\u601d\u7ef4\u5bfc\u56fe\uff1a\n\n\u4e3b\u9898\uff1a{chapter_title}\n\n\u53c2\u8003\u5185\u5bb9\uff1a\n{rag_content}"

    if profile:
        style_hint = (
            f"\n学生画像：知识基础={profile.get('knowledge_base', '')}，"
            f"认知风格={profile.get('cognitive_style', '')}，请据此调整导图深度和层次。"
        )
        user_prompt += style_hint

    return [
        {"role": "system", "content": SYSTEM_PROMPT},
        {"role": "user", "content": user_prompt},
    ]


async def generate_mindmap(
    chapter_title: str,
    chapter_content: str = "",
    chapter_id: int = None,
    profile: dict = None,
    user_query: str = None,
) -> str:
    messages = await _build_messages(chapter_title, chapter_content, chapter_id, profile, user_query)
    return await llm_chat(messages)


async def generate_mindmap_stream(
    chapter_title: str,
    chapter_content: str = "",
    chapter_id: int = None,
    profile: dict = None,
    user_query: str = None,
):
    messages = await _build_messages(chapter_title, chapter_content, chapter_id, profile, user_query)
    async for chunk in llm_chat_stream(messages):
        yield chunk
