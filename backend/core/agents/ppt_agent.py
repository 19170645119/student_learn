"""PPT生成Agent - 两段式生成：骨架 + 逐页扩充"""
from core.openai_service import chat as llm_chat, chat_stream as llm_chat_stream
from core.rag import build_chapter_rag, build_rag_context
import json, asyncio

SYSTEM_PROMPT = "你是教学PPT设计师，只输出JSON。"

SKELETON_PROMPT = """请为主题生成8-12页PPT骨架JSON。只需要page/title/layout/bullets/key_point，其他字段留空。

布局按顺序:
1. title_slide: 标题+Hook问题(严禁"目录"!)
2-3. title_content: 为什么学+核心概念
4-6. title_content/diagram/table: 主体讲解(必须穿插1个case_study和1个data_highlight)
7. audience_question: 互动提问
8. two_column: 对比分析
9-12. summary: 总结+行动建议

输出骨架JSON:
{"title":"...","slides":[{"page":1,"title":"...","layout":"title_slide","bullets":["Hook问题"],"key_point":"..."},...]}"""


def _safe_parse_json(text):
    if "{" not in text:
        return None
    strategies = [(text.index("{"), text.rindex("}") + 1)]
    last = text.rfind('"}')
    if last > 0:
        strategies.append((text.index("{"), last + 2))
    for start, end in strategies:
        try:
            return json.loads(text[start:end])
        except (json.JSONDecodeError, ValueError, IndexError):
            continue
    return None


async def _gen_elaboration(title, bullets, rag, topic):
    context = "\n".join(f"- {b}" for b in bullets[:3]) if bullets else title
    prompt = (
        f"用100-200字通俗讲解以下概念，面向大学生。只输出讲解文字，不要标题:\n\n"
        f"主题: {topic}\n标题: {title}\n要点: {context}\n参考: {rag[:800]}"
    )
    try:
        result = await llm_chat([{"role": "user", "content": prompt}])
        text = result.strip()
        if len(text) > 20:
            return {"elaboration": text}
    except Exception:
        pass
    return {}


async def _expand_bullets(bullets, rag, topic):
    if not bullets:
        return {}
    joined = "\n".join(f"{i+1}. {b}" for i, b in enumerate(bullets))
    prompt = (
        f"将以下要点扩展为15-35字的完整解释句（主语+谓语+解释）。"
        f"保持编号，每行一句，只输出结果:\n\n{joined}"
    )
    try:
        result = await llm_chat([{"role": "user", "content": prompt}])
        lines = [l.strip() for l in result.strip().split("\n") if l.strip()]
        expanded = []
        for line in lines:
            for sep in [". ", "、", ") ", "） "]:
                idx = line.find(sep)
                if 0 < idx < 4:
                    line = line[idx + len(sep):]
                    break
            if len(line) >= 8:
                expanded.append(line)
        if len(expanded) >= len(bullets):
            return {"bullets": expanded[:len(bullets)]}
    except Exception:
        pass
    return {}


async def _gen_case_study(title, rag, topic):
    prompt = (
        f"为主题「{topic} - {title}」提供一个80-150字的真实应用案例。"
        f"包含: 案例名称、具体做法、关键成果。然后给一句洞察。"
        f"参考: {rag[:600]}\n\n"
        f"输出格式:\n案例: <内容>\n洞察: <一句话>"
    )
    try:
        result = await llm_chat([{"role": "user", "content": prompt}])
        text = result.strip()
        case_content = ""
        case_insight = ""
        for line in text.split("\n"):
            line = line.strip()
            if line.startswith("案例:") or line.startswith("案例："):
                case_content = line[3:].strip()
            elif line.startswith("洞察:") or line.startswith("洞察："):
                case_insight = line[3:].strip()
        if not case_content:
            case_content = text[:150]
        return {
            "case_title": title,
            "case_content": case_content,
            "case_insight": case_insight,
        }
    except Exception:
        return {}


async def _gen_data_highlight(title, rag, topic):
    prompt = (
        f"为主题「{topic} - {title}」提供2-3条关键数据或里程碑。"
        f"每条包含: 指标名、数值、简短说明。参考: {rag[:600]}\n\n"
        f'输出JSON数组: [{{"label":"指标","value":"数值","desc":"说明"}},...]'
    )
    try:
        result = await llm_chat([{"role": "user", "content": prompt}])
        text = result.strip()
        if "[" in text and "]" in text:
            arr = json.loads(text[text.index("["):text.rindex("]") + 1])
            if isinstance(arr, list) and len(arr) >= 2:
                return {"metrics": arr}
    except Exception:
        pass
    return {}


async def _gen_speaker_notes(slide, rag, topic):
    title = slide.get("title", "")
    bullets = slide.get("bullets", [])
    key = slide.get("key_point", "")
    context = " | ".join(bullets[:3]) if bullets else title
    prompt = (
        f"为以下PPT页写一段演讲备注(40-80字)，包含: 怎么讲、过渡句、预计用时。\n"
        f"标题: {title}\n要点: {context}\n核心: {key}\n\n只输出备注文字:"
    )
    try:
        result = await llm_chat([{"role": "user", "content": prompt}])
        text = result.strip()
        if len(text) > 15:
            return {"speaker_notes": text}
    except Exception:
        pass
    return {}


