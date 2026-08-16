#!/usr/bin/env python3
# ============================================================
#  scheduler.py — Agendador com fuso horario + segmentacao
#
#  - Envia no horario LOCAL de cada membro (ET, CT, MT, PT)
#  - Free: 1 deal/horario da categoria escolhida
#  - VIP:  3 deals/horario de ate 5 categorias
#  - VIP recebe 2h antes dos Free
#
#  Uso:
#    python scheduler.py           — roda em loop
#    python scheduler.py --test    — testa agora
#    python scheduler.py --status  — mostra status
# ============================================================

import os
import sys
import time
import json
import random
import logging
from datetime import datetime, timedelta
from pathlib import Path

import config
from categories import (
    TIMEZONES, get_timezone, get_plan_rules,
    get_category_label, CATEGORY_ORDER
)
from scanner      import load_db, save_db, run_scan, run_scan_mock
from sender       import format_message, format_message_telegram, _send_message, _send_whatsapp, load_sent, save_sent
from alert_checker import check_price_alerts
from product_matcher import fetch_source_details, find_offers
from services.tracked_product_service import refresh_coupons

try:
    from news_fetcher import fetch_and_process as fetch_news
except ImportError:
    fetch_news = None

Path("data").mkdir(exist_ok=True)
Path("logs").mkdir(exist_ok=True)

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(message)s",
    handlers=[
        logging.FileHandler(config.LOG_FILE),
        logging.StreamHandler(),
    ],
)
log = logging.getLogger("scheduler")

# ============================================================
#  CONFIGURACAO DE ENVIO
# ============================================================

# Horarios locais de envio (iguais para todos os fusos)
LOCAL_SEND_HOURS = [9, 13, 20]

# Slots do dia
SLOT_NAMES = {9: "manha", 13: "almoco", 20: "noite"}

# Arquivo de controle diario
SLOTS_FILE = "data/slots_diarios.json"
SCAN_HOUR  = 6   # varredura automatica as 6h ET


# ============================================================
#  MEMBROS — simulacao local (em producao vem do Supabase)
# ============================================================

def load_members() -> list:
    """
    Carrega membros ativos do Supabase quando disponivel.
    Fallback: arquivo local de teste (desenvolvimento).
    """
    supabase_url = os.environ.get("SUPABASE_URL", "")
    supabase_key = os.environ.get("SUPABASE_SERVICE_KEY", "")

    if supabase_url and supabase_key:
        try:
            import sys as _sys
            _clubeusa = str(Path(__file__).resolve().parent.parent / "clubeusa")
            if _clubeusa not in _sys.path:
                _sys.path.insert(0, _clubeusa)
            from utils.security import decrypt
            from supabase import create_client

            sb = create_client(supabase_url, supabase_key)
            result = sb.table("members").select(
                "id,phone_enc,plan,categories,state,language"
            ).eq("status", "active").is_("deleted_at", "null").execute()

            members = []
            for row in (result.data or []):
                try:
                    phone = decrypt(row["phone_enc"])
                except Exception:
                    continue  # pula se descriptografia falhar
                members.append({
                    "id":         row["id"],
                    "phone":      phone,
                    "plan":       row["plan"],
                    "categories": row["categories"] or ["all"],
                    "state":      row.get("state") or "massachusetts",
                    "language":   row.get("language", "pt"),
                })
            log.info(f"Membros carregados do Supabase: {len(members)}")
            return members
        except Exception as e:
            log.warning(f"Supabase indisponivel, usando fallback local: {e}")

    # Fallback local para desenvolvimento
    p = Path("data/members_test.json")
    if p.exists():
        return json.loads(p.read_text())

    members = [
        {"id":"m1","phone":"+15085551001","plan":"free",
         "categories":["electronics"],"state":"massachusetts","language":"pt"},
        {"id":"m2","phone":"+16175551002","plan":"vip",
         "categories":["beauty","fashion","shoes"],"state":"new york","language":"pt"},
        {"id":"m3","phone":"+14085551003","plan":"free",
         "categories":["baby"],"state":"california","language":"pt"},
        {"id":"m4","phone":"+13055551004","plan":"vip",
         "categories":["fitness","electronics","home"],"state":"florida","language":"es"},
        {"id":"m5","phone":"+17735551005","plan":"free",
         "categories":["home"],"state":"illinois","language":"pt"},
        {"id":"m6","phone":"+13235551006","plan":"vip",
         "categories":["fashion","shoes","fragrance","beauty","automotive"],
         "state":"california","language":"es"},
    ]
    p.write_text(json.dumps(members, indent=2))
    log.info(f"Criados {len(members)} membros de teste em data/members_test.json")
    return members


