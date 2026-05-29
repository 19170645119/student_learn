from fastapi import APIRouter, Body, Depends, HTTPException
from fastapi.responses import StreamingResponse
from sqlalchemy.ext.asyncio import AsyncSession
import json
from dependencies import get_session as get_db
from models import AsyncSessionFactory
from repository.profile_repo import ProfileRepository
from repository.conversation_repo import SessionRepository, MemoryRepository
from core.agents.profile_agent import run_profile_agent_stream
from core.auth import AuthHandler
from schemas.profile import ProfileChatIn, ProfileOut, ProfileUpdateIn
from schemas import ResponseOut
from models.profile import ProfileSnapshot

router = APIRouter(prefix="/profile")
auth_handler = AuthHandler()


@router.get("/", response_model=ProfileOut)
async def get_profile(
    user_id: int = Depends(auth_handler.auth_access_dependency),
    db: AsyncSession = Depends(get_db),
):
    repo = ProfileRepository(db)
    profile = await repo.get_by_user_id(user_id)
    if not profile:
        return ProfileOut(id=0, user_id=user_id, knowledge_base="", cognitive_style="",
                          learning_goal="", error_prone="", learning_pace="", interest_direction="")
    return profile


@router.put("/", response_model=ResponseOut)
async def update_profile(
    data: ProfileUpdateIn,
    user_id: int = Depends(auth_handler.auth_access_dependency),
    db: AsyncSession = Depends(get_db),
):
    repo = ProfileRepository(db)
    update_data = {k: v for k, v in data.model_dump().items() if v is not None}
    await repo.create_or_update(user_id, **update_data)
    # 清空画像时同步清空快照历史
    is_clear = update_data and all(v == "" for v in update_data.values())
    if is_clear:
        from sqlalchemy import delete
        await db.execute(delete(ProfileSnapshot).where(ProfileSnapshot.user_id == user_id))
    await db.commit()
    return ResponseOut(message="画像更新成功")


# ==================== \u4f1a\u8bdd\u7ba1\u7406 ====================

@router.get("/sessions")
async def list_sessions(
    user_id: int = Depends(auth_handler.auth_access_dependency),
    db: AsyncSession = Depends(get_db),
):
    repo = SessionRepository(db)
    sessions = await repo.get_by_user(user_id, source="profile")
    return [{"id": s.id, "title": s.title, "status": s.status,
             "msg_count": len(s.messages or []),
             "created_time": s.created_time.isoformat() if s.created_time else "",
             "updated_time": s.updated_time.isoformat() if s.updated_time else ""}
            for s in sessions]


@router.post("/sessions")
async def create_session(
    data: dict = Body(None),
    user_id: int = Depends(auth_handler.auth_access_dependency),
    db: AsyncSession = Depends(get_db),
):
    s_repo = SessionRepository(db)
    title = (data or {}).get("title", "") if data else ""
    s = await s_repo.create(user_id, title=title if title else "画像构建对话")
    p_repo = ProfileRepository(db)
    await p_repo.create_or_update(user_id, active_session_id=s.id)
    await db.commit()
    return {"id": s.id, "title": s.title, "status": s.status, "messages": s.messages or []}


@router.get("/sessions/{session_id}")
async def get_session(
    session_id: int,
    user_id: int = Depends(auth_handler.auth_access_dependency),
    db: AsyncSession = Depends(get_db),
):
    repo = SessionRepository(db)
    s = await repo.get_by_id(session_id)
    if not s or s.user_id != user_id:
        raise HTTPException(404, detail="\u4f1a\u8bdd\u4e0d\u5b58\u5728")
    return {"id": s.id, "title": s.title, "status": s.status,
            "messages": s.messages or [],
            "created_time": s.created_time.isoformat() if s.created_time else ""}


