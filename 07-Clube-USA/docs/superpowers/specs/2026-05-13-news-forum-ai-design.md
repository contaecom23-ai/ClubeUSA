# Clube USA — News + Fórum + Assistente IA
**Data:** 2026-05-13  
**Status:** Aprovado para implementação

---

## Visão Geral

Expandir a plataforma ClubeUSA com três novos pilares que aumentam engajamento e retenção:
1. **Feed de Notícias** — agregação RSS + curadoria IA + distribuição Telegram/plataforma
2. **Fórum da Comunidade** — Q&A por tópico com resposta automática da IA
3. **Assistente IA** — chat flutuante na plataforma para dúvidas dos membros

Público: imigrantes brasileiros nos EUA. Temas: ofertas, imigração, política americana, vida nos EUA.

---

## Seção 1: Arquitetura

**Princípio:** zero serviços novos. Tudo cresce no Supabase e FastAPI existentes.

### Novas tabelas (migrations)

```sql
-- Notícias
news_sources     -- fontes RSS configuradas
news_articles    -- artigos agregados + traduzidos

-- Fórum
forum_categories -- tópicos (Imigração, Emprego, Moradia...)
forum_posts      -- perguntas e discussões
forum_replies    -- respostas (humanas + IA)
forum_votes      -- upvotes

-- IA
ai_sessions      -- sessões por membro
ai_messages      -- mensagens individuais
```

### Integração com sistema existente
- `member_id` (FK) conecta tudo ao membro existente
- JWT auth existente protege todos os endpoints novos
- Leitura de notícia → +5 pontos (leaderboard existente)
- Post no fórum → +20 pontos
- Resposta no fórum → +10 pontos

---

## Seção 2: Pipeline de Notícias

### Fontes RSS
| Fonte | Foco | Idioma |
|-------|------|--------|
| G1/Globo | Brasil geral | PT |
| BBC Brasil | Brasil + mundo | PT |
| Reuters | Política americana | EN |
| USCIS.gov | Imigração oficial | EN |
| BrasilUSA.com | Comunidade | PT |

### Fluxo
```
[A cada 2h] RSS Fetcher (job no scheduler.py)
    → salva em news_articles (status: pending)
    → Groq avalia relevância (0–100) + traduz + resume em PT
    → se score < 40 → rejected (automático)
    → se score ≥ 40 → ready_for_review
    → Admin aprova no /admin/news
    → status: published
    → scheduler envia digest top-5 diário no Telegram (8h ET)
    → plataforma exibe via GET /news
```

### Categorias de artigo
`immigration` | `politics` | `community` | `brazil` | `economy`

---

## Seção 3: Fórum da Comunidade

### Tópicos
- Imigração & Documentos
- Emprego & Carreira
- Moradia & Apartamento
- Saúde & Plano de Saúde
- Finanças & Banco
- Vida nos EUA
- Política Americana

### Fluxo de post
```
Membro posta pergunta
    → forum_posts criado
    → Groq gera resposta automática (is_ai=true, em segundos)
    → comunidade humana complementa depois
    → upvotes determinam melhor resposta
```

### Regras
- Posts: qualquer membro autenticado
- Replies: qualquer membro autenticado
- Votos: 1 por membro por post/reply
- Moderação: admin pode deletar via /admin/forum

---

## Seção 4: Assistente IA

### Onde aparece
- **Chat flutuante** na plataforma (botão canto inferior direito)
- **Fórum**: IA responde automaticamente perguntas novas

### Comportamento
- Contexto: especialista em vida de imigrante brasileiro nos EUA
- Temas: imigração, documentos, empregos, finanças, saúde, compras
- Idioma: PT por padrão, detecta ES automaticamente
- Memória: últimas 10 mensagens da sessão (ai_messages)
- Modelo: Groq llama-3.1-70b-versatile (já integrado)

### System prompt (base)
> "Você é o Assistente Clube USA, especializado em ajudar imigrantes brasileiros nos EUA. Responda em português, seja direto e prático. Temas: imigração, vistos, documentos, emprego, moradia, saúde, compras nos EUA. Nunca dê conselhos jurídicos formais — sugira consultar um advogado para casos complexos."

---

## Endpoints novos

```
GET  /news                    — feed paginado (auth)
GET  /news/{id}               — artigo + mark as read (+5 pts)
GET  /news/categories         — lista de categorias

GET  /forum/categories        — lista de tópicos
GET  /forum/posts             — posts por categoria, paginado
POST /forum/posts             — criar post (+20 pts)
GET  /forum/posts/{id}        — post + replies
POST /forum/posts/{id}/reply  — responder (+10 pts)
POST /forum/posts/{id}/vote   — upvote

POST /assistant/chat          — mensagem para a IA (auth)
GET  /assistant/history       — histórico da sessão atual

POST /admin/news/{id}/approve — aprovar artigo
POST /admin/news/{id}/reject  — rejeitar artigo
GET  /admin/news              — lista artigos pendentes
DELETE /admin/forum/posts/{id} — moderar post
```

---

## Frontend (platform.html)

### Novas seções na nav
`Deals` | `Notícias` | `Fórum` | `Indicações` | `Ranking` | `Perfil`

### Componentes
- **NewsCard** — imagem, título PT, resumo 2 linhas, tag categoria, fonte, data
- **ForumPost** — título, categoria, preview, contagem de respostas, upvotes
- **ForumThread** — post completo + replies ordenados por votos + caixa de resposta
- **AiChatWidget** — botão flutuante azul navy, janela de chat 400×500px
- **AdminNewsTab** — lista artigos pendentes com botões aprovar/rejeitar

---

## Ordem de implementação

1. Migration SQL (tabelas novas)
2. Backend: routers /news, /forum, /assistant
3. Background job: RSS fetcher + Groq processor
4. Admin: novos tabs no painel existente
5. Frontend: novas seções no platform.html
6. Digest diário no scheduler.py existente
