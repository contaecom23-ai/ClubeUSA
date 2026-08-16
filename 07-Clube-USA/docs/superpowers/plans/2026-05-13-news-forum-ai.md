# News + Fórum + Assistente IA — Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Adicionar feed de notícias curado por IA, fórum de comunidade com resposta automática da IA, e chat assistente flutuante à plataforma ClubeUSA.

**Architecture:** Tudo cresce no Supabase e FastAPI existentes. Novas tabelas via migration SQL. Novos endpoints em routers FastAPI separados incluídos no main.py existente. Frontend em vanilla JS no platform.html existente.

**Tech Stack:** Python 3.11, FastAPI, Supabase (PostgreSQL), Groq API (llama-3.1-70b), feedparser, vanilla JS/CSS no platform.html.

---

## Mapa de Arquivos

| Ação | Arquivo | Responsabilidade |
|------|---------|-----------------|
| Criar | `clubeusa/db/news_forum_migration.sql` | Tabelas: news_sources, news_articles, news_reads, forum_*, ai_* |
| Criar | `clubeusa/api/deps.py` | Dependências compartilhadas (get_current_member, require_admin, _sb) |
| Criar | `clubeusa/api/routers/__init__.py` | Package marker |
| Criar | `clubeusa/api/routers/news.py` | GET /news, GET /news/{id}, GET /news/categories |
| Criar | `clubeusa/api/routers/forum.py` | CRUD posts, replies, votes + IA auto-reply |
| Criar | `clubeusa/api/routers/assistant.py` | POST /assistant/chat, GET /assistant/history |
| Criar | `dealscanner2/news_fetcher.py` | RSS fetch + Groq relevância/tradução |
| Criar | `tests/test_news_forum_ai.py` | Testes de unidade e integração |
| Modificar | `clubeusa/api/main.py` | Include routers, extrair deps para deps.py, admin news endpoints |
| Modificar | `dealscanner2/scheduler.py` | Job RSS a cada 2h + digest diário Telegram |
| Modificar | `clubeusa/platform.html` | Nav expandida + seções News, Forum, AI chat widget |
| Modificar | `requirements.txt` | Adicionar feedparser |

---

## Task 1: Migration SQL — Todas as tabelas novas

**Files:**
- Criar: `clubeusa/db/news_forum_migration.sql`

- [ ] **Step 1: Criar o arquivo de migration**

```sql
-- clubeusa/db/news_forum_migration.sql
-- Migration: news + forum + ai_assistant
-- Executar no Supabase SQL Editor em bancos existentes

-- ============================================================
--  NOTICIAS
-- ============================================================
CREATE TABLE IF NOT EXISTS news_sources (
    id                  UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    name                TEXT NOT NULL,
    url                 TEXT NOT NULL UNIQUE,
    language            VARCHAR(2) NOT NULL DEFAULT 'pt',
    category            VARCHAR(50) DEFAULT 'general',
    active              BOOLEAN NOT NULL DEFAULT TRUE,
    fetch_interval_min  INTEGER NOT NULL DEFAULT 120,
    last_fetched_at     TIMESTAMPTZ,
    created_at          TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

CREATE TABLE IF NOT EXISTS news_articles (
    id                  UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    source_id           UUID REFERENCES news_sources(id) ON DELETE CASCADE,
    url                 TEXT NOT NULL UNIQUE,
    title_original      TEXT NOT NULL,
    title_pt            TEXT,
    summary_pt          TEXT,
    image_url           TEXT,
    category            VARCHAR(50) NOT NULL DEFAULT 'general',
    relevance_score     SMALLINT NOT NULL DEFAULT 0,
    language_original   VARCHAR(2) NOT NULL DEFAULT 'en',
    status              VARCHAR(20) NOT NULL DEFAULT 'pending'
                        CHECK (status IN ('pending','ready_for_review','published','rejected')),
    published_at        TIMESTAMPTZ,
    sent_in_digest      BOOLEAN NOT NULL DEFAULT FALSE,
    created_at          TIMESTAMPTZ NOT NULL DEFAULT NOW()
);
CREATE INDEX IF NOT EXISTS idx_news_status    ON news_articles (status);
CREATE INDEX IF NOT EXISTS idx_news_published ON news_articles (published_at DESC) WHERE status = 'published';
CREATE INDEX IF NOT EXISTS idx_news_category  ON news_articles (category);

CREATE TABLE IF NOT EXISTS news_reads (
    id          UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    member_id   UUID NOT NULL REFERENCES members(id) ON DELETE CASCADE,
    article_id  UUID NOT NULL REFERENCES news_articles(id) ON DELETE CASCADE,
    created_at  TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    UNIQUE (member_id, article_id)
);

-- ============================================================
--  FORUM
-- ============================================================
CREATE TABLE IF NOT EXISTS forum_categories (
    id          UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    name        TEXT NOT NULL,
    slug        VARCHAR(50) NOT NULL UNIQUE,
    description TEXT,
    icon        VARCHAR(10) DEFAULT '💬',
    sort_order  SMALLINT NOT NULL DEFAULT 0,
    active      BOOLEAN NOT NULL DEFAULT TRUE
);

-- Categorias iniciais
INSERT INTO forum_categories (name, slug, description, icon, sort_order) VALUES
  ('Imigração & Documentos', 'imigracao', 'Vistos, green card, naturalização, SSN', '📋', 1),
  ('Emprego & Carreira',     'emprego',   'Vagas, currículo, direitos trabalhistas',  '💼', 2),
  ('Moradia & Apartamento',  'moradia',   'Aluguel, compra, bairros, utilities',      '🏠', 3),
  ('Saúde & Plano de Saúde', 'saude',     'Seguro saúde, médicos, farmácias',        '🏥', 4),
  ('Finanças & Banco',       'financas',  'Conta bancária, crédito, impostos',       '💰', 5),
  ('Vida nos EUA',           'vida-eua',  'Cultura, transporte, escola, rotina',     '🇺🇸', 6),
  ('Política Americana',     'politica',  'Eleições, leis, governo, imigração',      '⚖️', 7)
ON CONFLICT (slug) DO NOTHING;

CREATE TABLE IF NOT EXISTS forum_posts (
    id          UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    member_id   UUID NOT NULL REFERENCES members(id) ON DELETE CASCADE,
    category_id UUID NOT NULL REFERENCES forum_categories(id),
    title       TEXT NOT NULL,
    body        TEXT NOT NULL,
    vote_count  INTEGER NOT NULL DEFAULT 0,
    reply_count INTEGER NOT NULL DEFAULT 0,
    is_deleted  BOOLEAN NOT NULL DEFAULT FALSE,
    created_at  TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    updated_at  TIMESTAMPTZ NOT NULL DEFAULT NOW()
);
CREATE INDEX IF NOT EXISTS idx_forum_posts_cat    ON forum_posts (category_id, created_at DESC);
CREATE INDEX IF NOT EXISTS idx_forum_posts_member ON forum_posts (member_id);

CREATE TABLE IF NOT EXISTS forum_replies (
    id          UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    post_id     UUID NOT NULL REFERENCES forum_posts(id) ON DELETE CASCADE,
    member_id   UUID REFERENCES members(id) ON DELETE SET NULL,
    body        TEXT NOT NULL,
    is_ai       BOOLEAN NOT NULL DEFAULT FALSE,
    vote_count  INTEGER NOT NULL DEFAULT 0,
    is_deleted  BOOLEAN NOT NULL DEFAULT FALSE,
    created_at  TIMESTAMPTZ NOT NULL DEFAULT NOW()
);
CREATE INDEX IF NOT EXISTS idx_forum_replies_post ON forum_replies (post_id, vote_count DESC);

CREATE TABLE IF NOT EXISTS forum_votes (
    id          UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    member_id   UUID NOT NULL REFERENCES members(id) ON DELETE CASCADE,
    target_type VARCHAR(10) NOT NULL CHECK (target_type IN ('post','reply')),
    target_id   UUID NOT NULL,
    created_at  TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    UNIQUE (member_id, target_type, target_id)
);

-- ============================================================
--  ASSISTENTE IA
-- ============================================================
CREATE TABLE IF NOT EXISTS ai_sessions (
    id          UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    member_id   UUID NOT NULL REFERENCES members(id) ON DELETE CASCADE,
    created_at  TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    updated_at  TIMESTAMPTZ NOT NULL DEFAULT NOW()
);
CREATE INDEX IF NOT EXISTS idx_ai_sessions_member ON ai_sessions (member_id, updated_at DESC);

CREATE TABLE IF NOT EXISTS ai_messages (
    id          UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    session_id  UUID NOT NULL REFERENCES ai_sessions(id) ON DELETE CASCADE,
    role        VARCHAR(10) NOT NULL CHECK (role IN ('user','assistant')),
    content     TEXT NOT NULL,
    created_at  TIMESTAMPTZ NOT NULL DEFAULT NOW()
);
CREATE INDEX IF NOT EXISTS idx_ai_messages_session ON ai_messages (session_id, created_at);
```

