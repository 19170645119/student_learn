"""
画像构建Agent - 流式输出 + RAG + 跨会话记忆
"""
from core.llm_service import chat_stream as llm_chat_stream, chat as llm_chat
from core.rag import build_rag_context
import json

SYSTEM_PROMPT = """【任务】与学生对话，提取6个维度构建学习画像。每个维度值控制在50字以内，写核心关键词。

【维度定义-勿混淆】
1. knowledge_base（知识基础）：已有知识储备，如"Python基础、线性代数"。不要写学习方式或目标。
2. cognitive_style（认知风格）：信息接收偏好，如"视觉型、动手型、听觉型、阅读型"。不要写学习节奏。
3. learning_goal（学习目标）：想达成什么，如"期末考试、考研、参加竞赛、找工作"。不要写兴趣方向。
4. error_prone（易错点）：常出问题的环节，如"数学公式推导、代码调试、环境配置"。
5. learning_pace（学习节奏）：学习速度，如"快速浏览、稳扎稳打、先快后深"。不要写认知风格。
6. interest_direction（兴趣方向）：对什么领域感兴趣，如"计算机视觉、NLP、强化学习"。不要写目标。

【输出铁律】回复最后一行必须且只能是：
:::JSON{"knowledge_base":"值","cognitive_style":"值","learning_goal":"值","error_prone":"值","learning_pace":"值","interest_direction":"值","completed":false,"message_summary":"20字摘要","memory_save":[{"key":"键","value":"值"}],"memory_use":[]}:::

【示例】
学生：我学过Python，喜欢看视频+动手，想通过期末，对CV感兴趣
回复：
明白了！你喜欢视频+动手的方式学习，目标是期末考过，对计算机视觉感兴趣。还有什么其他情况想分享吗？
:::JSON{"knowledge_base":"Python基础","cognitive_style":"视觉型+动手型","learning_goal":"期末考试","error_prone":"","learning_pace":"","interest_direction":"计算机视觉","completed":false,"message_summary":"有Python基础，视觉动手型，目标期末","memory_save":[],"memory_use":[]}:::

记住：JSON最后一行的值要精确、简短，不要跨维度混入信息。
"""


async def run_profile_agent_stream(user_message: str, current_profile: dict, chat_history: list, memories: list = None, all_history: list = None):
    """流式画像对话 + RAG + 综合所有会话记忆"""

    profile_str = json.dumps(current_profile, ensure_ascii=False) if current_profile else "{}"

    # RAG检索
    rag_context = await build_rag_context(user_message, top_k=3)

    # 构建记忆上下文
    memory_context = ""
    if memories:
        memory_lines = ["【长期记忆 - 跨会话信息】"]
        for m in memories[-10:]:
            memory_lines.append(f"- {m.get('key','')}: {m.get('value','')}")
        memory_context = "\n".join(memory_lines)

    messages = [
        {"role": "system", "content": SYSTEM_PROMPT},
        {"role": "system", "content": f"当前已获取的画像信息：{profile_str}"},
    ]
    if memory_context:
        messages.append({"role": "system", "content": memory_context})

    # 综合所有历史对话作为画像分析依据
    if all_history:
        history_summary = []
        for m in all_history[-30:]:  # 最近30条
            role = "学生" if m.get("role") == "user" else "AI"
            content_preview = m.get("content", "")[:200]
            if content_preview.strip():
                history_summary.append(f"[{role}]: {content_preview}")
        if history_summary:
            all_ctx = "【综合历史对话摘要（用于画像分析）】\n" + "\n".join(history_summary)
            messages.append({"role": "system", "content": all_ctx})

    if rag_context:
        messages.append({"role": "system", "content": rag_context})

    for msg in chat_history[-10:]:
        messages.append(msg)
    messages.append({"role": "user", "content": user_message})

    full_text = ""
    async for chunk in llm_chat_stream(messages):
        if chunk.get("done"):
            full_text = chunk.get("full_text", full_text)
            break
        yield {"type": "token", "text": chunk.get("text", "")}

    # 解析响应
    profile_update = {}
    completed = False
    memory_updates = {}
    message_summary = ""

    if ":::JSON" in full_text:
        try:
            json_str = full_text.split(":::JSON")[1].split(":::")[0]
            print(f"[Agent] JSON extracted: {json_str[:200]}")
            data = json.loads(json_str)
            profile_update = {k: v for k, v in data.items() if k not in ("completed", "memory_save", "memory_use", "message_summary") and v and isinstance(v, str)}
            completed = data.get("completed", False)
            message_summary = data.get("message_summary", "")
            for item in data.get("memory_save", []):
                if isinstance(item, dict) and "key" in item:
                    memory_updates[item["key"]] = item["value"]
            full_text = full_text.split(":::JSON")[0].strip()
            print(f"[Agent] JSON parsed: profile_update={profile_update}")
        except (json.JSONDecodeError, IndexError) as e:
            print(f"[Agent] JSON parse error: {e}")
    else:
        # 兜底：追加一次结构化提取调用
        print("[Agent] No JSON marker, launching secondary extraction call...")
        extract_prompt = """根据对话内容，提取学生画像。只返回JSON。

字段说明：
- knowledge_base: 已有知识（如"Python基础、线性代数"），不要写学习方式
- cognitive_style: 认知偏好（如"视觉型"、"动手型"、"听觉型"），不要写学习节奏
- learning_goal: 具体目标（如"期末考试"、"考研"），不要写兴趣方向
- error_prone: 容易出错的环节（如"公式推导"、"代码调试"）
- learning_pace: 学习速度偏好（如"快速浏览"、"稳扎稳打"、"先快后深"），不要写认知风格
- interest_direction: 感兴趣的领域（如"计算机视觉"、"NLP"），不要写目标
- message_summary: 20字以内的摘要
- memory_save: 值得记住的事实 [{"key":"简短键名","value":"事实值"}]

每个维度值控制在50字以内，写最核心的关键词。

对话：
"""
        context_text = []
        for m in messages[-8:]:  # 最近8条消息
            role = "学生" if m["role"] == "user" else "AI"
            ctx = m.get("content", "")[:300]
            if ctx.strip():
                context_text.append(f"[{role}]: {ctx}")
        context_text.append(f"[AI最后回复]: {full_text[-500:]}")
        
        extract_prompt += "\n".join(context_text)
        
        try:
            result = await llm_chat([{"role": "user", "content": extract_prompt}])
            print(f"[Agent] Extraction result: {result[:300]}")
            # 尝试从结果中提取JSON
            if "{" in result and "}" in result:
                json_start = result.index("{")
                json_end = result.rindex("}") + 1
                json_str = result[json_start:json_end]
                data = json.loads(json_str)
                profile_update = {k: v for k, v in data.items() if k not in ("completed", "memory_save", "memory_use", "message_summary") and v and isinstance(v, str)}
                message_summary = data.get("message_summary", "")
                for item in data.get("memory_save", []):
                    if isinstance(item, dict) and "key" in item:
                        memory_updates[item["key"]] = item["value"]
                print(f"[Agent] Secondary extraction success: profile_update={profile_update}")
        except Exception as e:
            print(f"[Agent] Secondary extraction failed: {e}")


    yield {
        "type": "done",
        "message": full_text,
        "message_summary": message_summary,
        "profile_update": profile_update,
        "memory_updates": memory_updates,
        "completed": completed,
    }
