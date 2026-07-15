# DECISOES — Clube USA

> Fila de decisões que dependem do dono do produto (você).
> Para cada item: data, contexto, pergunta objetiva, opções com prós/contras e recomendação do Claude.
> Claude NÃO age em itens desta lista sem sua aprovação explícita.

---

## Como usar

Quando o Claude travar em algo que só você pode decidir (orçamento, preços, escolhas de produto/negócio, aprovação de gasto, chaves/contas externas, direção estratégica, qualquer coisa irreversível ou com custo), ele registra aqui e segue para outra tarefa.

---

## Decisões Pendentes

### [2026-07-15] Serviço de email para confirmação de conta

**Contexto:** A Fase 0.1 está implementada. O backend envia email de confirmação via SMTP — mas sem SMTP configurado, apenas loga o link no console (OK para dev, bloqueante para produção).

**Pergunta:** Qual serviço de email usar em produção?

**Opções:**
- **A — Resend (resend.com):** 3.000 emails/mês grátis, API simples, boa deliverability. Pró: barato, fácil. Contra: serviço externo que pode mudar preço.
- **B — SendGrid:** Tier gratuito generoso (100/dia), muito estabelecido. Pró: confiável, bem documentado. Contra: setup ligeiramente mais burocrático.
- **C — Supabase Auth nativo:** Usar o sistema de auth embutido do Supabase (que inclui email de confirmação automático). Pró: zero configuração adicional, emails grátis incluídos. Contra: acoplamento maior ao Supabase; migrações futuras do backend de auth ficam mais difíceis.
- **D — AWS SES:** Baratíssimo em escala (~$0,10/1.000 emails). Pró: escala infinita. Contra: setup mais complexo, exige conta AWS verificada.

**Recomendação:** Opção A (Resend) para começar — integração em 30 minutos, tier gratuito suficiente para os primeiros 3.000 usuários/mês. Se crescer, migrar para SES é simples. O backend já tem o slot de configuração SMTP pronto (`.env.example`), então só precisa da chave da API.

**O que o Claude faz quando você decidir:** Integra o serviço escolhido nas variáveis de ambiente e documenta o setup para o deploy.

**Status:** PENDENTE

---

### [2026-07-15] URL de produção da plataforma

**Contexto:** O link de confirmação de email usa `FRONTEND_URL` do `.env`. Em dev é `localhost:3000`. Para produção precisa da URL real.

**Pergunta:** Qual será o domínio da plataforma? (ex: clubeusa.com, app.clubeusa.com, etc.)

**Opções:** Qualquer domínio que você possua.

**Recomendação:** Registre `clubeusa.com` se disponível. Como a plataforma serve imigrantes brasileiros nos EUA, um `.com` tem mais credibilidade que `.com.br`.

**Status:** PENDENTE

---

*Atualizado em: 2026-07-15*
