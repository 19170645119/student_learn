"""资源对话Agent - 意图分析 + 知识点匹配 + 画像驱动推荐"""
from core.openai_service import chat as llm_chat
from core.rag import build_rag_context
from models import AsyncSessionFactory
from models.learning_path import KnowledgeNode
from sqlalchemy import select
import json

SYSTEM_PROMPT = """你是学习资源推荐助手兼知识答疑老师。根据学生请求和画像判断意图：

【意图分类】
- chat: 学生闲聊、打招呼或提问非学习类问题
- generate: 学生表达学习意愿（想学/想了解/帮我学习/生成文档/教我），一律返回generate

【输出格式铁律】只返回JSON：
{"intent":"chat或generate","reply":"友好回复","matched_chapter":{"id":章节ID,"title":"章节标题"},"user_query":"学生想学的核心主题","suggested_action":"建议操作文字"}

【画像驱动推荐规则】根据学生画像智能推荐：
- interest_direction: 优先推荐兴趣领域相关章节
- error_prone: 重点推荐知识短板对应的章节（帮学生补弱）
- knowledge_base: 基础弱→推荐入门章节，基础好→推荐进阶章节
- learning_goal: 考试目标→推荐理论重点章节，项目/工作→推荐实践章节
- cognitive_style: 视觉型→推荐图表丰富的章节，动手型→推荐代码实训章节
- learning_pace: 快节奏→推荐核心精要章节，慢节奏→推荐详细讲解章节
- memory中的"专业""课程"信息辅助判断学生背景，匹配合适章节

【通用规则】
- 学生表达学习意愿 → intent:"generate"
- matched_chapter从可用章节中选最相关的填，完全无关时matched_chapter为null
- 即使matched_chapter为null，也要intent:"generate"
- 学生闲聊/问候 → intent:"chat"
- 回复要亲切鼓励，体现对学生的了解（引用画像信息），长度适中
"""


async def _get_all_chapters() -> list:
    async with AsyncSessionFactory() as session:
        async with session.begin():
            result = await session.execute(
                select(KnowledgeNode).where(KnowledgeNode.parent_id.is_(None)).order_by(KnowledgeNode.order_num)
            )
            return list(result.scalars().all())


async def resource_chat(user_message: str, profile: dict = None, memory: dict = None) -> dict:
    chapters = await _get_all_chapters()
    chapter_list = [{"id": c.id, "title": c.title} for c in chapters]

    rag_context = await build_rag_context(user_message, top_k=3)

    # 构建丰富的用户上下文
    user_prompt = f"学生请求：{user_message}\n\n可用知识章节：{json.dumps(chapter_list, ensure_ascii=False)}\n\n知识库相关内容：\n{rag_context}"

    if profile and any(profile.values()):
        profile_lines = []
        if profile.get("knowledge_base"):
            profile_lines.append(f"- 知识基础：{profile['knowledge_base']}")
        if profile.get("cognitive_style"):
            profile_lines.append(f"- 认知风格：{profile['cognitive_style']}")
        if profile.get("learning_goal"):
            profile_lines.append(f"- 学习目标：{profile['learning_goal']}")
        if profile.get("error_prone"):
            profile_lines.append(f"- 知识短板：{profile['error_prone']}")
        if profile.get("learning_pace"):
            profile_lines.append(f"- 学习节奏：{profile['learning_pace']}")
        if profile.get("interest_direction"):
            profile_lines.append(f"- 兴趣方向：{profile['interest_direction']}")
        if profile_lines:
            user_prompt += f"\n\n【学生画像】\n" + "\n".join(profile_lines)
            user_prompt += "\n请根据以上画像信息进行个性化推荐。"

    if memory:
        mem_items = [f"{k}={v}" for k, v in memory.items() if v]
        if mem_items:
            user_prompt += f"\n\n【学习记忆】{', '.join(mem_items)}"

    messages = [
        {"role": "system", "content": SYSTEM_PROMPT},
        {"role": "user", "content": user_prompt},
    ]

    try:
        response = await llm_chat(messages)
        if "{" in response and "}" in response:
            start = response.index("{")
            end = response.rindex("}") + 1
            data = json.loads(response[start:end])

            if data.get("matched_chapter") and data["matched_chapter"].get("id"):
                chap_id = data["matched_chapter"]["id"]
                found = next((c for c in chapters if c.id == chap_id), None)
                if found:
                    data["matched_chapter"]["title"] = found.title
                else:
                    data["matched_chapter"] = None

            if data.get("intent") == "generate" and not data.get("user_query"):
                data["user_query"] = user_message

            if data.get("intent") == "generate" and not data.get("suggested_action"):
                data["suggested_action"] = "可以为你生成一份学习文档"

            return data
    except Exception as e:
        print(f"[ResourceChat] LLM error: {e}")

    return {
        "intent": "chat",
        "reply": "你好！我是你的学习助手。可以问我知识问题，或者说'帮我学习XXX'来生成课程文档。",
        "matched_chapter": None,
        "user_query": None,
        "suggested_action": None,
    }