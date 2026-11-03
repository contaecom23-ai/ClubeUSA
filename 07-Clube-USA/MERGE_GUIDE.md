# GUIA DE MERGE — Clube USA
> Criado em: 2026-11-03 | Para: dono do produto

## O problema em uma linha

O builder criou 154 PRs. Nenhum foi mergeado. O projeto está parado desde julho de 2026.
Este guia te diz exatamente O QUE FAZER, em ordem.

---

## PASSO 1 — Abra o GitHub no navegador

Acesse: **https://github.com/contaecom23-ai/ClubeUSA/pulls**

---

## PASSO 2 — Mergea estes PRs, NESTA ordem

Clique no PR → botão verde "Merge pull request" → "Confirm merge".
Faça um de cada vez. Espere o anterior fechar antes do próximo.

### Fase 0 (faça TUDO antes de avançar)

| Ordem | PR # | Link | O que faz |
|-------|------|------|-----------|
| 1º | **#46** | https://github.com/contaecom23-ai/ClubeUSA/pull/46 | Fase 0.1 — cadastro + email confirmado (implementação mais limpa) |
| 2º | **#57** | https://github.com/contaecom23-ai/ClubeUSA/pull/57 | Fix referral: captura ?ref= na URL |
| 3º | **#67** | https://github.com/contaecom23-ai/ClubeUSA/pull/67 | Fase 0.3 — analytics básico |
| 4º | **#58** | https://github.com/contaecom23-ai/ClubeUSA/pull/58 | Fase 0.4 — cadastro válido + anti-fraude |

### Fase 1 (depois que Fase 0 estiver mergeada)

| Ordem | PR # | Link | O que faz |
|-------|------|------|-----------|
| 5º | **#12** | https://github.com/contaecom23-ai/ClubeUSA/pull/12 | Fase 1.1 — Promoções/Achados |
| 6º | **#14** | https://github.com/contaecom23-ai/ClubeUSA/pull/14 | Fase 1.2 — Busca por ZIP |
| 7º | **#16** | https://github.com/contaecom23-ai/ClubeUSA/pull/16 | Fase 1.3 — Programa de influenciadores |
| 8º | **#19** | https://github.com/contaecom23-ai/ClubeUSA/pull/19 | Fase 1.4 — Board de empregos |
| 9º | **#20** | https://github.com/contaecom23-ai/ClubeUSA/pull/20 | Fase 1.5 — Moradia/quartos |

---

## PASSO 3 — Feche os PRs duplicados

Depois de mergear os acima, todos os outros PRs são duplicatas obsoletas.
Feche-os em massa indo em cada um e clicando "Close pull request" (sem merge).

Ou use o GitHub CLI:
```bash
gh pr list --state open --limit 200 --json number | \
  jq '.[].number' | \
  xargs -I{} gh pr close {}
```
(rode isso só DEPOIS de completar o Passo 2)

---

## POR QUE O BUILDER CRIOU 154 PRs?

O builder roda 3× ao dia. A regra dele é: "nunca mergeie na main, abra PR".
Mas como nenhum PR foi mergeado, ele continua vendo as mesmas tarefas pendentes
e criando novas implementações. É um loop. **A única saída é você mergear os PRs acima.**

---

## PERGUNTAS FREQUENTES

**Tenho medo de quebrar algo.** Não vai quebrar — os PRs são aditivos (adicionam código, não deletam). O pior cenário é um conflict de merge, que o GitHub mostra na hora com opção de resolver.

**E se o PR tiver conflito?** Clique em "Resolve conflicts" no GitHub, aceite a versão mais recente, salve.

**Preciso testar antes?** Não para os PRs de documentação/schema. Para código Python, rode `pytest 07-Clube-USA/clubeusa/tests/` depois de mergear.

**Quanto tempo leva?** ~15 minutos para mergear os 9 PRs acima.

---

## APÓS O MERGE

Responda neste PR ou escreva em DECISOES.md:
- As credenciais Supabase estão configuradas? (SUPABASE_URL, SUPABASE_SERVICE_KEY)
- O Render/deploy está configurado?
- A Z-API (WhatsApp) está ativa?

Com isso, o builder pode retomar o trabalho de forma produtiva.

---

*Gerado pelo builder autônomo em 2026-11-03*
