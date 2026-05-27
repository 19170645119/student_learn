"""练习题目生成Agent - 混合模式：题库 + LLM"""
from core.openai_service import chat as llm_chat
from core.rag import build_chapter_rag, build_rag_context
from models import AsyncSessionFactory
from repository.question_bank_repo import QuestionBankRepository
import json


SYSTEM_PROMPT = """你是一位资深考试命题专家。请严格基于提供的知识内容，生成指定数量和难度的题目。

【难度标准】
- easy：基础概念记忆，直接可从内容中找到答案
- medium：理解与应用，需要联系多个知识点
- hard：综合分析，需要深度思考和推理

【题目类型与格式】输出严格JSON数组，不要包裹在代码块中：
[
  {"type":"choice","question":"...","options":["A. ...","B. ...","C. ...","D. ..."],"answer":"B","explanation":"..."},
  {"type":"truefalse","question":"...","answer":true,"explanation":"..."},
  {"type":"fillblank","question":"...（用___标记空缺）","answer":"正确答案","explanation":"..."},
  {"type":"shortanswer","question":"...","reference_answer":"参考答案要点","explanation":"评分要点：..."}
]

【出题原则】
- type只能是 choice/truefalse/fillblank/shortanswer
- answer字段：choice填选项字母，truefalse填true/false，fillblank填答案文本，shortanswer不需answer字段
- 每个题目必须有 explanation，解释为什么对/错
- 选择题的干扰项要有迷惑性但不明显错误
- 填空题的空缺应是关键概念，答案唯一
- 不要编造知识内容中没有的信息
- 【铁律】如果用户指定了题型（choice/truefalse/fillblank/shortanswer），必须100%只生成该类型题目，绝对不要混入其他类型。例如指定choice就只出选择题，不要出现任何填空/判断/简答
- 默认题目类型分布：约40%选择、20%判断、20%填空、20%简答
- 仅输出JSON数组，不要任何额外文字
"""


async def generate_quiz(
    chapter_title: str,
    chapter_content: str = "",
    chapter_id: int = None,
    difficulty: str = "medium",
    count: int = 5,
    profile: dict = None,
    question_type: str = None,
) -> list:
    # Step 1: Try question bank first (with optional type filter)
    bank_questions = []
    need_count = count

    if chapter_id:
        async with AsyncSessionFactory() as session:
            async with session.begin():
                repo = QuestionBankRepository(session)
                bank_questions = await repo.random_sample(chapter_id, difficulty, count)
                need_count = count - len(bank_questions)

    # Step 2: LLM generate remaining if needed
    llm_questions = []
    if need_count > 0:
        rag_content = chapter_content
        if chapter_id:
            full = await build_chapter_rag(chapter_id)
            if full:
                rag_content = full

        if not rag_content.strip():
            rag_content = f"关于「{chapter_title}」的基础知识介绍。"

        diff_hint = {"easy": "基础概念记忆题", "medium": "理解应用题", "hard": "综合分析题"}
        type_hint = ""
        if question_type:
            type_names = {"choice":"选择题","truefalse":"判断题","fillblank":"填空题","shortanswer":"简答题"}
            type_hint = f"""
指定题型：只生成{type_names.get(question_type, question_type)}，不要生成其他类型的题目。"""
        user_prompt = f"""主题：{chapter_title}
难度：{difficulty}（{diff_hint.get(difficulty, '')}）
生成数量：{need_count}道{type_hint}

参考内容：
{rag_content}"""

        messages = [
            {"role": "system", "content": SYSTEM_PROMPT},
            {"role": "user", "content": user_prompt},
        ]

        try:
            response = await llm_chat(messages)
            if "[" in response and "]" in response:
                start = response.index("[")
                end = response.rindex("]") + 1
                llm_questions = json.loads(response[start:end])
        except Exception as e:
            print(f"[QuizAgent] LLM error: {e}")

        # Step 3: Save new questions to bank
        if llm_questions and chapter_id:
            for q in llm_questions:
                q["chapter_id"] = chapter_id
                q["difficulty"] = difficulty
            try:
                async with AsyncSessionFactory() as session:
                    async with session.begin():
                        repo = QuestionBankRepository(session)
                        await repo.batch_insert(llm_questions)
                        await session.commit()
            except Exception as e:
                print(f"[QuizAgent] Bank save error: {e}")

    # Merge and return
    result = []
    for q in bank_questions:
        result.append({
            "id": q.id, "type": q.type, "difficulty": q.difficulty,
            "question": q.question, "options": q.options,
            "answer": q.answer, "explanation": q.explanation,
        })
    for q in llm_questions:
        q.pop("chapter_id", None)
        q.pop("difficulty", None)
        result.append(q)

    return result
