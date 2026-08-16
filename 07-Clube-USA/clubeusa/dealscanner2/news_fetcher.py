# dealscanner2/news_fetcher.py
"""
RSS Fetcher + Groq Processor para noticias do Clube USA.

Fluxo:
  1. Busca artigos novos de fontes RSS ativas no Supabase
  2. Deduplica por URL
  3. Envia para Groq: avalia relevancia (0-100) + traduz + resume em PT
  4. Salva em news_articles com status adequado
"""

import os
import logging
import json
from datetime import datetime, timezone
from pathlib import Path

import feedparser
import requests

log = logging.getLogger("news_fetcher")

RELEVANCE_PROMPT = """Você é um editor especializado em notícias para imigrantes brasileiros nos EUA.

Avalie este artigo e responda em JSON com este formato exato:
{{
  "score": <0-100>,
  "category": "<immigration|politics|community|brazil|economy|general>",
  "title_pt": "<título traduzido para português>",
  "summary_pt": "<resumo de 2-3 frases em português>"
}}

Critérios de score:
- 80-100: Diretamente relevante para brasileiros nos EUA (imigração, deportação, vistos, política americana que afeta imigrantes, comunidade brasileira nos EUA)
- 50-79: Relevante indiretamente (economia americana, notícias do Brasil, política geral)
- 20-49: Pouco relevante (esportes, entretenimento, tecnologia genérica)
- 0-19: Irrelevante (clima local, esportes locais, política municipal sem relação)

Artigo:
Título: {title}
Fonte: {source}
Descrição: {description}

Responda APENAS o JSON, sem explicações."""

DEFAULT_SOURCES = [
    {"name": "BBC Brasil", "url": "https://feeds.bbci.co.uk/portuguese/rss.xml",
     "language": "pt", "category": "brazil"},
    {"name": "G1 - Brasil", "url": "https://g1.globo.com/rss/g1/brasil/",
     "language": "pt", "category": "brazil"},
    {"name": "Reuters - US Politics", "url": "https://feeds.reuters.com/reuters/politicsNews",
     "language": "en", "category": "politics"},
    {"name": "USCIS News", "url": "https://www.uscis.gov/feeds/newsroom.xml",
     "language": "en", "category": "immigration"},
]


def _sb():
    from supabase import create_client
    return create_client(
        os.environ.get("SUPABASE_URL", ""),
        os.environ.get("SUPABASE_SERVICE_KEY", ""),
    )


def _ensure_sources():
    """Garante que as fontes padrão existam no Supabase."""
    if not os.environ.get("SUPABASE_URL"):
        return
    sb = _sb()
    for src in DEFAULT_SOURCES:
        try:
            sb.table("news_sources").upsert(src, on_conflict="url").execute()
        except Exception as e:
            log.warning(f"Erro ao inserir fonte {src['name']}: {e}")


def _fetch_rss(url: str) -> list:
    """Retorna lista de entradas do feed RSS."""
    try:
        feed = feedparser.parse(url)
        return feed.entries or []
    except Exception as e:
        log.error(f"Erro ao buscar RSS {url}: {e}")
        return []


def _evaluate_article(title: str, description: str, source_name: str) -> dict:
    """Chama Groq para avaliar relevancia e traduzir o artigo."""
    key = os.environ.get("GROQ_API_KEY", "")
    if not key:
        return {"score": 50, "category": "general", "title_pt": title, "summary_pt": description[:200]}

    prompt = RELEVANCE_PROMPT.format(
        title=title[:300],
        source=source_name,
        description=(description or "")[:500],
    )
    try:
        resp = requests.post(
            "https://api.groq.com/openai/v1/chat/completions",
            headers={"Authorization": f"Bearer {key}", "Content-Type": "application/json"},
            json={
                "model": "llama-3.1-8b-instant",
                "messages": [{"role": "user", "content": prompt}],
                "max_tokens": 300,
                "temperature": 0.3,
            },
            timeout=10,
        )
        if resp.status_code == 200:
            text = resp.json()["choices"][0]["message"]["content"].strip()
            text = text.strip("```json").strip("```").strip()
            return json.loads(text)
    except Exception as e:
        log.warning(f"Groq evaluate error: {e}")

    return {"score": 50, "category": "general", "title_pt": title, "summary_pt": ""}


def fetch_and_process():
    """
    Job principal: busca noticias de todas as fontes ativas,
    avalia com IA e salva no Supabase.
    """
    if not os.environ.get("SUPABASE_URL"):
        log.warning("Supabase nao configurado — news_fetcher ignorado.")
        return

    _ensure_sources()
    sb = _sb()

    sources = sb.table("news_sources").select("*").eq("active", True).execute().data or []
    log.info(f"Buscando noticias de {len(sources)} fontes...")

    total_new = 0

    for source in sources:
        entries = _fetch_rss(source["url"])
        log.info(f"  {source['name']}: {len(entries)} entradas")

        for entry in entries[:10]:  # max 10 por fonte por rodada
            url   = entry.get("link", "")
            title = entry.get("title", "").strip()
            desc  = entry.get("summary", "") or entry.get("description", "")

            if not url or not title:
                continue

            existing = sb.table("news_articles").select("id").eq("url", url).execute()
            if existing.data:
                continue

            evaluation = _evaluate_article(title, desc, source["name"])
            score    = evaluation.get("score", 0)
            category = evaluation.get("category", "general")
            title_pt = evaluation.get("title_pt", title)
            summary  = evaluation.get("summary_pt", "")

            status = "ready_for_review" if score >= 40 else "rejected"

            image_url = None
            if hasattr(entry, "media_content") and entry.media_content:
                image_url = entry.media_content[0].get("url")
            elif hasattr(entry, "links"):
                for lnk in entry.links:
                    if lnk.get("type", "").startswith("image/"):
                        image_url = lnk.get("href")
                        break

            try:
                sb.table("news_articles").insert({
                    "source_id":         source["id"],
                    "url":               url,
                    "title_original":    title,
                    "title_pt":          title_pt,
                    "summary_pt":        summary,
                    "image_url":         image_url,
                    "category":          category,
                    "relevance_score":   score,
                    "language_original": source.get("language", "en"),
                    "status":            status,
                }).execute()
                total_new += 1
                log.info(f"    + [{score:3d}] {status[:8]} — {title[:50]}")
            except Exception as e:
                log.warning(f"    ! Erro ao salvar artigo: {e}")

        sb.table("news_sources").update({
            "last_fetched_at": datetime.now(timezone.utc).isoformat()
        }).eq("id", source["id"]).execute()

    log.info(f"News fetch concluido: {total_new} artigos novos")
    return total_new


if __name__ == "__main__":
    import sys
    sys.path.insert(0, str(Path(__file__).parent))
    import config  # noqa
    logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(message)s")
    fetch_and_process()
