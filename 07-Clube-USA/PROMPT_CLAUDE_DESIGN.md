# PROMPT PARA CLAUDE.AI — Clube USA Platform

Cole o texto abaixo diretamente no Claude.ai para gerar a plataforma completa.

---

## PROMPT:

Crie uma plataforma web completa chamada **Clube USA** — um clube de ofertas americanas para latinos (Brasil, México, Argentina, etc.). É uma Single Page Application (SPA) em HTML + CSS + JavaScript puro, sem frameworks, em um único arquivo.

---

### IDENTIDADE VISUAL

- **Fontes:** Bebas Neue (títulos/números), Barlow (corpo) — Google Fonts
- **Cores principais:**
  - Navy: `#0D1B3E` (fundo escuro, nav, sidebar)
  - Gold: `#C9961A` / Light Gold: `#F0BC3A` / `#FFD966` (destaque, CTAs)
  - WhatsApp Green: `#25D366`
  - Off-white: `#F3F0E8` (fundo claro das seções)
  - Vermelho desconto: `#dc2626`
  - Verde preço: `#16a34a`
- **Estilo:** profissional, moderno, confiável — não é um grupo amador, é uma plataforma séria

---

### ESTRUTURA DA PÁGINA (estados)

A página tem 3 estados que alternam via JavaScript:

**Estado 1: LANDING PAGE** (visitante não logado)
**Estado 2: MODAL DE AUTENTICAÇÃO** (overlay sobre a landing)
**Estado 3: PAINEL DO MEMBRO** (logado)

---

### ESTADO 1 — LANDING PAGE

#### Navbar fixa
- Logo "CLUBE USA" (Bebas Neue, gold) + tagline "Save More. Every Day."
- Links: "Como funciona" | "Deals" 
- Botão "Entrar Grátis" (gold, arredondado) → abre modal de autenticação
- Quando logado: mostra nome do membro + indicador verde online + esconde botão