@router.delete("/sessions/{session_id}")
async def delete_session(
    session_id: int,
    user_id: int = Depends(auth_handler.auth_access_dependency),
    db: AsyncSession = Depends(get_db),
):
    repo = SessionRepository(db)
    s = await repo.get_by_id(session_id)
    if not s or s.user_id != user_id:
        raise HTTPException(404, detail="\u4f1a\u8bdd\u4e0d\u5b58\u5728")
    await repo.delete(session_id)
    p_repo = ProfileRepository(db)
    profile = await p_repo.get_by_user_id(user_id)
    if profile and getattr(profile, 'active_session_id', None) == session_id:
        await p_repo.create_or_update(user_id, active_session_id=None)
    await db.commit()
    return ResponseOut(message="\u4f1a\u8bdd\u5df2\u5220\u9664")


@router.put("/sessions/{session_id}/activate")
async def activate_session(
    session_id: int,
    user_id: int = Depends(auth_handler.auth_access_dependency),
    db: AsyncSession = Depends(get_db),
):
    repo = SessionRepository(db)
    s = await repo.get_by_id(session_id)
    if not s or s.user_id != user_id:
        raise HTTPException(404, detail="\u4f1a\u8bdd\u4e0d\u5b58\u5728")
    p_repo = ProfileRepository(db)
    await p_repo.create_or_update(user_id, active_session_id=session_id)
    return ResponseOut(message="\u5df2\u5207\u6362\u4f1a\u8bdd")


@router.put("/sessions/{session_id}/rename")
async def rename_session(
    session_id: int,
    data: dict = Body(...),
    user_id: int = Depends(auth_handler.auth_access_dependency),
    db: AsyncSession = Depends(get_db),
):
    repo = SessionRepository(db)
    s = await repo.get_by_id(session_id)
    if not s or s.user_id != user_id:
        raise HTTPException(404, detail="\u4f1a\u8bdd\u4e0d\u5b58\u5728")
    s.title = data.get("title", s.title)[:50]
    await db.commit()
    return ResponseOut(message="\u91cd\u547d\u540d\u6210\u529f")



# ==================== \u8bb0\u5fc6\u7ba1\u7406 ====================

@router.get("/memory")
async def get_memory(
    user_id: int = Depends(auth_handler.auth_access_dependency),
    db: AsyncSession = Depends(get_db),
):
    repo = MemoryRepository(db)
    entries = await repo.get_by_user(user_id)
    return [{"id": e.id, "key": e.key, "value": e.value,
             "category": e.category, "session_id": e.session_id,
             "created_time": e.created_time.isoformat() if e.created_time else ""}
            for e in entries]


@router.delete("/memory/{memory_id}")
async def delete_memory(
    memory_id: int,
    user_id: int = Depends(auth_handler.auth_access_dependency),
    db: AsyncSession = Depends(get_db),
):
    repo = MemoryRepository(db)
    await repo.delete(memory_id)
    return ResponseOut(message="\u8bb0\u5fc6\u5df2\u5220\u9664")


# ==================== \u6d41\u5f0f\u804a\u5929 ====================

