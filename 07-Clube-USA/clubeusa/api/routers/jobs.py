# clubeusa/api/routers/jobs.py — Fase 1.4: Empregos
import os
from typing import Optional
from datetime import datetime, timezone

from fastapi import APIRouter, Depends, HTTPException, Query
from pydantic import BaseModel, field_validator, model_validator
from supabase import create_client

from deps import get_current_member, require_admin

router = APIRouter(prefix="/jobs", tags=["jobs"])

JOB_CATEGORIES = [
    "construction", "cleaning", "food_service", "retail",
    "healthcare", "tech", "transportation", "domestic", "other",
]

EMPLOYMENT_TYPES = ["full_time", "part_time", "contract", "temp"]

SALARY_PERIODS = ["hour", "week", "month", "year"]

# Colunas retornadas em listagens públicas — sem PII
_PUBLIC_COLS = (
    "id,title,company,city,state_code,zip_code,"
    "employment_type,category,salary_min,salary_max,salary_period,"
    "contact_url,language,created_at,expires_at"
)


def _sb():
    return create_client(os.environ["SUPABASE_URL"], os.environ["SUPABASE_SERVICE_KEY"])


def _is_expired(job: dict) -> bool:
    if not job.get("expires_at"):
        return False
    exp = job["expires_at"]
    if isinstance(exp, str):
        exp = datetime.fromisoformat(exp.replace("Z", "+00:00"))
    return exp < datetime.now(timezone.utc)


# ── Schemas ────────────────────────────────────────────────────

class JobCreate(BaseModel):
    title:           str
    company:         str
    description:     str
    city:            Optional[str] = None
    state_code:      Optional[str] = None
    zip_code:        Optional[str] = None
    employment_type: str = "full_time"
    category:        str = "other"
    salary_min:      Optional[float] = None
    salary_max:      Optional[float] = None
    salary_period:   Optional[str] = "hour"
    contact_url:     Optional[str] = None
    language:        str = "pt"
    expires_at:      Optional[str] = None

    @field_validator("employment_type")
    @classmethod
    def validate_employment_type(cls, v):
        if v not in EMPLOYMENT_TYPES:
            raise ValueError(f"employment_type deve ser um de: {EMPLOYMENT_TYPES}")
        return v

    @field_validator("category")
    @classmethod
    def validate_category(cls, v):
        if v not in JOB_CATEGORIES:
            raise ValueError(f"category deve ser um de: {JOB_CATEGORIES}")
        return v

    @field_validator("language")
    @classmethod
    def validate_language(cls, v):
        if v not in ("pt", "es"):
            raise ValueError("language deve ser 'pt' ou 'es'")
        return v

    @field_validator("salary_period")
    @classmethod
    def validate_salary_period(cls, v):
        if v and v not in SALARY_PERIODS:
            raise ValueError(f"salary_period deve ser um de: {SALARY_PERIODS}")
        return v

    @model_validator(mode="after")
    def validate_salary_range(self):
        if self.salary_min is not None and self.salary_max is not None:
            if self.salary_min > self.salary_max:
                raise ValueError("salary_min não pode ser maior que salary_max")
        return self

    @field_validator("title", "company", "description")
    @classmethod
    def no_empty_strings(cls, v):
        if not v or not v.strip():
            raise ValueError("Campo obrigatório não pode ser vazio")
        return v.strip()

    @field_validator("zip_code")
    @classmethod
    def validate_zip(cls, v):
        if v and not v.replace("-", "").isdigit():
            raise ValueError("zip_code deve conter apenas dígitos")
        return v


class JobUpdate(BaseModel):
    title:           Optional[str] = None
    company:         Optional[str] = None
    description:     Optional[str] = None
    city:            Optional[str] = None
    state_code:      Optional[str] = None
    zip_code:        Optional[str] = None
    employment_type: Optional[str] = None
    category:        Optional[str] = None
    salary_min:      Optional[float] = None
    salary_max:      Optional[float] = None
    salary_period:   Optional[str] = None
    contact_url:     Optional[str] = None
    language:        Optional[str] = None
    expires_at:      Optional[str] = None
    is_active:       Optional[bool] = None

    @field_validator("employment_type")
    @classmethod
    def validate_employment_type(cls, v):
        if v is not None and v not in EMPLOYMENT_TYPES:
            raise ValueError(f"employment_type deve ser um de: {EMPLOYMENT_TYPES}")
        return v

    @field_validator("category")
    @classmethod
    def validate_category(cls, v):
        if v is not None and v not in JOB_CATEGORIES:
            raise ValueError(f"category deve ser um de: {JOB_CATEGORIES}")
        return v

    @field_validator("language")
    @classmethod
    def validate_language(cls, v):
        if v is not None and v not in ("pt", "es"):
            raise ValueError("language deve ser 'pt' ou 'es'")
        return v