- [ ] **Step 2: Executar no Supabase**

Abrir Supabase → SQL Editor → colar o conteúdo do arquivo → Run.
Verificar que todas as tabelas foram criadas sem erro.

- [ ] **Step 3: Commit**

```bash
git add clubeusa/db/news_forum_migration.sql
git commit -m "feat(db): migration news, forum e ai_sessions"
```

---

## Task 2: deps.py — Dependências compartilhadas

**Files:**
- Criar: `clubeusa/api/deps.py`
- Criar: `clubeusa/api/routers/__init__.py`
- Modificar: `clubeusa/api/main.py` (importar de deps.py)

- [ ] **Step 1: Criar deps.py extraindo funções de main.py**

```python
# clubeusa/api/deps.py
import os
import hmac
from fastapi import Depends, Header, HTTPException
from supabase import create_client


def _sb():
    return create_client(os.environ["SUPABASE_URL"], os.environ["SUPABASE_SERVICE_KEY"])


def get_current_member(authorization: str = Header(None)) -> dict:
    from utils.security import verify_token
    if not authorization or not authorization.startswith("Bearer "):
        raise HTTPException(status_code=401, detail="Token nao fornecido.")
    token = authorization.split(" ", 1)[1]
    payload = verify_token(token)
    if not payload:
        raise HTTPException(status_code=401, detail="Token invalido ou expirado.")
    return payload


def require_vip(member: dict = Depends(get_current_member)) -> dict:
    if member.get("plan") != "vip":
        raise HTTPException(status_code=403, detail="Recurso exclusivo para membros VIP.")
    return member


def require_paid_plan(member: dict = Depends(get_current_member)) -> dict:
    if member.get("plan") not in ("vip",):
        raise HTTPException(status_code=403, detail="Faca upgrade do seu plano.")
    return member


def require_admin(authorization: str = Header(None)) -> None:
    secret = os.environ.get("ADMIN_SECRET", "")
    expected = f"Bearer {secret}"
    if not secret or not hmac.compare_digest(
        (authorization or "").encode(), expected.encode()
    ):
        raise HTTPException(status_code=401, detail="Acesso negado.")
```

- [ ] **Step 2: Criar routers/__init__.py**

```python
# clubeusa/api/routers/__init__.py
```

- [ ] **Step 3: Atualizar main.py para importar de deps.py**

Em `clubeusa/api/main.py`, substituir as definições locais de `get_current_member`, `require_vip`, `require_paid_plan`, `require_admin` por imports:

```python
# Adicionar no topo de main.py (após os imports existentes):
from deps import get_current_member, require_vip, require_paid_plan, require_admin
```

E remover as funções duplicadas do main.py (linhas ~139–175).

- [ ] **Step 4: Testar que a API ainda funciona**

```bash
cd clubeusa && python -c "from api.main import app; print('OK')"
```
Esperado: `OK` sem erros de import.

- [ ] **Step 5: Commit**

```bash
git add clubeusa/api/deps.py clubeusa/api/routers/__init__.py clubeusa/api/main.py
git commit -m "refactor(api): extrair deps compartilhados para deps.py"
```

---

## Task 3: Router de Notícias (`/news`)

**Files:**
- Criar: `clubeusa/api/routers/news.py`
- Modificar: `clubeusa/api/main.py` (include router)
- Criar: `tests/test_news_forum_ai.py` (testes iniciais)

- [ ] **Step 1: Escrever testes que falham**

```python
# tests/test_news_forum_ai.py
import pytest
from unittest.mock import patch, MagicMock

# Dados mock
MOCK_ARTICLE = {
    "id": "article-1",
    "title_pt": "EUA anuncia nova regra de visto",
    "summary_pt": "A nova regra afeta imigrantes brasileiros.",
    "category": "immigration",
    "relevance_score": 85,
    "published_at": "2026-05-13T10:00:00+00:00",
    "url": "https://example.com/news/1",
    "image_url": None,
    "status": "published",
}

MOCK_TOKEN_PAYLOAD = {"sub": "member-1", "plan": "free"}


def make_sb_mock(data):
    """Retorna mock do Supabase com data fixo."""
    m = MagicMock()
    m.table.return_value.select.return_value.eq.return_value.order.return_value.limit.return_value.execute.return_value.data = data
    m.table.return_value.select.return_value.order.return_value.limit.return_value.execute.return_value.data = data
    return m


def test_news_categories_structure():
    """Categorias de notícias têm os campos esperados."""
    from clubeusa.api.routers.news import NEWS_CATEGORIES
    assert len(NEWS_CATEGORIES) >= 4
    for cat in NEWS_CATEGORIES:
        assert "slug" in cat
        assert "name" in cat


def test_relevance_threshold():
    """Artigos com score < 40 não aparecem no feed."""
    from clubeusa.api.routers.news import is_relevant
    assert is_relevant(39) is False
    assert is_relevant(40) is True
    assert is_relevant(100) is True
```

- [ ] **Step 2: Executar testes — devem falhar**

```bash
cd "C:\Users\g-fil\Documents\Projetos Claude\projetos-organizados\07-BrasilDeals-Clube-USA"
python -m pytest tests/test_news_forum_ai.py -v 2>&1 | head -30
```
Esperado: `ImportError` ou `ModuleNotFoundError`.

- [ ] **Step 3: Criar o router de notícias**

```python
# clubeusa/api/routers/news.py
import os
from typing import Optional
from fastapi import APIRouter, Depends, HTTPException
from deps import get_current_member, require_admin
from supabase import create_client

router = APIRouter(prefix="/news", tags=["news"])

NEWS_CATEGORIES = [
    {"slug": "immigration", "name": "Imigração",         "icon": "📋"},
    {"slug": "politics",    "name": "Política Americana", "icon": "⚖️"},
    {"slug": "community",   "name": "Comunidade",         "icon": "🤝"},
    {"slug": "brazil",      "name": "Brasil",             "icon": "🇧🇷"},
    {"slug": "economy",     "name": "Economia",           "icon": "💰"},
    {"slug": "general",     "name": "Geral",              "icon": "📰"},
]


def is_relevant(score: int) -> bool:
    return score >= 40


def _sb():
    return create_client(os.environ["SUPABASE_URL"], os.environ["SUPABASE_SERVICE_KEY"])


@router.get("/categories")
async def list_categories():
    return {"categories": NEWS_CATEGORIES}


@router.get("")
async def list_news(
    category: Optional[str] = None,
    limit: int = 20,
    offset: int = 0,
    member: dict = Depends(get_current_member),
):
    sb = _sb()
    limit = min(limit, 50)
    query = (
        sb.table("news_articles")
        .select("id,title_pt,summary_pt,category,relevance_score,published_at,url,image_url,source_id")
        .eq("status", "published")
        .order("published_at", desc=True)
        .limit(limit)
        .offset(offset)
    )
    if category:
        query = query.eq("category", category)

    result = query.execute()
    return {"articles": result.data or [], "offset": offset, "limit": limit}


@router.get("/{article_id}")
async def get_article(article_id: str, member: dict = Depends(get_current_member)):
    sb = _sb()
    result = sb.table("news_articles").select("*").eq("id", article_id).eq("status", "published").execute()
    if not result.data:
        raise HTTPException(status_code=404, detail="Artigo não encontrado.")

    # Registrar leitura e adicionar pontos (idempotente)
    try:
        sb.table("news_reads").insert({
            "member_id": member["sub"],
            "article_id": article_id,
        }).execute()
        sb.rpc("increment_points", {"p_member_id": member["sub"], "p_points": 5}).execute()
    except Exception:
        pass  # UNIQUE constraint — já leu antes, ignora

    return result.data[0]


# ── Admin ──────────────────────────────────────────────────────

@router.get("/admin/pending", dependencies=[Depends(require_admin)])
async def admin_pending_news(limit: int = 50):
    sb = _sb()
    result = (
        sb.table("news_articles")
        .select("id,title_original,title_pt,summary_pt,category,relevance_score,url,source_id,created_at")
        .eq("status", "ready_for_review")
        .order("relevance_score", desc=True)
        .limit(limit)
        .execute()
    )
    return {"articles": result.data or []}


@router.post("/admin/{article_id}/approve", dependencies=[Depends(require_admin)])
async def admin_approve_article(article_id: str):
    from datetime import datetime, timezone
    sb = _sb()
    result = sb.table("news_articles").update({
        "status": "published",
        "published_at": datetime.now(timezone.utc).isoformat(),
    }).eq("id", article_id).execute()
    if not result.data:
        raise HTTPException(status_code=404, detail="Artigo não encontrado.")
    return {"ok": True}


@router.post("/admin/{article_id}/reject", dependencies=[Depends(require_admin)])
async def admin_reject_article(article_id: str):
    sb = _sb()
    result = sb.table("news_articles").update({"status": "rejected"}).eq("id", article_id).execute()
    if not result.data:
        raise HTTPException(status_code=404, detail="Artigo não encontrado.")
    return {"ok": True}
```

