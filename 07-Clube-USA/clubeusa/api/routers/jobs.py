# api/routers/jobs.py — Clube USA — Fase 1.4
import re
import logging
from typing import Optional
from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel, field_validator
from deps import get_current_member, require_admin
from services.job_service import (
    list_jobs, get_job, create_job, update_job, deactivate_job,
    JOB_TYPES, SALARY_PERIODS,
)

router = APIRouter(prefix="/jobs", tags=["jobs"])
log = logging.getLogger("jobs")

_ZIP_RE = re.compile(r"^\d{5}(-\d{4})?$")


# ── Schemas ──────────────────────────────────────────────────

class JobCreate(BaseModel):
    title: str
    company: str
    description: str
    location_city: Optional[str] = None
    location_state: Optional[str] = None
    zip_code: Optional[str] = None
    job_type: str = "full_time"
    salary_min: Optional[int] = None
    salary_max: Optional[int] = None
    salary_period: Optional[str] = None
    contact_email: Optional[str] = None
    contact_url: Optional[str] = None
    expires_at: Optional[str] = None

    @field_validator("title")
    @classmethod
    def validate_title(cls, v):
        v = v.strip()
        if len(v) < 5:
            raise ValueError("Título deve ter pelo menos 5 caracteres.")
        return v[:200]

    @field_validator("description")
    @classmethod
    def validate_description(cls, v):
        v = v.strip()
        if len(v) < 20:
            raise ValueError("Descrição deve ter pelo menos 20 caracteres.")
        return v[:5000]

    @field_validator("company")
    @classmethod
    def validate_company(cls, v):
        return v.strip()[:100]

    @field_validator("zip_code")
    @classmethod
    def validate_zip(cls, v):
        if v is None:
            return v
        if not _ZIP_RE.match(v.strip()):
            raise ValueError("ZIP inválido (use 12345 ou 12345-6789).")
        return v.strip()

    @field_validator("job_type")
    @classmethod
    def validate_job_type(cls, v):
        if v not in JOB_TYPES:
            raise ValueError(f"job_type deve ser um de: {', '.join(JOB_TYPES)}.")
        return v

    @field_validator("salary_period")
    @classmethod
    def validate_salary_period(cls, v):
        if v is not None and v not in SALARY_PERIODS:
            raise ValueError(f"salary_period deve ser um de: {', '.join(SALARY_PERIODS)}.")
        return v


class JobUpdate(BaseModel):
    title: Optional[str] = None
    company: Optional[str] = None
    description: Optional[str] = None
    location_city: Optional[str] = None
    location_state: Optional[str] = None
    zip_code: Optional[str] = None
    job_type: Optional[str] = None
    salary_min: Optional[int] = None
    salary_max: Optional[int] = None
    salary_period: Optional[str] = None
    contact_email: Optional[str] = None
    contact_url: Optional[str] = None
    is_active: Optional[bool] = None
    expires_at: Optional[str] = None


# ── Member endpoints ─────────────────────────────────────────

@router.get("")
async def list_job_listings(
    zip_code: Optional[str] = None,
    job_type: Optional[str] = None,
    state: Optional[str] = None,
    limit: int = 20,
    offset: int = 0,
    member: dict = Depends(get_current_member),
):
    """Lista vagas de emprego ativas. Filtra por ZIP, tipo e estado."""
    jobs = list_jobs(
        zip_code=zip_code,
        job_type=job_type,
        location_state=state,
        limit=limit,
        offset=offset,
    )
    return {"jobs": jobs, "count": len(jobs)}


@router.get("/{job_id}")
async def get_job_listing(job_id: str, member: dict = Depends(get_current_member)):
    """Retorna detalhes completos de uma vaga ativa."""
    job = get_job(job_id)
    if not job:
        raise HTTPException(status_code=404, detail="Vaga não encontrada.")
    return job


# ── Admin endpoints ──────────────────────────────────────────

@router.post("/admin", status_code=201, dependencies=[Depends(require_admin)])
async def admin_create_job(body: JobCreate):
    """Admin: cria uma nova vaga (seed manual)."""
    try:
        job = create_job(**body.model_dump())
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    return job


@router.patch("/admin/{job_id}", dependencies=[Depends(require_admin)])
async def admin_update_job(job_id: str, body: JobUpdate):
    """Admin: atualiza campos de uma vaga."""
    try:
        updated = update_job(job_id, **body.model_dump(exclude_none=True))
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    if not updated:
        raise HTTPException(status_code=404, detail="Vaga não encontrada.")
    return updated


@router.delete("/admin/{job_id}", dependencies=[Depends(require_admin)])
async def admin_deactivate_job(job_id: str):
    """Admin: desativa uma vaga (soft delete)."""
    ok = deactivate_job(job_id)
    if not ok:
        raise HTTPException(status_code=404, detail="Vaga não encontrada.")
    return {"ok": True}
