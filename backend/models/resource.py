from . import Base
from sqlalchemy.orm import mapped_column, Mapped
from sqlalchemy import Integer, String, DateTime, Text, JSON, ForeignKey
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
    chapter_id: Mapped[int] = mapped_column(Integer, ForeignKey("knowledge_node.id"), nullable=True)
    resource_type: Mapped[str] = mapped_column(String(20), default="doc")
    title: Mapped[str] = mapped_column(String(200))
    content: Mapped[str] = mapped_column(Text, default="")
    extra_data: Mapped[dict] = mapped_column(JSON, default=dict)
    status: Mapped[str] = mapped_column(String(20), default="generating")
    created_time: Mapped[datetime] = mapped_column(DateTime, default=datetime.now)


class ResourceSession(Base):
    __tablename__ = "resource_session"
    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    user_id: Mapped[int] = mapped_column(Integer, ForeignKey("user.id", ondelete="CASCADE"))
    title: Mapped[str] = mapped_column(String(100), default="资源学习对话")
    messages: Mapped[list] = mapped_column(JSON, default=list, comment="[{role, content, created_time}]")
    status: Mapped[str] = mapped_column(String(20), default="active")
    created_time: Mapped[datetime] = mapped_column(DateTime, default=datetime.now)
    updated_time: Mapped[datetime] = mapped_column(DateTime, default=datetime.now, onupdate=datetime.now)