- [ ] **Step 4: Include router no main.py**

No topo de `clubeusa/api/main.py`, adicionar após os imports existentes:

```python
from routers.news import router as news_router
```

E após a criação do `app`, antes das rotas existentes:

```python
app.include_router(news_router)
```

- [ ] **Step 5: Executar testes — devem passar**

```bash
python -m pytest tests/test_news_forum_ai.py::test_news_categories_structure tests/test_news_forum_ai.py::test_relevance_threshold -v
```
Esperado: 2 PASSED.

- [ ] **Step 6: Commit**

```bash
git add clubeusa/api/routers/news.py clubeusa/api/main.py tests/test_news_forum_ai.py
git commit -m "feat(api): router /news com CRUD e admin endpoints"
```

---

## Task 4: Router do Fórum (`/forum`)

**Files:**
- Criar: `clubeusa/api/routers/forum.py`
- Modificar: `clubeusa/api/main.py`
- Modificar: `tests/test_news_forum_ai.py`

- [ ] **Step 1: Adicionar testes ao arquivo de testes**

Adicionar em `tests/test_news_forum_ai.py`:

```python
def test_forum_post_points():
    """Criar post dá 20 pontos, reply dá 10."""
    from clubeusa.api.routers.forum import POST_POINTS, REPLY_POINTS
    assert POST_POINTS == 20
    assert REPLY_POINTS == 10


def test_forum_vote_idempotent():
    """Votar duas vezes no mesmo post não lança exceção — retorna already_voted."""
    from clubeusa.api.routers.forum import handle_vote_conflict
    result = handle_vote_conflict()
    assert result == {"ok": False, "reason": "already_voted"}
```

- [ ] **Step 2: Executar testes — devem falhar**

```bash
python -m pytest tests/test_news_forum_ai.py::test_forum_post_points -v
```
Esperado: `ImportError`.

- [ ] **Step 3: Criar o router do fórum**

```python
# clubeusa/api/routers/forum.py
import os
import logging
from typing import Optional
from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel, field_validator
from deps import get_current_member, require_admin
from supabase import create_client

router = APIRouter(prefix="/forum", tags=["forum"])
log = logging.getLogger("forum")

POST_POINTS  = 20
REPLY_POINTS = 10

AI_SYSTEM_PROMPT = (
    "Você é o Assistente Clube USA, especializado em ajudar imigrantes brasileiros nos EUA. "
    "Responda em português, seja direto e prático. Temas: imigração, vistos, documentos, "
    "emprego, moradia, saúde, finanças, compras nos EUA. "
    "Nunca dê conselhos jurídicos formais — sugira consultar um advogado para casos complexos. "
    "Seja acolhedor e empático — o imigrante enfrenta desafios reais."
)


def handle_vote_conflict() -> dict:
    return {"ok": False, "reason": "already_voted"}


def _sb():
    return create_client(os.environ["SUPABASE_URL"], os.environ["SUPABASE_SERVICE_KEY"])


def _groq_reply(question_title: str, question_body: str, lang: str = "pt") -> str:
    """Gera resposta da IA via Groq para uma pergunta do fórum."""
    import requests
    key = os.environ.get("GROQ_API_KEY", "")
    if not key:
        return ""
    prompt = (
        f"Um membro do Clube USA fez esta pergunta no fórum:\n\n"
        f"**{question_title}**\n\n{question_body}\n\n"
        f"Responda de forma direta, prática e acolhedora. Máximo 3 parágrafos."
    )
    try:
        resp = requests.post(
            "https://api.groq.com/openai/v1/chat/completions",
            headers={"Authorization": f"Bearer {key}", "Content-Type": "application/json"},
            json={
                "model": "llama-3.1-70b-versatile",
                "messages": [
                    {"role": "system", "content": AI_SYSTEM_PROMPT},
                    {"role": "user",   "content": prompt},
                ],
                "max_tokens": 400,
                "temperature": 0.6,
            },
            timeout=15,
        )
        if resp.status_code == 200:
            return resp.json()["choices"][0]["message"]["content"].strip()
    except Exception as e:
        log.warning(f"Groq forum reply error: {e}")
    return ""


# ── Schemas ────────────────────────────────────────────────────

class PostCreate(BaseModel):
    category_id: str
    title: str
    body: str

    @field_validator("title")
    @classmethod
    def validate_title(cls, v):
        if len(v.strip()) < 10:
            raise ValueError("Título deve ter pelo menos 10 caracteres.")
        return v.strip()[:200]

    @field_validator("body")
    @classmethod
    def validate_body(cls, v):
        if len(v.strip()) < 20:
            raise ValueError("Conteúdo deve ter pelo menos 20 caracteres.")
        return v.strip()[:5000]


class ReplyCreate(BaseModel):
    body: str

    @field_validator("body")
    @classmethod
    def validate_body(cls, v):
        if len(v.strip()) < 5:
            raise ValueError("Resposta muito curta.")
        return v.strip()[:3000]


# ── Endpoints ──────────────────────────────────────────────────

@router.get("/categories")
async def list_forum_categories():
    sb = _sb()
    result = (
        sb.table("forum_categories")
        .select("id,name,slug,description,icon,sort_order")
        .eq("active", True)
        .order("sort_order")
        .execute()
    )
    return {"categories": result.data or []}


@router.get("/posts")
async def list_posts(
    category_slug: Optional[str] = None,
    limit: int = 20,
    offset: int = 0,
    member: dict = Depends(get_current_member),
):
    sb = _sb()
    limit = min(limit, 50)
    query = (
        sb.table("forum_posts")
        .select("id,title,vote_count,reply_count,created_at,category_id")
        .eq("is_deleted", False)
        .order("created_at", desc=True)
        .limit(limit)
        .offset(offset)
    )
    if category_slug:
        cat = sb.table("forum_categories").select("id").eq("slug", category_slug).execute()
        if cat.data:
            query = query.eq("category_id", cat.data[0]["id"])

    result = query.execute()
    return {"posts": result.data or []}


@router.post("/posts", status_code=201)
async def create_post(body: PostCreate, member: dict = Depends(get_current_member)):
    sb = _sb()

    # Verificar categoria existe
    cat = sb.table("forum_categories").select("id").eq("id", body.category_id).eq("active", True).execute()
    if not cat.data:
        raise HTTPException(status_code=400, detail="Categoria inválida.")

    result = sb.table("forum_posts").insert({
        "member_id":   member["sub"],
        "category_id": body.category_id,
        "title":       body.title,
        "body":        body.body,
    }).execute()

    if not result.data:
        raise HTTPException(status_code=500, detail="Erro ao criar post.")

    post = result.data[0]
    post_id = post["id"]

    # Pontos pelo post
    sb.rpc("increment_points", {"p_member_id": member["sub"], "p_points": POST_POINTS}).execute()

    # IA responde automaticamente em background (não bloqueia o response)
    import threading
    def ai_reply():
        try:
            ai_text = _groq_reply(body.title, body.body)
            if ai_text:
                sb2 = _sb()
                sb2.table("forum_replies").insert({
                    "post_id":  post_id,
                    "body":     ai_text,
                    "is_ai":    True,
                }).execute()
                sb2.table("forum_posts").update({"reply_count": 1}).eq("id", post_id).execute()
        except Exception as e:
            log.warning(f"AI reply failed for post {post_id}: {e}")

    threading.Thread(target=ai_reply, daemon=True).start()

    return post


@router.get("/posts/{post_id}")
async def get_post(post_id: str, member: dict = Depends(get_current_member)):
    sb = _sb()
    post = sb.table("forum_posts").select("*").eq("id", post_id).eq("is_deleted", False).execute()
    if not post.data:
        raise HTTPException(status_code=404, detail="Post não encontrado.")

    replies = (
        sb.table("forum_replies")
        .select("id,body,is_ai,vote_count,created_at,member_id")
        .eq("post_id", post_id)
        .eq("is_deleted", False)
        .order("is_ai", desc=True)   # IA reply primeiro
        .order("vote_count", desc=True)
        .execute()
    )
    return {"post": post.data[0], "replies": replies.data or []}


@router.post("/posts/{post_id}/reply", status_code=201)
async def reply_post(post_id: str, body: ReplyCreate, member: dict = Depends(get_current_member)):
    sb = _sb()
    post = sb.table("forum_posts").select("id,reply_count").eq("id", post_id).eq("is_deleted", False).execute()
    if not post.data:
        raise HTTPException(status_code=404, detail="Post não encontrado.")

    result = sb.table("forum_replies").insert({
        "post_id":   post_id,
        "member_id": member["sub"],
        "body":      body.body,
        "is_ai":     False,
    }).execute()

    if not result.data:
        raise HTTPException(status_code=500, detail="Erro ao criar resposta.")

    # Atualizar reply_count
    new_count = (post.data[0].get("reply_count") or 0) + 1
    sb.table("forum_posts").update({"reply_count": new_count}).eq("id", post_id).execute()

    # Pontos pela resposta
    sb.rpc("increment_points", {"p_member_id": member["sub"], "p_points": REPLY_POINTS}).execute()

    return result.data[0]


@router.post("/posts/{post_id}/vote")
async def vote_post(post_id: str, member: dict = Depends(get_current_member)):
    sb = _sb()
    try:
        sb.table("forum_votes").insert({
            "member_id":   member["sub"],
            "target_type": "post",
            "target_id":   post_id,
        }).execute()
        # Incrementar vote_count
        post = sb.table("forum_posts").select("vote_count").eq("id", post_id).execute()
        if post.data:
            sb.table("forum_posts").update({"vote_count": (post.data[0]["vote_count"] or 0) + 1}).eq("id", post_id).execute()
        return {"ok": True}
    except Exception:
        return handle_vote_conflict()


@router.delete("/admin/posts/{post_id}", dependencies=[Depends(require_admin)])
async def admin_delete_post(post_id: str):
    sb = _sb()
    sb.table("forum_posts").update({"is_deleted": True}).eq("id", post_id).execute()
    return {"ok": True}
```

