# -*- coding: utf-8 -*-
"""代码实操案例 Agent — RAG 检索增强 + LLM 生成可运行代码"""
import json, re
from core.openai_service import chat as llm_chat, chat_stream as llm_chat_stream
from core.rag import build_chapter_rag, build_rag_context


SYSTEM_PROMPT = """你是一位资深编程讲师兼算法竞赛教练。请根据提供的知识内容，生成一份完整的代码实操学习案例。

【输出格式铁律】只返回纯 JSON，不要包裹在 ```json ``` 中，不要任何额外文字。JSON 中的所有换行用 \\n 表示：

{
  "language": "python",
  "title": "快速排序算法",
  "difficulty": "medium",
  "problem": {
    "statement": "实现快速排序算法，对整数数组进行升序排列。\\n\\n快速排序的核心思想是分治法：选择一个基准元素，将数组分为小于基准和大于基准的两部分，然后递归排序。",
    "input_spec": "输入: arr (List[int]) — 待排序的整数数组",
    "output_spec": "输出: List[int] — 升序排列后的数组",
    "constraints": ["1 <= len(arr) <= 10^5", "-10^9 <= arr[i] <= 10^9"]
  },
  "examples": [
    {"input": "[3, 1, 4, 1, 5, 9, 2, 6]", "output": "[1, 1, 2, 3, 4, 5, 6, 9]", "explanation": "标准示例，包含重复元素"},
    {"input": "[1]", "output": "[1]", "explanation": "单元素边界情况"}
  ],
  "approach": {
    "thinking": "分治思想三步走：\\n1. 选择基准（pivot）— 选中间元素避免最坏情况\\n2. 分区（partition）— 小于基准放左边，大于放右边，等于放中间\\n3. 递归 — 对左右子数组分别快排，最后拼接",
    "steps": ["选择基准元素（建议选中间位置，避免已排序数组退化为O(n^2)）", "遍历数组，将元素分别放入left/middle/right三个列表", "递归调用quick_sort对left和right排序", "拼接 left + middle + right 得到结果"],
    "tip": "Python用列表推导式可以一行完成分区，但注意这会创建新列表而非原地排序"
  },
  "starter_code": "def quick_sort(arr):\\n    # TODO: 实现快速排序\\n    # 1. 处理基线条件\\n    # 2. 选择基准元素\\n    # 3. 分区\\n    # 4. 递归排序并返回\\n    pass",
  "solution": {
    "code": "def quick_sort(arr):\\n    if len(arr) <= 1:\\n        return arr\\n    pivot = arr[len(arr) // 2]\\n    left = [x for x in arr if x < pivot]\\n    middle = [x for x in arr if x == pivot]\\n    right = [x for x in arr if x > pivot]\\n    return quick_sort(left) + middle + quick_sort(right)",
    "line_explanation": {"1": "函数定义，接收列表参数", "2-3": "基线条件：长度<=1时直接返回（已排序）", "4": "选择中间位置的元素作为基准", "5": "列表推导式：筛选所有小于基准的元素", "6": "筛选等于基准的元素（处理重复值）", "7": "筛选大于基准的元素", "8": "递归排序左右子数组，拼接结果"},
    "time_complexity": "O(n log n) 平均情况，O(n^2) 最坏情况（每次选到最小/最大元素）",
    "space_complexity": "O(n) — 创建新列表而非原地排序，每层递归需要额外空间"
  },
  "common_mistakes": [
    {"mistake": "总是选第一个元素作为基准", "fix": "选中间元素或随机选择，避免已排序数组导致O(n^2)", "example": "arr = [1,2,3,4,5] 时选arr[0]每次只能排除一个元素"},
    {"mistake": "忘记处理重复元素", "fix": "将等于基准的元素单独放入middle列表", "example": "arr = [3,3,3] 时如果只分left/right会死循环"},
    {"mistake": "递归深度过大导致栈溢出", "fix": "Python默认递归深度约1000，超大数据集考虑用迭代+栈实现"}
  ],
  "practice": [
    {"title": "原地快速排序", "description": "修改代码实现原地排序版本（in-place），不创建新列表，使用双指针交换元素"},
    {"title": "三路快速排序", "description": "当数组中有大量重复元素时，实现三路快排（< pivot, == pivot, > pivot）来优化性能"}
  ]
}

【字段说明】
- difficulty: "easy"/"medium"/"hard"
- problem: 题目描述，必须包含 statement + input_spec + output_spec + constraints
- examples: 2-3 个测试用例，各含 input/output/explanation
- approach: thinking（思路简述）+ steps（分步指导）+ tip（小技巧，可选）
- starter_code: 脚手架代码，关键逻辑用 # TODO 和 pass 留空，函数签名保持完整
- solution.code: 完整的、可直接运行的答案代码
- solution.line_explanation: 行号→解释，用"1"或"2-3"格式
- common_mistakes: 2-3 个常见错误，各含 mistake/fix/example
- practice: 2 道变体练习，各含 title/description

【要求】
1. 严格按 JSON 格式输出，code 中的换行用 \\n
2. starter_code 和 solution.code 是不同的！前者的核心逻辑留空
3. 所有字段都必须填写，没有内容的填空字符串""或空数组[]
4. 基于提供的知识内容，不要编造不存在的信息
"""




