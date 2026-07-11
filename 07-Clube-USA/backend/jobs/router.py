from fastapi import APIRouter, Depends, Header, HTTPException, Query, status
from supabase import Client

from config import settings
from db.supabase import get_supabase
from jobs.schemas import (
    JobCreate,
    JobListResponse,
    JobResponse,
    JobSearchResponse,
)
from jobs.service import (
    create_job,
    deactivate_job,
    get_job,
    list_jobs,
    search_jobs_by_zip,
)

router = APIRouter(tags=["jobs"])
admin_router = APIRouter(tags=["admin"])


def _require_admin(x_admin_key: str = Header(..., alias="X-Admin-Key")) -> None:
    if not settings.ADMIN_API_KEY:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="Admin não configurado — defina ADMIN_API_KEY no servidor.",
        )
    if x_admin_key != settings.ADMIN_API_KEY:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Admin key inválida.",
        )


@router.get(
    "/jobs/search",
    response_model=JobSearchResponse,
    summary="Busca vagas por ZIP + raio (público)",
)
def search_jobs(
    zip: str = Query(..., pattern=r"^\d{5}$", description="ZIP code de 5 dígitos"),
    radius: float = Query(10.0, ge=0.1, le=50.0, description="Raio em milhas (padrão 10)"),
    category: str = Query(None, description="Filtrar por categoria"),
    job_type: str = Query(None, description="Filtrar por tipo: full_time, part_time, contract, gig"),
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
    supabase: Client = Depends(get_supabase),
) -> JobSearchResponse:
    try:
        return search_jobs_by_zip(
            supabase,
            zip_code=zip,
            radius_miles=radius,
            page=page,
            page_size=page_size,
            category=category,
            job_type=job_type,
        )
    except ValueError as exc:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail=str(exc),
        )


@router.get(
    "/jobs",
    response_model=JobListResponse,
    summary="Lista vagas ativas (público). Use ?zip=XXXXX&radius=10 para filtrar por proximidade.",
)
def list_jobs_endpoint(
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
    zip: str = Query(None, pattern=r"^\d{5}$", description="ZIP code para busca geográfica"),
    radius: float = Query(10.0, ge=0.1, le=50.0),
    category: str = Query(None, description="Filtrar por categoria"),
    job_type: str = Query(None, description="Filtrar por tipo"),
    supabase: Client = Depends(get_supabase),
):
    if zip:
        try:
            return search_jobs_by_zip(
                supabase,
                zip_code=zip,
                radius_miles=radius,
                page=page,
                page_size=page_size,
                category=category,
                job_type=job_type,
            )
        except ValueError as exc:
            raise HTTPException(
                status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
                detail=str(exc),
            )
    return list_jobs(supabase, page=page, page_size=page_size, category=category, job_type=job_type)


@router.get(
    "/jobs/{job_id}",
    response_model=JobResponse,
    summary="Detalhes de uma vaga (público)",
)
def get_job_endpoint(
    job_id: str,
    supabase: Client = Depends(get_supabase),
) -> JobResponse:
    job = get_job(supabase, job_id)
    if job is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Vaga não encontrada",
        )
    return job


@admin_router.post(
    "/admin/jobs",
    response_model=JobResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Cria vaga (admin)",
)
def create_job_endpoint(
    data: JobCreate,
    _: None = Depends(_require_admin),
    supabase: Client = Depends(get_supabase),
) -> JobResponse:
    return create_job(supabase, data)


@admin_router.delete(
    "/admin/jobs/{job_id}",
    status_code=status.HTTP_204_NO_CONTENT,
    summary="Desativa vaga (admin)",
)
def deactivate_job_endpoint(
    job_id: str,
    _: None = Depends(_require_admin),
    supabase: Client = Depends(get_supabase),
) -> None:
    found = deactivate_job(supabase, job_id)
    if not found:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Vaga não encontrada",
        )
