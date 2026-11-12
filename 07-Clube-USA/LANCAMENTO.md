# Lancamento Black Friday — 27 nov 2026

Checklist vivo do lancamento enxuto (lean launch). Atualizado em 11 nov 2026.

## Feito (semana 1)

- [x] PR #78 — plano VIP preservado no re-login (merge a52632d)
- [x] PR #110 — webhook Z-API com segredo + correcoes (merge 4688192)
- [x] PR #163 — CORS com default seguro (merge 160c0ab)
- [x] PR #175 — tag FTC de afiliado nos links PT/ES (merge 1bf9652)
- [x] PR #176 — validacao de env no startup (Z-API obrigatorio p/ OTP) (merge acf44af)
- [x] PR #177 — suite de 48 testes API portada do #103 (merge b0d50f0)
- [x] PR #178 — busca de deals por ZIP + raio geografico, portado do #65 (merge 36fd39f)
- [x] CI: clubeusa-builder.yml corrigido e PAUSADO (so workflow_dispatch; sem cron)
- [x] Testes verdes na main: 35 (externos) + 134 (internos)
- [x] Pack de tutoriais de cupons (File privado, rascunho para membros)

## Falta — depende do Gerson (um de cada vez)

1. **Render/producao**: credenciais e aprovacao para deploy + migrations. ANTES do deploy, rodar no Supabase, NESTA ORDEM, as migrations pendentes:
   - `clubeusa/db/email_confirm_migration.sql` (se ainda não rodou — base da próxima)
   - `clubeusa/db/valid_registration_migration.sql` (anti-fraude #181 — depende da email_confirm)
   - `clubeusa/db/zip_search_migration.sql` (colunas de geo — sem ela, /member/deals quebra)
   - `clubeusa/db/promotions_migration.sql` (promoções #182)
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
