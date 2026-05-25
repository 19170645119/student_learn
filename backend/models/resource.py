from . import Base
from sqlalchemy.orm import mapped_column, Mapped
from sqlalchemy import Integer, String, DateTime, Text, JSON, ForeignKey, Enum as SAEnum
from datetime import datetime
import enum

class ResourceType(str, enum.Enum):
    DOC = "doc"
    MINDMAP = "mindmap"
    QUIZ = "quiz"
    CODE = "code"
    VIDEO = "video"

class ResourceStatus(str, enum.Enum):
    GENERATING = "generating"
    COMPLETED = "completed"
    FAILED = "failed"

class LearningResource(Base):
    __tablename__ = "learning_resource"
    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    user_id: Mapped[int] = mapped_column(Integer, ForeignKey("user.id", ondelete="CASCADE"))
    profile_id: Mapped[int] = mapped_column(Integer, ForeignKey("student_profile.id"), nullable=True)
    chapter_id: Mapped[int] = mapped_column(Integer, ForeignKey("knowledge_node.id"), nullable=True)
    resource_type: Mapped[ResourceType] = mapped_column(SAEnum(ResourceType), default=ResourceType.DOC)
    title: Mapped[str] = mapped_column(String(200))
    content: Mapped[str] = mapped_column(Text, default="")
    extra_data: Mapped[dict] = mapped_column(JSON, default=dict, comment="额外数据(题目答案/视频脚本等)")
    status: Mapped[ResourceStatus] = mapped_column(SAEnum(ResourceStatus), default=ResourceStatus.GENERATING)
    created_time: Mapped[datetime] = mapped_column(DateTime, default=datetime.now)
