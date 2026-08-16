# Clube USA — Spec da Plataforma

**Data:** 2026-05-10
**Status:** Aprovado em brainstorm
**Objetivo:** Construir o maior clube de ofertas americanas para latinos

---

## 1. Visão Geral

Clube USA é uma plataforma SaaS de ofertas americanas para latino-americanos (BR, MX, AR, etc.). O modelo é híbrido: comissões de afiliado financiam a operação, assinatura VIP é o upside premium. A prioridade atual é **crescimento de audiência** — monetização vem depois de ter massa crítica.

**Stack atual:**
- Backend: FastAPI + Supabase (Python)
- Scanner: dealscanner2/ (Amazon, Walmart, eBay, BestBuy, Slickdeals RSS)
- WhatsApp: Z-API (dev) → 360dialog (produção)
- Pagamentos: Stripe (VIP $4.99/mês)
- Frontend: HTML + CSS + JS (sem framework)

---

## 2. Decisões de Arquitetura

### Canal de distribuição
**Grupos WhatsApp restritos** (só admin envia) como canal principal de deals.
- Iniciar com grupos restritos (Z-API)
- Migrar para WhatsApp Canais quando API suportar automação oficial
- 360dialog para toda comunicação 1:1 (OTP, alertas, boas-vindas VIP)

### Segurança de audiência
Grupos configurados como "somente admin envia". O risco de cópia de contatos existe mas é mitigado pela restrição de envio. Meta: migrar para Canais assim que possível.

### Curadoria de deals
Modelo híbrido:
- Score ≥ 85 + Slickdeals validado → fila de revisão rápida (30s no admin)
- Score 60-84 → revisão humana obrigatória
- Score < 60 → descartado automaticamente
- Validar preço histórico antes de aprovar (anti-inflação Amazon)

### API WhatsApp
- **Desenvolvimento:** Z-API (número dedicado, nunca pessoal)
- **Produção:** 360dialog (oficial Meta, zero risco de ban)
- 360dialog para 1:1, grupo restrito para broadcast de deals

---

## 3. Sistema de Grupos no Site

### Regra dos 2 grupos
O site sempre exibe exatamente 2 links de grupo ativos:
1. O grupo mais cheio que ainda tem vaga (aproveitamento máximo)
2. O grupo mais recente (para novos membros)

### Fluxo automático
1. `GET /public/groups` retorna os 2 grupos ativos (endpoint a criar)
2. Webhook Z-API atualiza `member_count` em tempo real (entradas e saídas)
3. Quando grupo atinge 90% → sistema cria próximo automaticamente
4. Grupo 100% lotado → sai do site, continua recebendo deals
5. Se alguém sair de um grupo "lotado" → vaga detectada, link volta ao site

### Endpoint a criar
```
GET /public/groups
Response: { groups: [{ name, invite_link, member_count, capacity, language }] }
```

---

## 4. Informações de Preço por Deal

### No WhatsApp/Canal (texto)
- Badge: "MENOR PREÇO DE SEMPRE" ou "MENOR EM 90 DIAS"
- Preço era / preço atual / % OFF + economia em $
- Média dos últimos 90 dias
- Tendência: ↓ caindo / → estável / ↑ subindo
- Há quanto tempo está nesse preço
- Alerta de estoque baixo

### No painel web (card visual)
Tudo acima mais:
- Mini gráfico histórico 6 meses
- Cupom adicional clicável
- Frequência de promoção histórica
- Quantos membros do clube clicaram
- Equivalente em R$/MXN/COP (câmbio do dia)

---

## 5. Mecânicas de Crescimento

### Viral loop principal
"Indique 3 amigos que fiquem 7+ dias → VIP grátis por 30 dias"
- Custo zero para o negócio na fase de crescimento
- Rastreado via tabela `referrals` (já existe no banco)
- Link de indicação enviado automaticamente na boas-vindas

### Engajamento recorrente
- **Top 5 Deals da Semana** — todo domingo 18h automático
- **Sorteio semanal** — entre quem clicou em ≥1 deal na semana
- **Leaderboard semanal** — "Top 3 Indicadores" publicado no grupo
- **Bot de comandos** — PONTOS, TOP5, STOP, VIP (via Z-API mensagem direta)

