# Rastreador de Produtos Multi-Marketplace + Verificação de Cupons — Design Spec
**Data:** 2026-08-16
**Status:** Aprovado

---

## Visão Geral

Extensão do sistema de alertas de preço (hoje limitado a Amazon + um alvo de preço único) para permitir que o membro:

1. Cole o link de um produto (Amazon, Walmart, Target ou BestBuy)
2. Veja automaticamente o preço desse mesmo produto nos outros marketplaces suportados
3. Veja cupons candidatos encontrados para esse produto/marketplace
4. Saiba, com um selo claro, se cada cupom foi **realmente confirmado** (testado no carrinho do site de destino) ou é apenas **não confirmado** (candidato não testável automaticamente)
5. Continue monitorando esse produto ao longo do tempo, recebendo notificação (WhatsApp/Telegram) se o preço cair ou um cupom confirmado aparecer

Adicionalmente, o campo `categories` já existente no cadastro (nichos) passa a ser editável pelo membro no perfil, não só no registro.

A tabela `price_alerts` existente (Amazon + preço-alvo único) **não é alterada nem removida** — continua funcionando como está. Esta é uma funcionalidade nova e paralela.

Feature exclusiva de plano pago, seguindo o mesmo padrão de `require_paid_plan` já usado em `/alerts/*`.

---

## Por que a verificação de cupom não é 100% garantida

Confirmar que um cupom funciona de verdade exige simular o carrinho de compra no site de destino e aplicar o código — isso só é viável de forma automatizada e sustentável para um conjunto limitado de marketplaces (Amazon, Walmart, Target, BestBuy no lançamento). Sites fora dessa lista, ou casos em que a automação falha (mudança de HTML, CAPTCHA, bloqueio anti-bot), ficam com o cupom marcado como **não confirmado** em vez de omitido ou apresentado como garantido. Essa é uma decisão de produto deliberada: melhor ser transparente sobre a incerteza do que fingir 100% de certeza.

---

## Banco de Dados

Três tabelas novas no Supabase, independentes de `price_alerts`:

```sql
CREATE TABLE tracked_products (
    id            UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    member_id     UUID NOT NULL REFERENCES members(id) ON DELETE CASCADE,
    source_url    TEXT NOT NULL,
    source        VARCHAR(20) NOT NULL CHECK (source IN ('amazon','walmart','target','bestbuy')),
    source_id     VARCHAR(64) NOT NULL,       -- ASIN/SKU/TCIN na origem
    title         TEXT,
    image_url     TEXT,
    status        VARCHAR(20) NOT NULL DEFAULT 'active'
                  CHECK (status IN ('active', 'paused', 'cancelled')),
    created_at    TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

CREATE INDEX idx_tracked_member ON tracked_products (member_id);
CREATE INDEX idx_tracked_active ON tracked_products (status) WHERE status = 'active';

CREATE TABLE tracked_product_offers (
    id                 UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    tracked_product_id UUID NOT NULL REFERENCES tracked_products(id) ON DELETE CASCADE,
    marketplace        VARCHAR(20) NOT NULL CHECK (marketplace IN ('amazon','walmart','target','bestbuy')),
    price              NUMERIC(10,2),
    url                TEXT NOT NULL,
    last_checked_at    TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    UNIQUE (tracked_product_id, marketplace)
);

CREATE TABLE tracked_product_coupons (
    id                 UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    tracked_product_id UUID NOT NULL REFERENCES tracked_products(id) ON DELETE CASCADE,
    marketplace        VARCHAR(20) NOT NULL,
    code               VARCHAR(64) NOT NULL,
    description        TEXT,
    source             VARCHAR(40),            -- de onde veio o candidato (ex: 'slickdeals', 'retailmenot')
    verified           BOOLEAN,                 -- true=confirmado, false=testado e invalido, null=nao testavel
    last_verified_at   TIMESTAMPTZ,
    created_at         TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    UNIQUE (tracked_product_id, marketplace, code)
);

CREATE INDEX idx_coupons_product ON tracked_product_coupons (tracked_product_id);

ALTER TABLE tracked_products ENABLE ROW LEVEL SECURITY;
ALTER TABLE tracked_product_offers ENABLE ROW LEVEL SECURITY;
ALTER TABLE tracked_product_coupons ENABLE ROW LEVEL SECURITY;

CREATE POLICY tracked_products_own_select ON tracked_products
    FOR SELECT USING (member_id = auth.uid());
CREATE POLICY tracked_products_own_insert ON tracked_products
    FOR INSERT WITH CHECK (member_id = auth.uid());
CREATE POLICY tracked_products_own_update ON tracked_products
    FOR UPDATE USING (member_id = auth.uid());

-- offers e coupons sao lidos via join com tracked_products (mesma regra de posse),
-- escrita feita apenas pelo service role (scanner/API backend)
CREATE POLICY offers_via_product ON tracked_product_offers
    FOR SELECT USING (
        tracked_product_id IN (SELECT id FROM tracked_products WHERE member_id = auth.uid())
    );
CREATE POLICY coupons_via_product ON tracked_product_coupons
    FOR SELECT USING (
        tracked_product_id IN (SELECT id FROM tracked_products WHERE member_id = auth.uid())
    );
```

