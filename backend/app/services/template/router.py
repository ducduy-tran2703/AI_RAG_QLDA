from fastapi import APIRouter, Depends, HTTPException, UploadFile, File, Form, Query
from sqlalchemy.ext.asyncio import AsyncSession
from uuid import UUID
from typing import Optional, List
from ...shared.database import get_db
from ..auth.dependencies import get_current_active_user, require_roles
from ...shared.models.user import User
from .service import TemplateService
from .schemas import TemplateDto, TemplateCreateRequest, TemplateUpdateRequest, TemplateComparisonDto
from fastapi.responses import RedirectResponse

router = APIRouter(prefix="/templates", tags=["Templates"])


@router.get("", response_model=dict)
async def list_templates(
    page: int = Query(1, ge=1),
    limit: int = Query(20, ge=1, le=100),
    doc_type: Optional[str] = Query(None),
    is_active: Optional[bool] = Query(None),
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_active_user)
):
    templates, total = await TemplateService.get_templates(db, page, limit, doc_type, is_active)
    return {
        "templates": [TemplateDto.model_validate(t) for t in templates],
        "meta": {"page": page, "limit": limit, "total": total}
    }


@router.get("/{template_id}", response_model=TemplateDto)
async def get_template(
    template_id: int,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_active_user)
):
    template = await TemplateService.get_template(db, template_id)
    return TemplateDto.model_validate(template)


@router.get("/{template_id}/download")
async def download_template(
    template_id: int,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_active_user)
):
    url = await TemplateService.get_download_url(db, template_id)
    return RedirectResponse(url=url)


@router.post("", response_model=TemplateDto, status_code=201)
async def create_template(
    template_name: str = Form(...),
    template_code: str = Form(...),
    description: Optional[str] = Form(None),
    rule_set_id: int = Form(...),
    doc_types: str = Form("[]"),
    file: UploadFile = File(...),
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(require_roles("BIZ_ADMIN"))
):
    import json
    data = TemplateCreateRequest(
        template_name=template_name,
        template_code=template_code,
        description=description,
        rule_set_id=rule_set_id,
        doc_types=json.loads(doc_types)
    )
    template = await TemplateService.create_template(db, data, file, current_user)
    return TemplateDto.model_validate(template)


@router.put("/{template_id}", response_model=TemplateDto)
async def update_template(
    template_id: int,
    data: TemplateUpdateRequest,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(require_roles("BIZ_ADMIN"))
):
    template = await TemplateService.update_template(db, template_id, data)
    return TemplateDto.model_validate(template)


@router.post("/{check_result_id}/compare/{template_id}", response_model=TemplateComparisonDto)
async def compare_with_template(
    check_result_id: UUID,
    template_id: int,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_active_user)
):
    comparison = await TemplateService.compare_template(db, check_result_id, template_id)
    return TemplateComparisonDto.model_validate(comparison)