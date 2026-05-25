"""资源对话Agent - 意图分析 + 知识点匹配"""
from core.llm_service import chat as llm_chat
from core.rag import search_knowledge
import json

SYSTEM_PROMPT = """你是学习资源推荐助手。根据学生请求分析意图，匹配知识库中知识点。

【输出格式-铁律】只返回JSON：
{"intent":"学生学习意图一句话","matched_nodes":[{"id":节点ID,"title":"节点标题","reason":"匹配理由"}],"suggested_types":["doc","mindmap","quiz","code","video"],"reply":"给学生的友好回复（建议学习什么、为什么）"}

资源类型可选: doc(文档), mindmap(导图), quiz(题库), code(代码), video(视频)
建议2-4个最匹配的知识节点。
"""

async def analyze_intent(user_message: str, profile: dict = None) -> dict:
    user_prompt = f"学生请求：{user_message}"
    if profile:
        user_prompt += f"\n学生画像：{json.dumps(profile, ensure_ascii=False)}"

    messages = [
        {"role": "system", "content": SYSTEM_PROMPT},
        {"role": "user", "content": user_prompt}
    ]
    
    try:
        response = await llm_chat(messages)
        if "{" in response and "}" in response:
            start = response.index("{")
            end = response.rindex("}") + 1
            return json.loads(response[start:end])
    except Exception as e:
        print(f"[ResourceChat] Error: {e}")
    
    # Fallback: keyword search
    results = await search_knowledge(user_message, top_k=3)
    profile_note = ""
    if profile:
        parts = []
        if profile.get("cognitive_style"): parts.append(f"认知风格: {profile['cognitive_style']}")
        if profile.get("knowledge_base"): parts.append(f"知识基础: {profile['knowledge_base']}")
        if profile.get("learning_pace"): parts.append(f"学习节奏: {profile['learning_pace']}")
        if parts: profile_note = "根据你的画像（" + " | ".join(parts) + "）为你个性化生成"
    return {
        "intent": user_message[:30],
        "matched_nodes": [{"id": r["id"], "title": r["title"], "reason": "关键词匹配"} for r in results],
        "suggested_types": ["doc", "mindmap", "quiz"],
        "reply": f"找到{len(results)}个相关知识点，请问需要生成哪些类型的资源？",
        "profile_note": profile_note
    }

async def recommend_by_profile(profile: dict, knowledge_nodes: list) -> list:
    """根据画像推荐下一步学习的知识点"""
    interest = profile.get("interest_direction", "")
    weakness = profile.get("error_prone", "")
    knowledge = profile.get("knowledge_base", "")
    
    scored = []
    for node in knowledge_nodes:
        score = 0
        title_lower = node.title.lower()
        if interest and any(w in title_lower for w in interest.replace("、"," ").split()):
            score += 3
        if weakness and any(w in title_lower for w in weakness.replace("、"," ").split()):
            score += 2
        if knowledge and any(w in title_lower for w in knowledge.replace("、"," ").split()):
            score -= 1  # 已掌握，降权
        if score > 0:
            scored.append({"id": node.id, "title": node.title, "score": score})
    
    scored.sort(key=lambda x: x["score"], reverse=True)
    return scored[:5]
