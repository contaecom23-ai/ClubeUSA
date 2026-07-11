# DECISOES — Clube USA

> Fila de decisões que dependem do dono do produto (você).
> Para cada item: data, contexto, pergunta objetiva, opções com prós/contras e recomendação do Claude.
> Claude NÃO age em itens desta lista sem sua aprovação explícita.

---

## Como usar

Quando o Claude travar em algo que só você pode decidir (orçamento, preços, escolhas de produto/negócio, aprovação de gasto, chaves/contas externas, direção estratégica, qualquer coisa irreversível ou com custo), ele registra aqui e segue para outra tarefa.

---

## Decisões Pendentes

---

### [2026-07-11] Provedor de email transacional

**Contexto:** A Fase 0.1 (cadastro + email confirmado) está pronta no código. O fluxo de verificação de email funciona em modo `log` (imprime no terminal), mas para produção precisa de um provedor real que entrega o email ao usuário.

**Pergunta:** Qual provedor usar para envio de emails transacionais (confirmação de cadastro, etc.)?

**Opções:**

| Provedor | Custo | Facilidade | Recomendo? |
|---|---|---|---|
| **Resend** (resend.com) | Free até 3k/mês, depois $20/mês | Muito fácil — 1 API key, SDK Python | ✅ **Sim** |
| **SendGrid** | Free até 100/dia, depois $19,95/mês | Médio — mais configuração | Aceitável |
| **AWS SES** | ~$0,10 por 1k emails | Barato em escala, mas mais setup (DNS, sandbox) | Para depois dos 100k |
| **Mailgun** | Free 100/dia (3 meses trial) | Médio | Aceitável |
| **Supabase Auth** | Incluído no plano Supabase | Troca o sistema de auth que construímos | Não recomendo agora |

**Recomendação:** **Resend** — menor fricção, preço zero para os primeiros 3k emails/mês (muito além dos primeiros 1.000 usuários), integração em 10 min. Para ativar: criar conta em resend.com, gerar API key, eu adiciono o suporte em `email.py` com uma pull request separada.

**Para aprovar:** Me diga "use Resend" (ou o provedor escolhido) e me passe a API key via secret do repositório (`RESEND_API_KEY`). Eu integro no próximo ciclo.

**Status:** PENDENTE

---

### [2026-07-11] Credenciais do Supabase + domínio da app

**Contexto:** O backend está pronto para deploy, mas precisa de variáveis de ambiente reais para funcionar. Todas estão documentadas em `07-Clube-USA/backend/.env.example`.

**Pergunta:** Você tem um projeto Supabase criado? Se sim, quais são as credenciais?

**O que preciso para o deploy funcionar:**
- `SUPABASE_URL` (ex: `https://xyzxyz.supabase.co`)
- `SUPABASE_SERVICE_ROLE_KEY` (de Project Settings → API → service_role)
- `JWT_SECRET` — posso gerar um aleatório para você: `python -c "import secrets; print(secrets.token_urlsafe(64))"`
- `APP_BASE_URL` — o domínio final (ex: `https://clubeusa.com`)

**Ação:** Com essas informações, rodo a migration `001_users.sql` no Supabase e o sistema fica live.

**Status:** PENDENTE

---

*Atualizado em: 2026-07-11*
