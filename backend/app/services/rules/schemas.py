import uuid
from datetime import datetime
from typing import Optional, List, Any
from pydantic import BaseModel, Field

# ---------- Rule Schemas ----------
class RuleBase(BaseModel):
    rule_code: str = Field(..., min_length=1, max_length=100)
    category: str = Field(...)  # font, margin, spacing, etc.
    name: str = Field(..., min_length=1, max_length=200)
    description: Optional[str] = None
    check_property: Optional[str] = None
    expected_value: Any  # JSON
    tolerance: Optional[Any] = None
    severity: str = "warning"  # critical, warning, info
    error_message: str
    fix_suggestion: Optional[str] = None
    is_active: bool = True
    sort_order: int = 0

class RuleCreate(RuleBase):
    pass

class RuleUpdate(BaseModel):
    rule_code: Optional[str] = None
    category: Optional[str] = None
    name: Optional[str] = None
    description: Optional[str] = None
    check_property: Optional[str] = None
    expected_value: Optional[Any] = None
    tolerance: Optional[Any] = None
    severity: Optional[str] = None
    error_message: Optional[str] = None
    fix_suggestion: Optional[str] = None
    is_active: Optional[bool] = None
    sort_order: Optional[int] = None

class RuleDto(RuleBase):
    id: uuid.UUID
    rule_set_id: int
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True

# ---------- Rule Set Schemas ----------
class RuleSetBase(BaseModel):
    name: str = Field(..., min_length=1, max_length=200)
    code: str = Field(..., min_length=1, max_length=100)
    description: Optional[str] = None
    doc_types: List[str] = []
    is_default: bool = False
    is_active: bool = True
    version: str = "1.0"

class RuleSetCreate(RuleSetBase):
    pass

class RuleSetUpdate(BaseModel):
    name: Optional[str] = None
    code: Optional[str] = None
    description: Optional[str] = None
    doc_types: Optional[List[str]] = None
    is_default: Optional[bool] = None
    is_active: Optional[bool] = None
    version: Optional[str] = None

class RuleSetDto(RuleSetBase):
    id: int
    created_by: Optional[uuid.UUID] = None
    created_at: datetime
    updated_at: datetime
    rules: List[RuleDto] = []

    class Config:
        from_attributes = True

class RuleSetSummaryDto(RuleSetBase):
    id: int
    rule_count: int = 0

    class Config:
        from_attributes = True

class RuleSetCloneRequest(BaseModel):
    new_name: str
    new_code: str
