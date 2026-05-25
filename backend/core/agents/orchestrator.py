import asyncio
from core.agents.doc_agent import generate_doc
from core.agents.mindmap_agent import generate_mindmap
from core.agents.quiz_agent import generate_quiz
from core.agents.code_agent import generate_code
from core.agents.video_agent import generate_video_script
from models.resource import ResourceType

AGENT_MAP = {
    ResourceType.DOC: ("课程文档", generate_doc),
    ResourceType.MINDMAP: ("思维导图", generate_mindmap),
    ResourceType.QUIZ: ("练习题", generate_quiz),
    ResourceType.CODE: ("代码案例", generate_code),
    ResourceType.VIDEO: ("教学视频", generate_video_script),
}


async def orchestrate_resource_generation(
    chapter_title: str,
    chapter_content: str = "",
    chapter_id: int = None,
    resource_types: list = None,
    profile: dict = None,
    memory_entries: list = None,
    progress_callback=None
) -> list:
    results = []

    async def run_agent(resource_type, agent_func, *args):
        try:
            result = await agent_func(*args)
            if isinstance(result, dict):
                content = str(result)
                extra = result
            else:
                content = result
                extra = {}
            results.append({
                "type": resource_type.value,
                "title": f"{chapter_title} - {AGENT_MAP[resource_type][0]}",
                "content": content,
                "extra_data": extra,
                "success": True
            })
        except Exception as e:
            results.append({
                "type": resource_type.value,
                "title": f"{chapter_title} - {AGENT_MAP[resource_type][0]}",
                "content": f"生成失败：{str(e)}",
                "extra_data": {},
                "success": False
            })

    tasks = []
    for rt in resource_types:
        if rt == ResourceType.DOC:
            tasks.append(run_agent(rt, generate_doc, chapter_title, chapter_content, chapter_id, profile, memory_entries))
        elif rt == ResourceType.MINDMAP:
            tasks.append(run_agent(rt, generate_mindmap, chapter_title, chapter_content, chapter_id, profile, memory_entries))
        elif rt == ResourceType.QUIZ:
            tasks.append(run_agent(rt, generate_quiz, chapter_title, chapter_content, chapter_id, profile, memory_entries))
        elif rt == ResourceType.CODE:
            tasks.append(run_agent(rt, generate_code, chapter_title, chapter_content, chapter_id, profile, memory_entries))
        elif rt == ResourceType.VIDEO:
            tasks.append(run_agent(rt, generate_video_script, chapter_title, chapter_content, chapter_id, profile, memory_entries))

    await asyncio.gather(*tasks)
    return results
