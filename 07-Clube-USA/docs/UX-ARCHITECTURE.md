# Clube USA — UX Architecture (landing)

## Fluxo narrativo (substitui Hero→Cards→Features→CTA)

1. **Hero editorial** — headline assimétrica ("PARE DE PAGAR / O QUE NÃO PRECISA") + mockup de WhatsApp integrado à composição (deslocado, sobreposto, não centralizado). CTA "Entrar no Clube" com fricção zero reforçada abaixo. Sem stats na primeira dobra.
2. **Tensão** — "Você está pagando mais do que devia" — dado de contexto curto, tipografia grande, fundo paper.
3. **Descoberta** — "Nós procuramos nos 5 marketplaces" — comparação visual ativa (Amazon/Walmart/eBay/BestBuy/Target), não grid de logo.
4. **Verificação** — o Cartão de Investigação com sparkline de preço real de 90 dias. Seção mais forte da página.
5. **Entrega** — sequência WhatsApp (encontramos → verificamos → enviamos → você decide), 4 passos com peso editorial, não numerados genéricos.
6. **Curadoria/confiança** — "Não somos grupo de spam" como storytelling, não bullet list.
7. **Comunidade** — indicação + níveis, tratado como clube/status.
8. **Prova + números** — manchete editorial (12.4K / 320 / 43%), não proof-strip.
9. **CTA final** — "Entrar no Clube", reforço de fricção zero.

## Hierarquia de conversão
CTA primário ("Entrar no Clube") aparece 3x: hero, fim da seção de verificação, CTA final. CTA secundário ("Já é membro? Entrar no painel") só no header e footer — nunca compete com o primário.

## Navegação
Header sticky minimalista: logo + 2 links de âncora (Como funciona, Ver deal) + CTA. Sem mega-menu, sem excesso de links.

## Mobile
Ordem preservada; WhatsApp ganha um CTA fixo inferior (thumb zone); Cartão de Investigação vira full-bleed; sparkline simplifica pontos mas mantém a curva real.

## Fora de escopo desta fase
Painel logado (`#dashboard`) mantém arquitetura/IA visual atuais — é produto funcional (SaaS-like por natureza: navegação por abas, tabelas, formulários), não peça de marca. Redesenhar o dashboard é uma iniciativa separada.