### Aquisição
- Meta Pixel na landing page (retargeting)
- UTMs em todos os links de deal (rastreamento por membro)
- Deal Cards visuais gerados automaticamente (compartilhamento social)

---

## 6. Segmentação

### Por idioma
- Grupos PT: brasileiros e portugueses
- Grupos ES: mexicanos, argentinos, colombianos, etc.
- Mensagens de deals no idioma correto por grupo

### Por categoria (fase 2)
- Membro escolhe categorias no cadastro (electronics, kitchen, baby, etc.)
- No grupo recebe todos os deals
- Na DM recebe alertas extras das categorias escolhidas

---

## 7. Monetização (quando tiver massa crítica)

### Plano VIP ($4.99/mês)
- Deals 2h antes de todo mundo
- Alertas de preço por ASIN (Amazon PA-API)
- Grupos VIP exclusivos
- Sorteio VIP mensal $150
- Trial 30 dias para quem indicar 3 amigos

### Afiliado
- Slickdeals RSS: funciona sem credencial (já ativo)
- Amazon PA-API: ativar quando tiver 3 vendas (requisito deles)
- Walmart, eBay, BestBuy: ativar conforme tráfego cresce
- Comissões: Amazon 4%, Target 5%, Walmart/eBay 3%, BestBuy 1%

---

## 8. Identidade Visual

### Cores
| Token | Hex | Uso |
|---|---|---|
| Navy | `#0D1B3E` | Fundo, nav, sidebar |
| Gold | `#F0BC3A` | Títulos, CTAs, destaques |
| WhatsApp | `#25D366` | Botões de grupo |
| Price Green | `#16a34a` | Preços, economia |
| Desconto | `#dc2626` | Badges de % OFF |
| Urgência | `#d97706` | Estoque, horas |
| Off-White | `#F3F0E8` | Fundo seções claras |

### Fontes
- **Bebas Neue** — títulos heroicos, scores, números grandes
- **Barlow** — corpo, botões, labels
- **Barlow Condensed** — preços no painel

### Tom de voz
- Direto, transparente, baseado em dados
- Urgência honesta (nunca falsa)
- Sem hype, sem caps lock excessivo
- Comunitário: "feito para latinos"

---

## 9. Bugs Críticos a Corrigir

1. **`sender.py:67`** — `import os` faltando → quebra envio Z-API em produção
2. **`_otp_store` em memória** — OTPs perdidos ao reiniciar servidor → migrar para Supabase com TTL

---

## 10. Ordem de Implementação

| Fase | O que fazer |
|---|---|
| **Hoje** | Corrigir bug `os` · Rodar schema Supabase · Conectar landing ao `/auth/register` |
| **Semana 1** | Admin panel funcional · Scanner Slickdeals rodando · Primeiro grupo WA criado |
| **Semana 2** | Link de indicação automático · Painel do membro conectado · Endpoint `/public/groups` |
| **Semana 3-4** | Bot de comandos WA · Meta Pixel · Top 5 domingo automático · Deal Cards visuais |
| **Mês 2** | Sorteio automático · Leaderboard semanal · Verificação de preço antes de enviar |
| **Com massa** | Ativar VIP + Stripe · Alertas de preço · APIs afiliado pagas |

---

## 11. Arquivos Relevantes

| Arquivo | Descrição |
|---|---|
| `clubeusa/api/main.py` | FastAPI — todos os endpoints |
| `clubeusa/services/group_manager.py` | Criação automática de grupos WA |
| `clubeusa/services/alert_service.py` | Alertas de preço por ASIN |
| `clubeusa/db/schema.sql` | Schema Supabase — rodar uma vez |
| `dealscanner2/scanner.py` | Scanner multi-marketplace + score engine |
| `dealscanner2/sender.py` | Formatação e envio de deals (tem bug do os) |
| `dealscanner2/config.py` | Configurações e credenciais |
| `clubeusa/platform.html` | Frontend SPA completo |
| `PROMPT_CLAUDE_DESIGN.md` | Prompt para Claude.ai gerar o site |