#### Hero Section (fundo navy, gradiente escuro)
- Badge animado: "● O maior clube de deals para latinos"
- Título grande Bebas Neue: "ECONOMIZE" + "DE VERDADE" (gold)
- Subtítulo: "Deals reais verificados, com histórico de preço real. Direto no seu WhatsApp — grátis."
- Faixa de estatísticas: `12.4K Membros` | `320 Deals/mês` | `43% Desconto médio`
- **Seção dos 2 grupos WhatsApp:**
  - Título: "📲 Escolha seu grupo e entre agora"
  - 2 botões verdes (#25D366) lado a lado com ícone WhatsApp SVG:
    - Botão 1: "🇧🇷 Clube USA — Grupo 1" + "177 vagas disponíveis"
    - Botão 2: "🇲🇽 Club USA — Grupo 2" + "712 vagas disponíveis"
  - Os botões devem carregar dinamicamente via `GET /public/groups`
  - Fallback estático se API falhar
  - Link abaixo: "Já é membro? Entrar no painel"

#### Seção "Como Funciona" (fundo off-white)
3 cards horizontais:
1. **Entre no grupo** — Clique no link do grupo WhatsApp. Gratuito, sem senha.
2. **Receba os deals** — 3x por dia você recebe os melhores deals verificados com histórico de preço real.
3. **Economize de verdade** — Clique no link, compre direto na loja. Sem mistério.

#### Seção "Exemplo de Deal Real" (fundo navy)
Card de deal completo mostrando:
- Header: badge da loja (Amazon laranja), Score "91 · Excelente"
- Badges: "🏆 MENOR PREÇO DE SEMPRE" (vermelho)
- Título: "Sony WH-1000XM5 Wireless Noise Canceling Headphones"
- Preço: ~~$349.99~~ → **$229.00** com badge **-34%**
- Grid 2x2 de stats:
  - Menor em 90 dias: $229 ✓ agora (verde)
  - Média 90 dias: $299.00
  - Você economiza: $120.99 (verde)
  - Nesse preço há: 18 horas (laranja)
- Extras: 📦 Poucas unidades | 🎟️ Cupom +5% na página | 📉 Tendência: ↓ caindo | ⭐ 4.7 · 28.400 avaliações
- Botão: "📲 Entrar para ver todos os deals →"

#### Seção "Por que o Clube USA?" (fundo off-white)
Grid 3x2 de cards com ícone + título + descrição:
1. 📊 Histórico de preço real — Cada deal tem histórico dos últimos 90 dias. Você vê se o desconto é real.
2. ✅ Curadoria humana — Todo deal é revisado antes de enviar. Só o que vale a pena.
3. 🔒 Privacidade total — Você nunca vê o número de outros membros. Grupo 100% seguro.
4. 🏪 5 marketplaces — Amazon, Walmart, eBay, BestBuy e Target. O melhor preço de qualquer loja.
5. 🎁 Indique e ganhe — Cada amigo vale +200 pontos. 3 indicações = VIP grátis por 30 dias.
6. 🔔 Alertas de preço (VIP) — Defina o preço alvo e receba aviso automático.

#### Faixa de prova social (fundo navy2 #152347)
Horizontal: `12.4K Membros ativos` | `R$847 Economia média/membro` | `4.9⭐ Avaliação` | `0 Deals falsos enviados`

#### Footer CTA (fundo gold)
- Título Bebas Neue navy: "PRONTO PARA ECONOMIZAR?"
- Subtítulo
- Os mesmos 2 botões de grupo WhatsApp (navy escuro)

#### Footer final (navy)
Links: Privacidade | Termos | Contato | Painel do membro
© 2025 Clube USA

---

### ESTADO 2 — MODAL DE AUTENTICAÇÃO

Overlay escuro com blur. Card centralizado (off-white, borda gold no topo, animação popIn).

**3 etapas:**

**Etapa 1 — Telefone:**
- Campo nome (só no cadastro, oculto no login)
- Campo telefone com hint: "+55 Brasil, +52 México, +1 EUA/Canadá"
- Botão verde WhatsApp: "📲 Receber código no WhatsApp"
- Chama: `POST /auth/register` (se cadastro) + `POST /auth/otp/request`

**Etapa 2 — OTP:**
- Input centralizado com letra-spacing grande, máx 6 dígitos
- Auto-submit ao digitar 6 dígitos
- Link "Reenviar código"
- Chama: `POST /auth/otp/verify`
- Salva token no localStorage

**Etapa 3 — Sucesso:**
- Ícone 🎉
- "BEM-VINDO AO CLUBE!"
- Botão: "Ir para o painel →" → mostra Estado 3

---

### ESTADO 3 — PAINEL DO MEMBRO

Layout grid: sidebar fixa (240px navy) + área principal (off-white).

#### Sidebar
- Logo "CLUBE USA" (gold)
- Badge do plano (Free ou ⭐ VIP)
- Menu: 🔥 Deals de Hoje | 🎁 Indicações | 🏆 Ranking | 👤 Perfil
- Botão sair no fundo

#### Saudação
- "Olá, [Nome]! 👋"
- Subtítulo dinâmico ("Aqui estão os melhores deals de hoje")

#### Aba: DEALS DE HOJE
Grid responsivo de cards de deal. Cada card:
- Header navy: badge da loja colorido + score
- Body:
  - Badges condicionais (🏆 Menor de sempre / 📉 Menor em 90 dias)
  - Título do produto
  - Preço agora (verde grande) + preço era (riscado) + badge desconto (vermelho)
  - Grid 2x2: Você economiza | Contexto histórico | Avaliação | Reviews
  - Botão navy "🛒 Ver na loja →" → chama `POST /member/click` → abre URL rastreada

Carregado via: `GET /member/deals?limit=20` (com Authorization Bearer)

#### Aba: INDICAÇÕES
- Card de progresso VIP: barra de progresso 0/3 indicações
  - "Indique 3 amigos que fiquem 7 dias → ganhe VIP grátis por 30 dias"
- Card com link de indicação:
  - Campo readonly com a URL
  - Botão "Copiar"
  - Botão verde "📲 Compartilhar no WhatsApp" → abre wa.me com mensagem pronta
- Card de stats: Indicações | Pontos | Nível

Carregado via: `GET /member/referral`

#### Aba: RANKING
- Título "🏆 Top Indicadores do Clube"
- Lista de membros: posição (🥇🥈🥉 para top 3) + nome anonimizado + indicações + pontos
- Destaca posição do membro logado

Carregado via: `GET /member/leaderboard`

#### Aba: PERFIL
- Plano | Pontos | Nível | Indicações

Carregado via: `GET /member/profile`

---

### INTEGRAÇÃO COM API

```javascript
// URL configurável no topo do arquivo
const API_URL = 'http://localhost:8000';
const APP_URL = 'https://clubeusa.com';
```

**Endpoints usados:**
- `GET  /public/groups`           → 2 grupos WhatsApp ativos (sem auth)
- `POST /auth/register`           → cadastro (phone, name, language)
- `POST /auth/otp/request`        → solicita OTP via WhatsApp
- `POST /auth/otp/verify`         → verifica OTP, retorna JWT
- `GET  /member/profile`          → perfil do membro (Bearer token)
- `GET  /member/deals?limit=20`   → deals do dia (Bearer token)
- `POST /member/click`            → rastreia clique, retorna URL com UTM
- `GET  /member/referral`         → link e stats de indicação (Bearer token)
- `GET  /member/leaderboard`      → ranking (Bearer token)

**Auth flow:**
- Token salvo em `localStorage.setItem('cu_token', token)`
- Membro salvo em `localStorage.setItem('cu_member', JSON.stringify({id, plan}))`
- Ao carregar a página: se token existe → vai direto para o painel

---

### DETALHES TÉCNICOS

- **Responsivo:** mobile-first, sidebar vira menu hamburguer no mobile
- **Sem dependências externas** além do Google Fonts
- **Fallbacks:** se API falhar, mostra dados estáticos (grupos, deals de exemplo)
- **Loading states:** spinner animado enquanto carrega
- **Error states:** mensagens amigáveis em português/espanhol
- **OTP:** auto-submit ao digitar 6 dígitos, campo com letter-spacing grande
- **Copy to clipboard:** botão copiar com feedback visual
- **WhatsApp share:** abre wa.me com mensagem pré-formatada
- **CORS:** API deve ter CORS configurado para o domínio do site

---

### RESPONSIVIDADE MOBILE

- Nav: esconde links, mantém logo + botão CTA
- Hero: empilha verticalmente, botões WhatsApp em coluna
- Dashboard: sidebar vira bottom nav ou menu hamburguer
- Cards de deals: 1 coluna no mobile

---

Gere o HTML completo, funcional, em um único arquivo com todo CSS inline no `<style>` e JavaScript no `<script>`. O código deve ser limpo, bem comentado por seção, e pronto para produção.
