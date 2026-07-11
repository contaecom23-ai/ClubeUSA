from datetime import datetime, timezone
from typing import Optional

from supabase import Client

from geo.haversine import haversine_miles
from jobs.schemas import (
    JobCreate,
    JobListResponse,
    JobResponse,
    JobSearchResponse,
    JobWithDistanceResponse,
)


def _lookup_zip_coords(supabase: Client, zip_code: str) -> Optional[tuple[float, float]]:
    result = (
        supabase.table("zip_codes")
        .select("latitude,longitude")
        .eq("zip", zip_code)
        .maybe_single()
        .execute()
    )
    if not result.data:
        return None
    return result.data["latitude"], result.data["longitude"]


def list_jobs(
    supabase: Client,
    page: int = 1,
    page_size: int = 20,
    category: Optional[str] = None,
    job_type: Optional[str] = None,
) -> JobListResponse:
    offset = (page - 1) * page_size
    now_iso = datetime.now(timezone.utc).isoformat()

    query = (
        supabase.table("jobs")
        .select("*", count="exact")
        .eq("active", True)
        .or_(f"expires_at.is.null,expires_at.gt.{now_iso}")
    )
    if category:
        query = query.eq("category", category)
    if job_type:
        query = query.eq("job_type", job_type)

    result = (
        query
        .order("created_at", desc=True)
        .range(offset, offset + page_size - 1)
        .execute()
    )

    items = [JobResponse(**row) for row in (result.data or [])]
    total = result.count or 0

    return JobListResponse(
        items=items,
        total=total,
        page=page,
        page_size=page_size,
        has_more=(offset + page_size) < total,
    )


def search_jobs_by_zip(
    supabase: Client,
    zip_code: str,
    radius_miles: float,
    page: int = 1,
    page_size: int = 20,
    category: Optional[str] = None,
    job_type: Optional[str] = None,
) -> JobSearchResponse:
    """
    Retorna vagas dentro de `radius_miles` do ZIP informado.

    Vagas sem zip_code (remotas / nacionais) são sempre inclusas sem distância.
    Mesma estratégia Haversine em Python das promoções — aceitável até ~10k vagas.
    """
    origin = _lookup_zip_coords(supabase, zip_code)
    if origin is None:
        raise ValueError(
            f"ZIP {zip_code!r} não encontrado. "
            "Verifique se o seed de zip_codes foi executado no Supabase."
        )
    origin_lat, origin_lng = origin
    now_iso = datetime.now(timezone.utc).isoformat()

    query = (
        supabase.table("jobs")
        .select("*")
        .eq("active", True)
        .or_(f"expires_at.is.null,expires_at.gt.{now_iso}")
    )
    if category:
        query = query.eq("category", category)
    if job_type:
        query = query.eq("job_type", job_type)

    result = query.execute()

    local_items: list[JobWithDistanceResponse] = []
    remote_items: list[JobWithDistanceResponse] = []

    for row in result.data or []:
        job_lat = row.get("latitude")
        job_lng = row.get("longitude")

        if job_lat is not None and job_lng is not None:
            dist = haversine_miles(origin_lat, origin_lng, job_lat, job_lng)
            if dist > radius_miles:
                continue
            local_items.append(
                JobWithDistanceResponse(**row, distance_miles=round(dist, 2))
            )
        else:
            remote_items.append(JobWithDistanceResponse(**row, distance_miles=None))

    local_items.sort(key=lambda j: j.distance_miles or 0)
    remote_items.sort(key=lambda j: j.created_at, reverse=True)

    sorted_all = local_items + remote_items
    total = len(sorted_all)
    offset = (page - 1) * page_size
    page_items = sorted_all[offset : offset + page_size]

    return JobSearchResponse(
        items=page_items,
        total=total,
        page=page,
        page_size=page_size,
        has_more=(offset + page_size) < total,
        search_zip=zip_code,
        radius_miles=radius_miles,
    )


def get_job(supabase: Client, job_id: str) -> Optional[JobResponse]:
    result = (
        supabase.table("jobs")
        .select("*")
        .eq("id", job_id)
        .eq("active", True)
        .maybe_single()
        .execute()
    )
    if not result.data:
        return None
    return JobResponse(**result.data)


def create_job(supabase: Client, data: JobCreate) -> JobResponse:
    payload = data.model_dump(exclude_none=True)
    if "expires_at" in payload and payload["expires_at"] is not None:
        payload["expires_at"] = payload["expires_at"].isoformat()
    if "contact_email" in payload and payload["contact_email"] is not None:
        payload["contact_email"] = str(payload["contact_email"])

    if data.zip_code:
        coords = _lookup_zip_coords(supabase, data.zip_code)
        if coords:
            payload["latitude"], payload["longitude"] = coords

    result = supabase.table("jobs").insert(payload).execute()
    return JobResponse(**result.data[0])


def deactivate_job(supabase: Client, job_id: str) -> bool:
    result = (
        supabase.table("jobs")
        .update({"active": False})
        .eq("id", job_id)
        .execute()
    )
    return bool(result.data)