def _detect_language(user_query: str = "", extra: dict = None) -> str:
    """从用户输入中检测目标编程语言"""
    if extra and extra.get("language"):
        return extra["language"].lower()

    if not user_query:
        return "python"

    lang_map = {
        "python": ["python", "py", "Python"],
        "java": ["java", "Java"],
        "cpp": ["c++", "C++", "cpp", "CPP"],
        "javascript": ["javascript", "JavaScript", "js", "JS"],
        "go": ["go", "Go", "golang", "Golang"],
        "rust": ["rust", "Rust"],
        "typescript": ["typescript", "TypeScript", "ts", "TS"],
    }

    for lang, keywords in lang_map.items():
        for kw in keywords:
            if kw in user_query:
                return lang

    return "python"


def _sanitize_json(raw: str) -> str:
    """清理 LLM 响应中的非法 JSON 字符"""
    # Remove ASCII control characters except tab, newline, carriage return
    cleaned = re.sub(r"[\x00-\x08\x0b\x0c\x0e-\x1f\x7f]", "", raw)
    # Escape backslashes in code blocks (LLM may output raw backslashes)
    return cleaned


def _safe_parse_json(text: str) -> dict:
    """安全解析 JSON，处理常见的 LLM 输出格式问题（真实换行在 JSON 字符串中）"""
    text = _sanitize_json(text)

    # Try to extract JSON from markdown code blocks
    code_block_match = re.search(r"```(?:json)?\s*(\{.*?\})\s*```", text, re.DOTALL)
    if code_block_match:
        text = code_block_match.group(1)

    # Try to find bare JSON
    json_match = re.search(r"\{.*\}", text, re.DOTALL)
    if json_match:
        text = json_match.group()

    # Approach 1: direct parse
    try:
        return json.loads(text)
    except json.JSONDecodeError:
        pass

    # Approach 2: escape newlines ONLY within JSON string values
    # Match "key": "value" and escape newlines inside the value
    def escape_newlines_in_values(s):
        # Find all quoted strings and escape newlines within them
        result = []
        i = 0
        in_string = False
        string_char = None
        escape_next = False
        while i < len(s):
            c = s[i]
            if escape_next:
                result.append(c)
                escape_next = False
                i += 1
                continue
            if not in_string:
                if c in ('"', "'"):
                    in_string = True
                    string_char = c
                result.append(c)
            else:
                if c == '\\':
                    escape_next = True
                    result.append(c)
                elif c == string_char:
                    in_string = False
                    result.append(c)
                elif c == '\n':
                    result.append('\\n')
                elif c == '\r':
                    if i + 1 < len(s) and s[i + 1] == '\n':
                        result.append('\\n')
                        i += 1  # skip the \n
                    else:
                        result.append('\\n')
                elif c == '\t':
                    result.append('\\t')
                else:
                    result.append(c)
            i += 1
        return ''.join(result)

    try:
        escaped = escape_newlines_in_values(text)
        return json.loads(escaped)
    except json.JSONDecodeError as e:
        print(f"[CodeAgent] JSON parse error after escaping: {e}")
        print(f"[CodeAgent] raw[:300]: {text[:300]}")
        raise


