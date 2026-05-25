from . import Base
from sqlalchemy.orm import mapped_column, Mapped, relationship
from sqlalchemy import Integer, String, DateTime, Text, JSON, ForeignKey
from datetime import datetime
import enum

class KnowledgeLevel(str, enum.Enum):
    BEGINNER = "beginner"
    INTERMEDIATE = "intermediate"
    ADVANCED = "advanced"

class KnowledgeNode(Base):
    __tablename__ = "knowledge_node"
    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    parent_id: Mapped[int] = mapped_column(Integer, ForeignKey("knowledge_node.id"), nullable=True, comment="父节点ID")
    title: Mapped[str] = mapped_column(String(200))
    content: Mapped[str] = mapped_column(Text, default="")
    level: Mapped[KnowledgeLevel] = mapped_column(String(20), default=KnowledgeLevel.BEGINNER)
    order_num: Mapped[int] = mapped_column(Integer, default=0, comment="排序序号")
    extra: Mapped[dict] = mapped_column(JSON, default=dict, comment="扩展字段")
    created_time: Mapped[datetime] = mapped_column(DateTime, default=datetime.now)

    # 知识点类型: chapter(章) / section(节) / concept(知识点)
    node_type: Mapped[str] = mapped_column(String(20), default="concept")

class LearningPath(Base):
    __tablename__ = "learning_path"
    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    user_id: Mapped[int] = mapped_column(Integer, ForeignKey("user.id", ondelete="CASCADE"))
    profile_id: Mapped[int] = mapped_column(Integer, ForeignKey("student_profile.id"))
    nodes: Mapped[list] = mapped_column(JSON, default=list, comment="路径节点列表[{node_id, order, resource_ids}]")
    is_active: Mapped[bool] = mapped_column(Integer, default=True)
    created_time: Mapped[datetime] = mapped_column(DateTime, default=datetime.now)
    updated_time: Mapped[datetime] = mapped_column(DateTime, default=datetime.now, onupdate=datetime.now)

