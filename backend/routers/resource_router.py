from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from dependencies import get_session
from repository.resource_repo import ResourceRepository
from repository.learning_repo import KnowledgeRepository
from repository.profile_repo import ProfileRepository
from repository.conversation_repo import MemoryRepository
from core.agents.orchestrator import orchestrate_resource_generation
from core.agents.resource_chat_agent import analyze_intent, recommend_by_profile
from core.auth import AuthHandler
from schemas.resource import ResourceGenerateIn, ResourceOut
from models.resource import ResourceType

router = APIRouter(prefix="/resource")
auth_handler = AuthHandler()


@router.get("/")
async def get_resources(
    resource_type: str = None,
    user_id: int = Depends(auth_handler.auth_access_dependency),
    session: AsyncSession = Depends(get_session),
):
    repo = ResourceRepository(session)
    resources = await repo.get_by_user(user_id, resource_type)
    return [ResourceOut(
        id=r.id, user_id=r.user_id, chapter_id=r.chapter_id,
        resource_type=r.resource_type, title=r.title, content=r.content,
        extra_data=r.extra_data, status=r.status,
        created_time=r.created_time.isoformat() if r.created_time else ""
    ) for r in resources]


@router.get("/recommend")
async def recommend_nodes(
    user_id: int = Depends(auth_handler.auth_access_dependency),
    session: AsyncSession = Depends(get_session),
):
    profile_repo = ProfileRepository(session)
    profile = await profile_repo.get_by_user_id(user_id)
    if not profile:
        return {"nodes": [], "message": "请先完善学习画像"}
    
    profile_dict = {
        "interest_direction": profile.interest_direction or "",
        "error_prone": profile.error_prone or "",
        "knowledge_base": profile.knowledge_base or "",
    }
    knowledge_repo = KnowledgeRepository(session)
    all_nodes = await knowledge_repo.get_all_nodes()
    recs = await recommend_by_profile(profile_dict, all_nodes)
    return {"nodes": recs, "message": "根据你的画像推荐以下学习内容"}


@router.get("/chapters/list")
async def get_chapters(
    user_id: int = Depends(auth_handler.auth_access_dependency),
    session: AsyncSession = Depends(get_session),
):
    repo = KnowledgeRepository(session)
    chapters = await repo.get_chapters()
    return [{"id": c.id, "title": c.title, "order": c.order_num} for c in chapters]



@router.get("/{resource_id}")
async def get_resource(
    resource_id: int,
    user_id: int = Depends(auth_handler.auth_access_dependency),
    session: AsyncSession = Depends(get_session),
):
    repo = ResourceRepository(session)
    r = await repo.get_by_id(resource_id)
    if not r or r.user_id != user_id:
        raise HTTPException(404, detail="资源不存在")
    return ResourceOut(
        id=r.id, user_id=r.user_id, chapter_id=r.chapter_id,
        resource_type=r.resource_type, title=r.title, content=r.content,
        extra_data=r.extra_data, status=r.status,
        created_time=r.created_time.isoformat() if r.created_time else ""
    )


@router.post("/generate")
async def generate_resources(
    data: ResourceGenerateIn,
    user_id: int = Depends(auth_handler.auth_access_dependency),
    session: AsyncSession = Depends(get_session),
):
    knowledge_repo = KnowledgeRepository(session)
    chapter = await knowledge_repo.get_by_id(data.chapter_id)
    if not chapter:
        raise HTTPException(404, detail="章节不存在")
    profile_repo = ProfileRepository(session)
    profile = await profile_repo.get_by_user_id(user_id)
    profile_dict = None
    if profile:
        profile_dict = {
            "knowledge_base": profile.knowledge_base,
            "cognitive_style": profile.cognitive_style,
            "learning_goal": profile.learning_goal,
            "learning_pace": profile.learning_pace,
            "interest_direction": profile.interest_direction,
        }

    resource_repo = ResourceRepository(session)

    # Create resource records
    created_resources = []
    for rt in data.resource_types:
        r = await resource_repo.create(
            user_id=user_id,
            resource_type=rt.value,
            title=f"{chapter.title}",
            chapter_id=data.chapter_id,
            profile_id=profile.id if profile else None,
            status="generating",
        )
        created_resources.append(r)

    # Load memory entries
    mem_repo = MemoryRepository(session)
    mem_entries = await mem_repo.get_by_user(user_id)
    memory_list = [{"key": e.key, "value": e.value, "category": e.category} for e in mem_entries]

    # Run orchestration
    results = await orchestrate_resource_generation(
        chapter_title=chapter.title,
        chapter_content=chapter.content or "",
        chapter_id=data.chapter_id,
        resource_types=data.resource_types,
        profile=profile_dict,
        memory_entries=memory_list if memory_list else None,
    )

    # Update resources
    updated = []
    for i, result in enumerate(results):
        if i < len(created_resources):
            r = await resource_repo.update(
                created_resources[i].id,
                title=result["title"],
                content=result["content"],
                extra_data=result.get("extra_data", {}),
                status="completed" if result["success"] else "failed",
            )
            updated.append({"id": created_resources[i].id, "type": result["type"], "title": result["title"], "success": result["success"]})

    await session.commit()
    return {"message": "资源生成完成", "resources": updated}



@router.post("/chat")
async def resource_chat(
    data: dict,
    user_id: int = Depends(auth_handler.auth_access_dependency),
    session: AsyncSession = Depends(get_session),
):
    profile_repo = ProfileRepository(session)
    profile = await profile_repo.get_by_user_id(user_id)
    profile_dict = {}
    if profile:
        profile_dict = {
            "knowledge_base": profile.knowledge_base or "",
            "cognitive_style": profile.cognitive_style or "",
            "learning_goal": profile.learning_goal or "",
            "error_prone": profile.error_prone or "",
            "learning_pace": profile.learning_pace or "",
            "interest_direction": profile.interest_direction or "",
        }
    result = await analyze_intent(data.get("message", ""), profile_dict)
    return result

