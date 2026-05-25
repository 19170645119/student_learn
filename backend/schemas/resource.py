from pydantic import BaseModel, Field
from typing import Annotated, Optional, List
from models.resource import ResourceType, ResourceStatus

class ResourceGenerateIn(BaseModel):
    chapter_id: int
    resource_types: List[ResourceType]

class ResourceOut(BaseModel):
    id: int
    user_id: int
    chapter_id: Optional[int] = None
    resource_type: ResourceType
    title: str
    content: str
    extra_data: dict = {}
    status: ResourceStatus
    created_time: str = ""

    class Config:
        from_attributes = True
