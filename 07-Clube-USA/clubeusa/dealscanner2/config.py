# ============================================================
#  config.py — Clube USA Deal Scanner
# ============================================================

import os
from dotenv import load_dotenv
load_dotenv(os.path.join(os.path.dirname(__file__), "..", ".env"))

# --- Amazon PA-API ---
AMAZON_ACCESS_KEY  = os.environ.get("AMAZON_ACCESS_KEY", "")
AMAZON_SECRET_KEY  = os.environ.get("AMAZON_SECRET_KEY", "")
AMAZON_PARTNER_TAG = os.environ.get("AMAZON_PARTNER_TAG", "clubeusa-20")

# --- Walmart Affiliate (via Impact.com) ---
WALMART_PUBLISHER_ID = os.environ.get("WALMART_PUBLISHER_ID", "")
WALMART_API_KEY      = os.environ.get("WALMART_API_KEY", "")

# --- eBay Partner Network ---
EBAY_APP_ID      = os.environ.get("EBAY_APP_ID", "")
EBAY_CAMPAIGN_ID = os.environ.get("EBAY_CAMPAIGN_ID", "")
EBAY_CUSTOM_ID   = "clubeusa"

# --- Target Affiliate (via Impact.com) ---
TARGET_PUBLISHER_ID = os.environ.get("TARGET_PUBLISHER_ID", "")

# --- BestBuy (developer.bestbuy.com — cadastro gratis) ---
BESTBUY_API_KEY      = os.environ.get("BESTBUY_API_KEY", "")
BESTBUY_PUBLISHER_ID = os.environ.get("BESTBUY_PUBLISHER_ID", "")

# --- Slickdeals RSS (sem credencial) ---
SLICKDEALS_ENABLED = True

# ============================================================
#  FILTROS DE QUALIDADE
# ============================================================
MIN_DISCOUNT_PCT = 20
MIN_RATING       = 3.8
MIN_REVIEWS      = 50
MAX_PRICE        = 600.0
MIN_PRICE        = 5.0
TOP_N_DEALS      = 150
MIN_SCORE        = 40

# --- Auto-aprovacao ---
AUTO_APPROVE_ENABLED      = True
AUTO_APPROVE_MIN_SCORE    = 85
AUTO_APPROVE_MIN_REVIEWS  = 500
AUTO_APPROVE_MIN_DISCOUNT = 30

# --- Cache de scan (minutos entre varreduras) ---
SCAN_CACHE_MINUTES = 60

# --- Delay de envio anti-spam (segundos) ---
SEND_DELAY_MIN = 30
SEND_DELAY_MAX = 120

# --- Historico de preco ---
PRICE_HISTORY_FILE  = "data/price_history.json"
PRICE_CONTEXT_LABEL = True

# --- Mensageiro ativo: "telegram" ou "zapi" ---
MESSENGER = os.environ.get("MESSENGER", "telegram")

# --- Telegram ---
TELEGRAM_BOT_TOKEN   = os.environ.get("TELEGRAM_BOT_TOKEN", "")
TELEGRAM_CHANNEL_PT  = os.environ.get("TELEGRAM_CHANNEL_PT", "")
TELEGRAM_CHANNEL_ES  = os.environ.get("TELEGRAM_CHANNEL_ES", "")

# --- WhatsApp (Z-API) ---
WHATSAPP_API_URL  = ""
WHATSAPP_GROUP_ID = ""

# --- Arquivos ---
DB_FILE    = "data/deals.json"
SENT_FILE  = "data/sent_ids.json"
LOG_FILE   = "logs/scanner.log"
CACHE_FILE = "data/scan_cache.json"

# --- Supabase ---
SUPABASE_URL         = os.environ.get("SUPABASE_URL", "")
SUPABASE_SERVICE_KEY = os.environ.get("SUPABASE_SERVICE_KEY", "")
ENCRYPTION_KEY       = os.environ.get("ENCRYPTION_KEY", "")
ZAPI_CLIENT_TOKEN    = os.environ.get("ZAPI_CLIENT_TOKEN", "")
APP_URL              = os.environ.get("APP_URL", "https://clubeusa.com")
