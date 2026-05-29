# -*- coding: utf-8 -*-
"""视频链接推荐 Agent — LLM 提炼关键词 + B站搜索 API"""
import json, re, math, time, httpx
from core.openai_service import chat as llm_chat

BILIBILI_SEARCH_URL = "https://api.bilibili.com/x/web-interface/search/all/v2"
BILIBILI_HEADERS = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
    "Referer": "https://www.bilibili.com",
}

KEYWORD_SYSTEM_PROMPT = """你是视频搜索关键词提炼专家。根据用户的学习需求，提炼1-3个最适合在B站搜索的学习视频关键词。

规则：
1. 关键词要精准、简短（2-8个字），适合搜索引擎
2. 去除"帮我找""我想学""视频"等冗余词
3. 优先保留核心主题词，如"深度学习""CNN""Python基础"
4. 可适当加"教程""入门""实战"等修饰词提升搜索质量
5. 输出为JSON数组字符串，如：["深度学习入门教程","神经网络实战"]

只输出JSON数组，不要其他内容。"""



def _parse_duration_seconds(duration_str: str) -> int:
    """解析 B站时长格式 'HH:MM:SS' 或 'MM:SS' 为秒数"""
    try:
        parts = duration_str.strip().split(":")
        if len(parts) == 3:
            return int(parts[0]) * 3600 + int(parts[1]) * 60 + int(parts[2])
        elif len(parts) == 2:
            return int(parts[0]) * 60 + int(parts[1])
        return 0
    except (ValueError, AttributeError):
        return 0


def _clean_html(text: str) -> str:
    """去除 HTML 标签（B站返回的 title 含 <em> 标签）"""
    return re.sub(r"<[^>]+>", "", text)


def _format_play_count(count) -> str:
    """格式化播放量"""
    try:
        n = int(count)
        if n >= 10000:
            return f"{n/10000:.1f}万"
        return str(n)
    except (ValueError, TypeError):
        return str(count or "0")


async def search_bilibili(keyword: str, count: int = 15) -> list:
    """搜索B站视频，返回原始列表，最多 count 条"""
    try:
        async with httpx.AsyncClient(timeout=10.0) as client:
            resp = await client.get(
                BILIBILI_SEARCH_URL,
                params={"keyword": keyword, "page": 1},
                headers=BILIBILI_HEADERS,
            )
            if resp.status_code != 200:
                print(f"[VideoLink] Bilibili HTTP {resp.status_code}: {resp.text[:200]}")
                return []

            data = resp.json()
            if data.get("code") != 0:
                print(f"[VideoLink] Bilibili API error: code={data.get('code')}")
                return []

            video_items = []
            for item in data.get("data", {}).get("result", []):
                if item.get("result_type") != "video":
                    continue
                for v in item.get("data", []):
                    video_items.append({
                        "title": _clean_html(v.get("title", "")),
                        "url": v.get("arcurl", ""),
                        "author": v.get("author", ""),
                        "play": _format_play_count(v.get("play", 0)),
                        "duration": v.get("duration", ""),
                        "bvid": v.get("bvid", ""),
                        # Raw fields for scoring
                        "_play_raw": int(v.get("play", 0)),
                        "_fav": int(v.get("favorites", 0)),
                        "_review": int(v.get("video_review", 0)),
                        "_danmaku": int(v.get("danmaku", 0)),
                        "_pubdate": int(v.get("pubdate", 0)) if v.get("pubdate") else 0,
                        "_duration_str": v.get("duration", "0:00"),
                    })
            return video_items[:count]
    except Exception as e:
        print(f"[VideoLink] Search error: {e}")
        return []



# ---- 标题党关键词 ----
CLICKBAIT_WORDS = ["速通", "爆炸", "最好", "全网最", "一口气", "三天", "3天", "绝了", "封神", "天坑"]
QUALITY_WORDS = ["官方", "公认", "配套", "课件", "代码", "实战", "动手"]


