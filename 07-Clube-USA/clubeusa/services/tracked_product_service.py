# ============================================================
#  services/tracked_product_service.py — Clube USA
#  Rastreamento de produto multi-marketplace + cupons
# ============================================================

import os
import sys
import logging
from datetime import datetime, timedelta

sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'dealscanner2'))

from product_matcher import identify_source, fetch_source_details, find_offers
from coupon_finder    import find_candidates
from coupon_verifier  import verify

log = logging.getLogger("tracked_product_service")

MAX_TRACKED_PRODUCTS = 10
RECHECK_VERIFIED_AFTER_DAYS = 7


def _supabase():
    from supabase import create_client
    return create_client(os.environ["SUPABASE_URL"], os.environ["SUPABASE_SERVICE_KEY"])


def _trigger_coupon_refresh_async(tracked_id: str):
    """Dispara refresh_coupons em background (thread) para nao bloquear a resposta da API."""
    import threading
    threading.Thread(target=refresh_coupons, args=(tracked_id,), daemon=True).start()


def create_tracked_product(member_id: str, url: str) -> dict:
    sb = _supabase()

    existing = (
        sb.table("tracked_products")
        .select("id")
        .eq("member_id", member_id)
        .eq("status", "active")
        .execute()
    )
    if len(existing.data) >= MAX_TRACKED_PRODUCTS:
        raise ValueError(f"Limite de {MAX_TRACKED_PRODUCTS} produtos rastreados atingido.")

    source, source_id = identify_source(url)
    details = fetch_source_details(source, source_id)

    insert_result = (
        sb.table("tracked_products")
        .insert({
            "member_id":  member_id,
            "source_url": url,
            "source":     source,
            "source_id":  source_id,
            "title":      details["title"],
            "image_url":  details.get("image_url"),
        })
        .execute()
    ).data
    if not insert_result:
        raise ValueError("Não foi possível criar o produto rastreado.")
    inserted = insert_result[0]

    offers = [{"marketplace": source, "price": details["price"], "url": details["url"]}]
    offers += find_offers(details["title"], exclude_source=source)

    try:
        for offer in offers:
            sb.table("tracked_product_offers").upsert({
                "tracked_product_id": inserted["id"],
                "marketplace":        offer["marketplace"],
                "price":              offer["price"],
                "url":                offer["url"],
            }, on_conflict="tracked_product_id,marketplace").execute()
    except Exception:
        sb.table("tracked_products").delete().eq("id", inserted["id"]).execute()
        raise ValueError("Não foi possível salvar as ofertas encontradas. Tente novamente.")

    _trigger_coupon_refresh_async(inserted["id"])

    inserted["offers"] = offers
    return inserted


def list_tracked_products(member_id: str) -> list:
    sb = _supabase()
    products = (
        sb.table("tracked_products")
        .select("*")
        .eq("member_id", member_id)
        .neq("status", "cancelled")
        .order("created_at", desc=True)
        .execute()
    ).data

    for p in products:
        p["offers"]  = sb.table("tracked_product_offers").select("*").eq("tracked_product_id", p["id"]).execute().data
        p["coupons"] = sb.table("tracked_product_coupons").select("*").eq("tracked_product_id", p["id"]).execute().data

    return products


def get_tracked_product(tracked_id: str, member_id: str) -> dict | None:
    sb = _supabase()
    result = (
        sb.table("tracked_products")
        .select("*")
        .eq("id", tracked_id)
        .eq("member_id", member_id)
        .execute()
    )
    if not result.data:
        return None

    p = result.data[0]
    p["offers"]  = sb.table("tracked_product_offers").select("*").eq("tracked_product_id", tracked_id).execute().data
    p["coupons"] = sb.table("tracked_product_coupons").select("*").eq("tracked_product_id", tracked_id).execute().data
    return p


def cancel_tracked_product(tracked_id: str, member_id: str) -> bool:
    sb = _supabase()
    result = (
        sb.table("tracked_products")
        .update({"status": "cancelled"})
        .eq("id", tracked_id)
        .eq("member_id", member_id)
        .execute()
    )
    return len(result.data) > 0


def refresh_coupons(tracked_id: str):
    """Busca cupons candidatos e verifica os elegiveis. Chamado apos criar o produto e no ciclo do scheduler."""
    sb = _supabase()

    product_rows = sb.table("tracked_products").select("id, title").eq("id", tracked_id).execute().data
    if not product_rows:
        return
    product = product_rows[0]

    offers = sb.table("tracked_product_offers").select("marketplace, url").eq("tracked_product_id", tracked_id).execute().data

    for offer in offers:
        marketplace = offer["marketplace"]
        candidates  = find_candidates(product["title"], marketplace)

        for cand in candidates:
            existing = (
                sb.table("tracked_product_coupons")
                .select("verified, last_verified_at")
                .eq("tracked_product_id", tracked_id)
                .eq("marketplace", marketplace)
                .eq("code", cand["code"])
                .execute()
            ).data

            needs_verify = True
            if existing:
                last = existing[0].get("last_verified_at")
                if isinstance(last, str) and existing[0].get("verified") is not None:
                    age = datetime.now() - datetime.fromisoformat(last)
                    needs_verify = age > timedelta(days=RECHECK_VERIFIED_AFTER_DAYS)

            row = {
                "tracked_product_id": tracked_id,
                "marketplace":        marketplace,
                "code":               cand["code"],
                "description":        cand["description"],
                "source":             cand["source"],
            }

            if needs_verify:
                result = verify(marketplace, cand["code"], offer["url"])
                row["verified"]         = result
                row["last_verified_at"] = datetime.now().isoformat()

            sb.table("tracked_product_coupons").upsert(
                row, on_conflict="tracked_product_id,marketplace,code"
            ).execute()