- [ ] **Step 4: Include router no main.py**

```python
# Adicionar em main.py após o import do news_router:
from routers.forum import router as forum_router
# ...
app.include_router(forum_router)
```

- [ ] **Step 5: Executar testes**

```bash
python -m pytest tests/test_news_forum_ai.py::test_forum_post_points tests/test_news_forum_ai.py::test_forum_vote_idempotent -v
```
Esperado: 2 PASSED.

- [ ] **Step 6: Commit**

```bash
git add clubeusa/api/routers/forum.py clubeusa/api/main.py tests/test_news_forum_ai.py
git commit -m "feat(api): router /forum com posts, replies, votes e IA auto-reply"
```

---

## Task 5: Router do Assistente IA (`/assistant`)

**Files:**
- Criar: `clubeusa/api/routers/assistant.py`
- Modificar: `clubeusa/api/main.py`

- [ ] **Step 1: Adicionar teste**

```python
# Em tests/test_news_forum_ai.py, adicionar:
def test_assistant_system_prompt_has_context():
    from clubeusa.api.routers.assistant import AI_SYSTEM_PROMPT
    assert "imigrante" in AI_SYSTEM_PROMPT.lower()
    assert "brasileiro" in AI_SYSTEM_PROMPT.lower()
    assert "advogado" in AI_SYSTEM_PROMPT.lower()


def test_assistant_history_limit():
    from clubeusa.api.routers.assistant import MAX_HISTORY_MESSAGES
    assert MAX_HISTORY_MESSAGES == 10
```

- [ ] **Step 2: Executar — deve falhar**

```bash
python -m pytest tests/test_news_forum_ai.py::test_assistant_system_prompt_has_context -v
```
Esperado: `ImportError`.

- [ ] **Step 3: Criar o router do assistente**

```python
# clubeusa/api/routers/assistant.py
import os
import logging
import requests
from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel
from deps import get_current_member
from supabase import create_client

router = APIRouter(prefix="/assistant", tags=["assistant"])
log = logging.getLogger("assistant")

MAX_HISTORY_MESSAGES = 10

AI_SYSTEM_PROMPT = (
    "Você é o Assistente Clube USA, especializado em ajudar imigrantes brasileiros nos EUA. "
    "Responda em português (ou espanhol se o usuário escrever em espanhol). "
    "Seja direto, prático e acolhedor. "
    "Temas que você domina: imigração, vistos, green card, documentos, SSN, ITIN, "
    "emprego, currículo, direitos trabalhistas, moradia, aluguel, saúde, plano de saúde, "
    "finanças, conta bancária, crédito, impostos, compras nos EUA, vida cotidiana. "
    "IMPORTANTE: Nunca dê conselhos jurídicos formais. Para casos complexos de imigração, "
    "sempre sugira consultar um advogado de imigração. "
    "Seja empático — o imigrante enfrenta desafios reais e merece respeito."
)


def _sb():
    return create_client(os.environ["SUPABASE_URL"], os.environ["SUPABASE_SERVICE_KEY"])


def _get_or_create_session(member_id: str) -> str:
    """Retorna session_id ativa do membro (ou cria uma nova)."""
    sb = _sb()
    result = (
        sb.table("ai_sessions")
        .select("id")
        .eq("member_id", member_id)
        .order("updated_at", desc=True)
        .limit(1)
        .execute()
    )
    if result.data:
        return result.data[0]["id"]

    new_session = sb.table("ai_sessions").insert({"member_id": member_id}).execute()
    return new_session.data[0]["id"]


def _call_groq(messages: list) -> str:
    """Chama Groq API com histórico da conversa."""
    key = os.environ.get("GROQ_API_KEY", "")
    if not key:
        return "Assistente temporariamente indisponível. Tente novamente em instantes."
    try:
        resp = requests.post(
            "https://api.groq.com/openai/v1/chat/completions",
            headers={"Authorization": f"Bearer {key}", "Content-Type": "application/json"},
            json={
                "model": "llama-3.1-70b-versatile",
                "messages": [{"role": "system", "content": AI_SYSTEM_PROMPT}] + messages,
                "max_tokens": 500,
                "temperature": 0.7,
            },
            timeout=20,
        )
        if resp.status_code == 200:
            return resp.json()["choices"][0]["message"]["content"].strip()
        log.error(f"Groq error {resp.status_code}: {resp.text[:200]}")
    except Exception as e:
        log.error(f"Groq exception: {e}")
    return "Não consegui processar sua mensagem agora. Tente novamente."


# ── Schemas ────────────────────────────────────────────────────

class ChatMessage(BaseModel):
    content: str

    def validate_content(self):
        if len(self.content.strip()) < 2:
            raise ValueError("Mensagem muito curta.")
        return self.content.strip()[:2000]


# ── Endpoints ──────────────────────────────────────────────────

@router.post("/chat")
async def chat(body: ChatMessage, member: dict = Depends(get_current_member)):
    sb = _sb()
    member_id = member["sub"]
    user_text = body.content.strip()[:2000]

    if not user_text:
        raise HTTPException(status_code=422, detail="Mensagem vazia.")

    session_id = _get_or_create_session(member_id)

    # Busca histórico recente
    history = (
        sb.table("ai_messages")
        .select("role,content")
        .eq("session_id", session_id)
        .order("created_at", desc=True)
        .limit(MAX_HISTORY_MESSAGES)
        .execute()
    )
    messages = list(reversed(history.data or []))
    messages.append({"role": "user", "content": user_text})

    # Salvar mensagem do usuário
    sb.table("ai_messages").insert({"session_id": session_id, "role": "user", "content": user_text}).execute()

    # Chamar IA
    ai_response = _call_groq(messages)

    # Salvar resposta da IA
    sb.table("ai_messages").insert({"session_id": session_id, "role": "assistant", "content": ai_response}).execute()

    # Atualizar timestamp da sessão
    from datetime import datetime, timezone
    sb.table("ai_sessions").update({"updated_at": datetime.now(timezone.utc).isoformat()}).eq("id", session_id).execute()

    return {"response": ai_response, "session_id": session_id}


@router.get("/history")
async def get_history(member: dict = Depends(get_current_member)):
    sb = _sb()
    session_id = _get_or_create_session(member["sub"])
    result = (
        sb.table("ai_messages")
        .select("role,content,created_at")
        .eq("session_id", session_id)
        .order("created_at")
        .limit(MAX_HISTORY_MESSAGES)
        .execute()
    )
    return {"messages": result.data or [], "session_id": session_id}


@router.delete("/history")
async def clear_history(member: dict = Depends(get_current_member)):
    """Apaga histórico e cria nova sessão."""
    sb = _sb()
    old = sb.table("ai_sessions").select("id").eq("member_id", member["sub"]).execute()
    for s in (old.data or []):
        sb.table("ai_sessions").delete().eq("id", s["id"]).execute()
    new_session = sb.table("ai_sessions").insert({"member_id": member["sub"]}).execute()
    return {"ok": True, "session_id": new_session.data[0]["id"]}
```

