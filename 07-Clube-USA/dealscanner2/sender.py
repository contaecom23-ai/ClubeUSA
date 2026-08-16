# ============================================================
#  sender.py — Formatacao e envio com suporte a fuso + plano
# ============================================================

import os
import json
import time
import random
import logging
import requests
from datetime import datetime
from pathlib import Path

import config

log = logging.getLogger("sender")


def format_message(deal: dict, lang: str = "pt") -> str:
    """Formata mensagem com contexto de preco, badge de loja e tendencia."""
    from price_history import get_trend

    stars  = int(deal.get("rating", 0))
    star_s = "★" * stars + f" {deal['rating']}" if stars else ""
    rev    = f"{deal['reviews']:,}" if deal.get("reviews") else ""
    ctx    = deal.get("price_context")
    src    = deal.get("source_label", "")
    trend  = deal.get("trend") or get_trend(deal.get("asin", ""))

    if lang == "es":
        lines = [f"*{deal['title'][:80]}*", ""]
        if ctx:
            lines += [f"*{ctx.upper()}*", ""]
        lines += [
            f"Antes: ~${deal['price_was']:.2f}~   Ahora: *${deal['price_now']:.2f}*",
            f"Descuento: *{deal['discount_pct']}% OFF*   Tendencia: {trend}",
        ]
        if star_s:
            lines.append(f"Calificacion: {star_s}  ({rev} resenas)")
        lines += ["", deal["affiliate_url"], "",
                  f"_Club USA — Score {deal.get('score','')} ({deal.get('score_label','')}) · {src}_"]
    else:
        lines = [f"*{deal['title'][:80]}*", ""]
        if ctx:
            lines += [f"*{ctx.upper()}*", ""]
        lines += [
            f"De: ~${deal['price_was']:.2f}~   Por: *${deal['price_now']:.2f}*",
            f"Desconto: *{deal['discount_pct']}% OFF*   Tendencia: {trend}",
        ]
        if star_s:
            lines.append(f"Avaliacao: {star_s}  ({rev} reviews)")
        lines += ["", deal["affiliate_url"], "",
                  f"_Clube USA — Score {deal.get('score','')} ({deal.get('score_label','')}) · {src}_"]

    return "\n".join(lines)


def _trend_label(trend: str, lang: str) -> str:
    """Converte seta de tendencia em texto legivel. Omite se neutro."""
    if trend == "↓":
        return "📉 Preço caindo" if lang == "pt" else "📉 Precio bajando"
    if trend == "↑":
        return "📈 Preço subindo" if lang == "pt" else "📈 Precio subiendo"
    return ""  # → neutro: nao exibe nada


def format_message_telegram(deal: dict, lang: str = "pt") -> str:
    """Formata mensagem em HTML para Telegram."""
    from price_history import get_trend
    from deal_translator import translate_title

    rating  = deal.get("rating") or 0
    reviews = deal.get("reviews") or 0
    ctx     = deal.get("price_context")
    src     = deal.get("source_label", "")
    url     = deal["affiliate_url"]

    raw_title   = deal["title"]
    local_title = translate_title(raw_title, lang)
    title       = local_title[:80].replace("&", "&amp;").replace("<", "&lt;").replace(">", "&gt;")

    price_was_str = f"<s>${deal['price_was']:.2f}</s>   " if deal.get("price_was") else ""

    if rating and reviews:
        filled  = int(rating)
        empty   = 5 - filled
        stars_s = "★" * filled + "☆" * empty
        if lang == "es":
            rating_line = f"{stars_s} <b>{rating}</b>  ·  {reviews:,} reseñas"
        else:
            rating_line = f"{stars_s} <b>{rating}</b>  ·  {reviews:,} avaliações"
    else:
        rating_line = ""

    if lang == "es":
        cta   = f'<a href="{url}"><b>🔥 OBTENER MI OFERTA  →</b></a>'
        lines = [f"🛒 <b>{title}</b>", ""]
        if ctx:
            lines += [f"<b>{ctx.upper()}</b>", ""]
        lines += [
            f"Antes: {price_was_str}Ahora: <b>${deal['price_now']:.2f}</b>",
            f"<b>{deal['discount_pct']}% OFF</b>",
        ]
        if rating_line:
            lines.append(rating_line)
        lines += ["", cta, f"<i>Club USA · {src}</i>"]
    else:
        cta   = f'<a href="{url}"><b>🔥 GARANTIR MINHA OFERTA  →</b></a>'
        lines = [f"🛒 <b>{title}</b>", ""]
        if ctx:
            lines += [f"<b>{ctx.upper()}</b>", ""]
        lines += [
            f"De: {price_was_str}Por: <b>${deal['price_now']:.2f}</b>",
            f"<b>{deal['discount_pct']}% OFF</b>",
        ]
        if rating_line:
            lines.append(rating_line)
        lines += ["", cta, f"<i>Clube USA · {src}</i>"]

    return "\n".join(lines)