async def _enrich_slide(slide, rag, topic):
    layout = slide.get("layout", "")
    title = slide.get("title", "")
    bullets = slide.get("bullets", [])
    tasks = []

    # elaboration: 仅 title_content
    if layout == "title_content":
        tasks.append(_gen_elaboration(title, bullets, rag, topic))

    # bullet扩展: title_content + case_study + summary
    if layout in ("title_content", "case_study", "summary"):
        tasks.append(_expand_bullets(bullets, rag, topic))

    # 案例内容
    if layout == "case_study":
        tasks.append(_gen_case_study(title, rag, topic))

    # 数据指标
    if layout == "data_highlight":
        tasks.append(_gen_data_highlight(title, rag, topic))

    # speaker_notes: 所有页
    tasks.append(_gen_speaker_notes(slide, rag, topic))

    results = await asyncio.gather(*tasks)
    for r in results:
        if r:
            slide.update(r)
    return slide


async def _build_rag(chapter_title, chapter_content, chapter_id, profile, user_query):
    rag = chapter_content
    if chapter_id:
        full = await build_chapter_rag(chapter_id)
        if full:
            rag = full
    if user_query:
        extra = await build_rag_context(user_query, top_k=5)
        if extra:
            rag = rag + "\n\n" + extra if rag else extra
    if not rag.strip():
        rag = f"关于「{chapter_title}」的基础知识介绍。"
    if len(rag) > 2000:
        try:
            r = await llm_chat([{"role": "user", "content": f"将以下内容提炼为600字摘要(保留关键概念和数据):\n\n{rag[:4000]}"}])
            if r and len(r) > 20:
                rag = r
        except Exception:
            pass
    return rag


async def _fix_skeleton(skeleton, rag, topic):
    slides = skeleton.get("slides", [])
    for s in slides:
        if s.get("title", "") in ("目录", "目录"):
            s["title"] = f"为什么学{topic[:8]}？"
            s["layout"] = "title_content"
            s["bullets"] = [f"了解{topic}能解决什么实际问题"]
    layouts = [s.get("layout", "") for s in slides]
    if "case_study" not in layouts:
        for s in reversed(slides):
            if s.get("layout") == "title_content" and s.get("page", 0) > 3:
                s["layout"] = "case_study"
                s["title"] = f"案例: {topic}的实际应用"
                break
    if "data_highlight" not in layouts:
        for s in reversed(slides):
            if s.get("layout") == "title_content" and s.get("page", 0) > 4:
                s["layout"] = "data_highlight"
                s["title"] = f"关键数据: {topic}"
                break
    return skeleton


async def generate_ppt(
    chapter_title="", chapter_content="", chapter_id=None,
    profile=None, user_query=None, extra=None,
):
    rag = await _build_rag(chapter_title, chapter_content, chapter_id, profile, user_query)
    messages = [
        {"role": "system", "content": SYSTEM_PROMPT},
        {"role": "user", "content": f"{SKELETON_PROMPT}\n\n主题: {chapter_title}\n参考:\n{rag}"},
    ]
    result = await llm_chat(messages)
    skeleton = _safe_parse_json(result)
    if skeleton is None or "slides" not in skeleton:
        return result
    skeleton = await _fix_skeleton(skeleton, rag, chapter_title)
    slides = skeleton.get("slides", [])
    enriched = await asyncio.gather(*[_enrich_slide(s, rag, chapter_title) for s in slides])
    skeleton["slides"] = list(enriched)
    return json.dumps(skeleton, ensure_ascii=False)


async def generate_ppt_stream(
    chapter_title="", chapter_content="", chapter_id=None,
    profile=None, user_query=None, extra=None,
):
    rag = await _build_rag(chapter_title, chapter_content, chapter_id, profile, user_query)
    messages = [
        {"role": "system", "content": SYSTEM_PROMPT},
        {"role": "user", "content": f"{SKELETON_PROMPT}\n\n主题: {chapter_title}\n参考:\n{rag}"},
    ]
    full_text = ""
    async for chunk in llm_chat_stream(messages):
        if chunk.get("done"):
            full_text = chunk.get("full_text", full_text)
            break
        yield chunk

    skeleton = _safe_parse_json(full_text)
    if skeleton is None or "slides" not in skeleton:
        yield {"done": True, "full_text": full_text}
        return

    skeleton = await _fix_skeleton(skeleton, rag, chapter_title)
    slides = skeleton.get("slides", [])
    total = len(slides)
    enriched_slides = []
    for i, slide in enumerate(slides):
        yield {"done": False, "text": f"\n[正在优化第{i+1}/{total}页: {slide.get('title', '')[:20]}...]\n"}
        try:
            enriched_slides.append(await _enrich_slide(slide, rag, chapter_title))
        except Exception:
            enriched_slides.append(slide)
    skeleton["slides"] = enriched_slides
    yield {"done": True, "full_text": json.dumps(skeleton, ensure_ascii=False)}