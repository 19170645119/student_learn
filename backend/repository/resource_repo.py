from models import AsyncSession
from models.resource import LearningResource
from sqlalchemy import select, desc


class ResourceRepository:
    def __init__(self, session: AsyncSession):
        self.session = session

    async def create(self, user_id: int, resource_type: str, title: str,
                     content: str = "", chapter_id: int = None,
                     extra_data: dict = None,
                     status: str = "generating") -> LearningResource:
        resource = LearningResource(
            user_id=user_id, resource_type=resource_type, title=title,
            content=content, chapter_id=chapter_id,
            extra_data=extra_data or {}, status=status,
        )
        self.session.add(resource)
        await self.session.flush()
        return resource

    async def update(self, resource_id: int, **kwargs) -> LearningResource | None:
        resource = await self.session.scalar(
            select(LearningResource).filter(LearningResource.id == resource_id)
        )
        if resource:
            for key, value in kwargs.items():
                if value is not None:
                    setattr(resource, key, value)
        return resource

    async def get_by_id(self, resource_id: int) -> LearningResource | None:
        return await self.session.scalar(
            select(LearningResource).filter(LearningResource.id == resource_id)
        )

    async def get_by_user(self, user_id: int, resource_type: str = None, limit: int = 20) -> list:
        stmt = select(LearningResource).filter(LearningResource.user_id == user_id)
        if resource_type:
            stmt = stmt.filter(LearningResource.resource_type == resource_type)
        stmt = stmt.order_by(desc(LearningResource.created_time)).limit(limit)
        result = await self.session.execute(stmt)
        return list(result.scalars().all())
from models.resource import ResourceSession
from datetime import datetime
from sqlalchemy import delete


class ResourceSessionRepository:
    def __init__(self, session: AsyncSession):
        self.session = session

    async def get_by_user(self, user_id: int) -> list[ResourceSession]:
        stmt = select(ResourceSession).filter(ResourceSession.user_id == user_id)
        stmt = stmt.order_by(desc(ResourceSession.updated_time))
        result = await self.session.execute(stmt)
        return result.scalars().all()

    async def get_by_id(self, session_id: int) -> ResourceSession | None:
        return await self.session.scalar(
            select(ResourceSession).filter(ResourceSession.id == session_id)
        )

    async def create(self, user_id: int, title: str = "资源学习对话") -> ResourceSession:
        async with self.session.begin_nested():
            s = ResourceSession(user_id=user_id, title=title)
            self.session.add(s)
            await self.session.flush()
            return s

    async def delete(self, session_id: int):
        async with self.session.begin_nested():
            await self.session.execute(
                delete(ResourceSession).filter(ResourceSession.id == session_id)
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
