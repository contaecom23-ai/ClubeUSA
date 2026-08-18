# Clube USA — Design System (landing/marketing)

> Escopo: página pública (`#landing` em `platform.html`). O painel logado (`#dashboard`) mantém o sistema visual funcional existente (navy/vermelho/branco) por ser UI de aplicativo, não peça de marca.

## Typography

| Papel | Fonte | Peso | Uso |
|---|---|---|---|
| Display | Fraunces | 700–900 | Headlines, manchetes de número |
| H2/H3 | Fraunces | 600 | Títulos de seção |
| Body | Inter | 400–500 | Parágrafos, descrições |
| Labels/Caption | Inter | 600, uppercase, tracking +.04em | Eyebrows, legendas |
| Dados/preço/data | IBM Plex Mono | 500–700 | Preços, %, datas, timers |

## Color

```
--navy:      #0D1B3E   /* autoridade, fundos escuros */
--navy-2:    #152347
--paper:     #F6F1E7   /* fundo editorial claro */
--paper-2:   #EEE6D6
--ink:       #16181D   /* texto sobre paper */
--terracotta:#C1602B   /* acento primário — economia/ação */
--terracotta-d:#9c4c22
--olive:     #5C6B47   /* verificado/confiança */
--olive-l:   #7C8F5F
--red:       #B0202F   /* urgência genuína apenas */
--muted:     #8A8577
--line:      #DCD3C0   /* hairline */
```

## Spacing
Base 8px. Escala: 8 / 16 / 24 / 32 / 48 / 64 / 96 / 128.

## Grid
12 colunas, desktop max-width 1320px, gutters 24px. Seções editoriais usam offset de 1–2 colunas (conteúdo nunca preenche 100% nem fica sempre centralizado).

## Border-radius
- Dados/badges de preço: `2px` (quase reto)
- Botões: `100px` (pill, convite claro)
- Blocos editoriais/fotos: `0`
- Componente de deal (dossiê): `4px`

## Componente proprietário: "Cartão de Investigação" (deal)
Estrutura em camadas, não card de loja:
1. Cabeçalho: marketplace + selo de verificação (olive)
2. Título do produto (Inter, peso 600)
3. Preço: mono, tamanho manchete, preço anterior riscado ao lado
4. Sparkline de 90 dias (SVG desenhado, não texto)
5. Linha de metadados (cupom, estoque, avaliação) — hairline dividers, não boxes
6. CTA reto, texto ativo

## Selos
- Verificado (olive, ícone check)
- Menor preço em 90 dias (terracotta, quadrado)
- Estoque baixo (red, só quando genuíno)

## Botões
- Primário: terracotta sólido, pill, texto branco
- Secundário: outline navy/ink, pill
- Nunca gradiente

## Motion tokens
- Reveal: fade 400ms + translateY 16px, stagger 80ms
- Sparkline: stroke-dashoffset 0→length, 900ms ease-out
- Número manchete: count-up 1200ms cubic ease-out

## Responsivo
- Desktop: grid assimétrico 12 col
- Tablet (≤980px): 8 col, offset reduzido
- Mobile (≤640px): 1 col, WhatsApp ganha destaque de topo (CTA fixo inferior)