**Limite:** máximo 10 produtos com `status = 'active'` por membro (mesmo padrão de `MAX_ACTIVE_ALERTS`), validado na API antes de inserir.

---

## Módulos Novos (`dealscanner2/`)

### `product_matcher.py`
- `identify_source(url) -> (source, source_id)` — detecta o marketplace pela URL e extrai o ID. Reaproveita `extract_asin_from_url` (já existe em `services/alert_service.py`) para Amazon; adiciona equivalentes de regex para Walmart (`/ip/.../{id}`), Target (`/-/A-{tcin}`) e BestBuy (`/site/.../{sku}.p`).
- `find_offers(title, exclude_source) -> list[offer]` — busca o título nos clients já existentes do scanner (`amazon_api`, `walmart_api`, `ebay_api` não incluso pois não é um dos 4 suportados nesta v1, `bestbuy_api`, e Target via `slickdeals_api`/`target_api`), pulando a fonte de origem. Reaproveita os parsers `parse_walmart_item`, `parse_bestbuy_item` etc.

### `coupon_finder.py`
- `find_candidates(title, marketplace) -> list[coupon_candidate]` — consulta feeds/APIs de sites de cupom (reaproveitando o padrão de `slickdeals_api.py` para feeds RSS de cupom, mais RetailMeNot se houver feed público disponível) e retorna candidatos com `code`, `description`, `source`.

### `coupon_verifier.py`
- Módulo isolado, com um "driver" Playwright por marketplace suportado: `verify_amazon(code, product_url)`, `verify_walmart(...)`, `verify_target(...)`, `verify_bestbuy(...)`.
- Cada driver: abre o carrinho, adiciona o produto, aplica o código, compara o total antes/depois. Retorna `True`/`False`.
- `verify(marketplace, code, product_url) -> bool | None` — despacha para o driver certo; se o marketplace não tiver driver, ou o driver lançar exceção/timeout/CAPTCHA, retorna `None` (não verificável) e loga o motivo — nunca propaga a exceção para o chamador.
- Cada driver roda isolado (try/except próprio) para que uma falha em um marketplace não impeça a verificação dos demais.

---

## API Endpoints

Todos exigem JWT válido + plano pago (`require_paid_plan`), mesmo padrão de `/alerts/*`.

| Método | Rota | Descrição |
|--------|------|-----------|
| `POST` | `/products/track` | Recebe URL, cria produto rastreado, dispara busca de ofertas e cupons |
| `GET` | `/products/track` | Lista produtos rastreados do membro, com ofertas e cupons |
| `GET` | `/products/track/{id}` | Detalhe de um produto (ofertas + cupons + status de verificação) |
| `DELETE` | `/products/track/{id}` | Remove (cancela) o rastreamento |

### Payload `POST /products/track`
```json
{ "url": "https://www.amazon.com/dp/B08N5WRWNW" }
```

### Resposta `POST /products/track` (síncrona: identificação + ofertas; assíncrona: cupons)
```json
{
  "id": "uuid",
  "source": "amazon",
  "title": "Echo Dot (4th Gen) Smart Speaker with Alexa",
  "offers": [
    { "marketplace": "amazon",  "price": 22.99, "url": "..." },
    { "marketplace": "walmart", "price": 24.50, "url": "..." }
  ],
  "coupons_status": "verificando"
}
```
O cliente faz polling em `GET /products/track/{id}` (ou recebe via WebSocket/SSE, fora de escopo na v1) até `coupons_status` virar `pronto`.

### Extração de ID por marketplace (v1)
- Amazon: `/dp/{ASIN}`, `/gp/product/{ASIN}` (já existente)
- Walmart: `/ip/.../{id}` (dígitos)
- Target: `/-/A-{tcin}`
- BestBuy: `/site/.../{sku}.p`

URLs encurtadas ou de marketplaces fora dessa lista retornam `400` com mensagem clara pedindo um link direto de um dos 4 sites suportados.

---

## Fluxo Ponta a Ponta

1. Membro cola a URL em `POST /products/track`
2. `product_matcher.identify_source()` detecta marketplace + ID; se falhar → `400`
3. Busca detalhes do produto de origem (título, preço, imagem) via o client daquele marketplace
4. Grava `tracked_products` + primeira linha em `tracked_product_offers` (a própria origem)
5. `product_matcher.find_offers()` busca o título nos outros 3 marketplaces → grava `tracked_product_offers` adicionais
6. Resposta síncrona ao membro com as ofertas já encontradas (passos 1-5 são rápidos, segundos)
7. Em background (task assíncrona, não bloqueia a resposta):
   - `coupon_finder.find_candidates()` roda por marketplace com oferta encontrada
   - Para cada candidato, `coupon_verifier.verify()` roda (pode levar 10-30s por marketplace)
   - Grava/atualiza `tracked_product_coupons` conforme os resultados chegam