# ============================================================
#  CONTROLE DE SLOTS DIARIOS
# ============================================================

def load_slots() -> dict:
    p = Path(SLOTS_FILE)
    if not p.exists():
        return {}
    data = json.loads(p.read_text())
    if data.get("date") != datetime.now().strftime("%Y-%m-%d"):
        return {}
    return data.get("slots", {})


def save_slots(slots: dict):
    Path(SLOTS_FILE).write_text(json.dumps({
        "date":  datetime.now().strftime("%Y-%m-%d"),
        "slots": slots,
    }, indent=2))


def slot_key(member_id: str, hour_local: int, cat: str) -> str:
    return f"{member_id}:{hour_local}:{cat}"


# ============================================================
#  SELECAO DE DEALS POR MEMBRO
# ============================================================

def pick_deals_for_member(member: dict, n: int, exclude_ids: set) -> list:
    """
    Seleciona os melhores deals para um membro baseado
    nas categorias dele, evitando repeticao.
    """
    db         = load_db()
    sent       = load_sent()
    categories = member.get("categories", ["all"])
    plan       = member.get("plan", "free")

    # Pool de deals aprovados nao enviados para este membro
    candidates = []
    for deal in db:
        if deal["status"] not in ("approved", "sent"):
            continue
        if deal["id"] in sent:
            continue
        if deal["id"] in exclude_ids:
            continue

        # Filtra por categoria
        deal_cat = deal.get("category", "electronics")
        if "all" not in categories and deal_cat not in categories:
            continue

        candidates.append(deal)

    if not candidates:
        # Fallback: qualquer deal aprovado nao enviado hoje
        candidates = [
            d for d in db
            if d["status"] in ("approved","sent")
            and d["id"] not in sent
            and d["id"] not in exclude_ids
        ]

    if not candidates:
        return []

    # Ordena por score e pega os top N com leve randomizacao
    candidates.sort(key=lambda d: -d.get("score", 0))
    top = candidates[:max(n*3, 10)]
    selected = random.sample(top, min(n, len(top)))
    selected.sort(key=lambda d: -d.get("score", 0))
    return selected


# ============================================================
#  ENVIO PARA UM MEMBRO
# ============================================================

def send_to_member(member: dict, slot_name: str, slots_done: dict) -> int:
    """
    Envia deals para um membro no slot especificado.
    Retorna numero de deals enviados.
    """
    plan    = member.get("plan", "free")
    rules   = get_plan_rules(plan)
    n_deals = rules["deals_per_slot"]
    cats    = member.get("categories", ["all"])
    hour    = {"manha":9,"almoco":13,"noite":20}.get(slot_name, 9)

    # Verifica se ja enviou para este membro neste slot/categoria
    already_sent_ids = set()
    for cat in cats:
        key = slot_key(member["id"], hour, cat)
        if key in slots_done:
            already_sent_ids.update(slots_done[key])

    deals = pick_deals_for_member(member, n_deals, already_sent_ids)
    if not deals:
        log.info(f"  Membro {member['id']} ({plan}): sem deals disponiveis")
        return 0

    sent_count = 0
    sent       = load_sent()

    for deal in deals:
        # Adiciona categoria classificada
        if "category" not in deal or not deal["category"]:
            from categories import classify_deal
            deal["category"] = classify_deal(deal["title"], deal.get("source",""))

        lang   = member.get("language", "pt")
        msg    = format_message(deal, lang)
        msg_tg = format_message_telegram(deal, lang)
        ok     = _send_message(msg, msg_tg, recipient=member["phone"], lang=lang)

        if ok:
            sent_count += 1
            sent.add(deal["id"])

            # Registra no controle de slots
            for cat in cats:
                key = slot_key(member["id"], hour, cat)
                if key not in slots_done:
                    slots_done[key] = []
                slots_done[key].append(deal["id"])

            # Delay anti-spam entre mensagens
            if len(deals) > 1:
                delay = random.randint(3, 8)
                time.sleep(delay)

    save_sent(sent)
    return sent_count


