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

---

### [2026-10-16-A] Provedor de email para confirmação (Fase 0.1)

**Contexto:** O sistema atual autentica por OTP via WhatsApp — identidade é verificada. Para completar 0.1 com "email confirmado", precisamos enviar email de verificação. Isso requer uma conta em provedor externo.

**Pergunta:** Qual provedor de email transacional usar para confirmação de cadastro e alertas futuros?

**Opções:**
- **Resend** (resend.com): plano gratuito 3.000 emails/mês, API simples, integração fácil. Prós: gratuito até ~1k usuários, SDK Python pronto, reputação boa. Contras: limite baixo no free tier, produto novo.
- **Postmark** (postmarkapp.com): 100 emails/mês grátis, foco em deliverability transacional. Prós: entregabilidade excelente. Contras: limite gratuito muito baixo, caro em escala (custo ~$15/mês por 10k emails).
- **Supabase Auth built-in**: Supabase já tem flow de email confirmação nativo. Prós: zero configuração adicional, grátis até limite do plano. Contras: acopla auth ao Supabase Auth (mudança arquitetural — hoje auth é custom JWT+OTP). 
- **Adiar confirmação de email**: Aceitar cadastro sem email confirmado agora; adicionar confirmação quando atingir 500+ usuários. Prós: sem custo, sem dependência. Contras: emails inválidos acumulam; Fase 1.3 (influenciadores pagos) precisa de cadastro "válido" — pode usar phone OTP como substituto.

**Recomendação:** Adiar confirmação de email por enquanto. O phone OTP via WhatsApp é uma verificação de identidade mais forte que email. Para Fase 1.3 (pagar por cadastro válido), definir "válido" como: phone verificado (já é) + ≥1 ação real. Quando atingir 1k usuários, migrar para Resend (plano grátis aguenta). Registrar email como opcional mas não verificado.

**Status:** PENDENTE — aguarda decisão do dono.

---

### [2026-10-16-B] Definição formal de "cadastro válido" para Fase 1.3 (Influenciadores Pagos)

**Contexto:** A Fase 1.3 paga influenciadores por "cadastro válido". A definição precisa ser precisa o suficiente para evitar fraude (contas falsas) e justa para o influenciador. O sistema já calcula um protótipo em `/admin/analytics`.

**Pergunta:** Qual a definição oficial de "cadastro válido" para fins de pagamento de influenciadores?

**Opções:**
- **Opção A (atual/protótipo):** status=active AND (total_clicks >= 1 OR referral_count >= 1). Fácil de verificar, mas baixo — um clique é trivial de simular.
- **Opção B (mais rigorosa):** status=active AND total_clicks >= 3 AND conta tem >= 7 dias. Reduz bots, razoável para influenciadores legítimos.
- **Opção C (mais rigorosa ainda):** status=active AND (email confirmado OU número de WhatsApp exclusivo verificado) AND total_clicks >= 2 AND conta >= 14 dias. Praticamente anti-fraude, mas bloqueado pela decisão de email acima.

**Recomendação:** Opção B para o lançamento da Fase 1.3. Simples, sem dependência de email, reduz bots. Revisar em 30 dias com dados reais.

**Status:** PENDENTE — aguarda decisão do dono. Bloqueia implementação de Fase 1.3.

---

*Atualizado em: 2026-10-16*
