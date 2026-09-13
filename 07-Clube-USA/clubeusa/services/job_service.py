# ============================================================
#  services/job_service.py — Clube USA — Fase 1.4
#  Vagas de emprego com seed manual pelo admin
# ============================================================

import os
import logging
from datetime import datetime, timezone
from typing import Optional

log = logging.getLogger("job_service")

JOB_TYPES    = ("full_time", "part_time", "contract", "gig", "internship")
SALARY_PERIODS = ("hour", "week", "month", "year")
MAX_LIMIT    = 100


def _supabase():
    from supabase import create_client
    return create_client(os.environ["SUPABASE_URL"], os.environ["SUPABASE_SERVICE_KEY"])


# ============================================================
#  LEITURA
# ============================================================

def list_jobs(
    zip_code: Optional[str] = None,
    job_type: Optional[str] = None,
    location_state: Optional[str] = None,
    limit: int = 20,
    offset: int = 0,
) -> list:
    sb = _supabase()
    limit = min(limit, MAX_LIMIT)

    query = (
        sb.table("job_listings")
        .select(
            "id,title,company,location_city,location_state,zip_code,"
            "job_type,salary_min,salary_max,salary_period,created_at"
        )
        .eq("is_active", True)
        .order("created_at", desc=True)
        .limit(limit)
        .offset(offset)
    )

    if zip_code:
        query = query.eq("zip_code", zip_code.strip()[:10])
    if job_type and job_type in JOB_TYPES:
        query = query.eq("job_type", job_type)
    if location_state:
        query = query.eq("location_state", location_state.upper()[:2])

    now_iso = datetime.now(timezone.utc).isoformat()
    query = query.or_(f"expires_at.is.null,expires_at.gt.{now_iso}")

    result = query.execute()
    return result.data or []


def get_job(job_id: str) -> Optional[dict]:
    sb = _supabase()
    result = (
        sb.table("job_listings")
        .select("*")
        .eq("id", job_id)
        .eq("is_active", True)
        .execute()
    )
    if not result.data:
        return None
    job = result.data[0]
    if job.get("expires_at"):
        expires = datetime.fromisoformat(job["expires_at"].replace("Z", "+00:00"))
        if expires < datetime.now(timezone.utc):
            return None
    return job


# ============================================================
#  ESCRITA (admin only)
# ============================================================

def create_job(
    title: str,
    company: str,
    description: str,
    location_city: Optional[str] = None,
    location_state: Optional[str] = None,
    zip_code: Optional[str] = None,
    job_type: str = "full_time",
    salary_min: Optional[int] = None,
    salary_max: Optional[int] = None,
    salary_period: Optional[str] = None,
    contact_email: Optional[str] = None,
    contact_url: Optional[str] = None,
    posted_by: Optional[str] = None,
    expires_at: Optional[str] = None,
) -> dict:
    if job_type not in JOB_TYPES:
        raise ValueError(f"job_type inválido: {job_type}")
    if salary_period and salary_period not in SALARY_PERIODS:
        raise ValueError(f"salary_period inválido: {salary_period}")
    if salary_min is not None and salary_max is not None and salary_min > salary_max:
        raise ValueError("salary_min não pode ser maior que salary_max.")

    sb = _supabase()
    data = {
        "title":          title.strip()[:200],
        "company":        company.strip()[:100],
        "description":    description.strip()[:5000],
        "location_city":  location_city.strip()[:100] if location_city else None,
        "location_state": location_state.upper()[:2] if location_state else None,
        "zip_code":       zip_code.strip()[:10] if zip_code else None,
        "job_type":       job_type,
        "salary_min":     salary_min,
        "salary_max":     salary_max,
        "salary_period":  salary_period,
        "contact_email":  contact_email.strip()[:200] if contact_email else None,
        "contact_url":    contact_url.strip()[:500] if contact_url else None,
        "posted_by":      posted_by,
        "expires_at":     expires_at,
        "is_active":      True,
    }
    result = sb.table("job_listings").insert(data).execute()
    if not result.data:
        raise RuntimeError("Falha ao criar vaga.")
    log.info(f"Vaga criada: {result.data[0]['id']} — {title}")
    return result.data[0]


def update_job(job_id: str, **kwargs) -> Optional[dict]:
    """Atualiza campos permitidos de uma vaga. Campos nao mapeados sao ignorados."""
    allowed = {
        "title", "company", "description", "location_city", "location_state",
        "zip_code", "job_type", "salary_min", "salary_max", "salary_period",
        "contact_email", "contact_url", "is_active", "expires_at",
    }
    update_data = {k: v for k, v in kwargs.items() if k in allowed and v is not None}
    if not update_data:
        return get_job(job_id)

    sb = _supabase()
    result = sb.table("job_listings").update(update_data).eq("id", job_id).execute()
    return result.data[0] if result.data else None


def deactivate_job(job_id: str) -> bool:
    """Soft-delete: marca vaga como inativa sem apagar do banco."""
    sb = _supabase()
    result = sb.table("job_listings").update({"is_active": False}).eq("id", job_id).execute()
    return bool(result.data)
