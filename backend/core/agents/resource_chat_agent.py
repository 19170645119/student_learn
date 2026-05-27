"""资源对话Agent - 意图分析 + 知识点匹配 + 画像驱动推荐"""
from core.openai_service import chat as llm_chat
from core.rag import build_rag_context
from models import AsyncSessionFactory
from models.learning_path import KnowledgeNode
from sqlalchemy import select
import json

SYSTEM_PROMPT = """你是学习资源推荐助手兼知识答疑老师。根据学生请求和画像判断意图和资源类型。

【画像优先规则】当学生说“结合我的画像”“根据画像”“针对我的情况”等时，你必须：
1. 仔细分析学生画像中的 interest_direction（兴趣方向）、error_prone（知识短板）、learning_goal（学习目标）
2. 从可用章节中找到与画像最匹配的主题，而不是随机选择
3. 如果画像中某个方向明确（如兴趣方向=“深度学习”），则优先匹配该方向的章节
4. 如果画像中有知识短板，优先推荐短板相关章节（帮学生补弱）
5. reply中要明确说明“根据你的画像（兴趣方向=XX，知识短板=XX），推荐你学习YY”

【最重要规则：资源类型判断】
学生请求中只要出现以下任一关键词，必须设置 resource_type="mindmap"：
- "思维导图" "脑图" "导图" "知识图谱" "概念图"
- "梳理"配合知识内容（如"梳理XX"、"整理XX的知识"）
- "结构"配合知识内容（如"XX的知识结构"、"XX的结构"）
- "框架"配合知识内容（如"XX的知识框架"）
- "脉络" "体系" 配合知识内容（如"XX的知识脉络"）
- "总结"配合知识内容（如"总结XX"、"XX的知识点总结"）
- 明确请求"生成XX的思维导图/脑图" → resource_type="mindmap"，suggested_action="可以为你生成思维导图"

学生请求中出现以下任一关键词 → resource_type="quiz"：
- 含"出题"/"练习题"/"考试"/"测验"/"题库"/"刷题"/"题目"/"习题"/"试题" → resource_type="quiz"
- 学生说"选择题"/"单选题" → resource_type="quiz", extra.question_type="choice"，只出选择题
- 学生说"填空题" → resource_type="quiz", extra.question_type="fillblank"，只出填空题
- 学生说"判断题" → resource_type="quiz", extra.question_type="truefalse"，只出判断题
- 学生说"简答题"/"问答题" → resource_type="quiz", extra.question_type="shortanswer"，只出简答题
- "出几道"/"来几道"/"做几道" 后面紧跟题型词 → 严格设置question_type
- 若学生明确指定了题型，extra中必须设置question_type，且LLM出题时必须只生成该题型
- 明确请求"生成XX的练习题/考试题" → resource_type="quiz"，suggested_action="可以为你生成练习题"

其他情况 resource_type="doc"，suggested_action="可以为你生成一份学习文档"

【画像综合规划】
- 当学生说“结合画像”但没有指定具体主题时，matched_chapter可以为null
- user_query应总结画像核心信息，如“兴趣方向XX，知识短板YY，学习目标ZZ”
- 不要随机选择一个章节！画像综合规划时matched_chapter为null是正确的

【示例】
1. "强化学习的思维导图" → intent:"generate", resource_type:"mindmap", user_query:"强化学习"
2. "帮我生成深度学习的脑图" → intent:"generate", resource_type:"mindmap", user_query:"深度学习"
3. "梳理一下机器学习" → intent:"generate", resource_type:"mindmap", user_query:"机器学习"
4. "帮我学习Python" → intent:"generate", resource_type:"doc", user_query:"Python"
5. "什么是反向传播" → intent:"chat", resource_type:"doc"
6. "你好" → intent:"chat", resource_type:"doc"
7. "结合我的画像生成思维导图" → intent:"generate", resource_type:"mindmap", matched_chapter:null, user_query:"根据学生画像"
8. "帮我出5道深度学习的题" → intent:"generate", resource_type:"quiz", user_query:"深度学习", extra:{"count":5}
9. "出几道机器学习的选择题" → intent:"generate", resource_type:"quiz", user_query:"机器学习", extra:{"count":5,"question_type":"choice"}
10. "来几道Python的填空题" → intent:"generate", resource_type:"quiz", user_query:"Python", extra:{"count":5,"question_type":"fillblank"}

【意图分类】
- chat: 学生闲聊、打招呼或提问知识性问题
- generate: 学生表达学习/生成意愿（想学/想了解/帮我学习/生成/教我/梳理/总结/出题/做题/测验/考试/刷题/出几道/来几道）

【输出格式铁律】只返回纯JSON，不要任何额外文字：
{"intent":"chat或generate","reply":"友好回复","matched_chapter":{"id":章节ID,"title":"章节标题"},"user_query":"学生想学的核心主题","resource_type":"doc或mindmap或quiz","suggested_action":"建议操作文字","extra":{"count":题目数量,"question_type":"题型"}}

【画像驱动推荐规则】根据学生画像智能推荐：
- interest_direction: 优先推荐兴趣领域相关章节
- error_prone: 重点推荐知识短板对应的章节（帮学生补弱）
- knowledge_base: 基础弱→推荐入门章节，基础好→推荐进阶章节
- learning_goal: 考试目标→推荐理论重点章节，项目/工作→推荐实践章节
- cognitive_style: 视觉型→推荐图表丰富的章节，动手型→推荐代码实训章节
- learning_pace: 快节奏→推荐核心精要章节，慢节奏→推荐详细讲解章节

【通用规则】
- 学生表达学习/梳理/生成意愿 → intent:"generate"
- matched_chapter从可用章节中选最相关的填，完全无关时matched_chapter为null
- 即使matched_chapter为null，也要intent:"generate"，资源类型仍然按规则判断
- 回复要亲切鼓励，长度适中1-2句话"""


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
    # 检测用户是否要求画像驱动
    profile_keywords = ['结合画像', '根据画像', '我的画像', '针对我', '按我的']
    is_profile_driven = any(kw in user_message for kw in profile_keywords)

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
            if is_profile_driven:
                user_prompt += "\n\n【重要指令】学生要求结合画像推荐。请从上述画像中提取兴趣方向、知识短板、学习目标等信息，从可用章节中找到最匹配的主题。不要随机选择章节，必须基于画像数据。"
            else:
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

            if data.get("intent") == "generate" and not data.get("resource_type"):
                data["resource_type"] = "doc"

            if data.get("intent") == "generate" and not data.get("extra"):
                data["extra"] = {}

            if data.get("intent") == "generate" and not data.get("suggested_action"):
                rt = data.get("resource_type", "doc")
                if rt == "mindmap":
                    data["suggested_action"] = "可以为你生成思维导图"
                elif rt == "quiz":
                    data["suggested_action"] = "可以为你生成练习题"
                else:
                    data["suggested_action"] = "可以为你生成一份学习文档"

            return data
    except Exception as e:
        print(f"[ResourceChat] LLM error: {e}")

    return {
        "intent": "chat",
        "reply": "你好！我是你的学习助手。可以问我知识问题，或者说'帮我学习XXX'来生成课程文档。",
        "matched_chapter": None,
        "user_query": None,
        "resource_type": "doc",
        "extra": {},
        "suggested_action": None,
    }