import traceback, json
from fastapi import APIRouter, Depends, HTTPException, Query
from fastapi.responses import StreamingResponse
from sqlalchemy.ext.asyncio import AsyncSession
from dependencies import get_db
from repository.resource_repo import ResourceRepository, ResourceSessionRepository
from repository.learning_repo import KnowledgeRepository
from repository.profile_repo import ProfileRepository
from repository.conversation_repo import MemoryRepository
from models import AsyncSessionFactory
from core.agents.doc_agent import generate_doc, generate_doc_stream
from core.agents.resource_chat_agent import resource_chat
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
    print(f"[Resource] POST /generate chapter_id={data.chapter_id}")
    knowledge_repo = KnowledgeRepository(db)
    chapter = await knowledge_repo.get_by_id(data.chapter_id)
    if chapter:
        title = chapter.title; chapter_content = chapter.content or ""; cid = data.chapter_id
    else:
        title = data.user_query or f"???? #{data.chapter_id}"; chapter_content = ""; cid = None

    profile_repo = ProfileRepository(db)
    profile = await profile_repo.get_by_user_id(user_id)
    profile_dict = _build_profile_dict(profile)

    resource_repo = ResourceRepository(db)
    created = await resource_repo.create(
        user_id=user_id, resource_type="doc", title=title,
        chapter_id=data.chapter_id if chapter else None, status="generating",
    )
    try:
        content = await generate_doc(
            chapter_title=title, chapter_content=chapter_content,
            chapter_id=cid, profile=profile_dict,
            user_query=data.user_query if not chapter else None,
        )
        r = await resource_repo.update(created.id, content=content, status="completed")
        await db.commit()
        return {"id": r.id, "title": r.title, "content": content, "resource_type": "doc",
                "status": "completed", "created_time": r.created_time.isoformat() if r.created_time else ""}
    except Exception as e:
        traceback.print_exc()
        await resource_repo.update(created.id, status="failed")
        await db.commit()
        raise HTTPException(500, detail=f"??????: {str(e)}")


@router.post("/generate/stream")
async def generate_stream(
    data: ResourceGenerateIn,
    user_id: int = Depends(auth_handler.auth_access_dependency),
    db: AsyncSession = Depends(get_db),
):
    knowledge_repo = KnowledgeRepository(db)
    chapter = await knowledge_repo.get_by_id(data.chapter_id)
    if chapter:
        title = chapter.title; chapter_content = chapter.content or ""; cid = data.chapter_id
    else:
        title = data.user_query or f"???? #{data.chapter_id}"; chapter_content = ""; cid = None

    profile_repo = ProfileRepository(db)
    profile = await profile_repo.get_by_user_id(user_id)
    profile_dict = _build_profile_dict(profile)

    resource_repo = ResourceRepository(db)
    created = await resource_repo.create(
        user_id=user_id, resource_type="doc", title=title,
        chapter_id=data.chapter_id if chapter else None, status="generating",
    )
    await db.commit()

    async def event_stream():
        full_text = ""
        try:
            async for chunk in generate_doc_stream(
                chapter_title=title, chapter_content=chapter_content,
                chapter_id=cid, profile=profile_dict,
                user_query=data.user_query if not chapter else None,
            ):
                if chunk.get("done"):
                    async with AsyncSessionFactory() as s2:
                        r2 = ResourceRepository(s2)
                        await r2.update(created.id, content=full_text, status="completed")
                        await s2.commit()
                    yield f"data: {json.dumps({'done': True, 'id': created.id, 'title': title}, ensure_ascii=False)}\n\n"
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
        extra_data=r.extra_data, status=r.status,
        created_time=r.created_time.isoformat() if r.created_time else ""
    ).model_dump() for r in resources]


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
        extra_data=r.extra_data, status=r.status,
        created_time=r.created_time.isoformat() if r.created_time else ""
    ).model_dump()
