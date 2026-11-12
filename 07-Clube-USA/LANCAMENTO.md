# Lancamento Black Friday — 27 nov 2026

Checklist vivo do lancamento enxuto (lean launch). Atualizado em 11 nov 2026.

## Feito (semana 1)

- [x] PR #78 — plano VIP preservado no re-login (merge a52632d)
- [x] PR #110 — webhook Z-API com segredo + correcoes (merge 4688192)
- [x] PR #163 — CORS com default seguro (merge 160c0ab)
- [x] PR #175 — tag FTC de afiliado nos links PT/ES (merge 1bf9652)
- [x] Testes verdes na main: 35 (externos) + 69 (internos)
- [x] Pack de tutoriais de cupons (File privado, rascunho para membros)

## Falta — depende do Gerson (um de cada vez)

1. **Render/producao**: credenciais e aprovacao para deploy + migrations.
2. **Stripe live**: chaves live e criacao do preco VIP (decisao: US$ 2,99 vs US$ 4,99; e conta BR vs EUA — ver analise no chat).
3. **Z-API**: numero dedicado e instancia (risco de ban — nao usar numero pessoal).
4. **Contas de afiliado**: Amazon Associates, Impact (Home Depot, Lowe's etc.).
5. **Beta testers**: 5-10 pessoas para validar o bot antes do dia 27.

## Falta — agente (sem depender do Gerson)

- [ ] Revisar PRs abertos restantes (19, 20, 55, 58, 63, 65, 67, 68, 76, 80, 103, 104, 109, 113, 116, 173)
- [ ] Teste end-to-end do fluxo OTP -> onboarding -> primeiro alerta
- [ ] Textos fixos do bot (boas-vindas, ajuda, erro) revisados em PT/ES

## Riscos conhecidos

- **Ban WhatsApp**: volume automatizado em grupos e policiado; mitigacao = numero dedicado + Canal (broadcast) como vitrine principal.
- **CI**: workflow do builder esta quebrado (0 jobs); validacao atual = suite local (35+69).
- **FTC**: links de afiliado ja saem com disclosure (PR #175); manter a tag em todo canal novo (TikTok, Canal, tutoriais).