def _send_telegram(message: str, chat_id: str = None, lang: str = "pt", preview_url: str = None) -> bool:
    """Envia mensagem de texto via Telegram Bot API."""
    token = config.TELEGRAM_BOT_TOKEN
    if not token:
        log.info(f"[DRY-RUN Telegram]\n{message}\n{'—'*40}")
        return True

    if not chat_id:
        chat_id = config.TELEGRAM_CHANNEL_ES if lang == "es" else config.TELEGRAM_CHANNEL_PT

    if not chat_id:
        log.warning("TELEGRAM_CHANNEL_PT/ES nao configurado — dry-run")
        return True

    try:
        payload = {
            "chat_id": chat_id,
            "text": message,
            "parse_mode": "HTML",
        }
        if preview_url:
            # Bot API 7.0+: especifica qual URL usar para o link preview (mostra miniatura do produto)
            payload["link_preview_options"] = {
                "url": preview_url,
                "show_above_text": True,
                "prefer_large_media": True,
            }
        r = requests.post(
            f"https://api.telegram.org/bot{token}/sendMessage",
            json=payload,
            timeout=10,
        )
        if r.status_code != 200:
            log.error(f"Telegram {r.status_code}: {r.text[:200]}")
        return r.status_code == 200
    except Exception as e:
        log.error(f"Erro Telegram: {e}")
        return False


def _send_telegram_card(deal: dict, lang: str = "pt", chat_id: str = None) -> bool:
    """
    Envia deal como card visual (se tiver image_url) ou
    como mensagem de texto com link preview do Telegram (fallback).
    """
    token = config.TELEGRAM_BOT_TOKEN
    if not token:
        log.info("[DRY-RUN] Mensagem nao enviada")
        return True

    if not chat_id:
        chat_id = config.TELEGRAM_CHANNEL_ES if lang == "es" else config.TELEGRAM_CHANNEL_PT
    if not chat_id:
        return True

    # Com imagem: gera card visual
    if deal.get("image_url"):
        try:
            from card_generator import generate_deal_card
            card_bytes = generate_deal_card(deal, lang)
            url        = deal.get("affiliate_url", "")
            caption    = f'👉 <a href="{url}">Ver oferta</a>'
            r = requests.post(
                f"https://api.telegram.org/bot{token}/sendPhoto",
                data={"chat_id": chat_id, "caption": caption, "parse_mode": "HTML"},
                files={"photo": ("deal.png", card_bytes, "image/png")},
                timeout=20,
            )
            if r.status_code == 200:
                return True
            log.error(f"Telegram photo {r.status_code}: {r.text[:100]}")
        except Exception as e:
            log.error(f"Erro card: {e}")

    # Sem imagem: texto + link preview via link_preview_options (mostra miniatura do produto)
    return _send_telegram(
        format_message_telegram(deal, lang),
        chat_id=chat_id,
        lang=lang,
        preview_url=deal.get("affiliate_url"),
    )


def _send_whatsapp(message: str, phone: str = None) -> bool:
    """Envia mensagem via Z-API."""
    target = phone or config.WHATSAPP_GROUP_ID

    if not config.WHATSAPP_API_URL or not target:
        log.info(f"[DRY-RUN WhatsApp] Para: {target or 'grupo'}\n{message}\n{'—'*40}")
        return True

    try:
        r = requests.post(
            config.WHATSAPP_API_URL,
            json={"phone": target, "message": message},
            headers={"Client-Token": os.environ.get("ZAPI_CLIENT_TOKEN","")},
            timeout=10,
        )
        return r.status_code == 200
    except Exception as e:
        log.error(f"Erro WhatsApp: {e}")
        return False