- [ ] **Step 4: Include router no main.py**

```python
from routers.assistant import router as assistant_router
# ...
app.include_router(assistant_router)
```

- [ ] **Step 5: Executar testes**

```bash
python -m pytest tests/test_news_forum_ai.py -v
```
Esperado: todos os testes PASSED.

- [ ] **Step 6: Commit**

```bash
git add clubeusa/api/routers/assistant.py clubeusa/api/main.py tests/test_news_forum_ai.py
git commit -m "feat(api): router /assistant com chat IA e histórico de sessão"
```

---

## Task 6: RSS Fetcher + Groq Processor

**Files:**
- Criar: `dealscanner2/news_fetcher.py`
- Modificar: `requirements.txt` (adicionar feedparser)

- [ ] **Step 1: Adicionar feedparser ao requirements.txt**

Encontrar a linha `requests==2.32.3` em `requirements.txt` e adicionar após ela:

```
feedparser==6.0.11
```

- [ ] **Step 2: Criar o news_fetcher**

```python
# dealscanner2/news_fetcher.py
"""
RSS Fetcher + Groq Processor para notícias do Clube USA.

Fluxo:
  1. Busca artigos novos de fontes RSS ativas no Supabase
  2. Deduuplica por URL
  3. Envia para Groq: avalia relevância (0-100) + traduz + resume em PT
  4. Salva em news_articles com status adequado
"""

import os
import logging
import hashlib
from datetime import datetime, timezone
from pathlib import Path

import feedparser
import requests

log = logging.getLogger("news_fetcher")

RELEVANCE_PROMPT = """Você é um editor especializado em notícias para imigrantes brasileiros nos EUA.

Avalie este artigo e responda em JSON com este formato exato:
{
  "score": <0-100>,
  "category": "<immigration|politics|community|brazil|economy|general>",
  "title_pt": "<título traduzido para português>",
  "summary_pt": "<resumo de 2-3 frases em português>"
}

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
    """Chama Groq para avaliar relevância e traduzir o artigo."""
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
            import json
            text = resp.json()["choices"][0]["message"]["content"].strip()
            # Remove possível markdown code fence
            text = text.strip("```json").strip("```").strip()
            return json.loads(text)
    except Exception as e:
        log.warning(f"Groq evaluate error: {e}")

    return {"score": 50, "category": "general", "title_pt": title, "summary_pt": ""}


def fetch_and_process():
    """
    Job principal: busca notícias de todas as fontes ativas,
    avalia com IA e salva no Supabase.
    """
    if not os.environ.get("SUPABASE_URL"):
        log.warning("Supabase não configurado — news_fetcher ignorado.")
        return

    _ensure_sources()
    sb = _sb()

    sources = sb.table("news_sources").select("*").eq("active", True).execute().data or []
    log.info(f"Buscando notícias de {len(sources)} fontes...")

    total_new = 0

    for source in sources:
        entries = _fetch_rss(source["url"])
        log.info(f"  {source['name']}: {len(entries)} entradas")

        for entry in entries[:10]:  # máx 10 por fonte por rodada
            url   = entry.get("link", "")
            title = entry.get("title", "").strip()
            desc  = entry.get("summary", "") or entry.get("description", "")

            if not url or not title:
                continue

            # Deduplicar por URL
            existing = sb.table("news_articles").select("id").eq("url", url).execute()
            if existing.data:
                continue

            # Avaliar com IA
            evaluation = _evaluate_article(title, desc, source["name"])
            score    = evaluation.get("score", 0)
            category = evaluation.get("category", "general")
            title_pt = evaluation.get("title_pt", title)
            summary  = evaluation.get("summary_pt", "")

            # Determinar status
            status = "ready_for_review" if score >= 40 else "rejected"

            # Extrair imagem se disponível
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

        # Atualizar last_fetched_at da fonte
        sb.table("news_sources").update({
            "last_fetched_at": datetime.now(timezone.utc).isoformat()
        }).eq("id", source["id"]).execute()

    log.info(f"News fetch concluído: {total_new} artigos novos")
    return total_new


if __name__ == "__main__":
    import sys
    sys.path.insert(0, str(Path(__file__).parent))
    import config  # noqa — carrega .env
    logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(message)s")
    fetch_and_process()
```

- [ ] **Step 3: Testar manualmente (requer .env configurado)**

```bash
cd dealscanner2
python news_fetcher.py
```
Esperado: log com fontes e artigos processados. Se SUPABASE_URL não estiver configurado, loga aviso e sai.

- [ ] **Step 4: Commit**

```bash
git add dealscanner2/news_fetcher.py requirements.txt
git commit -m "feat(news): RSS fetcher + Groq evaluator para pipeline de noticias"
```

---

## Task 7: Scheduler — Job RSS + Digest Diário

**Files:**
- Modificar: `dealscanner2/scheduler.py`

- [ ] **Step 1: Adicionar import e job de notícias no scheduler**

Em `dealscanner2/scheduler.py`, no topo após os imports existentes, adicionar:

```python
from news_fetcher import fetch_and_process as fetch_news
```

- [ ] **Step 2: Adicionar job RSS no build_event_queue**

Em `scheduler.py`, dentro de `build_event_queue()`, após o bloco que adiciona o evento `scan` (por volta da linha `"secs": seconds_until_utc(11)`), adicionar:

```python
    # Fetch de notícias a cada 2h (UTC 7, 9, 11, 13, 15, 17, 19, 21)
    for news_hour in [7, 9, 13, 17, 21]:
        events.append({
            "utc_hour": news_hour,
            "type":     "news_fetch",
            "slot":     None,
            "tz":       "eastern",
            "plan":     None,
            "secs":     seconds_until_utc(news_hour),
        })
```

- [ ] **Step 3: Adicionar digest diário de notícias**

Criar função `send_news_digest` em `scheduler.py` antes de `run_loop()`:

```python
def send_news_digest():
    """Envia top 5 notícias do dia via Telegram (8h ET = 13h UTC)."""
    if not config.SUPABASE_URL:
        log.info("News digest: Supabase não configurado, ignorando.")
        return

    try:
        from supabase import create_client
        from datetime import datetime, timedelta, timezone
        sb = create_client(config.SUPABASE_URL, config.SUPABASE_SERVICE_KEY)
        since = (datetime.now(timezone.utc) - timedelta(hours=24)).isoformat()

        articles = (
            sb.table("news_articles")
            .select("title_pt,summary_pt,url,category")
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

        def make_digest(lang: str) -> str:
            if lang == "pt":
                header = "*📰 NOTÍCIAS DO DIA — CLUBE USA*\n"
                footer = "\n_Clube USA — Informação que você precisa_"
            else:
                header = "*📰 NOTICIAS DEL DÍA — CLUB USA*\n"
                footer = "\n_Club USA — La información que necesitas_"

            lines = [header]
            for i, art in enumerate(articles, 1):
                lines.append(f"{i}. *{art['title_pt'][:80]}*")
                if art.get("summary_pt"):
                    lines.append(f"   _{art['summary_pt'][:100]}_")
                lines.append(f"   🔗 {art['url']}")
                lines.append("")
            lines.append(footer)
            return "\n".join(lines)

        _send_message(make_digest("pt"), make_digest("pt"), lang="pt")
        time.sleep(random.randint(3, 6))
        _send_message(make_digest("es"), make_digest("es"), lang="es")

        # Marcar como enviados
        ids = [a["id"] for a in articles if "id" in a]
        if ids:
            sb.table("news_articles").update({"sent_in_digest": True}).in_("id", ids).execute()

        log.info(f"News digest enviado: {len(articles)} artigos")
    except Exception as e:
        log.error(f"Erro no news digest: {e}")
```

- [ ] **Step 4: Adicionar handler no run_loop**

