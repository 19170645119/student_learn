from pydantic import BaseModel, field_validator
from typing import Optional, List


VALID_RESOURCE_TYPES = {"doc", "mindmap", "quiz", "code", "video", "video_link", "ppt"}


class ResourceChatIn(BaseModel):
    message: str
    session_id: Optional[int] = None


class ResourceGenerateIn(BaseModel):
    chapter_id: int
    resource_types: List[str]
    user_query: Optional[str] = None
    extra: Optional[dict] = None

    @field_validator("resource_types")
    @classmethod
    def filter_valid_types(cls, v: List[str]) -> List[str]:
        filtered = [t for t in v if t in VALID_RESOURCE_TYPES]
        if not filtered:
            raise ValueError(f"resource_types must contain at least one valid type: {sorted(VALID_RESOURCE_TYPES)}")
        return filtered


class ResourceOut(BaseModel):
    id: int
    user_id: int
    chapter_id: Optional[int] = None
    resource_type: str
    title: str
    content: str
    extra_data: dict = {}
    status: str
    created_time: str = ""

    class Config:
        from_attributes = True


class ResourceSessionCreateIn(BaseModel):
    title: str = "资源学习对话"


class ResourceSessionRenameIn(BaseModel):
    title: str
