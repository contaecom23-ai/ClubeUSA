"""
Utilitários de geolocalização para busca por ZIP + raio.

Decisão de design (1k→1M):
- Haversine em Python é suficiente para filtrar ≤500 promoções (MVP).
- Quando o volume de promoções crescer (>50k), migrar para PostGIS
  ST_DWithin, que faz a filtragem no banco. Nenhuma decisão irreversível aqui:
  a tabela zip_codes e as colunas latitude/longitude já existem para essa migração futura.
"""
import math
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from supabase import Client

EARTH_RADIUS_MILES = 3956.0
MIN_RADIUS_MILES = 1.0
MAX_RADIUS_MILES = 50.0


def haversine_miles(lat1: float, lon1: float, lat2: float, lon2: float) -> float:
    """Distância em milhas entre dois pontos (fórmula de Haversine)."""
    dlat = math.radians(lat2 - lat1)
    dlon = math.radians(lon2 - lon1)
    a = (
        math.sin(dlat / 2) ** 2
        + math.cos(math.radians(lat1))
        * math.cos(math.radians(lat2))
        * math.sin(dlon / 2) ** 2
    )
    return EARTH_RADIUS_MILES * 2 * math.atan2(math.sqrt(a), math.sqrt(1.0 - a))


def clamp_radius(radius_miles: float) -> float:
    return max(MIN_RADIUS_MILES, min(MAX_RADIUS_MILES, float(radius_miles)))


def lookup_zip_centroid(db: "Client", zip_code: str) -> tuple[float, float] | None:
    """
    Retorna (latitude, longitude) do centroide do ZIP na tabela zip_codes,
    ou None se o ZIP não estiver cadastrado.
    Falha silenciosa: não quebra o fluxo se a tabela estiver vazia.
    """
    try:
        result = (
            db.table("zip_codes")
            .select("latitude,longitude")
            .eq("zip", zip_code.strip())
            .execute()
        )
        if result.data:
            row = result.data[0]
            lat = row.get("latitude")
            lon = row.get("longitude")
            if lat is not None and lon is not None:
                return float(lat), float(lon)
    except Exception:
        pass
    return None


def filter_promotions_by_zip(
    items: list[dict],
    zip_code: str,
    centroid: tuple[float, float] | None,
    radius_miles: float,
) -> list[dict]:
    """
    Filtra lista de promoções por ZIP + raio.

    Regras:
    - Promoção sem lat/lng e sem zip_code → nacional → sempre exibida.
    - Promoção sem lat/lng mas com zip_code → sem dado geo → fallback exact match.
    - Promoção com lat/lng → filtrada por distância ao centroide buscado.
    """
    radius = clamp_radius(radius_miles)

    if centroid:
        search_lat, search_lon = centroid

        def _keep(p: dict) -> bool:
            lat = p.get("latitude")
            lon = p.get("longitude")
            if lat is None or lon is None:
                # Sem coordenadas: nacional (sem zip_code) ou exact match
                return not p.get("zip_code") or p.get("zip_code") == zip_code
            return haversine_miles(search_lat, search_lon, float(lat), float(lon)) <= radius

        return [p for p in items if _keep(p)]
    else:
        # ZIP não na base: fallback exact match
        return [p for p in items if not p.get("zip_code") or p.get("zip_code") == zip_code]
