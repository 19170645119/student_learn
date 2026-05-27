from . import Base
from sqlalchemy.orm import mapped_column, Mapped
from sqlalchemy import Integer, String, DateTime, Text, JSON, ForeignKey
from datetime import datetime


class QuestionBank(Base):
    __tablename__ = "question_bank"
    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    chapter_id: Mapped[int] = mapped_column(Integer, ForeignKey("knowledge_node.id"), nullable=True)
    type: Mapped[str] = mapped_column(String(20), default="choice")
    difficulty: Mapped[str] = mapped_column(String(20), default="medium")
    question: Mapped[str] = mapped_column(Text)
    options: Mapped[list] = mapped_column(JSON, nullable=True)
    answer: Mapped[str] = mapped_column(String(500))
    explanation: Mapped[str] = mapped_column(Text, default="")
    usage_count: Mapped[int] = mapped_column(Integer, default=0)
    created_time: Mapped[datetime] = mapped_column(DateTime, default=datetime.now)