# ============================================================
#  DISPARO DE UM SLOT
# ============================================================

def fire_slot(slot_name: str, plan_filter: str = None):
    """
    Dispara envios para um slot (manha/almoco/noite).
    plan_filter: 'vip' envia so para VIP, None envia para todos.
    """
    members    = load_members()
    slots_done = load_slots()
    now_utc    = datetime.utcnow()
    total_sent = 0

    log.info(f"Slot '{slot_name}' | plano={plan_filter or 'todos'} | {len(members)} membros")

    for member in members:
        plan  = member.get("plan", "free")

        # Filtra por plano se especificado
        if plan_filter and plan != plan_filter:
            continue

        # Verifica fuso horario do membro
        state       = member.get("state", "massachusetts")
        tz_key      = get_timezone(state)
        tz_data     = TIMEZONES[tz_key]
        hour_local  = {"manha":9,"almoco":13,"noite":20}[slot_name]

        # Converte hora local para UTC e verifica se e agora (+/- 30min)
        offset    = tz_data["utc_offset"]  # fixed offset — DST transitions not handled
        hour_utc  = (hour_local - offset) % 24
        diff_mins = abs((now_utc.hour * 60 + now_utc.minute) - hour_utc * 60)

        if diff_mins > 35 and "--test" not in sys.argv:
            continue  # nao e a hora certa para este fuso

        n = send_to_member(member, slot_name, slots_done)
        total_sent += n
        save_slots(slots_done)

        # Delay entre membros (anti-spam)
        if n > 0:
            time.sleep(random.randint(config.SEND_DELAY_MIN, config.SEND_DELAY_MAX))

    log.info(f"Slot '{slot_name}' concluido: {total_sent} mensagens enviadas")
    return total_sent


# ============================================================
#  VARREDURA AUTOMATICA
# ============================================================

def maybe_scan():
    from scanner import can_scan
    ok, msg = can_scan()
    if not ok:
        log.info(f"Scan cache: {msg}")
        return
    log.info("Iniciando varredura automatica...")
    try:
        deals, err = run_scan()
        if err:
            log.warning(f"Scan: {err}")
        else:
            auto = sum(1 for d in deals if d.get("auto_approved"))
            log.info(f"Scan: {len(deals)} novos deals ({auto} auto-aprovados)")
    except Exception as e:
        log.error(f"Scan erro: {e}")


# ============================================================
#  DIGEST SEMANAL — Domingo 18h ET
# ============================================================

def send_sunday_digest():
    """Envia Top 5 Deals da Semana para o grupo principal de cada idioma."""
    from datetime import datetime, timedelta

    db = load_db()
    week_ago = datetime.now() - timedelta(days=7)

    week_deals = [
        d for d in db
        if d.get("status") == "sent"
        and d.get("sent_at")
        and datetime.fromisoformat(d["sent_at"]) > week_ago
    ]

    if not week_deals:
        log.info("Digest domingo: nenhum deal enviado essa semana")
        return

    week_deals.sort(key=lambda d: -d.get("score", 0))
    top5 = week_deals[:5]

    def make_digest(lang: str) -> str:
        if lang == "es":
            header = "*🏆 TOP 5 DEALS DE LA SEMANA — CLUB USA*\n"
            footer = "\n_Club USA — Cada semana los mejores deals para ti_"
        else:
            header = "*🏆 TOP 5 DEALS DA SEMANA — CLUBE USA*\n"
            footer = "\n_Clube USA — Toda semana os melhores deals para você_"

        items = []
        for i, deal in enumerate(top5, 1):
            if lang == "es":
                line = (
                    f"{i}. *{deal['title'][:60]}*\n"
                    f"   Antes: ~${deal['price_was']:.2f}~  Ahora: *${deal['price_now']:.2f}* (-{deal['discount_pct']}%)\n"
                    f"   {deal['affiliate_url']}"
                )
            else:
                line = (
                    f"{i}. *{deal['title'][:60]}*\n"
                    f"   De: ~${deal['price_was']:.2f}~  Por: *${deal['price_now']:.2f}* (-{deal['discount_pct']}%)\n"
                    f"   {deal['affiliate_url']}"
                )
            items.append(line)

        return header + "\n\n".join(items) + footer

    _send_message(make_digest("pt"), make_digest("pt"), lang="pt")
    time.sleep(random.randint(5, 10))
    _send_message(make_digest("es"), make_digest("es"), lang="es")
    log.info(f"Digest domingo enviado: {len(top5)} deals")


