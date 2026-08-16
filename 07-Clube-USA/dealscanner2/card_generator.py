# ============================================================
#  card_generator.py — Card visual 1080x1080 para Telegram
# ============================================================

import io, os, requests, textwrap
from PIL import Image, ImageDraw, ImageFont, ImageFilter

W, H = 1080, 1080

# Paleta
DARKER = (10,  10,  18)
NAVY   = (12,  31,  77)
RED    = (200, 16,  46)
GREEN  = (0,   210, 100)
WHITE  = (255, 255, 255)
GRAY   = (170, 170, 185)
YELLOW = (255, 204,  0)


def _font(name: str, size: int) -> ImageFont.FreeTypeFont:
    candidates = [
        f"C:/Windows/Fonts/{name}.ttf",
        f"C:/Windows/Fonts/{name}.TTF",
        f"/usr/share/fonts/truetype/liberation/Liberation{'Sans-Bold' if 'bd' in name else 'Sans-Regular'}.ttf",
    ]
    for p in candidates:
        if os.path.exists(p):
            try: return ImageFont.truetype(p, size)
            except Exception: pass
    try: return ImageFont.truetype(name + ".ttf", size)  # PIL system search
    except Exception: return ImageFont.load_default()


def _fetch_product_image(url: str) -> Image.Image | None:
    if not url:
        return None
    try:
        headers = {"User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36"}
        resp = requests.get(url, headers=headers, timeout=10)
        img  = Image.open(io.BytesIO(resp.content)).convert("RGBA")
        # Remove fundo branco (imagens Amazon)
        data     = img.getdata()
        new_data = [
            (r, g, b, 0) if r > 238 and g > 238 and b > 238 else (r, g, b, a)
            for r, g, b, a in data
        ]
        img.putdata(new_data)
        return img
    except Exception:
        return None


def _generate_copy(deal: dict, lang: str) -> tuple[str, str]:
    """Gera copy curto de venda via Groq. Fallback: titulo limpo."""
    import os, requests as req
    key = os.environ.get("GROQ_API_KEY", "")
    if key:
        try:
            brand = deal.get("title", "").split()[0]
            if lang == "es":
                prompt = (
                    f"Crea un copy de venta CORTO (máx 2 líneas, 6 palabras cada una) "
                    f"para este producto americano dirigido a latinoamericanos. "
                    f"Debe ser directo, emocional, sin precio. Usa salto de línea entre las 2 líneas. "
                    f"Solo el copy, sin comillas ni explicaciones.\n\nProducto: {deal['title']}"
                )
            else:
                prompt = (
                    f"Crie um copy de venda CURTO (máx 2 linhas, 6 palavras cada) "
                    f"para este produto americano voltado para brasileiros. "
                    f"Direto, emocional, sem preço. Use quebra de linha entre as 2 linhas. "
                    f"Apenas o copy, sem aspas nem explicações.\n\nProduto: {deal['title']}"
                )
            resp = req.post(
                "https://api.groq.com/openai/v1/chat/completions",
                headers={"Authorization": f"Bearer {key}", "Content-Type": "application/json"},
                json={"model": "llama-3.1-8b-instant", "messages": [{"role":"user","content":prompt}],
                      "max_tokens": 40, "temperature": 0.7},
                timeout=6,
            )
            if resp.status_code == 200:
                copy = resp.json()["choices"][0]["message"]["content"].strip().strip('"\'')
                lines = [l.strip() for l in copy.split("\n") if l.strip()][:2]
                if lines:
                    sub = "Oferta por tempo limitado" if lang == "pt" else "Oferta por tiempo limitado"
                    return "\n".join(lines), sub
        except Exception:
            pass

    # Fallback: primeiras palavras do titulo
    words = deal.get("title", "").split()
    title = " ".join(words[:5])
    sub   = "Oferta por tempo limitado" if lang == "pt" else "Oferta por tiempo limitado"
    return title, sub


