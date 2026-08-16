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
    category_id UUID NOT NULL REFERENCES forum_categories(id) ON DELETE RESTRICT,
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
