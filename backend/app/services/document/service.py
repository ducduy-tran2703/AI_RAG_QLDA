import uuid
import hashlib
from datetime import datetime
from typing import Optional, List
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func, update, delete
from sqlalchemy.orm import selectinload
from ...shared.models.document import Document, DocumentFolder, DocumentVersion
from ...shared.models.user import User
from ...shared.storage import upload_file, get_file_url, delete_file
from .schemas import DocumentUpdateRequest, FolderCreateRequest, FolderUpdateRequest
from fastapi import UploadFile, HTTPException, status

class DocumentService:
    ALLOWED_MIME_TYPES = {
        "application/vnd.openxmlformats-officedocument.wordprocessingml.document",  # .docx
        "application/pdf"
    }
    MAX_FILE_SIZE = 50 * 1024 * 1024  # 50MB

    @staticmethod
    async def upload(
        db: AsyncSession,
        file: UploadFile,
        user: User,
        folder_id: Optional[uuid.UUID] = None
    ) -> Document:
        # Kiểm tra extension
        if not (file.filename.endswith('.docx') or file.filename.endswith('.pdf')):
            raise HTTPException(status_code=400, detail="Chỉ hỗ trợ file .docx hoặc .pdf")
        
        # Đọc nội dung file
        content = await file.read()
        file_size = len(content)
        if file_size > DocumentService.MAX_FILE_SIZE:
            raise HTTPException(status_code=400, detail="File vượt quá kích thước cho phép (50MB)")
        
        # Kiểm tra MIME type (có thể dùng python-magic sau, hiện tạm dựa vào extension)
        if file.filename.endswith('.docx'):
            mime_type = "application/vnd.openxmlformats-officedocument.wordprocessingml.document"
        else:
            mime_type = "application/pdf"
        
        if mime_type not in DocumentService.ALLOWED_MIME_TYPES:
            raise HTTPException(status_code=400, detail="Định dạng file không được hỗ trợ")
        
        # Tính checksum SHA256
        sha256_hash = hashlib.sha256(content).hexdigest()
        
        # Tạo object key duy nhất
        object_key = f"{user.id}/{uuid.uuid4()}_{file.filename}"
        
        # Upload lên MinIO
        await upload_file(object_key, content, mime_type)
        
        # Tạo bản ghi Document
        file_type = 'docx' if file.filename.endswith('.docx') else 'pdf'
        # Kiểm tra folder_id nếu có
        if folder_id:
            folder = await db.get(DocumentFolder, folder_id)
            if not folder or folder.user_id != user.id:
                folder_id = None  # bỏ qua folder_id không hợp lệ
        doc = Document(
            user_id=user.id,
            department_id=user.department_id,
            folder_id=folder_id,
            original_filename=file.filename,
            display_name=file.filename,
            file_type=file_type,
            file_size_bytes=file_size,
            minio_object_key=object_key,
            checksum_sha256=sha256_hash,
            mime_type=mime_type,
        )
        db.add(doc)
        await db.commit()
        await db.refresh(doc)
        return doc

    @staticmethod
    async def get_document(db: AsyncSession, document_id: uuid.UUID, user: User) -> Document:
        result = await db.execute(
            select(Document).where(Document.id == document_id, Document.user_id == user.id, Document.is_deleted == False)
        )
        doc = result.scalar_one_or_none()
        if not doc:
            raise HTTPException(status_code=404, detail="Không tìm thấy văn bản")
        return doc

    @staticmethod
    async def update_document(db: AsyncSession, document_id: uuid.UUID, user: User, data: DocumentUpdateRequest):
        doc = await DocumentService.get_document(db, document_id, user)
        update_data = data.model_dump(exclude_unset=True)
        # Xử lý folder_id đặc biệt: nếu là None và được gửi lên thì set về None
        for field, value in update_data.items():
            setattr(doc, field, value)
        doc.updated_at = datetime.utcnow()
        await db.commit()
        await db.refresh(doc)
        return doc

    @staticmethod
    async def delete_document(db: AsyncSession, document_id: uuid.UUID, user: User):
        doc = await DocumentService.get_document(db, document_id, user)
        # Soft delete
        doc.is_deleted = True
        doc.deleted_at = datetime.utcnow()
        await db.commit()
        return True

    @staticmethod
    async def create_folder(db: AsyncSession, user: User, data: FolderCreateRequest):
        folder = DocumentFolder(
            user_id=user.id,
            name=data.name,
            parent_id=data.parent_id,
            color=data.color,
            icon=data.icon
        )
        db.add(folder)
        await db.commit()
        await db.refresh(folder)
        return folder

    @staticmethod
    async def get_folders(db: AsyncSession, user: User):
        result = await db.execute(
            select(DocumentFolder).where(DocumentFolder.user_id == user.id).order_by(DocumentFolder.name)
        )
        return result.scalars().all()

    @staticmethod
    async def update_folder(db: AsyncSession, folder_id: uuid.UUID, user: User, data: FolderUpdateRequest):
        folder = await db.get(DocumentFolder, folder_id)
        if not folder or folder.user_id != user.id:
            raise HTTPException(status_code=404, detail="Không tìm thấy thư mục")
        update_data = data.model_dump(exclude_unset=True)
        for key, value in update_data.items():
            setattr(folder, key, value)
        await db.commit()
        await db.refresh(folder)
        return folder

    @staticmethod
    async def delete_folder(db: AsyncSession, folder_id: uuid.UUID, user: User):
        folder = await db.get(DocumentFolder, folder_id)
        if not folder or folder.user_id != user.id:
            raise HTTPException(status_code=404, detail="Không tìm thấy thư mục")
        # Kiểm tra có document nào trong folder không
        doc_count = await db.execute(
            select(func.count()).select_from(Document).where(
                Document.folder_id == folder_id,
                Document.is_deleted == False
            )
        )
        count = doc_count.scalar()
        if count > 0:
            raise HTTPException(status_code=400, detail=f"Không thể xóa thư mục có {count} văn bản. Vui lòng di chuyển văn bản trước.")
        await db.delete(folder)
        await db.commit()
        return True

    @staticmethod
    async def get_documents(
        db: AsyncSession,
        user: User,
        page: int = 1,
        limit: int = 20,
        folder_id: Optional[uuid.UUID] = None,
        search: Optional[str] = None,
        file_type: Optional[str] = None,
        sort: str = "created_at",
        order: str = "desc"
    ):
        query = select(Document).where(Document.user_id == user.id, Document.is_deleted == False)
        if folder_id is not None:
            query = query.where(Document.folder_id == folder_id)
        if search:
            query = query.where(Document.display_name.ilike(f"%{search}%"))
        if file_type:
            query = query.where(Document.file_type == file_type)
        
        # Đếm tổng
        count_query = select(func.count()).select_from(query.subquery())
        total = (await db.execute(count_query)).scalar()
        
        # Sắp xếp
        sort_column = getattr(Document, sort, Document.created_at)
        if order == "asc":
            query = query.order_by(sort_column.asc())
        else:
            query = query.order_by(sort_column.desc())
        
        # Phân trang
        offset = (page - 1) * limit
        query = query.offset(offset).limit(limit)
        result = await db.execute(query)
        documents = result.scalars().all()
        
        return documents, total

    @staticmethod
    async def create_version(db: AsyncSession, doc: Document, file: UploadFile, user: User, change_notes: Optional[str] = None):
        import hashlib
        
        # Lấy version_number hiện tại
        result = await db.execute(
            select(func.max(DocumentVersion.version_number))
            .where(DocumentVersion.document_id == doc.id)
        )
        max_version = result.scalar() or 0
        new_version = max_version + 1
        
        # Đọc nội dung file
        content = await file.read()
        sha256_hash = hashlib.sha256(content).hexdigest()
        object_key = f"{user.id}/{doc.id}/v{new_version}_{file.filename}"
        
        # Upload lên MinIO
        from ...shared.storage import upload_file as storage_upload
        await storage_upload(object_key, content, doc.mime_type)
        
        version = DocumentVersion(
            document_id=doc.id,
            version_number=new_version,
            version_label=f"v{new_version}",
            minio_object_key=object_key,
            file_size_bytes=len(content),
            checksum_sha256=sha256_hash,
            change_notes=change_notes,
            created_by=user.id,
        )
        db.add(version)
        await db.commit()
        await db.refresh(version)
        return version
