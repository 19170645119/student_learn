from models import AsyncSession
from models.resource import LearningResource
from sqlalchemy import select, desc

class ResourceRepository:
    def __init__(self, session: AsyncSession):
        self.session = session

    async def create(self, user_id: int, resource_type: str, title: str,
                     content: str = "", chapter_id: int = None,
                     profile_id: int = None, extra_data: dict = None,
                     status: str = "generating") -> LearningResource:
        resource = LearningResource(
            user_id=user_id, resource_type=resource_type, title=title,
            content=content, chapter_id=chapter_id, profile_id=profile_id,
            extra_data=extra_data or {}, status=status,
        )
        self.session.add(resource)
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
