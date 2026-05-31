from pydantic import BaseModel, Field
from typing import Optional, List, Any
from datetime import datetime

# ---------- Parser Config (Nested) ----------
class ParserConfigDto(BaseModel):
    chunk_token_num: Optional[int] = 128
    layout_recognize: Optional[bool] = True
    # Add other fields as needed based on RAGFlow response

# ---------- Document Schemas ----------
class KnowledgeDocDto(BaseModel):
    id: str
    name: str
    size: int
    type: Optional[str] = "doc"
    run: str  # e.g., "UNSTART", "RUNNING", "CANCEL", "DONE", "FAIL"
    status: str = "1" # "1": Enabled, "0": Disabled
    chunk_count: int = Field(alias="chunk_count", default=0) # Map RAGFlow's chunk_count
    knowledgebase_id: Optional[str] = None
    location: Optional[str] = None
    parser_config: Optional[dict] = None
    chunk_method: Optional[str] = None
    create_date: Optional[str] = None
    update_date: Optional[str] = None
    progress: Optional[float] = 0.0

    class Config:
        populate_by_name = True
        from_attributes = True

class KnowledgeDocListResponse(BaseModel):
    documents: List[KnowledgeDocDto]
    total: int
    page: int
    limit: int
    total_pages: int

class KnowledgeStatsResponse(BaseModel):
    total_docs: int
    total_chunks: int
    ready_docs: int
    error_docs: int
    size_mb: float

class KnowledgeDocUpdate(BaseModel):
    name: Optional[str] = None
    chunk_method: Optional[str] = None
    parser_config: Optional[dict] = None
    meta_fields: Optional[dict] = None
