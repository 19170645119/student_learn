import traceback, json, datetime
import io
from fastapi import APIRouter, Depends, HTTPException, Query
from pydantic import BaseModel
from fastapi.responses import StreamingResponse
from sqlalchemy.ext.asyncio import AsyncSession
from dependencies import get_db
from repository.resource_repo import ResourceRepository, ResourceSessionRepository
from repository.learning_repo import KnowledgeRepository
from repository.profile_repo import ProfileRepository
from repository.conversation_repo import MemoryRepository
from models import AsyncSessionFactory
from core.agents.doc_agent import generate_doc, generate_doc_stream
from core.agents.mindmap_agent import generate_mindmap, generate_mindmap_stream
from core.agents.quiz_agent import generate_quiz
from core.agents.resource_chat_agent import resource_chat
from core.agents.video_agent import generate_video_script, generate_video_script_stream
from core.agents.video_link_agent import generate_video_links, generate_video_links_stream
from core.agents.ppt_agent import generate_ppt, generate_ppt_stream
from core.ppt_export import export_pptx
from core.agents.code_agent import generate_code, generate_code_stream
from core.openai_service import chat as llm_chat
from core.auth import AuthHandler
from schemas.resource import ResourceChatIn, ResourceGenerateIn, ResourceOut, ResourceSessionCreateIn, ResourceSessionRenameIn

router = APIRouter(prefix="/resource")
auth_handler = AuthHandler()


def _build_profile_dict(profile):
    if not profile:
        return None
    return {
        "knowledge_base": profile.knowledge_base or "",
        "cognitive_style": profile.cognitive_style or "",
        "learning_goal": profile.learning_goal or "",
        "error_prone": profile.error_prone or "",
        "learning_pace": profile.learning_pace or "",
        "interest_direction": profile.interest_direction or "",
    }


# ==================== CHAT ====================

@router.post("/chat")
async def resource_chat_endpoint(
    data: ResourceChatIn,
    user_id: int = Depends(auth_handler.auth_access_dependency),
    db: AsyncSession = Depends(get_db),
):
    message = data.message
    session_id = data.session_id
    print(f"[Resource] POST /chat msg={message[:20]} sid={session_id}")

    s_repo = ResourceSessionRepository(db)
    if not session_id:
        s = await s_repo.create(user_id, title="??????")
        await db.flush()
        session_id = s.id

    conv = await s_repo.get_by_id(session_id)
    if not conv or conv.user_id != user_id:
        raise HTTPException(404, detail="?????")

    await s_repo.append_message(session_id, "user", message)

    profile_repo = ProfileRepository(db)
    profile = await profile_repo.get_by_user_id(user_id)
    profile_dict = _build_profile_dict(profile)

    mem_repo = MemoryRepository(db)
    memories = await mem_repo.get_by_user(user_id)
    memory_dict = {m.key: m.value for m in memories}

    result = await resource_chat(message, profile_dict, memory_dict)
    await s_repo.append_message(session_id, "assistant", result.get("reply", ""))
    await db.commit()
    result["session_id"] = session_id
    return result


# ==================== GENERATE ====================

