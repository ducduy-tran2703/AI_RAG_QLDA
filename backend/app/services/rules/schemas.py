from pydantic import BaseModel, Field
from typing import Optional, List, Any
from datetime import datetime

# ---------- Rule (Chunk) Schemas ----------
class RuleDto(BaseModel):
    id: str
    content: str
    available: bool = True
    important_keywords: List[str] = []
    tag_kwd: List[str] = []
    questions: List[str] = []
    positions: List[Any] = []
    image_base64: Optional[str] = None

    class Config:
        from_attributes = True

class RuleCreate(BaseModel):
    content: str
    important_keywords: Optional[List[str]] = []
    tag_kwd: Optional[List[str]] = []
    questions: Optional[List[str]] = []

class RuleUpdate(BaseModel):
    content: Optional[str] = None
    important_keywords: Optional[List[str]] = None
    tag_kwd: Optional[List[str]] = None
    questions: Optional[List[str]] = None
    available: Optional[bool] = None
    positions: Optional[List[Any]] = None
    image_base64: Optional[str] = None

class RuleListResponse(BaseModel):
    chunks: List[RuleDto]
    total: int

# ---------- Rule Set (Document) Schemas ----------
class RuleSetDto(BaseModel):
    id: str
    name: str
    chunk_count: int = 0
    run: str = "UNSTART"
    create_date: Optional[str] = None

    class Config:
        from_attributes = True

class RuleSetUpdate(BaseModel):
    name: Optional[str] = None