# ── Public endpoints ───────────────────────────────────────────

@router.get("/categories")
async def list_categories():
    return {
        "categories": JOB_CATEGORIES,
        "employment_types": EMPLOYMENT_TYPES,
        "salary_periods": SALARY_PERIODS,
    }


@router.get("")
async def list_jobs(
    category:        Optional[str] = Query(None),
    state_code:      Optional[str] = Query(None),
    zip_code:        Optional[str] = Query(None),
    employment_type: Optional[str] = Query(None),
    language:        Optional[str] = Query(None),
    limit:           int = Query(20, ge=1, le=50),
    offset:          int = Query(0, ge=0),
):
    sb = _sb()
    query = (
        sb.table("jobs")
        .select(_PUBLIC_COLS)
        .eq("is_active", True)
        .order("created_at", desc=True)
        .limit(limit)
        .offset(offset)
    )
    if category:
        if category not in JOB_CATEGORIES:
            raise HTTPException(status_code=400, detail="Categoria inválida.")
        query = query.eq("category", category)
    if state_code:
        query = query.eq("state_code", state_code.upper()[:2])
    if zip_code:
        query = query.eq("zip_code", zip_code)
    if employment_type:
        if employment_type not in EMPLOYMENT_TYPES:
            raise HTTPException(status_code=400, detail="Tipo de emprego inválido.")
        query = query.eq("employment_type", employment_type)
    if language:
        if language not in ("pt", "es"):
            raise HTTPException(status_code=400, detail="Idioma inválido.")
        query = query.eq("language", language)

    result = query.execute()
    # Filter expired server-side (RLS policy covers most cases, belt-and-suspenders)
    jobs = [j for j in (result.data or []) if not _is_expired(j)]
    return {"jobs": jobs, "offset": offset, "limit": limit, "total": len(jobs)}


@router.get("/{job_id}")
async def get_job(job_id: str):
    sb = _sb()
    result = (
        sb.table("jobs")
        .select(_PUBLIC_COLS + ",description")
        .eq("id", job_id)
        .eq("is_active", True)
        .execute()
    )
    if not result.data:
        raise HTTPException(status_code=404, detail="Vaga não encontrada.")
    job = result.data[0]
    if _is_expired(job):
        raise HTTPException(status_code=404, detail="Vaga não encontrada.")
    return job


# ── Admin endpoints ────────────────────────────────────────────

@router.post("/admin/jobs", status_code=201, dependencies=[Depends(require_admin)])
async def admin_create_job(body: JobCreate):
    sb = _sb()
    payload = body.model_dump(exclude_none=True)
    payload["posted_by_admin"] = True
    payload["is_active"] = True

    result = sb.table("jobs").insert(payload).execute()
    if not result.data:
        raise HTTPException(status_code=500, detail="Erro ao criar vaga.")
    return result.data[0]


@router.put("/admin/jobs/{job_id}", dependencies=[Depends(require_admin)])
async def admin_update_job(job_id: str, body: JobUpdate):
    sb = _sb()
    # Verify job exists
    existing = sb.table("jobs").select("id").eq("id", job_id).execute()
    if not existing.data:
        raise HTTPException(status_code=404, detail="Vaga não encontrada.")

    updates = {k: v for k, v in body.model_dump().items() if v is not None}
    if not updates:
        raise HTTPException(status_code=400, detail="Nenhum campo para atualizar.")

    result = sb.table("jobs").update(updates).eq("id", job_id).execute()
    if not result.data:
        raise HTTPException(status_code=500, detail="Erro ao atualizar vaga.")
    return result.data[0]


@router.delete("/admin/jobs/{job_id}", dependencies=[Depends(require_admin)])
async def admin_deactivate_job(job_id: str):
    sb = _sb()
    existing = sb.table("jobs").select("id,is_active").eq("id", job_id).execute()
    if not existing.data:
        raise HTTPException(status_code=404, detail="Vaga não encontrada.")

    result = sb.table("jobs").update({"is_active": False}).eq("id", job_id).execute()
    if not result.data:
        raise HTTPException(status_code=500, detail="Erro ao desativar vaga.")
    return {"ok": True, "id": job_id}


@router.get("/admin/jobs", dependencies=[Depends(require_admin)])
async def admin_list_jobs(
    is_active: Optional[bool] = Query(None),
    limit:     int = Query(50, ge=1, le=200),
    offset:    int = Query(0, ge=0),
):
    sb = _sb()
    query = (
        sb.table("jobs")
        .select("*")
        .order("created_at", desc=True)
        .limit(limit)
        .offset(offset)
    )
    if is_active is not None:
        query = query.eq("is_active", is_active)

    result = query.execute()
    return {"jobs": result.data or [], "offset": offset, "limit": limit}
