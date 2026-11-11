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

### [2026-11-11] Formato da URL de referral — `/r/CODE` vs `/i/nome` (Fase 0.2)
**Contexto:** A Fase 0.2 foi implementada com URLs no formato `/r/{CODIGO}` (ex: `/r/ABC123`), onde o código é o `referral_code` aleatório já existente no cadastro do membro. O ROADMAP original descrevia `clubeusa.com/i/joao` — um slug legível baseado no nome/username. O PR de 0.2 foi mesclado mas o item continua desmarcado no ROADMAP, sugerindo que o dono quer revisar o formato.

**Pergunta:** O formato atual `/r/ABC123` é aceitável, ou prefere `/i/joao` (slug amigável baseado no nome/username)?

**Opções:**
- **A — Manter `/r/CODE`** (atual): Sem mudança de código. Código já existe em `members.referral_code`. Não é memorável, mas funciona. Implementado e testado. **Mais rápido para seguir.**
- **B — Migrar para `/i/slug`**: Requer novo campo `referral_slug` (único, gerado a partir do nome, ex: "joao", "joao-2"), nova migration, novo endpoint `/i/{slug}`, atualização do frontend para exibir o link correto. URL mais amigável e compartilhável.

**Recomendação:** Opção A no curto prazo (já funciona), Opção B quando houver página de perfil onde o membro vê e compartilha seu link — aí vale o investimento no slug.

**O que fazer:** Se quiser manter A, marque 0.2 como `[x]` no ROADMAP. Se quiser B, responda aqui e o Claude implementa na próxima sessão.

**Status:** PENDENTE

---

### [2026-11-02] Provedor de email transacional para confirmação de email (Fase 0.1)
**Contexto:** O sistema envia emails de confirmação via SMTP. O `email_service.py` já está pronto e aceita qualquer provedor SMTP via env vars (`SMTP_HOST`, `SMTP_PORT`, `SMTP_USER`, `SMTP_PASS`). Em dev, só loga o link.

**Pergunta:** Qual provedor usar em produção?

**Opções:**
- **A — Resend** (resend.com): UI moderna, free até 3k/mês, SDK Python simples, excelente deliverability. Exige domínio verificado. ~$20/mês acima de 100k/mês. **Recomendação: melhor escolha para este estágio.**
- **B — SendGrid** (sendgrid.com): Mais robusto, free até 100/dia (muito pouco), $19.95/mês para 50k. Overkill para fase 0.
- **C — AWS SES**: $0.10 por 1000 emails, escala ilimitada, mas setup mais complexo (domínio + DKIM + sandbox release). Ótimo se já usa AWS.
- **D — Mailgun**: Free 1k/mês por 3 meses depois pago. Similar ao Resend.

**Recomendação:** Resend — melhor DX, free tier suficiente para os primeiros 1k usuários, muda só as env vars (SMTP é padrão). Não requer mudança de código.

**O que fazer:** Criar conta, verificar domínio `clubeusa.com`, pegar credenciais SMTP e adicionar ao Render/Supabase env vars. Custo: $0 até ~3k emails/mês.

**Status:** PENDENTE

---

*Atualizado em: 2026-11-11*
