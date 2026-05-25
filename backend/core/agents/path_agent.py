"""学习路径规划Agent - RAG检索增强"""
from core.llm_service import chat as llm_chat
from core.rag import build_rag_context
import json

SYSTEM_PROMPT = """你是一个学习路径规划专家。请根据学生的画像、课程知识结构和知识库内容，规划个性化的学习路径。

要求：
1. 分析知识节点的前置依赖关系
2. 根据学生的知识基础调整起点
3. 根据兴趣方向优先推荐相关章节
4. 根据学习节奏调整进度
5. 参考知识库内容确保路径合理

输出JSON格式：
```json
{
  "path_nodes": [
    {"node_id": 1, "order": 1, "title": "节点标题", "reason": "推荐理由", "resource_types": ["doc", "mindmap", "quiz"]}
  ],
  "summary": "路径总结说明"
}
```
"""

async def generate_learning_path(profile: dict, knowledge_nodes: list) -> dict:
    profile_str = json.dumps(profile, ensure_ascii=False)
    nodes_str = json.dumps([{"id": n.id, "title": n.title, "parent_id": n.parent_id,
                             "level": str(n.level) if hasattr(n, 'level') else "", "order": n.order_num}
                            for n in knowledge_nodes], ensure_ascii=False)

    # RAG检索：根据兴趣方向检索相关内容
    interest = profile.get("interest_direction", "")
    rag_context = ""
    if interest:
        rag_context = await build_rag_context(interest, top_k=5)

    user_prompt = f"学生画像：{profile_str}\n\n课程知识结构：{nodes_str}"
    if rag_context:
        user_prompt += f"\n\n{rag_context}"

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
        return {"path_nodes": [], "summary": "生成失败，请重试"}