Dentro de `run_loop()`, no bloco `if next_e["type"] == ...`, adicionar:

```python
        elif next_e["type"] == "news_fetch":
            fetch_news()
        elif next_e["type"] == "news_digest":
            send_news_digest()
```

- [ ] **Step 5: Adicionar evento de digest no build_event_queue**

```python
    # Digest de notícias — diário 13h UTC (8h ET)
    events.append({
        "utc_hour": 13,
        "type":     "news_digest",
        "slot":     None,
        "tz":       "eastern",
        "plan":     None,
        "secs":     seconds_until_utc(13),
    })
```

- [ ] **Step 6: Commit**

```bash
git add dealscanner2/scheduler.py
git commit -m "feat(scheduler): job RSS a cada 2h + digest de noticias diario no Telegram"
```

---

## Task 8: Frontend — Notícias

**Files:**
- Modificar: `clubeusa/platform.html`

- [ ] **Step 1: Adicionar "Notícias" na navegação**

Em `platform.html`, localizar os botões de navegação do painel do membro (a `<nav>` ou seção de abas do dashboard). Adicionar o botão de Notícias ao lado de "Deals de Hoje":

Localizar o bloco que define os tabs do painel (algo como `id="tab-deals"`) e adicionar:

```html
<button class="tab-btn" id="tab-news" onclick="showTab('news')">
  📰 Notícias
</button>
```

- [ ] **Step 2: Adicionar seção de Notícias no HTML**

Após a seção de deals (procurar por `id="section-deals"` ou equivalente), adicionar:

```html
<!-- ── NOTÍCIAS ─────────────────────────────────────── -->
<section id="section-news" class="tab-section" style="display:none">
  <div class="section-header">
    <h2 class="section-title">📰 Notícias</h2>
    <p class="section-sub">Informação para brasileiros nos EUA</p>
  </div>

  <!-- Filtro de categorias -->
  <div class="news-cats" id="news-cats">
    <button class="news-cat-btn active" data-cat="">Todas</button>
    <button class="news-cat-btn" data-cat="immigration">📋 Imigração</button>
    <button class="news-cat-btn" data-cat="politics">⚖️ Política</button>
    <button class="news-cat-btn" data-cat="community">🤝 Comunidade</button>
    <button class="news-cat-btn" data-cat="brazil">🇧🇷 Brasil</button>
    <button class="news-cat-btn" data-cat="economy">💰 Economia</button>
  </div>

  <div id="news-feed" class="news-feed">
    <div class="loading-state">Carregando notícias...</div>
  </div>
</section>
```

- [ ] **Step 3: Adicionar CSS para notícias**

Dentro do `<style>` de `platform.html`, adicionar:

```css
/* News */
.news-cats{display:flex;gap:8px;flex-wrap:wrap;margin-bottom:20px}
.news-cat-btn{padding:6px 14px;border-radius:100px;border:1.5px solid var(--border);
  background:transparent;font-size:12px;font-weight:600;cursor:pointer;color:var(--text2);transition:all .15s}
.news-cat-btn.active,.news-cat-btn:hover{background:var(--navy);color:#fff;border-color:var(--navy)}

.news-feed{display:flex;flex-direction:column;gap:16px}
.news-card{background:#fff;border-radius:var(--radius);border:1px solid var(--border);
  padding:18px;display:flex;gap:16px;cursor:pointer;transition:box-shadow .2s;text-decoration:none;color:inherit}
.news-card:hover{box-shadow:var(--shadow)}
.news-card-img{width:100px;height:70px;border-radius:8px;object-fit:cover;flex-shrink:0;background:var(--off2)}
.news-card-body{flex:1;min-width:0}
.news-card-tag{font-size:10px;font-weight:700;color:var(--gold);letter-spacing:.5px;text-transform:uppercase;margin-bottom:4px}
.news-card-title{font-size:15px;font-weight:700;color:var(--navy);line-height:1.3;margin-bottom:6px;
  display:-webkit-box;-webkit-line-clamp:2;-webkit-box-orient:vertical;overflow:hidden}
.news-card-summary{font-size:13px;color:var(--muted);line-height:1.5;
  display:-webkit-box;-webkit-line-clamp:2;-webkit-box-orient:vertical;overflow:hidden}
.news-card-date{font-size:11px;color:var(--muted);margin-top:6px}
```

- [ ] **Step 4: Adicionar JS para notícias**

No bloco `<script>` de `platform.html`, adicionar as funções de notícias:

```javascript
// ── NEWS ─────────────────────────────────────────────────────
let currentNewsCategory = '';

async function loadNews(category = '') {
  const feed = document.getElementById('news-feed');
  if (!feed) return;
  feed.innerHTML = '<div class="loading-state">Carregando notícias...</div>';
  try {
    const qs = category ? `?category=${category}&limit=20` : '?limit=20';
    const data = await api(`/news${qs}`);
    if (!data.articles || data.articles.length === 0) {
      feed.innerHTML = '<div class="empty-state">Nenhuma notícia disponível no momento.</div>';
      return;
    }
    feed.innerHTML = data.articles.map(a => newsCardHTML(a)).join('');
  } catch (e) {
    feed.innerHTML = '<div class="empty-state">Erro ao carregar notícias.</div>';
  }
}

function newsCardHTML(article) {
  const catLabels = {
    immigration:'Imigração', politics:'Política', community:'Comunidade',
    brazil:'Brasil', economy:'Economia', general:'Geral'
  };
  const date = article.published_at
    ? new Date(article.published_at).toLocaleDateString('pt-BR')
    : '';
  const img = article.image_url
    ? `<img src="${article.image_url}" class="news-card-img" onerror="this.style.display='none'" alt="">`
    : '';
  return `
    <a class="news-card" href="${article.url}" target="_blank" rel="noopener"
       onclick="markNewsRead('${article.id}')">
      ${img}
      <div class="news-card-body">
        <div class="news-card-tag">${catLabels[article.category] || 'Geral'}</div>
        <div class="news-card-title">${escHtml(article.title_pt || article.title_original || '')}</div>
        <div class="news-card-summary">${escHtml(article.summary_pt || '')}</div>
        <div class="news-card-date">${date}</div>
      </div>
    </a>`;
}

async function markNewsRead(articleId) {
  try { await api(`/news/${articleId}`); } catch(e) {}
}

function escHtml(str) {
  return (str || '').replace(/&/g,'&amp;').replace(/</g,'&lt;').replace(/>/g,'&gt;');
}

// Filtros de categoria
document.addEventListener('DOMContentLoaded', () => {
  document.querySelectorAll('.news-cat-btn').forEach(btn => {
    btn.addEventListener('click', () => {
      document.querySelectorAll('.news-cat-btn').forEach(b => b.classList.remove('active'));
      btn.classList.add('active');
      currentNewsCategory = btn.dataset.cat || '';
      loadNews(currentNewsCategory);
    });
  });
});

// Chamar loadNews quando a tab de notícias for exibida
// (integrar na função showTab existente):
// if (tab === 'news') loadNews(currentNewsCategory);
```

- [ ] **Step 5: Integrar na função showTab existente**

Localizar a função `showTab` em `platform.html` e adicionar:

```javascript
if (tab === 'news' && document.getElementById('news-feed').children.length <= 1) {
  loadNews(currentNewsCategory);
}
```

- [ ] **Step 6: Commit**

```bash
git add clubeusa/platform.html
git commit -m "feat(frontend): secao de noticias com feed, categorias e marcacao de leitura"
```

---

## Task 9: Frontend — Fórum

**Files:**
- Modificar: `clubeusa/platform.html`

- [ ] **Step 1: Adicionar aba Fórum na nav do painel**

```html
<button class="tab-btn" id="tab-forum" onclick="showTab('forum')">
  💬 Fórum
</button>
```

- [ ] **Step 2: Adicionar seção HTML do fórum**