# ============================================================
#  DIGEST DIARIO DE NOTICIAS — 13h UTC (8h ET)
# ============================================================

def _format_news_article(art: dict, lang: str) -> str:
    """Formata uma notícia como manchete para Telegram."""
    app_url    = getattr(config, "APP_URL", "https://clubeusa.com")
    title      = (art.get("title_pt") or "").strip()
    summary    = (art.get("summary_pt") or "").strip()
    source_url = art.get("url", "")
    article_id = art.get("id", "")

    # Trecho: primeiras 2 frases do resumo, máx 220 chars
    excerpt = summary
    sentences = summary.split(". ")
    if len(sentences) >= 2:
        excerpt = ". ".join(sentences[:2]).strip()
        if not excerpt.endswith("."):
            excerpt += "."
    excerpt = excerpt[:220]

    platform_link = f"{app_url}?article={article_id}"

    if lang == "es":
        cta   = f"[📲 Leer en Club USA →]({platform_link})"
        src   = f"_Fuente: [ver original]({source_url})_" if source_url else ""
        footer = "_Club USA — La información que necesitas_"
    else:
        cta   = f"[📲 Ler no Clube USA →]({platform_link})"
        src   = f"_Fonte: [ver original]({source_url})_" if source_url else ""
        footer = "_Clube USA — Informação que você precisa_"

    parts = [f"📰 *{title}*", "", excerpt, "", cta]
    if src:
        parts.append(src)
    parts.append(footer)
    return "\n".join(parts)


def send_news_digest():
    """Envia top 5 noticias do dia via Telegram — uma por mensagem (13h UTC = 8h ET)."""
    if not (getattr(config, 'SUPABASE_URL', None) and getattr(config, 'SUPABASE_SERVICE_KEY', None)):
        log.info("News digest: Supabase nao configurado, ignorando.")
        return

    try:
        import time as _time
        import random as _random
        from supabase import create_client
        from datetime import datetime as _dt, timedelta as _td, timezone

        sb = create_client(config.SUPABASE_URL, config.SUPABASE_SERVICE_KEY)
        since = (_dt.now(timezone.utc) - _td(hours=24)).isoformat()

        articles = (
            sb.table("news_articles")
            .select("id,title_pt,summary_pt,url,category,source_id")
            .eq("status", "published")
            .eq("sent_in_digest", False)
            .gte("published_at", since)
            .order("relevance_score", desc=True)
            .limit(5)
            .execute()
        ).data or []

        if not articles:
            log.info("News digest: sem artigos novos para enviar.")
            return

        for art in articles:
            msg_pt = _format_news_article(art, lang="pt")
            msg_es = _format_news_article(art, lang="es")
            _send_message(msg_pt, msg_pt, lang="pt")
            _time.sleep(_random.randint(4, 8))
            _send_message(msg_es, msg_es, lang="es")
            _time.sleep(_random.randint(8, 15))  # pausa entre artigos

        ids = [a["id"] for a in articles if "id" in a]
        if ids:
            sb.table("news_articles").update({"sent_in_digest": True}).in_("id", ids).execute()

        log.info(f"News digest enviado: {len(articles)} artigos (um por mensagem)")
    except Exception as e:
        log.error(f"Erro no news digest: {e}")


# ============================================================
#  PROXIMO EVENTO
# ============================================================

def seconds_until_utc(hour_utc: int) -> float:
    now    = datetime.utcnow()
    target = now.replace(hour=hour_utc, minute=0, second=5, microsecond=0)
    if target <= now:
        target += timedelta(days=1)
    return (target - now).total_seconds()


def seconds_until_sunday_23h_utc() -> float:
    """Segundos ate proximo domingo as 23h UTC (= 18h ET sem DST)."""
    now = datetime.utcnow()
    days_until_sunday = (6 - now.weekday()) % 7
    target = now.replace(hour=23, minute=0, second=5, microsecond=0) + timedelta(days=days_until_sunday)
    if target <= now:
        target += timedelta(days=7)
    return (target - now).total_seconds()


