import uuid
from datetime import datetime
from sqlalchemy import String, Boolean, DateTime, Integer, Float, ForeignKey, Text, JSON
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship
from ..database import Base

class CheckResult(Base):
    __tablename__ = "check_results"
    
    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    document_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("documents.id"), nullable=False)
    rule_set_id: Mapped[int] = mapped_column(Integer, nullable=True)  # Tạm để nullable, sau sẽ tạo rule_set mặc định
    score: Mapped[float] = mapped_column(Float, nullable=True)
    total_errors: Mapped[int] = mapped_column(Integer, default=0)
    critical_count: Mapped[int] = mapped_column(Integer, default=0)
    warning_count: Mapped[int] = mapped_column(Integer, default=0)
    info_count: Mapped[int] = mapped_column(Integer, default=0)
    ai_model: Mapped[str] = mapped_column(String(100), nullable=True)
    checked_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=datetime.utcnow)
    status: Mapped[str] = mapped_column(String(20), default="processing")  # processing, completed, error
    processing_time_ms: Mapped[int] = mapped_column(Integer, nullable=True)
    error_message: Mapped[str] = mapped_column(Text, nullable=True)
    extraction_data: Mapped[dict] = mapped_column(JSON, default={})
    rag_context: Mapped[dict] = mapped_column(JSON, default={})
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=datetime.utcnow)

    # Quan hệ
    errors = relationship("CheckError", back_populates="result", order_by="CheckError.severity")

class CheckError(Base):
    __tablename__ = "check_errors"
    
    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    result_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("check_results.id"), nullable=False)
    error_type: Mapped[str] = mapped_column(String(50), nullable=False)
    severity: Mapped[str] = mapped_column(String(10), nullable=False)  # critical, warning, info
    description: Mapped[str] = mapped_column(Text, nullable=False)
    current_value: Mapped[str] = mapped_column(Text, nullable=True)
    expected_value: Mapped[str] = mapped_column(Text, nullable=True)
    suggested_fix: Mapped[str] = mapped_column(Text, nullable=True)
    rag_reference: Mapped[str] = mapped_column(Text, nullable=True)
    location_info: Mapped[dict] = mapped_column(JSON, default={})
    confidence: Mapped[float] = mapped_column(Float, nullable=True)
    
    result = relationship("CheckResult", back_populates="errors")