@router.post("/generate")
async def generate_resources(
    data: ResourceGenerateIn,
    user_id: int = Depends(auth_handler.auth_access_dependency),
    db: AsyncSession = Depends(get_db),
):
    rtype = data.resource_types[0] if data.resource_types else "doc"
    print(f"[Resource] POST /generate chapter_id={data.chapter_id} rtype={rtype}")

    knowledge_repo = KnowledgeRepository(db)
    chapter = await knowledge_repo.get_by_id(data.chapter_id)
    if chapter:
        title = chapter.title; chapter_content = chapter.content or ""; cid = data.chapter_id
    else:
        title = data.user_query or f"\u672a\u77e5\u4e3b\u9898 #{data.chapter_id}"; chapter_content = ""; cid = None

    profile_repo = ProfileRepository(db)
    profile = await profile_repo.get_by_user_id(user_id)
    profile_dict = _build_profile_dict(profile)

    extra = data.extra or {}
    resource_repo = ResourceRepository(db)
    created = await resource_repo.create(
        user_id=user_id, resource_type=rtype, title=title,
        chapter_id=data.chapter_id if chapter else None, status="generating",
    )

    try:
        if rtype == "mindmap":
            content = await generate_mindmap(
                chapter_title=title, chapter_content=chapter_content,
                chapter_id=cid, profile=profile_dict,
                user_query=data.user_query if not chapter else None,
                extra=extra,
            )
        elif rtype == "quiz":
            difficulty = extra.get("difficulty", "medium")
            count = int(extra.get("count", 5))
            question_type = extra.get("question_type", None)
            questions = await generate_quiz(
                chapter_title=title, chapter_content=chapter_content,
                chapter_id=cid, difficulty=difficulty, count=count,
                profile=profile_dict, question_type=question_type,
            )
            content = json.dumps(questions, ensure_ascii=False)
            await resource_repo.update(created.id, content=content, status="completed",
                                       extra_data={"difficulty": difficulty, "count": count, "questions": questions})
            await db.commit()
            r = await resource_repo.get_by_id(created.id)
            return {"id": r.id, "title": r.title, "content": content, "resource_type": rtype,
                    "status": "completed", "extra_data": r.extra_data,
                    "created_time": r.created_time.isoformat() if r.created_time else ""}
        elif rtype == "video":
            content = await generate_video_script(
                chapter_title=title, chapter_content=chapter_content,
                chapter_id=cid, profile=profile_dict,
                user_query=data.user_query if not chapter else None,
                with_audio=True,
            )
        elif rtype == "ppt":
            content = await generate_ppt(
                chapter_title=title, chapter_content=chapter_content,
                chapter_id=cid, profile=profile_dict,
                user_query=data.user_query if not chapter else None,
                extra=extra,
            )
        elif rtype == "code":
            content = await generate_code(
                chapter_title=title, chapter_content=chapter_content,
                chapter_id=cid, profile=profile_dict,
                user_query=data.user_query if not chapter else None,
                extra=extra,
            )
        elif rtype == "video_link":
            content = await generate_video_links(
                chapter_title=title, chapter_content=chapter_content,
                chapter_id=cid, profile=profile_dict,
                user_query=data.user_query if not chapter else None,
            )
        else:
            content = await generate_doc(
                chapter_title=title, chapter_content=chapter_content,
                chapter_id=cid, profile=profile_dict,
                user_query=data.user_query if not chapter else None,
            )
        r = await resource_repo.update(created.id, content=content, status="completed")
        await db.commit()
        return {"id": r.id, "title": r.title, "content": content, "resource_type": rtype,
                "status": "completed", "created_time": r.created_time.isoformat() if r.created_time else ""}
    except Exception as e:
        traceback.print_exc()
        await resource_repo.update(created.id, status="failed")
        await db.commit()
        raise HTTPException(500, detail=f"\u751f\u6210\u5931\u8d25: {str(e)}")


@router.post("/generate/stream")
async def generate_stream(
    data: ResourceGenerateIn,
    user_id: int = Depends(auth_handler.auth_access_dependency),
    db: AsyncSession = Depends(get_db),
):
    rtype = data.resource_types[0] if data.resource_types else "doc"
    print(f"[Resource] POST /generate/stream chapter_id={data.chapter_id} rtype={rtype}")
    knowledge_repo = KnowledgeRepository(db)
    chapter = await knowledge_repo.get_by_id(data.chapter_id)
    if chapter:
        title = chapter.title; chapter_content = chapter.content or ""; cid = data.chapter_id
    else:
        title = data.user_query or f"???? #{data.chapter_id}"; chapter_content = ""; cid = None

    profile_repo = ProfileRepository(db)
    profile = await profile_repo.get_by_user_id(user_id)
    profile_dict = _build_profile_dict(profile)

    rtype = data.resource_types[0] if data.resource_types else "doc"
    resource_repo = ResourceRepository(db)
    created = await resource_repo.create(
        user_id=user_id, resource_type=rtype, title=title,
        chapter_id=data.chapter_id if chapter else None, status="generating",
    )
    await db.commit()

    async def event_stream():
        full_text = ""
        try:
            gen = generate_mindmap_stream if rtype == "mindmap" else (
                generate_ppt_stream if rtype == "ppt" else (
                generate_video_script_stream if rtype == "video" else generate_doc_stream
            ))
            async for chunk in gen(
                chapter_title=title, chapter_content=chapter_content,
                chapter_id=cid, profile=profile_dict,
                user_query=data.user_query if not chapter else None,
            ):
                if chunk.get("done"):
                    final_content = chunk.get("full_text", full_text)
                    async with AsyncSessionFactory() as s2:
                        r2 = ResourceRepository(s2)
                        await r2.update(created.id, content=final_content, status="completed")
                        await s2.commit()
                    yield f"data: {json.dumps({'done': True, 'id': created.id, 'title': title, 'resource_type': rtype, 'full_text': final_content}, ensure_ascii=False)}\n\n"
                else:
                    full_text += chunk.get("text", "")
                    yield f"data: {json.dumps({'done': False, 'text': chunk.get('text', '')}, ensure_ascii=False)}\n\n"
        except Exception as e:
            traceback.print_exc()
            async with AsyncSessionFactory() as s2:
                r2 = ResourceRepository(s2)
                await r2.update(created.id, status="failed")
                await s2.commit()
            yield f"data: {json.dumps({'done': True, 'error': str(e)}, ensure_ascii=False)}\n\n"

    return StreamingResponse(event_stream(), media_type="text/event-stream")