def build_event_queue() -> list:
    """
    Constroi fila de eventos considerando todos os fusos.
    VIP dispara 2h antes do Free em cada slot.
    """
    events = []

    for tz_key, tz_data in TIMEZONES.items():
        offset = tz_data["utc_offset"]
        for hour_local in LOCAL_SEND_HOURS:
            hour_utc = (hour_local - offset) % 24
            slot     = SLOT_NAMES[hour_local]

            # VIP dispara 2h antes (se VIP antecipacao ativada)
            vip_rules = get_plan_rules("vip")
            if vip_rules["advance_hours"] > 0:
                vip_utc = (hour_utc - vip_rules["advance_hours"]) % 24
                events.append({
                    "utc_hour": vip_utc,
                    "type":     "slot_vip",
                    "slot":     slot,
                    "tz":       tz_key,
                    "plan":     "vip",
                    "secs":     seconds_until_utc(vip_utc),
                })

            events.append({
                "utc_hour": hour_utc,
                "type":     "slot_free",
                "slot":     slot,
                "tz":       tz_key,
                "plan":     None,
                "secs":     seconds_until_utc(hour_utc),
            })

    # Varredura diaria as 6h ET = 11h UTC
    events.append({
        "utc_hour": 11,
        "type":     "scan",
        "slot":     None,
        "tz":       "eastern",
        "plan":     None,
        "secs":     seconds_until_utc(11),
    })

    # Fetch de noticias a cada 2h (UTC 7, 9, 13, 17, 21)
    for news_hour in [7, 9, 13, 17, 21]:
        events.append({
            "utc_hour": news_hour,
            "type":     "news_fetch",
            "slot":     None,
            "tz":       "eastern",
            "plan":     None,
            "secs":     seconds_until_utc(news_hour),
        })

    # Recheck de produtos rastreados a cada 6h (UTC 2, 8, 14, 20)
    for tp_hour in [2, 8, 14, 20]:
        events.append({
            "utc_hour": tp_hour,
            "type":     "tracked_products_check",
            "slot":     None,
            "tz":       "eastern",
            "plan":     None,
            "secs":     seconds_until_utc(tp_hour),
        })

    # Digest diario de noticias — 13h UTC (8h ET)
    events.append({
        "utc_hour": 13,
        "type":     "news_digest",
        "slot":     None,
        "tz":       "eastern",
        "plan":     None,
        "secs":     seconds_until_utc(13) + 60,  # 60s after news_fetch at 13h
    })

    # Digest semanal — todo domingo 18h ET = 23h UTC
    events.append({
        "utc_hour": 23,
        "type":     "sunday_digest",
        "slot":     None,
        "tz":       "eastern",
        "plan":     None,
        "secs":     seconds_until_sunday_23h_utc(),
    })

    events.sort(key=lambda e: e["secs"])
    return events


def _supabase():
    from supabase import create_client
    return create_client(config.SUPABASE_URL, config.SUPABASE_SERVICE_KEY)


def check_tracked_products():
    """Reconsulta preco de todos os produtos rastreados ativos e atualiza cupons."""
    if not config.SUPABASE_URL or not config.SUPABASE_SERVICE_KEY:
        log.warning("Supabase não configurado — rastreamento de produtos ignorado.")
        return

    sb = _supabase()
    products = sb.table("tracked_products").select("*").eq("status", "active").execute().data
    if not products:
        log.info("Nenhum produto rastreado ativo.")
        return

    log.info(f"Verificando {len(products)} produtos rastreados...")

    for product in products:
        try:
            details = fetch_source_details(product["source"], product["source_id"])
            sb.table("tracked_product_offers").upsert({
                "tracked_product_id": product["id"],
                "marketplace":        product["source"],
                "price":              details["price"],
                "url":                details["url"],
            }, on_conflict="tracked_product_id,marketplace").execute()

            for offer in find_offers(details["title"], exclude_source=product["source"]):
                sb.table("tracked_product_offers").upsert({
                    "tracked_product_id": product["id"],
                    "marketplace":        offer["marketplace"],
                    "price":              offer["price"],
                    "url":                offer["url"],
                }, on_conflict="tracked_product_id,marketplace").execute()

            refresh_coupons(product["id"])

        except Exception as e:
            log.error(f"Erro ao verificar produto rastreado {product['id']}: {e}")
            continue

    log.info("Verificação de produtos rastreados concluída.")


