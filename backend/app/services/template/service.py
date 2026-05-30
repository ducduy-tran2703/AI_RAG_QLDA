import uuid
from datetime import datetime
from typing import Optional, List
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func, update
from sqlalchemy.orm import selectinload
from ...shared.models.template import Template, TemplateComparison
from ...shared.models.user import User
from ...shared.storage import upload_file, get_file_url
from .schemas import TemplateCreateRequest, TemplateUpdateRequest
from fastapi import HTTPException, UploadFile


class TemplateService:
    @staticmethod
    async def get_templates(
        db: AsyncSession,
        page: int = 1,
        limit: int = 20,
        doc_type: Optional[str] = None,
        is_active: Optional[bool] = None
    ):
        query = select(Template)
        if doc_type:
            query = query.where(Template.doc_types.any(doc_type))
        if is_active is not None:
            query = query.where(Template.is_active == is_active)

        count_query = select(func.count()).select_from(query.subquery())
        total = (await db.execute(count_query)).scalar()

        query = query.order_by(Template.template_name).offset((page - 1) * limit).limit(limit)
        result = await db.execute(query)
        return result.scalars().all(), total

    @staticmethod
    async def get_template(db: AsyncSession, template_id: int) -> Template:
        template = await db.get(Template, template_id)
        if not template:
            raise HTTPException(status_code=404, detail="Không tìm thấy mẫu văn bản")
        return template

    @staticmethod
    async def create_template(
        db: AsyncSession,
        data: TemplateCreateRequest,
        file: UploadFile,
        user: User
    ) -> Template:
        # Check code uniqueness
        existing = await db.execute(select(Template).where(Template.template_code == data.template_code))
        if existing.scalar_one_or_none():
            raise HTTPException(status_code=400, detail="Mã mẫu văn bản đã tồn tại")

        # Upload file
        content = await file.read()
        object_key = f"templates/{uuid.uuid4()}_{file.filename}"
        mime_type = file.content_type or "application/octet-stream"
        await upload_file(object_key, content, mime_type)

        template = Template(
            template_name=data.template_name,
            template_code=data.template_code,
            description=data.description,
            minio_object_key=object_key,
            rule_set_id=data.rule_set_id,
            doc_types=data.doc_types,
            created_by=user.id
        )
        db.add(template)
        await db.commit()
        await db.refresh(template)
        return template

    @staticmethod
    async def update_template(db: AsyncSession, template_id: int, data: TemplateUpdateRequest) -> Template:
        template = await db.get(Template, template_id)
        if not template:
            raise HTTPException(status_code=404, detail="Không tìm thấy mẫu văn bản")

        update_data = data.model_dump(exclude_unset=True)
        for key, value in update_data.items():
            setattr(template, key, value)

        template.updated_at = datetime.utcnow()
        await db.commit()
        await db.refresh(template)
        return template

    @staticmethod
    async def get_download_url(db: AsyncSession, template_id: int) -> str:
        template = await TemplateService.get_template(db, template_id)
        template.download_count += 1
        await db.commit()
        return await get_file_url(template.minio_object_key)

    @staticmethod
    async def compare_template(db: AsyncSession, check_result_id: uuid.UUID, template_id: int) -> TemplateComparison:
        template = await db.get(Template, template_id)
        if not template:
            raise HTTPException(status_code=404, detail="Không tìm thấy mẫu văn bản")

        comparison = TemplateComparison(
            check_result_id=check_result_id,
            template_id=template_id,
            missing_sections={"sections": []},
            extra_sections={"sections": []},
            structural_score=0.0
        )
        db.add(comparison)
        await db.commit()
        await db.refresh(comparison)
        return comparison