# ==================== CHAPTERS ====================

@router.get("/chapters/list")
async def get_chapters(
    user_id: int = Depends(auth_handler.auth_access_dependency),
    db: AsyncSession = Depends(get_db),
):
    repo = KnowledgeRepository(db)
    chapters = await repo.get_chapters()
    return [{"id": c.id, "title": c.title, "order": c.order_num} for c in chapters]


# ==================== SESSIONS ====================

@router.get("/sessions")
async def list_sessions(
    user_id: int = Depends(auth_handler.auth_access_dependency),
    db: AsyncSession = Depends(get_db),
):
    repo = ResourceSessionRepository(db)
    sessions = await repo.get_by_user(user_id)
    return [{
        "id": s.id, "title": s.title,
        "message_count": len(s.messages or []),
        "created_time": s.created_time.isoformat() if s.created_time else "",
        "updated_time": s.updated_time.isoformat() if s.updated_time else "",
    } for s in sessions]


@router.post("/sessions")
async def create_session(
    data: ResourceSessionCreateIn,
    user_id: int = Depends(auth_handler.auth_access_dependency),
    db: AsyncSession = Depends(get_db),
):
    repo = ResourceSessionRepository(db)
    s = await repo.create(user_id, title=data.title)
    await db.commit()
    return {"id": s.id, "title": s.title}


@router.delete("/sessions/{session_id}")
async def delete_session(
    session_id: int,
    user_id: int = Depends(auth_handler.auth_access_dependency),
    db: AsyncSession = Depends(get_db),
):
    repo = ResourceSessionRepository(db)
    s = await repo.get_by_id(session_id)
    if not s or s.user_id != user_id:
        raise HTTPException(404, detail="?????")
    await repo.delete(session_id)
    await db.commit()
    return {"message": "???"}


@router.put("/sessions/{session_id}/rename")
async def rename_session(
    session_id: int,
    data: ResourceSessionRenameIn,
    user_id: int = Depends(auth_handler.auth_access_dependency),
    db: AsyncSession = Depends(get_db),
):
    repo = ResourceSessionRepository(db)
    s = await repo.get_by_id(session_id)
    if not s or s.user_id != user_id:
        raise HTTPException(404, detail="?????")
    await repo.rename(session_id, data.title)
    await db.commit()
    return {"message": "????"}


@router.get("/sessions/{session_id}")
async def get_session_detail(
    session_id: int,
    user_id: int = Depends(auth_handler.auth_access_dependency),
    db: AsyncSession = Depends(get_db),
):
    repo = ResourceSessionRepository(db)
    s = await repo.get_by_id(session_id)
    if not s or s.user_id != user_id:
        raise HTTPException(404, detail="?????")
    return {
        "id": s.id, "title": s.title,
        "messages": s.messages or [],
        "created_time": s.created_time.isoformat() if s.created_time else "",
    }



# ==================== GRADE ====================

class GradeIn(BaseModel):
    score: int
    total: int
    answers: list = []


@router.patch("/{resource_id}/grade")
async def grade_resource(
    resource_id: int,
    data: GradeIn,
    user_id: int = Depends(auth_handler.auth_access_dependency),
    db: AsyncSession = Depends(get_db),
):
    repo = ResourceRepository(db)
    r = await repo.get_by_id(resource_id)
    if not r or r.user_id != user_id:
        raise HTTPException(404, detail="资源不存在")
    attempts = (r.extra_data or {}).get("attempts", [])
    attempts.append({
        "score": data.score,
        "total": data.total,
        "answers": data.answers,
        "time": datetime.datetime.now().isoformat(),
    })
    await repo.update(resource_id, extra_data={**(r.extra_data or {}), "attempts": attempts})
    await db.commit()
    return {"message": "评分已保存", "attempts": attempts}

# ==================== LIST ====================

@router.get("/")
async def get_resources(
    resource_type: str | None = Query(default=None),
    user_id: int = Depends(auth_handler.auth_access_dependency),
    db: AsyncSession = Depends(get_db),
):
    repo = ResourceRepository(db)
    resources = await repo.get_by_user(user_id, resource_type)
    return [ResourceOut(
        id=r.id, user_id=r.user_id, chapter_id=r.chapter_id,
        resource_type=r.resource_type, title=r.title, content=r.content,
        extra_data=r.extra_data, status=(r.status or "").lower(),
        created_time=r.created_time.isoformat() if r.created_time else ""
    ).model_dump() for r in resources]