async def generate_code(
    chapter_title: str = "",
    chapter_content: str = "",
    chapter_id: int = None,
    profile: dict = None,
    user_query: str = None,
    extra: dict = None,
) -> str:
    """生成代码实操案例"""
    language = _detect_language(user_query, extra)

    # RAG 检索
    rag_content = chapter_content
    if chapter_id:
        full = await build_chapter_rag(chapter_id)
        if full:
            rag_content = full
    if user_query:
        extra_rag = await build_rag_context(user_query, top_k=5)
        if extra_rag:
            rag_content = (rag_content + "\n\n" + extra_rag) if rag_content else extra_rag

    user_prompt = "请为主题「" + (user_query or chapter_title) + "」生成一份 " + language + " 语言的代码实操案例。\n\n"
    user_prompt += "目标语言：" + language + "\n\n"

    if rag_content:
        user_prompt += "知识内容参考：\n" + rag_content[:3000] + "\n\n"

    if profile:
        profile_parts = []
        if profile.get("interest_direction"):
            profile_parts.append("兴趣方向：" + profile["interest_direction"])
        if profile.get("knowledge_base"):
            profile_parts.append("知识基础：" + profile["knowledge_base"])
        if profile_parts:
            user_prompt += "学生画像：\n" + "\n".join(profile_parts) + "\n\n"

    user_prompt += "请生成代码实操案例的 JSON。"

    try:
        response = await llm_chat([
            {"role": "system", "content": SYSTEM_PROMPT},
            {"role": "user", "content": user_prompt},
        ])

        data = _safe_parse_json(response)
        data["language"] = data.get("language", language)
        data.setdefault("title", user_query or chapter_title)
        data.setdefault("explanation", "")
        data.setdefault("code", "")
        data.setdefault("line_notes", {})
        data.setdefault("example_output", "")
        data.setdefault("time_complexity", "")
        data.setdefault("space_complexity", "")
        return json.dumps(data, ensure_ascii=False)

    except Exception as e:
        print(f"[CodeAgent] Error: {e}")
        return json.dumps({
            "language": language,
            "title": user_query or chapter_title,
            "difficulty": "medium",
            "problem": {"statement": "", "input_spec": "", "output_spec": "", "constraints": []},
            "examples": [],
            "approach": {"thinking": "", "steps": [], "tip": ""},
            "starter_code": "",
            "solution": {"code": "# 生成失败: " + str(e), "line_explanation": {}, "time_complexity": "", "space_complexity": ""},
            "common_mistakes": [],
            "practice": [],
        }, ensure_ascii=False)


async def generate_code_stream(
    chapter_title: str = "",
    chapter_content: str = "",
    chapter_id: int = None,
    profile: dict = None,
    user_query: str = None,
    extra: dict = None,
):
    """流式生成代码实操案例"""
    language = _detect_language(user_query, extra)

    # RAG 检索
    rag_content = chapter_content
    if chapter_id:
        full = await build_chapter_rag(chapter_id)
        if full:
            rag_content = full
    if user_query:
        extra_rag = await build_rag_context(user_query, top_k=5)
        if extra_rag:
            rag_content = (rag_content + "\n\n" + extra_rag) if rag_content else extra_rag

    user_prompt = "请为主题「" + (user_query or chapter_title) + "」生成一份 " + language + " 语言的代码实操案例。\n\n"
    user_prompt += "目标语言：" + language + "\n\n"
    if rag_content:
        user_prompt += "知识内容参考：\n" + rag_content[:3000] + "\n\n"
    user_prompt += "请生成代码实操案例的 JSON。"

    yield {"status": "generating", "text": "正在生成 " + language.upper() + " 代码实操案例...\n\n"}

    full_text = ""
    try:
        async for chunk in llm_chat_stream([
            {"role": "system", "content": SYSTEM_PROMPT},
            {"role": "user", "content": user_prompt},
        ]):
            full_text += chunk
            yield {"status": "generating", "text": chunk}
    except Exception as e:
        yield {"status": "done", "text": "\n\n生成失败: " + str(e), "result": {"error": str(e)}}
        return

    # 解析最终 JSON
    try:
        data = _safe_parse_json(full_text)
        data["language"] = data.get("language", language)
        data.setdefault("title", user_query or chapter_title)
        data.setdefault("explanation", "")
        data.setdefault("code", "")
        data.setdefault("line_notes", {})
        data.setdefault("example_output", "")
        data.setdefault("time_complexity", "")
        data.setdefault("space_complexity", "")
        yield {"status": "done", "text": "", "result": data}
    except Exception as e:
        yield {"status": "done", "text": "", "result": {"error": str(e)}}
