from pydantic import BaseModel, Field
from typing import Annotated, Optional

class ProfileChatIn(BaseModel):
    message: str
    session_id: Optional[int] = None

class ProfileDimension(BaseModel):
    knowledge_base: str = ""
    cognitive_style: str = ""
    learning_goal: str = ""
    error_prone: str = ""
    learning_pace: str = ""
    interest_direction: str = ""
    major_grade: str = ""
    weekly_hours: str = ""

class ProfileOut(BaseModel):
    id: int
    user_id: int
    knowledge_base: str
    cognitive_style: str
    learning_goal: str
    error_prone: str
    learning_pace: str
    interest_direction: str
    major_grade: str
    weekly_hours: str
    extra_dimensions: dict = {}

    class Config:
        from_attributes = True

class ProfileUpdateIn(BaseModel):
    knowledge_base: Optional[str] = None
    cognitive_style: Optional[str] = None
    learning_goal: Optional[str] = None
    error_prone: Optional[str] = None
    learning_pace: Optional[str] = None
    interest_direction: Optional[str] = None
    major_grade: Optional[str] = None
    weekly_hours: Optional[str] = None