def _send_message(message_wpp: str, message_tg: str, recipient: str = None, lang: str = "pt") -> bool:
    """Dispatcher: envia pelo mensageiro configurado em MESSENGER."""
    if config.MESSENGER == "telegram":
        return _send_telegram(message_tg, chat_id=recipient, lang=lang)
    return _send_whatsapp(message_wpp, phone=recipient)


def load_db():
    p = Path(config.DB_FILE)
    return json.loads(p.read_text()) if p.exists() else []

def save_db(deals):
    Path(config.DB_FILE).write_text(json.dumps(deals, indent=2, ensure_ascii=False))

def load_sent():
    p = Path(config.SENT_FILE)
    return set(json.loads(p.read_text())) if p.exists() else set()

def save_sent(ids):
    Path(config.SENT_FILE).write_text(json.dumps(list(ids)))


def send_deal_by_id(deal_id: str, recipient: str = None, lang: str = "pt") -> tuple:
    """Envia deal especifico pelo ID."""
    db   = load_db()
    sent = load_sent()
    for deal in db:
        if deal["id"] == deal_id:
            if deal["id"] in sent:
                return False, "Ja enviado."
            ok = _send_message(
                format_message(deal, lang),
                format_message_telegram(deal, lang),
                recipient=recipient,
                lang=lang,
            )
            if ok:
                deal["status"]  = "sent"
                deal["sent_at"] = datetime.now().isoformat()
                sent.add(deal["id"])
                save_db(db)
                save_sent(sent)
                return True, "Enviado."
            return False, "Erro no envio."
    return False, "Deal nao encontrado."


def auto_send_approved() -> int:
    """Envia todos os deals aprovados com delay anti-spam."""
    db   = load_db()
    sent = load_sent()
    n    = 0
    pending = [d for d in db if d["status"] == "approved" and d["id"] not in sent]

    for i, deal in enumerate(pending):
        ok = _send_message(
            format_message(deal),
            format_message_telegram(deal),
        )
        if ok:
            deal["status"]  = "sent"
            deal["sent_at"] = datetime.now().isoformat()
            sent.add(deal["id"])
            n += 1
        if i < len(pending) - 1:
            delay = random.randint(config.SEND_DELAY_MIN, config.SEND_DELAY_MAX)
            log.info(f"Aguardando {delay}s...")
            time.sleep(delay)

    save_db(db)
    save_sent(sent)
    log.info(f"Auto-send: {n} enviados.")
    return n


def send_price_alert(alert: dict, current_price: float, phone: str, lang: str = "pt") -> bool:
    """Envia notificacao de alerta de preco via WhatsApp."""
    title        = alert.get("product_title") or alert["asin"]
    price_before = alert.get("price_current")
    asin         = alert["asin"]
    affiliate    = f"https://www.amazon.com/dp/{asin}?tag={config.AMAZON_PARTNER_TAG}"

    if price_before:
        drop_pct = round((price_before - current_price) / price_before * 100)
        price_line = (
            f"Era: ~${price_before:.2f}~   Agora: *${current_price:.2f}*\n"
            f"Queda de *{drop_pct}% OFF* ↓"
            if lang != "es" else
            f"Antes: ~${price_before:.2f}~   Ahora: *${current_price:.2f}*\n"
            f"Bajó *{drop_pct}% OFF* ↓"
        )
    else:
        price_line = f"Agora: *${current_price:.2f}*" if lang != "es" else f"Ahora: *${current_price:.2f}*"

    if lang == "es":
        msg = (
            f"🔔 *Alerta de Precio — Club USA*\n\n"
            f"{title[:80]}\n\n"
            f"{price_line}\n\n"
            f"👉 {affiliate}"
        )
    else:
        msg = (
            f"🔔 *Alerta de Preço — Clube USA*\n\n"
            f"{title[:80]}\n\n"
            f"{price_line}\n\n"
            f"👉 {affiliate}"
        )

    if lang == "es":
        msg_tg = (
            f"🔔 <b>Alerta de Precio — Club USA</b>\n\n"
            f"{title[:80]}\n\n"
            f"{price_line}\n\n"
            f'👉 <a href="{affiliate}">Ver producto</a>'
        )
    else:
        msg_tg = (
            f"🔔 <b>Alerta de Preço — Clube USA</b>\n\n"
            f"{title[:80]}\n\n"
            f"{price_line}\n\n"
            f'👉 <a href="{affiliate}">Ver produto</a>'
        )

    return _send_message(msg, msg_tg, recipient=phone, lang=lang)