def _score_video(video: dict) -> float:
    """综合评分，满分 ~100"""
    play = video.get("_play_raw", 0)
    fav = video.get("_fav", 0)
    review = video.get("_review", 0)
    danmaku = video.get("_danmaku", 0)
    pubdate = video.get("_pubdate", 0)
    duration_sec = _parse_duration_seconds(video.get("_duration_str", "0:00"))
    title = video.get("title", "")

    # ---- 硬过滤 ----
    if duration_sec < 30:
        return -1
    if play < 10:
        return -1

    # ---- 1. 收藏质量 (35%) ----
    if play > 0:
        fav_ratio = math.log10(fav + 1) / math.log10(play + 1)
    else:
        fav_ratio = 0
    score_fav = min(fav_ratio * 100, 100) * 0.35

    # ---- 2. 播放量 (30%) ----
    score_play = min(math.log10(play + 1) / 6 * 100, 100) * 0.30

    # ---- 3. 参与度 (15%) ----
    if play > 0:
        engagement = (review + danmaku) / play * 1000
    else:
        engagement = 0
    score_engage = min(engagement, 100) * 0.15

    # ---- 4. 时效性 (10%) ----
    now = int(time.time())
    if pubdate > 0:
        age_days = (now - pubdate) / 86400
        if age_days <= 365:
            score_time = 100 - (age_days / 365) * 70  # 1年内 100→30
        else:
            score_time = 30
    else:
        score_time = 50
    score_time *= 0.10

    # ---- 5. 标题质量 (10%) ----
    score_title = 100
    for word in CLICKBAIT_WORDS:
        if word in title:
            score_title -= 50
            break
    # 有优质标志词略微加分
    quality_hits = sum(1 for w in QUALITY_WORDS if w in title)
    score_title += quality_hits * 5
    score_title = max(0, min(score_title, 100)) * 0.10

    total = score_fav + score_play + score_engage + score_time + score_title
    return round(total, 1)


def _rank_videos(videos: list, top_n: int = 5) -> list:
    """过滤 + 评分 + 排序，返回 top_n"""
    scored = []
    for v in videos:
        s = _score_video(v)
        if s < 0:
            continue  # 硬过滤掉
        scored.append((s, v))

    scored.sort(key=lambda x: x[0], reverse=True)

    result = []
    for _, v in scored[:top_n]:
        # 清理评分用临时字段
        clean = {k: v for k, v in v.items() if not k.startswith("_")}
        result.append(clean)

    return result


async def _extract_keywords(user_query: str) -> list:

    """用 LLM 从用户需求中提炼搜索关键词"""
    try:
        response = await llm_chat([
            {"role": "system", "content": KEYWORD_SYSTEM_PROMPT},
            {"role": "user", "content": user_query},
        ])
        # 提取 JSON 数组
        match = re.search(r"\[.*?\]", response, re.DOTALL)
        if match:
            keywords = json.loads(match.group())
            if isinstance(keywords, list) and len(keywords) > 0:
                return keywords[:3]
    except Exception as e:
        print(f"[VideoLink] Keyword extraction error: {e}")

    # 降级：直接用 user_query 作为关键词
    clean = user_query.replace("帮我找", "").replace("我想学", "").replace("视频", "").replace("推荐", "").strip()
    return [clean] if clean else [user_query]


async def generate_video_links(
    chapter_title: str = "",
    chapter_content: str = "",
    chapter_id: int = None,
    profile: dict = None,
    user_query: str = None,
) -> str:
    """生成视频链接推荐，返回 JSON 字符串"""
    # 构建搜索 query
    search_query = user_query or chapter_title or ""
    if profile:
        interest = profile.get("interest_direction", "")
        if interest and interest not in search_query:
            search_query = f"{search_query} {interest}"

    # 提炼关键词
    keywords = await _extract_keywords(search_query)
    print(f"[VideoLink] Keywords: {keywords}")

    # 逐关键词搜索
    all_videos = []
    seen_bvids = set()
    for kw in keywords:
        videos = await search_bilibili(kw, count=10)
        for v in videos:
            if v["bvid"] not in seen_bvids:
                seen_bvids.add(v["bvid"])
                all_videos.append(v)

    # 质量评分排序，取前5个
    result_videos = _rank_videos(all_videos, top_n=5)

    result = {
        "videos": result_videos,
        "keyword": keywords[0] if keywords else search_query,
        "source": "bilibili",
    }
    return json.dumps(result, ensure_ascii=False)


async def generate_video_links_stream(
    chapter_title: str = "",
    chapter_content: str = "",
    chapter_id: int = None,
    profile: dict = None,
    user_query: str = None,
):
    """流式生成视频链接（SSE）"""
    yield {"status": "searching", "text": f"正在B站搜索「{user_query or chapter_title}」的相关视频...\n\n"}

    result_json = await generate_video_links(
        chapter_title=chapter_title,
        chapter_content=chapter_content,
        chapter_id=chapter_id,
        profile=profile,
        user_query=user_query,
    )

    data = json.loads(result_json)
    videos = data.get("videos", [])

    if not videos:
        yield {"status": "done", "text": "\n未找到相关视频，请尝试更具体的关键词。"}
        return

    yield {"status": "searching", "text": f"找到 {len(videos)} 个视频，正在整理...\n\n"}

    for i, v in enumerate(videos):
        card = f"**{i+1}. [{v['title']}]({v['url']})**\n"
        card += f"   UP主：{v['author']} | 播放：{v['play']} | 时长：{v['duration']}\n\n"
        yield {"status": "searching", "text": card}

    yield {"status": "done", "text": "", "result": data}
