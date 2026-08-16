"""
Teste rápido: envia uma notícia de exemplo pro Telegram.
Roda da raiz do projeto: python test_news_telegram.py

Mostra de onde as mensagens vêm:
  - Se Supabase configurado: busca artigos publicados reais
  - Se não: usa dados mockados para mostrar o formato
"""

import os, sys, requests
sys.stdout.reconfigure(encoding="utf-8")
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "dealscanner2"))

from dotenv import load_dotenv
load_dotenv(os.path.join(os.path.dirname(__file__), ".env"))

BOT_TOKEN  = os.environ.get("TELEGRAM_BOT_TOKEN", "")
CHANNEL_PT = os.environ.get("TELEGRAM_CHANNEL_PT", "")
APP_URL    = os.environ.get("APP_URL", "https://clubeusa.com")
SUPABASE_URL = os.environ.get("SUPABASE_URL", "")
SUPABASE_KEY = os.environ.get("SUPABASE_SERVICE_KEY", "")

# ── Formato da mensagem ────────────────────────────────────────

def format_article(art: dict, lang: str = "pt") -> str:
    title      = (art.get("title_pt") or art.get("title_original") or "Notícia").strip()
    summary    = (art.get("summary_pt") or "").strip()
    source_url = art.get("url", "")
    article_id = art.get("id", "DEMO-ID")

    sentences = summary.split(". ")
    excerpt = ". ".join(sentences[:2]).strip() if len(sentences) >= 2 else summary
    if excerpt and not excerpt.endswith("."):
        excerpt += "."
    excerpt = excerpt[:220]

    platform_link = f"{APP_URL}?article={article_id}"

    if lang == "es":
        cta    = f"[📲 Leer en Club USA →]({platform_link})"
        src    = f"_Fuente: [ver original]({source_url})_" if source_url else ""
        footer = "_Club USA — La información que necesitas_"
    else:
        cta    = f"[📲 Ler no Clube USA →]({platform_link})"
        src    = f"_Fonte: [ver original]({source_url})_" if source_url else ""
        footer = "_Clube USA — Informação que você precisa_"

    parts = [f"📰 *{title}*", "", excerpt, "", cta]
    if src:
        parts.append(src)
    parts.append(footer)
    return "\n".join(parts)


def send_tg(token: str, chat_id: str, text: str) -> dict:
    r = requests.post(
        f"https://api.telegram.org/bot{token}/sendMessage",
        json={"chat_id": chat_id, "text": text, "parse_mode": "Markdown",
              "disable_web_page_preview": False},
        timeout=10,
        verify=False,  # SSL workaround para Python 3.14 no Windows
    )
    return r.json()


# ── Buscar artigos ─────────────────────────────────────────────

def get_articles() -> list:
    """Busca do Supabase se configurado, senão retorna mock."""
    if SUPABASE_URL and SUPABASE_KEY:
        try:
            from supabase import create_client
            sb = create_client(SUPABASE_URL, SUPABASE_KEY)
            result = (
                sb.table("news_articles")
                .select("id,title_pt,summary_pt,url,category,relevance_score")
                .eq("status", "published")
                .order("relevance_score", desc=True)
                .limit(3)
                .execute()
            )
            if result.data:
                print(f"[OK] Supabase: {len(result.data)} artigos publicados encontrados")
                return result.data
            else:
                print("[!] Supabase conectado mas sem artigos publicados ainda.")
                print("    Dica: aprove artigos em /admin/news ou rode o news_fetcher primeiro.")
        except Exception as e:
            print(f"[!] Erro ao conectar Supabase: {e}")
            print("    Usando artigo de exemplo para demonstrar o formato.")
    else:
        print("[i] Supabase nao configurado — usando artigo de exemplo (mock).")

    # Mock para demonstrar o formato
    return [{
        "id": "exemplo-123",
        "title_pt": "EUA endurece regras para vistos H-1B de trabalhadores imigrantes",
        "summary_pt": (
            "O Departamento de Segurança Interna anunciou novas exigências para renovação de vistos H-1B, "
            "afetando diretamente milhares de brasileiros que trabalham em empresas de tecnologia nos EUA. "
            "A medida entra em vigor em 90 dias e exige comprovação adicional de vínculo empregatício."
        ),
        "url": "https://www.uscis.gov",
        "category": "immigration",
        "relevance_score": 92,
    }]


# ── Main ───────────────────────────────────────────────────────

if __name__ == "__main__":
    print("\n=== TESTE — FORMATO DAS NOTÍCIAS NO TELEGRAM ===\n")

    articles = get_articles()

    if not BOT_TOKEN or not CHANNEL_PT:
        print("\n⚠️  TELEGRAM_BOT_TOKEN ou TELEGRAM_CHANNEL_PT não configurados no .env")
        print("   Mostrando apenas o formato da mensagem:\n")
        print("─" * 60)
        print(format_article(articles[0], lang="pt"))
        print("─" * 60)
        sys.exit(0)

    art = articles[0]
    msg = format_article(art, lang="pt")

    print("Mensagem que será enviada:\n")
    print("─" * 60)
    print(msg)
    print("─" * 60)
    print(f"\nEnviando para canal PT ({CHANNEL_PT})...")

    resp = send_tg(BOT_TOKEN, CHANNEL_PT, msg)
    if resp.get("ok"):
        print("✅ Mensagem enviada com sucesso!")
        print(f"   message_id: {resp['result']['message_id']}")
        print(f"   Link da matéria: {APP_URL}?article={art['id']}")
    else:
        print(f"❌ Erro: {resp}")
        print("\nPossíveis causas:")
        print("  - Bot não é admin do canal")
        print("  - TELEGRAM_CHANNEL_PT errado (use @username ou -100xxxxxxxxxx)")
        print("  - Token inválido")