@router.post("/chat")
async def chat_profile(
    data: ProfileChatIn,
    user_id: int = Depends(auth_handler.auth_access_dependency),
    db: AsyncSession = Depends(get_db),
):
    profile_repo = ProfileRepository(db)
    s_repo = SessionRepository(db)
    m_repo = MemoryRepository(db)
    profile = await profile_repo.get_by_user_id(user_id)

    session_id = data.session_id
    if not session_id:
        if profile and getattr(profile, 'active_session_id', None):
            session_id = getattr(profile, 'active_session_id', None)
        else:
            s = await s_repo.create(user_id)
            session_id = s.id
            await profile_repo.create_or_update(user_id, active_session_id=session_id)

    conv_session = await s_repo.get_by_id(session_id)
    if not conv_session or conv_session.user_id != user_id:
        raise HTTPException(404, detail="\u4f1a\u8bdd\u4e0d\u5b58\u5728")
    chat_history = conv_session.messages or []

    # 加载所有会话的消息用于综合画像分析
    all_sessions = await s_repo.get_by_user(user_id, source="profile")
    all_history = []
    for sess in all_sessions:
        for m in (sess.messages or []):
            all_history.append({"role": m.get("role",""), "content": m.get("content","")})

    memory_entries = await m_repo.get_by_user(user_id)
    memory_list = [{"key": e.key, "value": e.value, "category": e.category} for e in memory_entries]

    current_profile = {}
    if profile:
        current_profile = {
            "knowledge_base": profile.knowledge_base or "",
            "cognitive_style": profile.cognitive_style or "",
            "learning_goal": profile.learning_goal or "",
            "error_prone": profile.error_prone or "",
            "learning_pace": profile.learning_pace or "",
            "interest_direction": profile.interest_direction or "",
        }

    async def event_stream():
        async def _safe_write(operation):
            async with AsyncSessionFactory() as s:
                async with s.begin():
                    await operation(s)
        
        reply_message = ""
        profile_update = {}
        memory_updates = {}
        completed = False
        message_summary = ""

        async for chunk in run_profile_agent_stream(data.message, current_profile, chat_history, memory_list, all_history):
            if chunk["type"] == "token":
                reply_message += chunk.get("text", "")
                yield f"data: {json.dumps({'type': 'token', 'text': chunk['text']}, ensure_ascii=False)}\n\n"
            elif chunk["type"] == "done":
                reply_message = chunk.get("message", reply_message)
                profile_update = chunk.get("profile_update", {})
                memory_updates = chunk.get("memory_updates", {})
                completed = chunk.get("completed", False)
                message_summary = chunk.get("message_summary", "")

        if profile_update:
            update_data = {k: v for k, v in profile_update.items() if v}
            # 检测是否为重置（所有维度清空）
            all_empty = all(v == "" for v in profile_update.values())
            if update_data or all_empty:
                async def _update_profile(s):
                    repo = ProfileRepository(s)
                    if all_empty:
                        # 重置：写入空值 + 清空快照历史
                        from sqlalchemy import delete
                        await s.execute(delete(ProfileSnapshot).where(ProfileSnapshot.user_id == user_id))
                        await repo.create_or_update(user_id,
                            knowledge_base="", cognitive_style="", learning_goal="",
                            error_prone="", learning_pace="", interest_direction="",
                            major_grade="", weekly_hours="")
                    else:
                        await repo.create_or_update(user_id, **update_data)
                await _safe_write(_update_profile)

        for key, value in memory_updates.items():
            async def _upsert_mem(s):
                repo = MemoryRepository(s)
                await repo.upsert(user_id, key=key, value=value, session_id=session_id, category="fact")
            await _safe_write(_upsert_mem)

        async def _append_user(s):
            repo = SessionRepository(s)
            await repo.append_message(session_id, "user", data.message)
        await _safe_write(_append_user)
        if reply_message:
            async def _append_ai(s):
                repo = SessionRepository(s)
                await repo.append_message(session_id, "assistant", reply_message)
            await _safe_write(_append_ai)

        # \u66f4\u65b0\u4f1a\u8bdd\u6807\u9898
        if message_summary:
            s = await s_repo.get_by_id(session_id)
            if s:
                s.title = message_summary[:30]

        yield f"data: {json.dumps({'type': 'done', 'message': reply_message, 'message_summary': message_summary, 'profile_update': profile_update, 'completed': completed, 'session_id': session_id}, ensure_ascii=False)}\n\n"

    return StreamingResponse(event_stream(), media_type="text/event-stream")


@router.get("/history")
async def get_profile_history(
    user_id: int = Depends(auth_handler.auth_access_dependency),
    db: AsyncSession = Depends(get_db),
):
    """获取画像演变历史"""
    from sqlalchemy import select, desc
    result = await db.execute(
        select(ProfileSnapshot)
        .where(ProfileSnapshot.user_id == user_id)
        .order_by(desc(ProfileSnapshot.created_time))
        .limit(20)
    )
    snapshots = result.scalars().all()
    return [
        {
            "id": s.id,
            "snapshot": s.snapshot,
            "trigger": s.trigger,
            "created_time": s.created_time.isoformat() if s.created_time else "",
        }
        for s in snapshots
    ]