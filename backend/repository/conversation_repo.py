from models import AsyncSession
from models.conversation import ConversationSession, MemoryEntry
from sqlalchemy import select, delete
from datetime import datetime

class SessionRepository:
    def __init__(self, session: AsyncSession):
        self.session = session

    async def get_by_user(self, user_id: int, source: str = None) -> list[ConversationSession]:
        stmt = select(ConversationSession).filter(ConversationSession.user_id == user_id)
        if source:
            stmt = stmt.filter(ConversationSession.source == source)
        stmt = stmt.order_by(ConversationSession.updated_time.desc())
        result = await self.session.execute(stmt)
        return result.scalars().all()

    async def get_by_id(self, session_id: int) -> ConversationSession | None:
        return await self.session.scalar(
            select(ConversationSession).filter(ConversationSession.id == session_id)
        )

    async def create(self, user_id: int, title: str = "画像构建对话", source: str = "profile") -> ConversationSession:
        async with self.session.begin_nested():
            s = ConversationSession(user_id=user_id, title=title, source=source)
            self.session.add(s)
            await self.session.flush()
            return s

    async def delete(self, session_id: int):
        async with self.session.begin_nested():
            await self.session.execute(
                delete(ConversationSession).filter(ConversationSession.id == session_id)
            )

    async def append_message(self, session_id: int, role: str, content: str):
        s = await self.get_by_id(session_id)
        if s:
            s.messages = (s.messages or []) + [{"role": role, "content": content, "created_time": datetime.now().isoformat()}]
            s.messages = s.messages[-50:]
            s.updated_time = datetime.now()

    async def rename(self, session_id: int, title: str):
        s = await self.get_by_id(session_id)
        if s:
            s.title = title


class MemoryRepository:
    def __init__(self, session: AsyncSession):
        self.session = session

    async def get_by_user(self, user_id: int) -> list[MemoryEntry]:
        result = await self.session.execute(
            select(MemoryEntry).filter(MemoryEntry.user_id == user_id)
        )
        return result.scalars().all()

    async def upsert(self, user_id: int, key: str, value: str, category: str = "fact", session_id: int = None):
        existing = await self.session.scalar(
            select(MemoryEntry).filter(MemoryEntry.user_id == user_id, MemoryEntry.key == key)
        )
        if existing:
            existing.value = value
            existing.category = category
            if session_id:
                existing.session_id = session_id
        else:
            entry = MemoryEntry(user_id=user_id, session_id=session_id, key=key, value=value, category=category)
            self.session.add(entry)

    async def delete(self, memory_id: int):
        await self.session.execute(
            delete(MemoryEntry).filter(MemoryEntry.id == memory_id)
        )