```html
<!-- ── FÓRUM ─────────────────────────────────────────── -->
<section id="section-forum" class="tab-section" style="display:none">
  <div class="section-header">
    <h2 class="section-title">💬 Fórum da Comunidade</h2>
    <p class="section-sub">Perguntas e respostas de brasileiros nos EUA</p>
  </div>

  <!-- Vista: lista de posts / thread / novo post -->
  <div id="forum-view-list">
    <div class="forum-cats" id="forum-cats"></div>
    <button class="btn-primary" onclick="showForumNew()" style="margin-bottom:16px">
      ✏️ Nova Pergunta
    </button>
    <div id="forum-posts-list"></div>
  </div>

  <div id="forum-view-thread" style="display:none">
    <button class="btn-back" onclick="showForumList()">← Voltar</button>
    <div id="forum-thread-content"></div>
  </div>

  <div id="forum-view-new" style="display:none">
    <button class="btn-back" onclick="showForumList()">← Voltar</button>
    <h3 style="margin-bottom:16px;color:var(--navy)">Nova Pergunta</h3>
    <select id="forum-new-cat" class="form-input" style="margin-bottom:12px">
      <option value="">Selecione a categoria...</option>
    </select>
    <input id="forum-new-title" class="form-input" placeholder="Título da pergunta (mín. 10 caracteres)" style="margin-bottom:12px">
    <textarea id="forum-new-body" class="form-input" rows="5"
      placeholder="Descreva sua pergunta com detalhes..." style="margin-bottom:16px;resize:vertical"></textarea>
    <button class="btn-primary" onclick="submitForumPost()">Publicar Pergunta</button>
  </div>
</section>
```

- [ ] **Step 3: Adicionar CSS do fórum**

```css
/* Forum */
.forum-cats{display:flex;gap:8px;flex-wrap:wrap;margin-bottom:16px}
.forum-cat-btn{padding:5px 12px;border-radius:100px;border:1.5px solid var(--border);
  background:transparent;font-size:12px;font-weight:600;cursor:pointer;color:var(--text2);transition:all .15s}
.forum-cat-btn.active,.forum-cat-btn:hover{background:var(--navy);color:#fff;border-color:var(--navy)}

.forum-post-card{background:#fff;border-radius:var(--radius);border:1px solid var(--border);
  padding:16px;margin-bottom:12px;cursor:pointer;transition:box-shadow .2s}
.forum-post-card:hover{box-shadow:var(--shadow)}
.forum-post-title{font-size:15px;font-weight:700;color:var(--navy);margin-bottom:6px}
.forum-post-meta{display:flex;gap:12px;font-size:12px;color:var(--muted)}
.forum-post-meta span{display:flex;align-items:center;gap:4px}

.forum-reply{background:var(--off);border-radius:var(--radius-sm);padding:14px;margin-bottom:10px}
.forum-reply.is-ai{border-left:3px solid var(--gold);background:#FFFBF0}
.forum-reply-header{font-size:11px;color:var(--muted);margin-bottom:8px;font-weight:600}
.forum-reply-body{font-size:14px;color:var(--text);line-height:1.6;white-space:pre-wrap}

.btn-back{background:transparent;border:none;color:var(--navy);font-size:14px;
  font-weight:600;cursor:pointer;padding:0;margin-bottom:20px;display:flex;align-items:center;gap:6px}
```

- [ ] **Step 4: Adicionar JS do fórum**

```javascript
// ── FORUM ─────────────────────────────────────────────────────
let forumCategories = [];
let currentForumCat = '';

async function loadForum() {
  await loadForumCategories();
  loadForumPosts();
}

async function loadForumCategories() {
  try {
    const data = await api('/forum/categories');
    forumCategories = data.categories || [];
    const catsEl = document.getElementById('forum-cats');
    const newCatEl = document.getElementById('forum-new-cat');
    if (catsEl) {
      catsEl.innerHTML = '<button class="forum-cat-btn active" data-slug="" onclick="filterForum(this,\'\')">Todas</button>' +
        forumCategories.map(c =>
          `<button class="forum-cat-btn" data-slug="${c.slug}" onclick="filterForum(this,'${c.slug}')">${c.icon} ${c.name}</button>`
        ).join('');
    }
    if (newCatEl) {
      newCatEl.innerHTML = '<option value="">Selecione a categoria...</option>' +
        forumCategories.map(c => `<option value="${c.id}">${c.icon} ${c.name}</option>`).join('');
    }
  } catch(e) {}
}

async function loadForumPosts(categorySlug = '') {
  const el = document.getElementById('forum-posts-list');
  if (!el) return;
  el.innerHTML = '<div class="loading-state">Carregando...</div>';
  try {
    const qs = categorySlug ? `?category_slug=${categorySlug}&limit=20` : '?limit=20';
    const data = await api(`/forum/posts${qs}`);
    const posts = data.posts || [];
    if (!posts.length) {
      el.innerHTML = '<div class="empty-state">Nenhum post ainda. Seja o primeiro! 🙌</div>';
      return;
    }
    el.innerHTML = posts.map(p => `
      <div class="forum-post-card" onclick="loadForumThread('${p.id}')">
        <div class="forum-post-title">${escHtml(p.title)}</div>
        <div class="forum-post-meta">
          <span>💬 ${p.reply_count || 0} respostas</span>
          <span>👍 ${p.vote_count || 0} votos</span>
          <span>🕐 ${new Date(p.created_at).toLocaleDateString('pt-BR')}</span>
        </div>
      </div>`).join('');
  } catch(e) {
    el.innerHTML = '<div class="empty-state">Erro ao carregar posts.</div>';
  }
}

function filterForum(btn, slug) {
  document.querySelectorAll('.forum-cat-btn').forEach(b => b.classList.remove('active'));
  btn.classList.add('active');
  currentForumCat = slug;
  loadForumPosts(slug);
}

async function loadForumThread(postId) {
  document.getElementById('forum-view-list').style.display = 'none';
  document.getElementById('forum-view-thread').style.display = 'block';
  const el = document.getElementById('forum-thread-content');
  el.innerHTML = '<div class="loading-state">Carregando...</div>';
  try {
    const data = await api(`/forum/posts/${postId}`);
    const post = data.post;
    const replies = data.replies || [];
    el.innerHTML = `
      <div style="margin-bottom:20px">
        <h3 style="color:var(--navy);margin-bottom:8px">${escHtml(post.title)}</h3>
        <p style="color:var(--text2);line-height:1.6;margin-bottom:16px">${escHtml(post.body)}</p>
        <button class="forum-cat-btn" onclick="votePost('${post.id}')">👍 ${post.vote_count || 0} votos</button>
      </div>
      <h4 style="color:var(--navy);margin-bottom:12px">${replies.length} Resposta(s)</h4>
      ${replies.map(r => `
        <div class="forum-reply ${r.is_ai ? 'is-ai' : ''}">
          <div class="forum-reply-header">${r.is_ai ? '🤖 Assistente Clube USA' : '👤 Membro'} · ${new Date(r.created_at).toLocaleDateString('pt-BR')}</div>
          <div class="forum-reply-body">${escHtml(r.body)}</div>
        </div>`).join('')}
      <div style="margin-top:20px">
        <textarea id="reply-body" class="form-input" rows="3" placeholder="Escreva sua resposta..." style="margin-bottom:10px;resize:vertical"></textarea>
        <button class="btn-primary" onclick="submitReply('${post.id}')">Responder</button>
      </div>`;
  } catch(e) {
    el.innerHTML = '<div class="empty-state">Erro ao carregar post.</div>';
  }
}

function showForumList() {
  document.getElementById('forum-view-list').style.display = 'block';
  document.getElementById('forum-view-thread').style.display = 'none';
  document.getElementById('forum-view-new').style.display = 'none';
}

function showForumNew() {
  document.getElementById('forum-view-list').style.display = 'none';
  document.getElementById('forum-view-new').style.display = 'block';
}

async function submitForumPost() {
  const cat = document.getElementById('forum-new-cat').value;
  const title = document.getElementById('forum-new-title').value.trim();
  const body = document.getElementById('forum-new-body').value.trim();
  if (!cat) return alert('Selecione uma categoria.');
  if (title.length < 10) return alert('Título muito curto (mín. 10 caracteres).');
  if (body.length < 20) return alert('Descreva melhor sua pergunta (mín. 20 caracteres).');
  try {
    await api('/forum/posts', 'POST', {category_id: cat, title, body});
    showForumList();
    loadForumPosts(currentForumCat);
    alert('Pergunta publicada! A IA responderá em instantes. 🤖');
  } catch(e) { alert('Erro ao publicar. Tente novamente.'); }
}

async function submitReply(postId) {
  const body = document.getElementById('reply-body').value.trim();
  if (body.length < 5) return alert('Resposta muito curta.');
  try {
    await api(`/forum/posts/${postId}/reply`, 'POST', {body});
    loadForumThread(postId);
  } catch(e) { alert('Erro ao enviar resposta.'); }
}

async function votePost(postId) {
  try { await api(`/forum/posts/${postId}/vote`, 'POST', {}); } catch(e) {}
  loadForumThread(postId);
}
```

- [ ] **Step 5: Integrar na função showTab**

```javascript
if (tab === 'forum' && !forumCategories.length) loadForum();
```

