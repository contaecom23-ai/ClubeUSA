"""
utils/geo.py — Utilidades geograficas para busca por ZIP + raio

Estrategia: geocoding via Nominatim (OpenStreetMap, gratuito, sem API key).
- Taxa limite: 1 req/s — aceitavel porque so geocodificamos quando membro
  atualiza seu ZIP (evento raro vs consultas de deals que sao frequentes).
- Resultado armazenado no banco (lat/lng do membro); proximas consultas
  usam os valores salvos, sem nova chamada a API.
"""
from __future__ import annotations

import math
import time
import urllib.request
import urllib.parse
import json
import re
import logging

logger = logging.getLogger(__name__)

_US_ZIP_RE = re.compile(r"^\d{5}$")

# Simples throttle para respeitar rate-limit do Nominatim (1 req/s)
_last_nominatim_call: float = 0.0


def is_valid_us_zip(zip_code: str) -> bool:
    return bool(_US_ZIP_RE.match(zip_code or ""))


def geocode_zip(zip_code: str) -> tuple[float, float] | None:
    """
    Converte ZIP code US em (lat, lng) usando Nominatim.
    Retorna None se o ZIP nao for encontrado ou houver erro de rede.
    Nunca lanca excecao — falha silenciosa com log.
    """
    global _last_nominatim_call

    if not is_valid_us_zip(zip_code):
        return None

    # Throttle: espera ate 1s entre chamadas
    elapsed = time.monotonic() - _last_nominatim_call
    if elapsed < 1.0:
        time.sleep(1.0 - elapsed)

    params = urllib.parse.urlencode({
        "postalcode": zip_code,
        "country": "US",
        "format": "json",
        "limit": 1,
    })
    url = f"https://nominatim.openstreetmap.org/search?{params}"
    req = urllib.request.Request(url, headers={"User-Agent": "ClubeUSA/1.0 (contato@clubeusa.com)"})

    try:
        _last_nominatim_call = time.monotonic()
        with urllib.request.urlopen(req, timeout=5) as resp:
            data = json.loads(resp.read())
        if data:
            return float(data[0]["lat"]), float(data[0]["lon"])
        logger.warning("geocode_zip: ZIP %s nao encontrado no Nominatim", zip_code)
        return None
    except Exception as exc:
        logger.warning("geocode_zip: erro ao geocodificar %s: %s", zip_code, exc)
        return None


def haversine_miles(lat1: float, lng1: float, lat2: float, lng2: float) -> float:
    """Distancia em milhas entre dois pontos (lat/lng em graus decimais)."""
    R = 3_958.8  # raio da Terra em milhas
    phi1, phi2 = math.radians(lat1), math.radians(lat2)
    dphi = math.radians(lat2 - lat1)
    dlambda = math.radians(lng2 - lng1)
    a = math.sin(dphi / 2) ** 2 + math.cos(phi1) * math.cos(phi2) * math.sin(dlambda / 2) ** 2
    return R * 2 * math.atan2(math.sqrt(a), math.sqrt(1 - a))


def filter_deals_by_radius(
    deals: list[dict],
    member_lat: float,
    member_lng: float,
    radius_miles: float,
) -> list[dict]:
    """
    Filtra lista de deals:
    - Deals sem localizacao (is_local=False ou lat/lng nulos) passam sempre.
    - Deals locais so passam se estiverem dentro do raio.
    """
    result = []
    for deal in deals:
        if not deal.get("is_local") or deal.get("lat") is None or deal.get("lng") is None:
            result.append(deal)
            continue
        dist = haversine_miles(member_lat, member_lng, float(deal["lat"]), float(deal["lng"]))
        if dist <= radius_miles:
            deal = {**deal, "_distance_miles": round(dist, 1)}
            result.append(deal)
    return result
