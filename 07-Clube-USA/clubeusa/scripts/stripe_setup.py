#!/usr/bin/env python3
# ============================================================
#  stripe_setup.py — cria (idempotente) o produto VIP no Stripe
#
#  Uso:
#    export STRIPE_SECRET_KEY=sk_test_...   (ou coloque no .env da raiz)
#    python scripts/stripe_setup.py
#
#  Nao duplica: se ja existir um produto "Clube USA VIP" com um preco
#  mensal de $4.99, apenas reaproveita e imprime o Price ID.
#
#  Ao final, imprime a linha pronta para colar no .env / painel do Render.
# ============================================================

import os
import sys

try:
    import stripe
except ImportError:
    sys.exit("Faltou instalar a lib: pip install stripe")

# Carrega .env da raiz do projeto, se existir (mesma logica do run.py)
try:
    from dotenv import load_dotenv
    from pathlib import Path
    load_dotenv(Path(__file__).resolve().parent.parent.parent.parent / ".env")
except Exception:
    pass

PRODUCT_NAME = "Clube USA VIP"
AMOUNT_CENTS = 499          # $4.99
CURRENCY     = "usd"
INTERVAL     = "month"


def main():
    key = os.environ.get("STRIPE_SECRET_KEY", "").strip()
    if not key:
        sys.exit("STRIPE_SECRET_KEY nao definida. Exporte-a ou coloque no .env.")
    stripe.api_key = key

    mode = "TESTE" if key.startswith("sk_test_") else "PRODUCAO (LIVE)"
    print(f"Conectado ao Stripe em modo: {mode}\n")

    # 1. Procura produto existente pelo nome
    product = None
    for p in stripe.Product.list(active=True, limit=100).auto_paging_iter():
        if p.name == PRODUCT_NAME:
            product = p
            print(f"Produto ja existe: {product.id}")
            break

    if product is None:
        product = stripe.Product.create(
            name=PRODUCT_NAME,
            description="Assinatura VIP — alertas de preco, deals exclusivos e prioridade.",
        )
        print(f"Produto criado: {product.id}")

    # 2. Procura price mensal de 4.99 nesse produto
    price = None
    for pr in stripe.Price.list(product=product.id, active=True, limit=100).auto_paging_iter():
        recurring = pr.get("recurring") or {}
        if (pr.unit_amount == AMOUNT_CENTS
                and pr.currency == CURRENCY
                and recurring.get("interval") == INTERVAL):
            price = pr
            print(f"Price ja existe: {price.id}")
            break

    if price is None:
        price = stripe.Price.create(
            product=product.id,
            unit_amount=AMOUNT_CENTS,
            currency=CURRENCY,
            recurring={"interval": INTERVAL},
        )
        print(f"Price criado: {price.id}")

    # 3. Saida pronta para usar
    print("\n" + "=" * 52)
    print("Cole no seu .env / grupo de variaveis do Render:")
    print(f"STRIPE_VIP_PRICE_ID={price.id}")
    print("=" * 52)


if __name__ == "__main__":
    main()
