import uuid
import math
from datetime import datetime
from typing import Optional, List, Tuple
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func, update, delete
from sqlalchemy.orm import selectinload
from ...shared.models.knowledge import KnowledgeCategory, KnowledgeBaseDocument
from ...shared.models.user import User
from ...shared.storage import upload_file, delete_file
from .schemas import KnowledgeCategoryCreate, KnowledgeCategoryUpdate, KnowledgeDocUpdate
from fastapi import UploadFile, HTTPException, status

class KnowledgeService:
    @staticmethod
    async def create_category(db: AsyncSession, data: KnowledgeCategoryCreate) -> KnowledgeCategory:
        # Check if code exists
        result = await db.execute(select(KnowledgeCategory).where(KnowledgeCategory.code == data.code))
        if result.scalar_one_or_none():
            raise HTTPException(status_code=400, detail="Mã danh mục đã tồn tại")

        category = KnowledgeCategory(**data.model_dump())
        db.add(category)
        await db.commit()
        await db.refresh(category)
        return category

    @staticmethod
    async def get_categories(db: AsyncSession) -> List[KnowledgeCategory]:
        result = await db.execute(select(KnowledgeCategory).order_by(KnowledgeCategory.sort_order))
        return result.scalars().all()

    @staticmethod
    async def update_category(db: AsyncSession, category_id: int, data: KnowledgeCategoryUpdate) -> KnowledgeCategory:
        category = await db.get(KnowledgeCategory, category_id)
        if not category:
            raise HTTPException(status_code=404, detail="Không tìm thấy danh mục")

        update_data = data.model_dump(exclude_unset=True)
        for key, value in update_data.items():
            setattr(category, key, value)

        await db.commit()
        await db.refresh(category)
        return category

    @staticmethod
    async def delete_category(db: AsyncSession, category_id: int):
        category = await db.get(KnowledgeCategory, category_id)
        if not category:
            raise HTTPException(status_code=404, detail="Không tìm thấy danh mục")

        # Check if any documents belong to this category
        doc_count = await db.execute(
            select(func.count()).select_from(KnowledgeBaseDocument).where(KnowledgeBaseDocument.category_id == category_id)
        )
        if doc_count.scalar() > 0:
            raise HTTPException(status_code=400, detail="Không thể xóa danh mục đang có tài liệu")

        await db.delete(category)
        await db.commit()
        return True

    @staticmethod
    async def upload_document(
        db: AsyncSession,
        file: UploadFile,
        title: str,
        doc_type: str,
        category_id: Optional[int] = None,
        doc_code: Optional[str] = None,
        effective_date: Optional[datetime] = None,
        user: Optional[User] = None
    ) -> KnowledgeBaseDocument:
        # Check category exists
        if category_id:
            category = await db.get(KnowledgeCategory, category_id)
            if not category:
                category_id = None

        # Prepare storage
        content = await file.read()
        file_size_mb = len(content) / (1024 * 1024)
        object_key = f"knowledge/{uuid.uuid4()}_{file.filename}"

        # Upload to MinIO
        mime_type = file.content_type or "application/octet-stream"
        await upload_file(object_key, content, mime_type)

        doc = KnowledgeBaseDocument(
            category_id=category_id,
            title=title,
            doc_code=doc_code,
            doc_type=doc_type,
            minio_object_key=object_key,
            index_status="pending",
            effective_date=effective_date,
            uploaded_by=user.id if user else None,
            vector_size_mb=file_size_mb
        )
        db.add(doc)
        await db.commit()
        await db.refresh(doc)
        return doc

    @staticmethod
    async def get_documents(
        db: AsyncSession,
        page: int = 1,
        limit: int = 20,
        category_id: Optional[int] = None,
        status: Optional[str] = None,
        search: Optional[str] = None
    ) -> Tuple[List[KnowledgeBaseDocument], int]:
        query = select(KnowledgeBaseDocument).options(selectinload(KnowledgeBaseDocument.category))

        if category_id:
            query = query.where(KnowledgeBaseDocument.category_id == category_id)
        if status:
            query = query.where(KnowledgeBaseDocument.index_status == status)
        if search:
            query = query.where(KnowledgeBaseDocument.title.ilike(f"%{search}%"))

        # Count total
        count_query = select(func.count()).select_from(query.subquery())
        total = (await db.execute(count_query)).scalar()

        # Order and paginate
        query = query.order_by(KnowledgeBaseDocument.created_at.desc())
        offset = (page - 1) * limit
        query = query.offset(offset).limit(limit)

        result = await db.execute(query)
        return result.scalars().all(), total

    @staticmethod
    async def update_document(db: AsyncSession, doc_id: uuid.UUID, data: KnowledgeDocUpdate) -> KnowledgeBaseDocument:
        doc = await db.get(KnowledgeBaseDocument, doc_id)
        if not doc:
            raise HTTPException(status_code=404, detail="Không tìm thấy tài liệu")

        update_data = data.model_dump(exclude_unset=True)
        for key, value in update_data.items():
            setattr(doc, key, value)

        doc.updated_at = datetime.utcnow()
        await db.commit()
        await db.refresh(doc)
        return doc

    @staticmethod
    async def delete_document(db: AsyncSession, doc_id: uuid.UUID):
        doc = await db.get(KnowledgeBaseDocument, doc_id)
        if not doc:
            raise HTTPException(status_code=404, detail="Không tìm thấy tài liệu")

        # Delete from MinIO
        try:
            await delete_file(doc.minio_object_key)
        except Exception:
            pass # Ignore if already deleted

        await db.delete(doc)
        await db.commit()
        return True

    @staticmethod
    async def get_stats(db: AsyncSession):
        # Total documents
        total_docs = await db.execute(select(func.count()).select_from(KnowledgeBaseDocument))
        # Total chunks (mocked or from DB if available)
        total_chunks = await db.execute(select(func.sum(KnowledgeBaseDocument.chunk_count)).select_from(KnowledgeBaseDocument))
        # Ready documents
        ready_docs = await db.execute(select(func.count()).select_from(KnowledgeBaseDocument).where(KnowledgeBaseDocument.index_status == "ready"))
        # Error documents
        error_docs = await db.execute(select(func.count()).select_from(KnowledgeBaseDocument).where(KnowledgeBaseDocument.index_status == "error"))
        # Total size
        total_size = await db.execute(select(func.sum(KnowledgeBaseDocument.vector_size_mb)).select_from(KnowledgeBaseDocument))

        return {
            "total_docs": total_docs.scalar() or 0,
            "total_chunks": total_chunks.scalar() or 0,
            "ready_docs": ready_docs.scalar() or 0,
            "error_docs": error_docs.scalar() or 0,
            "size_mb": total_size.scalar() or 0.0
        }

    @staticmethod
    async def reindex_document(db: AsyncSession, doc_id: uuid.UUID):
        doc = await db.get(KnowledgeBaseDocument, doc_id)
        if not doc:
            raise HTTPException(status_code=404, detail="Không tìm thấy tài liệu")

        doc.index_status = "indexing"
        await db.commit()

        # TODO: Trigger RAGFlow reindexing task
        # For now, we mock the transition to ready after some time
        return True