- [ ] **Step 6: Commit**

```bash
git add clubeusa/platform.html
git commit -m "feat(frontend): secao de forum com posts, replies e IA auto-reply"
```

---

## Task 10: Frontend — Chat Widget do Assistente IA

**Files:**
- Modificar: `clubeusa/platform.html`

- [ ] **Step 1: Adicionar HTML do widget (antes de `</body>`)**

```html
<!-- ── AI CHAT WIDGET ──────────────────────────────────── -->
<div id="ai-chat-widget" style="display:none">
  <!-- Botão flutuante -->
  <button id="ai-chat-toggle" onclick="toggleAiChat()" title="Assistente Clube USA">
    🤖
  </button>

  <!-- Janela de chat -->
  <div id="ai-chat-window" style="display:none">
    <div id="ai-chat-header">
      <span>🤖 Assistente Clube USA</span>
      <button onclick="toggleAiChat()" style="background:none;border:none;color:#fff;cursor:pointer;font-size:18px">✕</button>
    </div>
    <div id="ai-chat-messages"></div>
    <div id="ai-chat-input-area">
      <input id="ai-chat-input" placeholder="Sua dúvida sobre vida nos EUA..."
        onkeydown="if(event.key==='Enter'&&!event.shiftKey){event.preventDefault();sendAiMessage()}">
      <button onclick="sendAiMessage()">→</button>
    </div>
  </div>
</div>
```

- [ ] **Step 2: Adicionar CSS do widget**

```css
/* AI Chat Widget */
#ai-chat-toggle{
  position:fixed;bottom:24px;right:24px;width:56px;height:56px;
  border-radius:50%;background:var(--navy);color:#fff;border:none;
  font-size:24px;cursor:pointer;box-shadow:0 4px 16px rgba(0,0,0,.25);
  z-index:1000;transition:transform .2s;display:flex;align-items:center;justify-content:center
}
#ai-chat-toggle:hover{transform:scale(1.08)}

#ai-chat-window{
  position:fixed;bottom:92px;right:24px;width:360px;height:500px;
  background:#fff;border-radius:16px;box-shadow:0 8px 40px rgba(0,0,0,.18);
  z-index:1000;display:flex;flex-direction:column;overflow:hidden;border:1px solid var(--border)
}
#ai-chat-header{
  background:var(--navy);color:#fff;padding:14px 16px;
  display:flex;justify-content:space-between;align-items:center;
  font-weight:700;font-size:14px
}
#ai-chat-messages{
  flex:1;overflow-y:auto;padding:16px;display:flex;flex-direction:column;gap:10px
}
.ai-msg{max-width:85%;padding:10px 14px;border-radius:12px;font-size:13px;line-height:1.5}
.ai-msg.user{background:var(--navy);color:#fff;align-self:flex-end;border-radius:12px 12px 2px 12px}
.ai-msg.assistant{background:var(--off);color:var(--text);align-self:flex-start;border-radius:12px 12px 12px 2px}
.ai-msg.assistant.loading{color:var(--muted);font-style:italic}

#ai-chat-input-area{
  display:flex;gap:8px;padding:12px;border-top:1px solid var(--border)
}
#ai-chat-input{
  flex:1;border:1.5px solid var(--border);border-radius:8px;padding:8px 12px;
  font-size:13px;outline:none;font-family:'Barlow',sans-serif
}
#ai-chat-input:focus{border-color:var(--navy)}
#ai-chat-input-area button{
  background:var(--navy);color:#fff;border:none;border-radius:8px;
  padding:8px 14px;cursor:pointer;font-size:16px;font-weight:700
}

@media(max-width:480px){
  #ai-chat-window{width:calc(100vw - 32px);right:16px;bottom:84px}
}
```

- [ ] **Step 3: Adicionar JS do widget**

```javascript
// ── AI CHAT WIDGET ────────────────────────────────────────────
let aiChatOpen = false;
let aiChatLoaded = false;

function toggleAiChat() {
  aiChatOpen = !aiChatOpen;
  document.getElementById('ai-chat-window').style.display = aiChatOpen ? 'flex' : 'none';
  if (aiChatOpen && !aiChatLoaded) {
    loadAiHistory();
    aiChatLoaded = true;
  }
  if (aiChatOpen) document.getElementById('ai-chat-input').focus();
}

async function loadAiHistory() {
  try {
    const data = await api('/assistant/history');
    const msgs = data.messages || [];
    if (!msgs.length) {
      appendAiMsg('assistant', 'Olá! Sou o Assistente Clube USA. 👋\nComo posso te ajudar hoje? Pode perguntar sobre imigração, documentos, emprego, moradia, saúde ou qualquer dúvida sobre vida nos EUA!');
    } else {
      msgs.forEach(m => appendAiMsg(m.role, m.content));
    }
  } catch(e) {
    appendAiMsg('assistant', 'Olá! Sou o Assistente Clube USA. Como posso te ajudar?');
  }
}

function appendAiMsg(role, content, isLoading = false) {
  const el = document.getElementById('ai-chat-messages');
  const div = document.createElement('div');
  div.className = `ai-msg ${role}${isLoading ? ' loading' : ''}`;
  div.textContent = content;
  el.appendChild(div);
  el.scrollTop = el.scrollHeight;
  return div;
}

async function sendAiMessage() {
  const input = document.getElementById('ai-chat-input');
  const text = input.value.trim();
  if (!text) return;
  input.value = '';

  appendAiMsg('user', text);
  const loadingEl = appendAiMsg('assistant', 'Pensando...', true);

  try {
    const data = await api('/assistant/chat', 'POST', {content: text});
    loadingEl.remove();
    appendAiMsg('assistant', data.response);
  } catch(e) {
    loadingEl.textContent = 'Erro ao processar. Tente novamente.';
    loadingEl.classList.remove('loading');
  }
}

// Mostrar widget quando membro está logado
function showAiWidget() {
  document.getElementById('ai-chat-widget').style.display = 'block';
}
// Chamar showAiWidget() logo após login bem-sucedido
```

- [ ] **Step 4: Chamar showAiWidget após login**

Localizar onde o painel do membro é exibido após login (função como `showDashboard()` ou `onLoginSuccess()`) e adicionar:

```javascript
showAiWidget();
```

- [ ] **Step 5: Verificar que a função `api()` suporta POST com body**

Localizar a função `api()` no platform.html e confirmar que aceita método e body:

```javascript
async function api(path, method = 'GET', body = null) {
  const opts = {
    method,
    headers: { 'Content-Type': 'application/json', 'Authorization': `Bearer ${token}` },
  };
  if (body) opts.body = JSON.stringify(body);
  const res = await fetch(`${API_URL}${path}`, opts);
  if (!res.ok) throw new Error(await res.text());
  return res.json();
}
```

Se a função existente não suporta body, atualizar para este padrão.

- [ ] **Step 6: Commit final**

```bash
git add clubeusa/platform.html
git commit -m "feat(frontend): chat widget IA flutuante com historico de sessao"
```

---

## Checklist de Spec Coverage

| Requisito da Spec | Task |
|------------------|------|
| Tabelas news_sources, news_articles, news_reads | Task 1 |
| Tabelas forum_categories, forum_posts, forum_replies, forum_votes | Task 1 |
| Tabelas ai_sessions, ai_messages | Task 1 |
| Categorias iniciais do fórum | Task 1 |
| deps.py com deps compartilhados | Task 2 |
| GET /news, GET /news/{id}, GET /news/categories | Task 3 |
| Admin: approve/reject artigo | Task 3 |
| +5 pontos por leitura de notícia | Task 3 |
| GET /forum/categories, /forum/posts, POST /forum/posts | Task 4 |
| GET /forum/posts/{id}, POST reply, POST vote | Task 4 |
| IA auto-reply em post novo | Task 4 |
| +20 pts post, +10 pts reply | Task 4 |
| POST /assistant/chat, GET /assistant/history | Task 5 |
| Groq system prompt especializado | Task 5 |
| MAX_HISTORY_MESSAGES = 10 | Task 5 |
| RSS fetcher com feedparser | Task 6 |
| Groq evaluator (score + tradução + resumo) | Task 6 |
| Score < 40 → rejected automático | Task 6 |
| Job RSS a cada 2h no scheduler | Task 7 |
| Digest diário de notícias no Telegram | Task 7 |
| Tab Notícias + feed + filtros na plataforma | Task 8 |
| Tab Fórum + posts + thread + reply | Task 9 |
| Chat widget flutuante com IA | Task 10 |
| feedparser no requirements.txt | Task 6 |
