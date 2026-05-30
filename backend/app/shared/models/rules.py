import uuid
from datetime import datetime
from sqlalchemy import String, Boolean, DateTime, Integer, Float, ForeignKey, Text, JSON, ARRAY
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship
from ..database import Base


class RuleSet(Base):
    __tablename__ = "rule_sets"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    name: Mapped[str] = mapped_column(String(200), nullable=False)
    code: Mapped[str] = mapped_column(String(100), unique=True, nullable=False)
    description: Mapped[str] = mapped_column(Text, nullable=True)
    doc_types: Mapped[list[str]] = mapped_column(ARRAY(String), default=[])
    is_default: Mapped[bool] = mapped_column(Boolean, default=False)
    is_active: Mapped[bool] = mapped_column(Boolean, default=True)
    version: Mapped[str] = mapped_column(String(20), default="1.0")
    created_by: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("users.id"), nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=datetime.utcnow)
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=datetime.utcnow, onupdate=datetime.utcnow)

    # Relationships
    rules = relationship("Rule", back_populates="rule_set", order_by="Rule.sort_order")


class Rule(Base):
    __tablename__ = "rules"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    rule_set_id: Mapped[int] = mapped_column(Integer, ForeignKey("rule_sets.id"), nullable=False)
    rule_code: Mapped[str] = mapped_column(String(100), nullable=False)
    category: Mapped[str] = mapped_column(String(50), nullable=False)
    # font, margin, spacing, heading, page_number, alignment, list,
    # header, footer, table, caption, quoc_hieu, co_quan, so_ky_hieu,
    # ngay_thang, noi_nhan, chu_ky, chinh_ta, viet_tat, so_tien
    name: Mapped[str] = mapped_column(String(200), nullable=False)
    description: Mapped[str] = mapped_column(Text, nullable=True)
    check_property: Mapped[str] = mapped_column(String(200), nullable=True)
    expected_value: Mapped[dict] = mapped_column(JSON, nullable=False)
    tolerance: Mapped[dict] = mapped_column(JSON, nullable=True)
    severity: Mapped[str] = mapped_column(String(10), default="warning")  # critical, warning, info
    error_message: Mapped[str] = mapped_column(Text, nullable=False)
    fix_suggestion: Mapped[str] = mapped_column(Text, nullable=True)
    is_active: Mapped[bool] = mapped_column(Boolean, default=True)
    sort_order: Mapped[int] = mapped_column(Integer, default=0)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=datetime.utcnow)
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=datetime.utcnow, onupdate=datetime.utcnow)

    rule_set = relationship("RuleSet", back_populates="rules")


class RuleSetDepartment(Base):
    __tablename__ = "rule_set_departments"

    rule_set_id: Mapped[int] = mapped_column(Integer, ForeignKey("rule_sets.id"), primary_key=True)
    department_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("departments.id"), primary_key=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=datetime.utcnow)


class RuleSetVersion(Base):
    __tablename__ = "rule_set_versions"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    rule_set_id: Mapped[int] = mapped_column(Integer, ForeignKey("rule_sets.id"), nullable=False)
    version: Mapped[str] = mapped_column(String(20), nullable=False)
    snapshot: Mapped[dict] = mapped_column(JSON, nullable=False)
    change_notes: Mapped[str] = mapped_column(Text, nullable=True)
    changed_by: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("users.id"), nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=datetime.utcnow)