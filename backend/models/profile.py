from . import Base
from sqlalchemy.orm import mapped_column, Mapped
from sqlalchemy import Integer, String, DateTime, Text, JSON, ForeignKey, Float
from datetime import datetime

class StudentProfile(Base):
    __tablename__ = "student_profile"
    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    user_id: Mapped[int] = mapped_column(Integer, ForeignKey("user.id", ondelete="CASCADE"), unique=True)
    # 6个维度
    knowledge_base: Mapped[str] = mapped_column(Text, default="", comment="知识基础")
    cognitive_style: Mapped[str] = mapped_column(String(50), default="", comment="认知风格(视觉型/听觉型/动手型)")
    learning_goal: Mapped[str] = mapped_column(Text, default="", comment="学习目标")
    error_prone: Mapped[str] = mapped_column(Text, default="", comment="易错点偏好")
    learning_pace: Mapped[str] = mapped_column(String(50), default="", comment="学习节奏(快/中/慢)")
    interest_direction: Mapped[str] = mapped_column(Text, default="", comment="兴趣方向")
    # 当前激活的会话ID
    active_session_id: Mapped[int] = mapped_column(Integer, nullable=True, comment="当前激活会话ID")
    # 扩展维度（JSON存储）
    extra_dimensions: Mapped[dict] = mapped_column(JSON, default=dict, comment="扩展维度")
    # 对话历史
    chat_history: Mapped[list] = mapped_column(JSON, default=list, comment="画像构建对话历史")
    updated_time: Mapped[datetime] = mapped_column(DateTime, default=datetime.now, onupdate=datetime.now)
    created_time: Mapped[datetime] = mapped_column(DateTime, default=datetime.now)
