import uuid
from datetime import datetime
from sqlalchemy import String, Boolean, DateTime, Integer, Float, ForeignKey, Text, JSON, ARRAY, Date
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship
from ..database import Base


class KnowledgeCategory(Base):
    __tablename__ = "knowledge_categories"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    name: Mapped[str] = mapped_column(String(200), nullable=False)
    code: Mapped[str] = mapped_column(String(50), unique=True, nullable=False)
    description: Mapped[str] = mapped_column(Text, nullable=True)
    sort_order: Mapped[int] = mapped_column(Integer, default=0)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=datetime.utcnow)

    documents = relationship("KnowledgeBaseDocument", back_populates="category")


class KnowledgeBaseDocument(Base):
    __tablename__ = "knowledge_base_documents"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    category_id: Mapped[int] = mapped_column(Integer, ForeignKey("knowledge_categories.id"), nullable=True)
    title: Mapped[str] = mapped_column(String(500), nullable=False)
    doc_code: Mapped[str] = mapped_column(String(100), nullable=True)
    doc_type: Mapped[str] = mapped_column(String(50), nullable=False)
    # nghi_dinh, thong_tu, quyet_dinh, huong_dan, khac
    minio_object_key: Mapped[str] = mapped_column(String(1000), nullable=False)
    ragflow_doc_id: Mapped[str] = mapped_column(String(100), nullable=True)
    chunk_count: Mapped[int] = mapped_column(Integer, default=0)
    vector_size_mb: Mapped[float] = mapped_column(Float, default=0)
    index_status: Mapped[str] = mapped_column(String(20), default="pending")
    # pending, indexing, ready, error
    is_active: Mapped[bool] = mapped_column(Boolean, default=True)
    effective_date: Mapped[datetime] = mapped_column(Date, nullable=True)
    replaced_by_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("knowledge_base_documents.id"), nullable=True)
    uploaded_by: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("users.id"), nullable=True)
    notes: Mapped[str] = mapped_column(Text, nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=datetime.utcnow)
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=datetime.utcnow, onupdate=datetime.utcnow)

    category = relationship("KnowledgeCategory", back_populates="documents")