# ============================================================
#  LOOP PRINCIPAL
# ============================================================

def run_loop():
    log.info("=" * 55)
    log.info("Scheduler Clube USA iniciado")
    log.info("Horarios locais: 09:00 | 13:00 | 20:00")
    log.info("VIP: 2h de antecedencia em cada fuso")
    log.info("Fusos: ET | CT | MT | PT | AKT | HST")
    log.info("=" * 55)

    while True:
        events = build_event_queue()
        next_e = events[0]

        now_str = datetime.utcnow().strftime("%H:%M UTC")
        log.info(
            f"Proximo: [{next_e['type']}] slot={next_e['slot']} "
            f"tz={next_e['tz']} em {int(next_e['secs']/60)} min "
            f"({now_str})"
        )

        time.sleep(next_e["secs"])

        if next_e["type"] == "scan":
            maybe_scan()
            check_price_alerts()
        elif next_e["type"] in ("slot_vip","slot_free"):
            plan = "vip" if next_e["type"] == "slot_vip" else None
            fire_slot(next_e["slot"], plan_filter=plan)
        elif next_e["type"] == "sunday_digest":
            from datetime import datetime
            if datetime.utcnow().weekday() == 6:  # 6 = domingo
                send_sunday_digest()
        elif next_e["type"] == "news_fetch":
            if fetch_news:
                fetch_news()
        elif next_e["type"] == "news_digest":
            send_news_digest()
        elif next_e["type"] == "tracked_products_check":
            check_tracked_products()

        time.sleep(90)  # buffer para nao re-disparar o mesmo evento


# ============================================================
#  MODO TEST
# ============================================================

def run_test():
    log.info("=== MODO TEST — disparando todos os slots agora ===")

    # Carrega mock se DB vazio
    db = load_db()
    if not db:
        run_scan_mock()

    # Aprova todos para o teste
    db = load_db()
    from categories import classify_deal
    for d in db:
        if d["status"] == "pending":
            d["status"] = "approved"
        if not d.get("category"):
            d["category"] = classify_deal(d["title"], d.get("source",""))
    save_db(db)

    # Limpa slots do dia
    Path(SLOTS_FILE).unlink(missing_ok=True)

    members = load_members()
    log.info(f"\n{len(members)} membros de teste:")
    for m in members:
        cats = ", ".join(m["categories"])
        tz   = get_timezone(m["state"])
        log.info(f"  {m['id']} | {m['plan'].upper()} | {m['state']} ({tz}) | cats: {cats}")

    log.info("\n--- Testando slot MANHA ---")
    fire_slot("manha")

    log.info("\n--- Testando slot ALMOCO ---")
    fire_slot("almoco")

    log.info("\n--- Testando slot NOITE ---")
    fire_slot("noite")

    log.info("\n=== Teste concluido ===")


# ============================================================
#  STATUS
# ============================================================

def show_status():
    members = load_members()
    db      = load_db()
    sent    = load_sent()

    approved   = sum(1 for d in db if d["status"] == "approved")
    pending    = sum(1 for d in db if d["status"] == "pending")
    sent_today = sum(1 for d in db if d.get("slot"))

    print("\n" + "="*55)
    print("CLUBE USA — STATUS DO SCHEDULER")
    print("="*55)
    print(f"Membros ativos:     {len(members)}")
    print(f"  Free:             {sum(1 for m in members if m['plan']=='free')}")
    print(f"  VIP:              {sum(1 for m in members if m['plan']=='vip')}")
    print(f"\nDeals disponiveis:  {approved} aprovados | {pending} pendentes")
    print(f"Enviados hoje:      {sent_today}")
    print(f"\nHorarios locais:    09:00 | 13:00 | 20:00")
    print(f"VIP antecipacao:    2h antes")
    print()

    # Proximos eventos
    events = build_event_queue()
    print("Proximos 5 eventos (UTC):")
    for e in events[:5]:
        mins = int(e["secs"]/60)
        hrs  = mins//60
        mins = mins%60
        print(f"  {e['utc_hour']:02d}:00 UTC | {e['type']:<12} | slot={e['slot']} | tz={e['tz']} | em {hrs}h{mins:02d}m")

    print("="*55+"\n")


if __name__ == "__main__":
    if "--test"   in sys.argv: run_test()
    elif "--status" in sys.argv: show_status()
    else: run_loop()
