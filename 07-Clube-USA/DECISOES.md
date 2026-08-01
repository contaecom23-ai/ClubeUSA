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

## Decisões Pendentes

### [2026-08-01] Infraestrutura: criar projeto Supabase

**Contexto:** O backend (Fase 0.1) está pronto mas precisa de um projeto Supabase real para rodar. Sem ele, nenhuma das funcionalidades de autenticação ou perfil funciona.

**Pergunta:** Você já tem (ou vai criar) um projeto Supabase? Quando for criado, preciso das seguintes variáveis para configurar o `.env`:

1. `SUPABASE_URL` — ex: `https://xxxxx.supabase.co`
2. `SUPABASE_SERVICE_ROLE_KEY` — em Dashboard > Settings > API (server only, nunca no frontend)
3. `SUPABASE_ANON_KEY` — em Dashboard > Settings > API (vai no `config.js` do frontend)
4. `SUPABASE_JWT_SECRET` — em Dashboard > Settings > API > JWT Settings

Após obter essas variáveis, execute também `db/schema.sql` no SQL Editor do Supabase.

**Opções:**
- **A (Recomendado): Supabase Free tier** — gratuito até 500 MB e 50k MAU, mais que suficiente para os primeiros 1.000 usuários. Sem custo agora, migra para Pro (~$25/mês) quando precisar.
- **B: Supabase Pro** — necessário só se quiser SLA (99.9%), backups diários ou PITR desde o dia 1. Não necessário agora.

**Recomendação:** Crie um projeto no Supabase Free tier agora. O custo para 1.000 usuários iniciais é zero. Compartilhe as 4 variáveis e eu configuro o deploy.

**Status:** PENDENTE

---

### [2026-08-01] Infraestrutura: hosting do frontend HTML

**Contexto:** O frontend (register.html, login.html, etc.) são arquivos HTML estáticos. Precisam ser servidos por alguma origem acessível ao usuário final.

**Pergunta:** Onde vamos hospedar o frontend?

**Opções:**
- **A (Recomendado): Vercel ou Netlify** — gratuito, deploy automático via Git push, HTTPS automático, CDN global. Ideal para começar. Zero custo para 1-10k usuários.
- **B: Supabase Storage** — pode servir arquivos estáticos, mas não é ideal para SPA/multi-page.
- **C: Servidor próprio (VPS)** — custo mínimo (~$5/mês), mais controle, mas você gerencia SSL e deploy.

**Recomendação:** Vercel (gratuito, deploy automático, domínio customizável). Se tiver domínio próprio (clubeusa.com), configura em minutos.

**Status:** PENDENTE

---

### [2026-08-01] Infraestrutura: SMTP para emails de confirmação

**Contexto:** O Supabase Auth envia email de confirmação de cadastro. No plano Free, usa o SMTP interno do Supabase (limitado a ~3 emails/hora — inviável para produção com muitos cadastros).

**Pergunta:** Qual provedor de email vamos usar para os emails transacionais?

**Opções:**
- **A (Recomendado): Resend** — gratuito até 3.000 emails/mês, API moderna, fácil de configurar no Supabase. Suficiente para os primeiros 1.000 usuários.
- **B: SendGrid** — gratuito até 100 emails/dia (muito restrito). Pago a partir daí.
- **C: Amazon SES** — baratíssimo ($0.10 por 1000 emails), mas setup mais complexo.

**Recomendação:** Resend (gratuito, simples de configurar no Supabase em < 5 minutos). Crie conta em resend.com, obtenha API key e configure em: Supabase Dashboard > Settings > Authentication > SMTP Settings.

**Status:** PENDENTE

---

### [2026-08-01] Domínio: URL pública da plataforma

**Contexto:** Para o link de confirmação de email funcionar (`emailRedirectTo`), o frontend precisa de uma URL pública real. Localmente não funciona para usuários reais.

**Pergunta:** Qual será o domínio do Clube USA?

**Opções:**
- **A: Domínio próprio** (ex: clubeusa.com, myclubeeusa.com) — profissional, necessário para lançamento real. Custo ~$10-15/ano no Namecheap ou Google Domains.
- **B: Subdomínio gratuito Vercel** (ex: clubeusa.vercel.app) — gratuito, funciona perfeitamente para MVP e testes, mas não é ideal para lançamento público sério.

**Recomendação:** Registre um domínio agora se tiver intenção de lançar em 30-60 dias. Se ainda está em fase de testes, o subdomínio .vercel.app é suficiente para validar o produto. Custo do domínio é trivial vs. o valor do produto.

**Status:** PENDENTE

---

*Atualizado em: 2026-08-01*