# ==================== CODE REVIEW ====================

class CodeReviewIn(BaseModel):
    code: str
    language: str = "python"

@router.post("/{resource_id}/review-code")
async def review_code(
    resource_id: int,
    data: CodeReviewIn,
    user_id: int = Depends(auth_handler.auth_access_dependency),
    db: AsyncSession = Depends(get_db),
):
    repo = ResourceRepository(db)
    r = await repo.get_by_id(resource_id)
    if not r or r.user_id != user_id:
        raise HTTPException(404, detail="?????")
    if r.resource_type != "code":
        raise HTTPException(400, detail="???????")

    try:
        sol_data = json.loads(r.content) if isinstance(r.content, str) else r.content
    except:
        sol_data = {}

    solution_code = sol_data.get("solution", {}).get("code", "")
    test_cases = sol_data.get("examples", [])
    problem_stmt = sol_data.get("problem", {}).get("statement", "")
    language = data.language or sol_data.get("language", "python")

    review_prompt = f"""?????????????????

????
{problem_stmt}

??????
{solution_code[:2000]}

??????
{json.dumps(test_cases, ensure_ascii=False)[:1000]}

??????
{data.code}

?????????????JSON?
{{
  "correct": true/false,
  "score": 0-100,
  "feedback": "?????1-2???",
  "issues": [{{"line": "?????", "severity": "error/warning/suggestion", "message": "????", "fix": "????"}}],
  "highlights": ["??????1", "??????2"],
  "comparison": "??????????",
  "improved_code": "?????????????????"
}}

???JSON????????"""

    try:
        response = await llm_chat([
            {"role": "system", "content": "???????????????????????????JSON?"},
            {"role": "user", "content": review_prompt},
        ])
        import re as _re
        json_match = _re.search(r"\{.*\}", response, _re.DOTALL)
        if json_match:
            review = json.loads(json_match.group())
        else:
            review = {"correct": False, "score": 0, "feedback": response[:500], "issues": [], "highlights": [], "comparison": "", "improved_code": ""}
        return {"review": review}
    except Exception as e:
        return {"review": {"correct": False, "score": 0, "feedback": "????: " + str(e), "issues": [], "highlights": [], "comparison": "", "improved_code": ""}}


# ==================== RESOURCE DETAIL (LAST) ====================

@router.delete("/{resource_id}")
async def delete_resource(
    resource_id: int,
    user_id: int = Depends(auth_handler.auth_access_dependency),
    db: AsyncSession = Depends(get_db),
):
    repo = ResourceRepository(db)
    r = await repo.get_by_id(resource_id)
    if not r or r.user_id != user_id:
        raise HTTPException(404, detail="?????")
    await repo.delete(resource_id)
    await db.commit()
    return {"message": "???"}


@router.get("/{resource_id}")
async def get_resource(
    resource_id: int,
    user_id: int = Depends(auth_handler.auth_access_dependency),
    db: AsyncSession = Depends(get_db),
):
    repo = ResourceRepository(db)
    r = await repo.get_by_id(resource_id)
    if not r or r.user_id != user_id:
        raise HTTPException(404, detail="?????")
    return ResourceOut(
        id=r.id, user_id=r.user_id, chapter_id=r.chapter_id,
        resource_type=r.resource_type, title=r.title, content=r.content,
        extra_data=r.extra_data, status=(r.status or "").lower(),
        created_time=r.created_time.isoformat() if r.created_time else ""
    ).model_dump()


@router.get("/{resource_id}/export/pptx")
async def export_resource_pptx(
    resource_id: int,
    user_id: int = Depends(auth_handler.auth_access_dependency),
    db: AsyncSession = Depends(get_db),
):
    """导出资源为PPTX文件"""
    repo = ResourceRepository(db)
    resource = await repo.get_by_id(resource_id)
    if not resource or resource.user_id != user_id:
        raise HTTPException(404, detail="资源不存在")
    if not resource.content:
        raise HTTPException(400, detail="资源内容为空")
    try:
        pptx_bytes = export_pptx(resource.content)
    except Exception as e:
        raise HTTPException(500, detail=f"PPTX生成失败: {str(e)}")
    return StreamingResponse(
        io.BytesIO(pptx_bytes),
        media_type="application/vnd.openxmlformats-officedocument.presentationml.presentation",
        headers={"Content-Disposition": f"attachment; filename=ppt_{resource_id}.pptx"}
    )