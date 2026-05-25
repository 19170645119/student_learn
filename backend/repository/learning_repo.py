from models import AsyncSession
from models.learning_path import LearningPath, KnowledgeNode
from sqlalchemy import select

class LearningPathRepository:
    def __init__(self, session: AsyncSession):
        self.session = session

    async def get_active_by_user(self, user_id: int) -> LearningPath | None:
        return await self.session.scalar(
            select(LearningPath).filter(
                LearningPath.user_id == user_id, LearningPath.is_active == True
            )
        )

    async def create_or_update(self, user_id: int, profile_id: int, nodes: list) -> LearningPath:
        path = await self.session.scalar(
            select(LearningPath).filter(
                LearningPath.user_id == user_id, LearningPath.is_active == True
            )
        )
        if path:
            path.nodes = nodes
        else:
            path = LearningPath(user_id=user_id, profile_id=profile_id, nodes=nodes)
            self.session.add(path)
        return path

class KnowledgeRepository:
    def __init__(self, session: AsyncSession):
        self.session = session

    async def get_chapters(self) -> list:
        result = await self.session.execute(
            select(KnowledgeNode).filter(KnowledgeNode.node_type == "chapter")
            .order_by(KnowledgeNode.order_num)
        )
        return list(result.scalars().all())

    async def get_by_id(self, node_id: int) -> KnowledgeNode | None:
        return await self.session.scalar(
            select(KnowledgeNode).filter(KnowledgeNode.id == node_id)
        )

    async def get_children(self, parent_id: int) -> list:
        result = await self.session.execute(
            select(KnowledgeNode).filter(KnowledgeNode.parent_id == parent_id)
            .order_by(KnowledgeNode.order_num)
        )
        return list(result.scalars().all())

    async def get_all_nodes(self) -> list:
        result = await self.session.execute(
            select(KnowledgeNode).order_by(KnowledgeNode.order_num)
        )
        return list(result.scalars().all())