8. Membro visualiza no painel: ofertas ordenadas por preço, cupons com selo confirmado/não confirmado

---

## Monitoramento Contínuo

Nova função `check_tracked_products()` em `dealscanner2/scheduler.py`, rodando em ciclo próprio (a cada 6h — mais espaçado que o scan geral, pois cada produto rastreado dispara N buscas de oferta + potencial verificação via navegador, que é caro).

### Fluxo do ciclo
1. Busca todos `tracked_products` com `status = 'active'`
2. Para cada um, reconsulta preço em todas as `tracked_product_offers` existentes (reaproveita os mesmos clients de API)
3. Roda `coupon_finder.find_candidates()` de novo; cupons candidatos novos entram como `verified = null`
4. Só dispara `coupon_verifier.verify()` para: cupons novos, ou cupons já verificados há mais de 7 dias (evita gastar automação de navegador à toa em cupons que não mudaram)
5. Se preço caiu em qualquer oferta, ou um cupom passou a `verified = true`: notifica o membro (reaproveita `sender.py`) e atualiza `last_checked_at`/`last_verified_at`

### Isolamento de falhas
Falha em um marketplace (rede, mudança de HTML, CAPTCHA) não interrompe o processamento dos demais produtos/marketplaces do ciclo — mesmo padrão de try/except por fonte já usado em `scanner.py`.

---

## Interface (`platform.html`)

### Preferências de nichos (perfil)
Campo `categories` do membro passa a ser editável via checkboxes no perfil (hoje só é setado no cadastro). Reaproveita a mesma lista de categorias já validada na API: `all, electronics, kitchen, baby, fitness, beauty, tools, pets, fashion, automotive, books`. Novo endpoint `PATCH /member/profile` com `{ "categories": [...] }`.

### "Adicionar produto"
Campo de colar link + botão. Estados:
- Buscando ofertas... (spinner curto)
- Lista de ofertas por marketplace, ordenada da mais barata pra mais cara
- Cupons: selo verde "✓ cupom confirmado" com código copiável, ou selo cinza "cupom não confirmado — pode não estar mais ativo"
- Erro claro se URL não for de um dos 4 marketplaces suportados

### "Meus produtos"
Lista de produtos rastreados: título, imagem, preço atual por marketplace, indicador se caiu desde que foi adicionado, botão remover.

---

## Notificação (WhatsApp/Telegram via `sender.py`)

```
💰 Queda de preço — Clube USA

[Nome do produto]
[Marketplace]: $XX.XX (antes $YY.YY)

🎟️ Cupom confirmado: CODIGO123 (-$Z)

👉 [link afiliado]
```

---

## Arquivos Afetados

| Arquivo | Mudança |
|---------|---------|
| `clubeusa/db/schema.sql` (nova migration `product_tracker_migration.sql`) | Tabelas `tracked_products`, `tracked_product_offers`, `tracked_product_coupons` |
| `clubeusa/api/main.py` | 4 novos endpoints `/products/track*`, endpoint `PATCH /member/profile` |
| `dealscanner2/product_matcher.py` | Novo — identificação de fonte + busca de ofertas |
| `dealscanner2/coupon_finder.py` | Novo — busca de cupons candidatos |
| `dealscanner2/coupon_verifier.py` | Novo — verificação via Playwright, um driver por marketplace |
| `dealscanner2/scheduler.py` | Nova função `check_tracked_products()` |
| `dealscanner2/sender.py` | Nova função `send_tracked_product_alert()` |
| `platform.html` | UI de nichos editáveis, adicionar produto, meus produtos |
| `requirements.txt` | Adiciona `playwright` |

---

## Restrições e Limites

- Máximo 10 produtos ativos rastreados por membro
- Marketplaces suportados na v1: Amazon, Walmart, Target, BestBuy (não eBay — sem driver de verificação nem busca de oferta nesta fase)
- Casamento de produto entre marketplaces é por similaridade de título (não por UPC/GTIN) — pode ocasionalmente casar variante errada (cor/tamanho); é uma limitação conhecida da v1
- Verificação de cupom não é garantida para 100% dos casos — cupons fora dos 4 marketplaces suportados, ou onde a automação falhar, ficam `verified = null` e são exibidos como "não confirmado", nunca omitidos nem apresentados como garantidos
- Verificação de cupom via Playwright é assíncrona e pode levar até ~30s por marketplace — não é resultado instantâneo
- Ciclo de recheck é de 6h (mais espaçado que o scanner geral) para conter custo de automação de navegador