def generate_deal_card(deal: dict, lang: str = "pt") -> bytes:
    card = Image.new("RGB", (W, H), DARKER)
    draw = ImageDraw.Draw(card)

    # --- Gradiente de fundo ---
    for y in range(H):
        t = y / H
        r = int(DARKER[0] + (NAVY[0]-DARKER[0]) * t * 0.7)
        g = int(DARKER[1] + (NAVY[1]-DARKER[1]) * t * 0.7)
        b = int(DARKER[2] + (NAVY[2]-DARKER[2]) * t * 0.7)
        draw.line([(0, y), (W, y)], fill=(r, g, b))

    # Barra vermelha esquerda
    draw.rectangle([0, 0, 8, H], fill=RED)

    # --- Fonts ---
    f_logo   = _font("arialbd", 32)
    f_store  = _font("arialbd", 26)
    f_titulo = _font("arialbd", 62)
    f_sub    = _font("arial",   30)
    f_label  = _font("arial",   30)
    f_old    = _font("arial",   34)
    f_new    = _font("arialbd", 96)
    f_pct    = _font("arialbd", 52)
    f_off    = _font("arialbd", 26)
    f_rev    = _font("arial",   28)
    f_urg    = _font("arialbd", 26)
    f_cta    = _font("arialbd", 40)

    # --- HEADER ---
    logo = "CLUBE USA" if lang == "pt" else "CLUB USA"
    draw.rectangle([22, 24, 260, 72], fill=RED)
    draw.text((30, 32), logo, font=f_logo, fill=WHITE)

    store = deal.get("source_label", "Amazon")
    sw = int(draw.textlength(store, font=f_store))
    draw.rectangle([W-sw-36, 24, W-22, 72], fill=(40, 40, 65), outline=(80,80,110), width=1)
    draw.text((W-sw-28, 32), store, font=f_store, fill=(200, 200, 220))

    # --- IMAGEM DO PRODUTO ---
    prod = _fetch_product_image(deal.get("image_url"))
    img_h = 420
    img_y = 90

    if prod:
        prod.thumbnail((680, img_h), Image.LANCZOS)
        pw, ph = prod.size
        px = (W - pw) // 2

        # Sombra
        shadow = Image.new("RGBA", (W, H), (0,0,0,0))
        sd = ImageDraw.Draw(shadow)
        sd.ellipse([px+30, img_y+ph-10, px+pw-30, img_y+ph+40], fill=(0,0,0,100))
        shadow = shadow.filter(ImageFilter.GaussianBlur(25))
        card.paste(shadow, (0,0), shadow)

        card.paste(prod, (px, img_y), prod)
        img_bottom = img_y + ph + 10
    else:
        img_bottom = img_y + 40

    # --- BADGE DE DESCONTO ---
    discount = deal.get("discount_pct", 0)
    bx, by, br = W - 120, 155, 100
    draw.ellipse([bx-br, by-br, bx+br, by+br], fill=RED)
    draw.ellipse([bx-br+4, by-br+4, bx+br-4, by+br-4], outline=(255,70,70), width=2)
    pct_str = f"{discount}%"
    pw2 = int(draw.textlength(pct_str, font=f_pct))
    draw.text((bx - pw2//2, by - 38), pct_str, font=f_pct, fill=WHITE)
    ow  = int(draw.textlength("OFF", font=f_off))
    draw.text((bx - ow//2, by + 22), "OFF", font=f_off, fill=(255,180,180))

    # --- COPY CURTO ---
    copy_title, copy_sub = _generate_copy(deal, lang)
    y = img_bottom + 18

    for linha in copy_title.split("\n")[:2]:
        draw.text((W//2, y), linha, font=f_titulo, fill=WHITE, anchor="mm")
        y += 72

    draw.text((W//2, y), copy_sub, font=f_sub, fill=GRAY, anchor="mm")
    y += 50

    # Linha separadora
    draw.line([(80, y), (W-80, y)], fill=(55,55,80), width=1)
    y += 24

    # --- PRECOS ---
    price_now = deal.get("price_now", 0)
    price_was = deal.get("price_was")
    de_lbl  = "De:" if lang == "pt" else "Antes:"
    por_lbl = "Por:" if lang == "pt" else "Ahora:"

    if price_was:
        lw = int(draw.textlength(de_lbl, font=f_label))
        draw.text((W//2 - lw//2 - 80, y + 4), de_lbl, font=f_label, fill=GRAY)
        old_str = f"  ${price_was:.2f}"
        draw.text((W//2 - lw//2 - 80 + lw, y + 4), old_str, font=f_old, fill=(130,130,145))
        # Risco no preco antigo
        bb = draw.textbbox((W//2 - lw//2 - 80 + lw, y + 4), old_str, font=f_old)
        draw.line([(bb[0], (bb[1]+bb[3])//2), (bb[2], (bb[1]+bb[3])//2)], fill=RED, width=3)
        y += 48

    lw2 = int(draw.textlength(por_lbl, font=f_label))
    nw  = int(draw.textlength(f"${price_now:.2f}", font=f_new))
    total_w = lw2 + 14 + nw
    x_start = (W - total_w) // 2
    draw.text((x_start, y), por_lbl, font=f_label, fill=WHITE)
    draw.text((x_start + lw2 + 14, y - 18), f"${price_now:.2f}", font=f_new, fill=GREEN)
    y += 95

    # --- PROVA SOCIAL ---
    rating  = deal.get("rating", 0)
    reviews = deal.get("reviews", 0)
    if rating and reviews:
        stars = "★" * min(int(rating), 5)
        rev_txt = f"{stars}  {rating}  —  {reviews:,} avaliacoes" if lang == "pt" else f"{stars}  {rating}  —  {reviews:,} resenas"
        rw = int(draw.textlength(rev_txt, font=f_rev))
        draw.text(((W-rw)//2, y), rev_txt, font=f_rev, fill=YELLOW)
        y += 46

    # --- URGÊNCIA ---
    urg = "Ultimas horas nesse preco" if lang == "pt" else "Ultimas horas con este precio"
    draw.rectangle([70, y, W-70, y+50], fill=(50,10,10), outline=(180,20,40), width=1)
    uw = int(draw.textlength(f"  {urg}", font=f_urg))
    draw.text(((W-uw)//2, y+11), f"  {urg}", font=f_urg, fill=(255,130,130))
    y += 66

    # --- CTA ---
    cta_y1 = H - 110
    draw.rectangle([50, cta_y1, W-50, cta_y1+78], fill=RED)
    draw.rectangle([50, cta_y1, W-50, cta_y1+78], outline=(255,80,80), width=2)
    cta = "GARANTIR MINHA OFERTA  →" if lang == "pt" else "OBTENER MI OFERTA  →"
    cw  = int(draw.textlength(cta, font=f_cta))
    draw.text(((W-cw)//2, cta_y1+18), cta, font=f_cta, fill=WHITE)

    # Barra inferior
    draw.rectangle([0, H-10, W, H], fill=RED)

    buf = io.BytesIO()
    card.save(buf, format="PNG", optimize=True)
    return buf.getvalue()
