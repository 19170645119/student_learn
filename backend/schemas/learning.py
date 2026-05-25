from pydantic import BaseModel, Field
from typing import List, Optional

class PathNodeSchema(BaseModel):
    node_id: int
    order: int
    title: str = ""
    resource_ids: List[int] = []

class PathOut(BaseModel):
    id: int
    user_id: int
    nodes: List[dict] = []
    is_active: bool
    created_time: str = ""

    class Config:
        from_attributes = True

class RecommendOut(BaseModel):
    resources: List[dict] = []
