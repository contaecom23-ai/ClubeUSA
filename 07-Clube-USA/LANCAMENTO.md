# Lancamento Black Friday - 27 nov 2026

Checklist vivo do lancamento enxuto (lean launch). Atualizado em 11 nov 2026 (2a atualizacao: decisao VIP).

## Decisao do Gerson (11 nov 2026, noite)

- **VIP = US$ 4,99** (valor que ja esta no codigo; nada de 2,99).
- **VIP NAO entra no lancamento de BF**: o dia 27 sai so com o plano gratuito.
- **Stripe live ADIADO para pos-lancamento**: chaves live e criacao do preco ficam para depois do dia 27. Nao e bloqueio do lancamento.
- PR #68 (billing) segue deferido. Codigo de cobranca existente NAO sera removido.

## Feito (semana 1)

- [x] PR #78 - plano VIP preservado no re-login (merge a52632d)
- [x] PR #110 - webhook Z-API com segredo + correcoes (merge 4688192)
- [x] PR #163 - CORS com default seguro (merge 160c0ab)
- [x] PR #175 - tag FTC de afiliado nos links PT/ES (merge 1bf9652)
- [x] PR #176 - validacao de env no startup (Z-API obrigatorio p/ OTP) (merge acf44af)
- [x] PR #177 - suite de 48 testes API portada do #103 (merge b0d50f0)
- [x] PR #178 - busca de deals por ZIP + raio geografico, portado do #65 (merge 36fd39f)
- [x] PRs #180, #181, #182, #183 - revisados, byte-verificados e mergeados (suite verde apos cada merge)
- [x] PRs #58, #104, #113, #116 fechados com comentario explicativo (branches preservados)
- [x] CI: clubeusa-builder.yml corrigido e PAUSADO (so workflow_dispatch; sem cron)
- [x] Testes verdes na main: 35 (externos) + 192 (internos)
- [x] Pack de tutoriais de cupons (File privado, rascunho para membros)
- [x] Fila de PRs revisada: abertos restantes 19, 20, 55, 63 e 68 - todos deferidos, nao bloqueiam o lancamento

## Falta - depende do Gerson (um de cada vez)

1. **Render/producao**: credenciais e aprovacao para deploy + migrations. ANTES do deploy, rodar no Supabase, NESTA ORDEM, as migrations pendentes:
   - `clubeusa/db/email_confirm_migration.sql` (se ainda nao rodou - base da proxima)
   - `clubeusa/db/valid_registration_migration.sql` (anti-fraude #181 - depende da email_confirm)
   - `clubeusa/db/zip_search_migration.sql` (colunas de geo - sem ela, /member/deals quebra)
   - `clubeusa/db/promotions_migration.sql` (promocoes #182)
2. **Z-API**: numero dedicado e instancia (risco de ban - nao usar numero pessoal).
3. **Contas de afiliado**: Amazon Associates, Impact (Home Depot, Lowe's etc.).
4. **Beta testers**: 5-10 pessoas para validar o bot antes do dia 27.

## Pos-lancamento (depois do dia 27)

1. **Stripe live + preco VIP US$ 4,99**: chaves live, criacao do preco e decisao conta BR vs EUA (ver analise no chat). PR #68 volta para revisao nessa fase.
2. **Reativacao do builder automatizado**: somente com OK explicito; hoje pausado.

## Falta - agente (sem depender do Gerson)

- [ ] Teste end-to-end do fluxo OTP -> onboarding -> primeiro alerta
- [ ] Textos fixos do bot (boas-vindas, ajuda, erro) revisados em PT/ES

## Riscos conhecidos

- **Ban WhatsApp**: volume automatizado em grupos e policiado; mitigacao = numero dedicado + Canal (broadcast) como vitrine principal.
- **CI**: workflow do builder pausado; validacao atual = suite local (35 + 192).
- **FTC**: links de afiliado ja saem com disclosure (PR #175); manter a tag em todo canal novo (TikTok, Canal, tutoriais).
