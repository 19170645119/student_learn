# -*- coding: utf-8 -*-
import json
from core.omni_service import omni_chat, omni_tts
from core.rag import build_chapter_rag

SYSTEM_PROMPT = """你是一位教学动画导演。你必须严格按以下格式输出JSON，字段名不能改变：

{"title":"课程标题","scenes":[
  {"type":"title","text":"主标题","subtitle":"副标题","narration":"今天我们来学习..."},
  {"type":"text_reveal","title":"小节标题","bullets":["要点1","要点2"],"narration":"第一点..."},
  {"type":"code_walkthrough","code":"def example():\\n    pass","highlights":[[0,1]],"narration":"这段代码..."},
  {"type":"diagram","mermaid":"graph TD\\n  输入图像 --> 卷积层[卷积层\\n特征提取]\\n  卷积层 --> 池化层[池化层\\n降维压缩]\\n  池化层 --> 全连接层[全连接层\\n分类决策]\\n  全连接层 --> 输出[输出结果]","build_steps":2,"narration":"这张图..."},
  {"type":"compare","left_title":"A","left_items":["点1"],"right_title":"B","right_items":["点1"],"narration":"对比..."},
  {"type":"quiz_card","question":"CNN中卷积层的作用是？","options":["特征提取","分类输出","降维压缩","梯度更新"],"answer":0,"explanation":"卷积层通过卷积核在输入上滑动来提取局部特征","narration":"来测一下，卷积层的作用是什么？"},
  {"type":"summary","key_points":["要点1","要点2"],"narration":"总结..."}
]}

铁律：
1. 字段名完全一致：narration/bullets/code/mermaid/key_points/options/answer/explanation，绝不用content/description
2. 每个scene必须有narration（150-300字）
3. text_reveal的bullets是字符串数组
4. code_walkthrough的code是完整代码
5. diagram的mermaid必须使用有意义的节点标签如卷积层/池化层等中文术语禁止A/B/C/D占位符
6. quiz_card的options是4个字符串，answer是正确选项索引(0-3)
7. 6-12个场景，title开头summary结尾，关键知识点后穿插2-3个quiz_card测试理解
8. 只返回纯JSON，不要包裹```json```"""


def _normalize_scenes(scenes):
    for scene in scenes:
        content = scene.pop("content", None)
        if content and not scene.get("narration"):
            scene["narration"] = str(content)
        t = scene.get("type", "")
        if t == "text_reveal":
            if not scene.get("bullets") and content:
                scene["bullets"] = [b.strip() for b in str(content).splitlines() if b.strip()]
            scene.setdefault("title", "知识要点")
        if t == "code_walkthrough":
            if not scene.get("code") and content:
                scene["code"] = str(content)
            scene.setdefault("highlights", [[0, 5]])
        if t == "diagram":
            if not scene.get("mermaid") and content:
                scene["mermaid"] = str(content)
            scene.setdefault("build_steps", 2)
        if t == "compare":
            if not scene.get("left_items") and content:
                lines = [l.strip() for l in str(content).splitlines() if l.strip()]
                mid = len(lines) // 2
                scene["left_items"] = lines[:mid] if mid > 0 else ["项目1"]
                scene["right_items"] = lines[mid:] if mid < len(lines) else ["项目2"]
            scene.setdefault("left_title", "方面A")
            scene.setdefault("right_title", "方面B")
        if t == "quiz_card":
            if not scene.get("options") and content:
                lines = [l.strip() for l in str(content).splitlines() if l.strip()]
                if len(lines) >= 2:
                    scene["options"] = lines[:4] if len(lines) >= 4 else lines
                    scene["question"] = lines[0] if len(lines) > 0 else "请选择正确答案"
            scene.setdefault("options", ["选项A", "选项B", "选项C", "选项D"])
            scene.setdefault("question", "请选择正确答案")
            scene.setdefault("answer", 0)
            scene.setdefault("explanation", "这是正确答案的解释")
        if t == "summary":
            if not scene.get("key_points") and content:
                scene["key_points"] = [b.strip() for b in str(content).splitlines() if b.strip()]
        if not scene.get("narration"):
            scene["narration"] = str(content or "") if content else "请继续观看..."
    return scenes


async def generate_video_script(chapter_title, chapter_content="", chapter_id=None, profile=None, user_query=None, with_audio=True):
    rag_content = chapter_content
    if chapter_id:
        full = await build_chapter_rag(chapter_id)
        if full:
            rag_content = full
    if not rag_content.strip():
        rag_content = "关于" + chapter_title + "的基础知识介绍。"
    title = chapter_title if chapter_title else (user_query or "未知主题")
    messages = [
        {"role": "system", "content": SYSTEM_PROMPT},
        {"role": "user", "content": "主题：" + title + "\n参考内容：\n" + rag_content},
    ]
    response = await omni_chat(messages)
    print("[VideoAgent] Raw (first 200): " + str(response[:200]))
    script = None
    json_str = None
    if "{" in response and "}" in response:
        start = response.index("{")
        end = response.rindex("}") + 1
        json_str = response[start:end]
    elif "```json" in response:
        parts = response.split("```json", 1)[1].split("```", 1)
        if parts:
            json_str = parts[0].strip()
    if json_str:
        try:
            script = json.loads(json_str)
        except Exception as e:
            print("[VideoAgent] JSON parse error: " + str(e))
    if not script or "scenes" not in script or not script["scenes"]:
        script = {
            "title": title,
            "scenes": [
                {"type": "title", "text": title, "subtitle": "", "narration": "欢迎来到" + title + "的学习课程"},
                {"type": "text_reveal", "title": "核心要点", "bullets": [rag_content[:80] + "..."], "narration": rag_content[:200]},
                {"type": "summary", "key_points": ["感谢观看"], "narration": "本次教学动画播放完毕"},
            ],
        }
    script["scenes"] = _normalize_scenes(script["scenes"])
    print("[VideoAgent] Generated " + str(len(script["scenes"])) + " scenes")
    if with_audio:
        script["audio"] = {}
        for i, scene in enumerate(script["scenes"]):
            n = scene.get("narration", "")
            if n and len(n) > 5:
                audio_b64 = await omni_tts(n)
                script["audio"]["scene_" + str(i)] = audio_b64 if audio_b64 else None
    return json.dumps(script, ensure_ascii=False)


async def generate_video_script_stream(*args, **kwargs):
    full_json = await generate_video_script(*args, **kwargs)
    script = json.loads(full_json)
    for i, scene in enumerate(script.get("scenes", [])):
        n = scene.get("narration", "")
        yield {"done": False, "text": "[" + scene.get("type", "") + "] " + n[:80] + "...\n"}
    yield {"done": True, "full_text": full_json}
