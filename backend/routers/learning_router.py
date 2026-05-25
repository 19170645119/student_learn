from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from dependencies import get_session
from repository.learning_repo import LearningPathRepository, KnowledgeRepository
from repository.resource_repo import ResourceRepository
from repository.profile_repo import ProfileRepository
from core.agents.path_agent import generate_learning_path
from core.auth import AuthHandler
from schemas.learning import PathOut, RecommendOut
from schemas import ResponseOut

router = APIRouter(prefix="/learning-path")
auth_handler = AuthHandler()


@router.get("/")
async def get_path(
    user_id: int = Depends(auth_handler.auth_access_dependency),
    session: AsyncSession = Depends(get_session),
):
    repo = LearningPathRepository(session)
    path = await repo.get_active_by_user(user_id)
    if not path:
        return PathOut(id=0, user_id=user_id, nodes=[], is_active=False, created_time="")
    return PathOut(
        id=path.id, user_id=path.user_id, nodes=path.nodes,
        is_active=path.is_active,
        created_time=path.created_time.isoformat() if path.created_time else ""
    )


@router.post("/generate", response_model=ResponseOut)
async def generate_path(
    user_id: int = Depends(auth_handler.auth_access_dependency),
    session: AsyncSession = Depends(get_session),
):
    profile_repo = ProfileRepository(session)
    profile = await profile_repo.get_by_user_id(user_id)
    if not profile:
        raise HTTPException(400, detail="请先完成学习画像构建")

    knowledge_repo = KnowledgeRepository(session)
    all_nodes = await knowledge_repo.get_all_nodes()
    if not all_nodes:
        raise HTTPException(400, detail="知识库为空，请先导入课程数据")

    profile_dict = {
        "knowledge_base": profile.knowledge_base,
        "cognitive_style": profile.cognitive_style,
        "learning_goal": profile.learning_goal,
        "learning_pace": profile.learning_pace,
        "interest_direction": profile.interest_direction,
    }

    result = await generate_learning_path(profile_dict, all_nodes)

    path_repo = LearningPathRepository(session)
    await path_repo.create_or_update(
        user_id=user_id,
        profile_id=profile.id,
        nodes=result.get("path_nodes", [])
    )

    await session.commit()
    return ResponseOut(message=f"学习路径已生成：{result.get('summary', '')}")


@router.get("/recommend")
async def recommend_resources(
    user_id: int = Depends(auth_handler.auth_access_dependency),
    session: AsyncSession = Depends(get_session),
):
    path_repo = LearningPathRepository(session)
    path = await path_repo.get_active_by_user(user_id)
    if not path or not path.nodes:
        return RecommendOut(resources=[])

    resource_repo = ResourceRepository(session)
    resources = []

    for node in path.nodes[:5]:  # 推荐前5个节点
        node_id = node.get("node_id") if isinstance(node, dict) else node
        knowledge_repo = KnowledgeRepository(session)
        kn = await knowledge_repo.get_by_id(node_id)
        if kn:
            user_resources = await resource_repo.get_by_user(user_id, limit=3)
            resources.append({
                "node_id": node_id,
                "node_title": kn.title,
                "resources": [
                    {"id": r.id, "title": r.title, "type": r.resource_type.value}
                    for r in user_resources if r.chapter_id == node_id
                ]
            })

    return RecommendOut(resources=resources)
