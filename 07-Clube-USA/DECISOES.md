# DECISOES — Clube USA

> Fila de decisões que dependem do dono do produto (você).
> Para cada item: data, contexto, pergunta objetiva, opções com prós/contras e recomendação.
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

### [2026-08-04] Qual serviço de email usar em produção?

**Contexto:** A Fase 0.1 (cadastro + confirmação de email) está pronta no backend. O código usa SMTP genérico (funciona com qualquer provedor). Em produção, precisamos configurar `SMTP_HOST`, `SMTP_PORT`, `SMTP_USER`, `SMTP_PASS`. Sem isso configurado, os emails simplesmente não saem (log de aviso, sem crash).

**Pergunta:** Qual provedor de email usar para os emails transacionais (confirmação de cadastro, futuramente redefinir senha, notificações)?

**Opções:**

- **A — Gmail SMTP (conta Google):**
  - Prós: grátis, imediato (você já tem uma conta Google), zero custo para os primeiros 1.000 usuários.
  - Contras: limite de 500 emails/dia, IP dinâmico pode cair em spam, não profissional.
  - Ideal para: fase de testes e primeiros 100 usuários.

- **B — Resend.com:**
  - Prós: 3.000 emails/mês grátis, excelente entregabilidade, SDK simples, dashboard com analytics. Recomendado para startups.
  - Contras: requer conta + verificar domínio (15 minutos), depende de serviço externo.
  - Ideal para: lançamento real.

- **C — SendGrid (Twilio):**
  - Prós: 100 emails/dia grátis, muito consolidado no mercado.
  - Contras: setup mais burocrtico, interface complexa, 100/dia é restritivo.

- **D — AWS SES:**
  - Prós: muito barato em escala ($0,10 por 1.000 emails), altamente confiável.
  - Contras: requer conta AWS, configuração mais complexa, não faz sentido até ter volume.

**Recomendação:** Começar com **Gmail SMTP** para os primeiros testes (custo zero, zero setup). Migrar para **Resend.com** antes de abrir para os primeiros 100 usuários reais — o plan free aguenta bem os primeiros 1.000. A mudança é só trocar as env vars, sem alterar código.

**Ação necessária:** Criar conta e adicionar as env vars `SMTP_HOST`, `SMTP_PORT`, `SMTP_USER`, `SMTP_PASS` na plataforma de deploy (Railway, Render, Fly.io, etc.).

**Status:** PENDENTE

---

### [2026-08-04] Onde hospedar o backend em produção?

**Contexto:** O backend FastAPI está pronto mas não tem plataforma de deploy configurada. Sem isso, o produto não fica online.

**Pergunta:** Qual plataforma usar para hospedar a API FastAPI (e futuramente o frontend)?

**Opções:**

- **A — Railway.app:**
  - Prós: deploy via GitHub em 3 minutos, $5/mês no plano Hobby, boa DX, suporta env vars com facilidade.
  - Contras: custo mensal desde o início.

- **B — Render.com:**
  - Prós: free tier disponível (dorme após inatividade), bom para MVP.
  - Contras: free tier "dorme" após 15 min sem tráfego (30s de cold start), não aceitável para produção.

- **C — Fly.io:**
  - Prós: free tier generoso, bom controle de regiões (importante: usuários nos EUA).
  - Contras: curva de aprendizado maior (CLI própria).

- **D — VPS (DigitalOcean/Hetzner):**
  - Prós: controle total, mais barato em escala.
  - Contras: overhead de DevOps, não recomendado para MVP.

**Recomendação:** **Railway.app** — melhor DX para o estágio atual, deploy em minutos, $5/mês é desprezível para um projeto com potencial de receita. Migrar para Fly.io ou VPS quando chegar a escala maior.

**Ação necessária:** Criar conta Railway, conectar ao repo GitHub, configurar as env vars do `.env.example`, e fazer o deploy do diretório `07-Clube-USA/backend`.

**Status:** PENDENTE

---

### [2026-08-04] Onde hospedar o frontend HTML?

**Contexto:** O frontend é HTML puro (sem build step). Pode ser hospedado em qualquer CDN estático.

**Pergunta:** Qual plataforma usar para o frontend HTML?

**Opções:**
- **A — Vercel:** free, deploy automático via GitHub, excelente CDN. Recomendado.
- **B — Netlify:** semelhante ao Vercel, também free.
- **C — GitHub Pages:** grátis, já estão no GitHub. Limitação: sem headers customizados.
- **D — Railway (mesmo serviço do backend):** simplifica mas mistura concerns.

**Recomendação:** **Vercel** para o frontend (grátis, CDN global, HTTPS automático). Configurar `CLUBE_USA_API` (URL da API) via variável de ambiente ou diretamente no HTML antes do deploy.

**Ação necessária:** Criar conta Vercel e apontar para a pasta `07-Clube-USA/frontend`.

**Status:** PENDENTE

---

### [2026-08-04] Aplicar schema SQL no Supabase

**Contexto:** O arquivo `07-Clube-USA/schema/001_initial.sql` contém o schema completo (tabelas `users` e `email_confirmations`). Precisa ser aplicado manualmente no Supabase antes do backend funcionar.

**Pergunta:** Confirma que você tem um projeto Supabase criado e pode aplicar o schema?

**Ação necessária:**
1. Acessar supabase.com > seu projeto > SQL Editor
2. Colar o conteúdo de `07-Clube-USA/schema/001_initial.sql`
3. Executar
4. Copiar `SUPABASE_URL` e `SUPABASE_SERVICE_KEY` (Settings > API) para as env vars do deploy

**Status:** PENDENTE

---

*Atualizado em: 2026-08-04*
