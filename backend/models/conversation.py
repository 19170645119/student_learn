from . import Base
from sqlalchemy.orm import mapped_column, Mapped
from sqlalchemy import Integer, String, DateTime, Text, JSON, ForeignKey
from datetime import datetime

class ConversationSession(Base):
    __tablename__ = "conversation_session"
    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    user_id: Mapped[int] = mapped_column(Integer, ForeignKey("user.id", ondelete="CASCADE"))
    title: Mapped[str] = mapped_column(String(100), default="画像构建对话")
    status: Mapped[str] = mapped_column(String(20), default="active")
    messages: Mapped[list] = mapped_column(JSON, default=list, comment="[{role, content, created_time}]")
    created_time: Mapped[datetime] = mapped_column(DateTime, default=datetime.now)
    updated_time: Mapped[datetime] = mapped_column(DateTime, default=datetime.now, onupdate=datetime.now)

class MemoryEntry(Base):
    __tablename__ = "memory_entry"
    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    user_id: Mapped[int] = mapped_column(Integer, ForeignKey("user.id", ondelete="CASCADE"))
    session_id: Mapped[int] = mapped_column(Integer, ForeignKey("conversation_session.id", ondelete="SET NULL"), nullable=True)
    key: Mapped[str] = mapped_column(String(50))
    value: Mapped[str] = mapped_column(Text)
    category: Mapped[str] = mapped_column(String(30), default="fact")
    created_time: Mapped[datetime] = mapped_column(DateTime, default=datetime.now)
    updated_time: Mapped[datetime] = mapped_column(DateTime, default=datetime.now, onupdate=datetime.now)
