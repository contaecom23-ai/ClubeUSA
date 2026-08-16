import sys, os
sys.path.insert(0, ".")
sys.path.insert(0, "dealscanner2")
from dotenv import load_dotenv
load_dotenv(".env")

from sender import format_message_telegram, _send_telegram, _send_telegram_card

deal = {
    "title": "Sony WH-1000XM5 Wireless Noise Canceling Headphones",
    "price_now": 279.99,
    "price_was": 399.99,
    "discount_pct": 30,
    "rating": 4.7,
    "reviews": 12453,
    "affiliate_url": "https://www.amazon.com/dp/B09XS7JWHH?tag=clubeusa-20",
    "source_label": "Amazon",
}

msg = format_message_telegram(deal, "pt")
print(msg)
print()
print("--- Enviando com link_preview_options ---")
ok = _send_telegram(msg, lang="pt", preview_url=deal["affiliate_url"])
print("OK" if ok else "FALHOU")
