# DECISOES — Clube USA

> Fila de decisões que dependem do dono do produto (você).
> Para cada item: data, contexto, pergunta objetiva, opções com prós/contras e recomendação do Claude.
> Claude NÃO age em itens desta lista sem sua aprovação explícita.

---

## Como usar

Quando o Claude travar em algo que só você pode decidir (orçamento, preços, escolhas de produto/negócio, aprovação de gasto, chaves/contas externas, direção estratégica, qualquer coisa irreversível ou com custo), ele registra aqui e segue para outra tarefa.

Formato de cada entrada:

```
### [DATA] Título da decisão
**Contexto:** ...
**Pergunta:** ...
**Opções:**
- Opção A: prós / contras
- Opção B: prós / contras
**Recomendação:** ...
**Status:** PENDENTE | APROVADO | REJEITADO
```

---

## 🚨 BLOQUEIO CRÍTICO — AÇÃO IMEDIATA NECESSÁRIA

### [2026-08-05] Loop de 44 PRs duplicados — projeto paralisado

**Contexto:** O agente autônomo roda 3x/dia. Cada vez que roda, ele vê que a Fase 0.1 não está marcada como concluída no ROADMAP.md (porque nenhum PR foi mergeado na main) e cria um novo PR. Resultado: **44 PRs abertos**, todos implementando essencialmente a mesma coisa (Fase 0.1 — cadastro + perfil + email), nenhum mergeado. O projeto está travado há semanas.

**Pergunta:** Você quer avançar com este projeto? Se sim, precisa de uma ação única: mergear o PR mais recente e fechar os demais.

**O que o PR #44 (mais recente, mais completo) já entrega:**
- Schema SQL para Supabase (tabelas `users` + `email_confirmations` + RLS preparado)
- Backend FastAPI com autenticação completa: registro, login, confirmação de email, perfil
- Segurança de produção: bcrypt, JWT 7 dias, rate-limit, security headers, CORS, timing-safe login
- Frontend HTML: `register.html`, `login.html`, `confirm.html`, `profile.html`
- 10 testes automatizados (incluindo isolamento cross-tenant)
- `referral_code` já no schema (prepara Fase 0.2 sem future migration)

**Link do PR #44:** https://github.com/contaecom23-ai/ClubeUSA/pull/44

**O que fazer (passos):**

1. **Abrir PR #44** → https://github.com/contaecom23-ai/ClubeUSA/pull/44
2. **Clicar em "Ready for review"** (tirar de draft) → depois **"Merge pull request"**
3. **Fechar os 43 outros PRs** (não têm código diferente, são duplicatas)
4. **Aplicar o schema SQL no Supabase** (instrução no PR, ação manual de 2 minutos)
5. **Configurar variáveis de ambiente** (SUPABASE_URL, SUPABASE_SERVICE_KEY, etc.)

**O que acontece se você não agir:**
- O agente vai continuar criando um novo PR a cada sessão (já são 44 — serão 50, 60, 100...)
- O projeto continua tecnicamente em Fase 0, mesmo com código pronto há semanas
- Nenhum usuário pode se cadastrar

**Recomendação:** Merge do PR #44 + fechar os outros 43. É a única ação que desbloqueia o projeto.

**Status:** PENDENTE — aguardando ação do dono

---

## Decisões de Infraestrutura (do PR #44 — pendentes após o merge)

### [2026-08-04] Qual serviço de email usar em produção?

**Contexto:** O backend usa SMTP genérico. Sem configurar SMTP, emails não saem (log de aviso, sem crash). Precisa de um provedor para emails transacionais (confirmação de cadastro, reset de senha).

**Opções:**
- **A — Gmail SMTP:** grátis, imediato, limite 500/dia. Bom para testes e primeiros 100 usuários.
- **B — Resend.com:** 3.000/mês grátis, excelente entregabilidade, dashboard analytics. Requer conta + verificar domínio (15 min). **Recomendado para lançamento real.**
- **C — SendGrid:** 100/dia grátis, consolidado. Setup mais burocrático.

**Recomendação:** Resend.com para produção (grátis até 3k/mês, simples, confiável).

**Status:** PENDENTE

---

### [2026-08-04] Onde hospedar o backend FastAPI?

**Contexto:** O backend está pronto para deploy. Precisa de uma plataforma para rodar `uvicorn`.

**Opções:**
- **A — Railway.app:** ~$5/mês, deploy via GitHub em 2 cliques, pausa automática em inatividade. **Recomendado.**
- **B — Render.com:** plano gratuito (sleep após 15min), pago a partir de $7/mês.
- **C — Fly.io:** mais flexível, curva de aprendizado maior.
- **D — VPS (DigitalOcean/Hetzner):** $4-6/mês, controle total, mais setup.

**Recomendação:** Railway.app para começar (deploy rápido, preço justo, não é free tier com sleep).

**Status:** PENDENTE

---

### [2026-08-04] Onde hospedar o frontend HTML?

**Contexto:** Frontend é HTML puro (sem build step). Qualquer CDN/static host funciona.

**Opções:**
- **A — Vercel:** deploy via GitHub, gratuito, HTTPS automático. **Recomendado.**
- **B — Netlify:** similar ao Vercel, igualmente bom.
- **C — GitHub Pages:** grátis, mas limitado (sem redirects server-side).

**Recomendação:** Vercel (zero custo, deploy automático no push, domínio customizado fácil).

**Status:** PENDENTE

---

### [2026-08-04] Aplicar schema SQL no Supabase

**Contexto:** Esta é uma ação manual. O arquivo `07-Clube-USA/schema/001_initial.sql` precisa ser rodado no SQL Editor do seu projeto Supabase.

**Pergunta:** Você já tem um projeto Supabase criado para o Clube USA?

**Ação:** Após merge do PR #44, abra o Supabase → SQL Editor → cole e execute `schema/001_initial.sql`.

**Status:** PENDENTE

---

*Atualizado em: 2026-08-05*
