# gerar_card.py — Card de deal Clube USA 1080x1080px
# Uso: pip install pillow requests && python gerar_card.py

import io, math, os, requests
from PIL import Image, ImageDraw, ImageFont, ImageFilter

# ============================================================
#  CONFIGURACAO — edite aqui para cada deal
# ============================================================
CONFIG = {
    "produto":     "Sony WH-1000XM5",
    "copy_titulo": "O melhor fone\ndo mundo",
    "copy_sub":    "Cancelamento de ruido ativo - Sem fio",
    "preco_de":    "$399.99",
    "preco_por":   "$229.99",
    "desconto":    "42%",
    "stars":       "4.7",
    "reviews":     "47.823 avaliacoes",
    "urgencia":    "Ultimas horas nesse preco",
    "loja":        "AMAZON",
    "img_url":     "",
    "output":      "card_clube_usa.png",
}

# ============================================================
#  CONSTANTES
# ============================================================
W, H   = 1080, 1080
BG_TOP = (8,    8,  16)
BG_BOT = (12,  31,  77)
RED    = (200,  16,  46)
GREEN  = (0,   210, 106)
WHITE  = (255, 255, 255)
GRAY   = (160, 160, 175)
YELLOW = (255, 200,   0)
D_RED  = (60,   10,  18)


# ============================================================
#  FONTES
# ============================================================
def _font(size: int, bold: bool = True) -> ImageFont.FreeTypeFont:
    suffix = "bd" if bold else ""
    candidates = [
        f"C:/Windows/Fonts/arial{suffix}.ttf",
        f"C:/Windows/Fonts/calibri{'b' if bold else ''}.ttf",
        "/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf" if bold
            else "/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf",
        "DejaVuSans-Bold.ttf" if bold else "DejaVuSans.ttf",
    ]
    for p in candidates:
        if os.path.exists(p):
            try: return ImageFont.truetype(p, size)
            except: pass
    try: return ImageFont.truetype(f"arial{suffix}.ttf", size)
    except: return ImageFont.load_default()


# ============================================================
#  ESTRELAS COMO POLIGONOS
# ============================================================
def _star_polygon(cx, cy, r_out, r_in, n=5):
    pts = []
    for i in range(n * 2):
        ang = math.pi * i / n - math.pi / 2
        r   = r_out if i % 2 == 0 else r_in
        pts.append((cx + r * math.cos(ang), cy + r * math.sin(ang)))
    return pts


def draw_stars(draw, cx, cy, rating: float, r=18):
    """Desenha 5 estrelas preenchidas proporcionalmente ao rating."""
    total    = 5
    spacing  = r * 2 + 10
    start_x  = cx - (total * spacing) // 2 + spacing // 2
    for i in range(total):
        sx      = start_x + i * spacing
        filled  = max(0.0, min(1.0, rating - i))
        outline = YELLOW if filled > 0 else GRAY
        pts     = _star_polygon(sx, cy, r, r * 0.42)
        draw.polygon(pts, fill=YELLOW if filled >= 0.75 else GRAY, outline=outline)


# ============================================================
#  ICONE DE RELOGIO
# ============================================================
def draw_clock(draw, cx, cy, r, color, width=2):
    draw.ellipse([cx-r, cy-r, cx+r, cy+r], outline=color, width=width)
    # Ponteiro das horas (~10h)
    ha = -math.pi / 2 - math.pi / 3
    draw.line([cx, cy,
               cx + r * 0.45 * math.cos(ha),
               cy + r * 0.45 * math.sin(ha)], fill=color, width=width)
    # Ponteiro dos minutos (12h)
    draw.line([cx, cy, cx, cy - r * 0.65], fill=color, width=width)
    # Centro
    draw.ellipse([cx-2, cy-2, cx+2, cy+2], fill=color)


# ============================================================
#  IMAGEM DO PRODUTO
# ============================================================
def _load_image(url_or_path: str) -> Image.Image | None:
    if not url_or_path:
        return None
    try:
        if url_or_path.startswith("http"):
            headers = {"User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36"}
            resp = requests.get(url_or_path, headers=headers, timeout=12)
            raw  = Image.open(io.BytesIO(resp.content))
        else:
            raw = Image.open(url_or_path)
        img = raw.convert("RGBA")
        # Remove fundo branco
        data = img.getdata()
        img.putdata([
            (r, g, b, 0) if r > 238 and g > 238 and b > 238 else (r, g, b, a)
            for r, g, b, a in data
        ])
        return img
    except Exception as e:
        print(f"[AVISO] Imagem nao carregada: {e}")
        return None


def _paste_with_shadow(card, prod_img, x, y):
    """Cola produto com sombra eliptica embaixo."""
    sw, sh = prod_img.size
    shadow = Image.new("RGBA", (W, H), (0, 0, 0, 0))
    sd     = ImageDraw.Draw(shadow)
    sd.ellipse([x + 30, y + sh - 10, x + sw - 30, y + sh + 40], fill=(0, 0, 0, 110))
    shadow = shadow.filter(ImageFilter.GaussianBlur(22))
    card.alpha_composite(shadow)
    card.alpha_composite(prod_img, (x, y))


# ============================================================
#  GERADOR PRINCIPAL
# ============================================================
def generate_card(cfg: dict) -> str:
    # --- Canvas com gradiente ---
    card = Image.new("RGBA", (W, H), BG_TOP)
    base = Image.new("RGBA", (W, H))
    bd   = ImageDraw.Draw(base)
    for y in range(H):
        t = y / H
        r = int(BG_TOP[0] + (BG_BOT[0] - BG_TOP[0]) * t)
        g = int(BG_TOP[1] + (BG_BOT[1] - BG_TOP[1]) * t)
        b = int(BG_TOP[2] + (BG_BOT[2] - BG_TOP[2]) * t)
        bd.line([(0, y), (W, y)], fill=(r, g, b, 255))
    card.alpha_composite(base)

    # --- Glow vermelho canto superior direito ---
    glow = Image.new("RGBA", (W, H), (0, 0, 0, 0))
    gd   = ImageDraw.Draw(glow)
    for i in range(6):
        gs   = 200 + i * 60
        alph = 50 - i * 7
        gd.ellipse([W - gs, -gs // 2, W + gs // 2, gs], fill=(*RED, max(0, alph)))
    glow = glow.filter(ImageFilter.GaussianBlur(45))
    card.alpha_composite(glow)

    draw = ImageDraw.Draw(card)

    # --- Bordas vermelhas laterais ---
    draw.rectangle([0, 0, 10, H], fill=(*RED, 255))
    draw.rectangle([W-10, 0, W, H], fill=(*RED, 255))

    # --- Fonts ---
    f_hdr  = _font(30, True)
    f_ttl  = _font(58, True)
    f_sub  = _font(27, False)
    f_lbl  = _font(28, False)
    f_old  = _font(32, False)
    f_new  = _font(92, True)
    f_pct  = _font(54, True)
    f_off  = _font(26, True)
    f_rev  = _font(26, False)
    f_urg  = _font(27, True)
    f_cta  = _font(42, True)

    # --- HEADER ---
    # Badge Clube USA
    draw.rectangle([22, 22, 270, 76], fill=RED)
    draw.text((35, 33), "CLUBE USA", font=f_hdr, fill=WHITE)
    # Badge loja
    loja = cfg.get("loja", "AMAZON")
    lw   = int(draw.textlength(loja, font=f_hdr))
    draw.rectangle([W-lw-56, 22, W-22, 76], fill=(35, 35, 58), outline=(75, 75, 100), width=1)
    draw.text((W-lw-42, 33), loja, font=f_hdr, fill=(200, 200, 220))

    # --- IMAGEM DO PRODUTO ---
    IMG_Y, IMG_H = 90, 420
    prod = _load_image(cfg.get("img_url", ""))
    if prod:
        prod.thumbnail((680, IMG_H), Image.LANCZOS)
        pw, ph = prod.size
        px = (W - pw) // 2
        py = IMG_Y + (IMG_H - ph) // 2
        _paste_with_shadow(card, prod, px, py)
        draw = ImageDraw.Draw(card)
    else:
        draw.rectangle([100, IMG_Y, W-100, IMG_Y+IMG_H], fill=(20, 20, 35), outline=(50, 50, 70))
        ph_txt = "Adicione img_url na CONFIG"
        tw = int(draw.textlength(ph_txt, font=f_sub))
        draw.text(((W-tw)//2, IMG_Y + IMG_H//2 - 14), ph_txt, font=f_sub, fill=(80, 80, 100))

    # --- BADGE DE DESCONTO ---
    bx, by, br = W - 135, 210, 98
    # Sombra do badge
    for i in range(4):
        sc = max(0, 40 - i*10)
        draw.ellipse([bx-br-i*2, by-br-i*2, bx+br+i*2, by+br+i*2], fill=(0, 0, 0, sc))
    draw.ellipse([bx-br, by-br, bx+br, by+br], fill=RED)
    draw.ellipse([bx-br+3, by-br+3, bx+br-3, by+br-3], outline=(255, 70, 70), width=2)
    desc_txt = cfg.get("desconto", "0%")
    dw = int(draw.textlength(desc_txt, font=f_pct))
    draw.text((bx - dw//2, by - 44), desc_txt, font=f_pct, fill=WHITE)
    ow = int(draw.textlength("OFF", font=f_off))
    draw.text((bx - ow//2, by + 22), "OFF", font=f_off, fill=(255, 190, 200))

    # --- LINHA DIVISORIA ---
    DIV_Y = IMG_Y + IMG_H + 14
    draw.line([(80, DIV_Y), (W-80, DIV_Y)], fill=(50, 55, 80), width=1)

    # --- TITULO E SUBTITULO ---
    y = DIV_Y + 22
    titulo_lines = cfg.get("copy_titulo", cfg.get("produto", "")).split("\n")[:2]
    for linha in titulo_lines:
        tw = int(draw.textlength(linha, font=f_ttl))
        # Sombra do texto
        draw.text(((W-tw)//2 + 2, y + 2), linha, font=f_ttl, fill=(0, 0, 0, 120))
        draw.text(((W-tw)//2, y), linha, font=f_ttl, fill=WHITE)
        y += 70

    sub_txt = cfg.get("copy_sub", "")
    if sub_txt:
        sw = int(draw.textlength(sub_txt, font=f_sub))
        draw.text(((W-sw)//2, y), sub_txt, font=f_sub, fill=GRAY)
        y += 44

    # --- PRECOS ---
    y += 10
    preco_de  = cfg.get("preco_de", "")
    preco_por = cfg.get("preco_por", "$0.00")

    if preco_de:
        de_lbl = "De:"
        dl = int(draw.textlength(de_lbl, font=f_lbl))
        ol = int(draw.textlength("  " + preco_de, font=f_old))
        total_w = dl + ol
        x0 = (W - total_w) // 2
        draw.text((x0, y + 4), de_lbl, font=f_lbl, fill=GRAY)
        draw.text((x0 + dl, y + 4), "  " + preco_de, font=f_old, fill=(130, 130, 145))
        # Risco vermelho no preco antigo
        bb = draw.textbbox((x0 + dl, y + 4), "  " + preco_de, font=f_old)
        mid_y = (bb[1] + bb[3]) // 2
        draw.line([(bb[0] + 8, mid_y), (bb[2], mid_y)], fill=RED, width=3)
        y += 50

    por_lbl = "Por:"
    pl  = int(draw.textlength(por_lbl, font=f_lbl))
    nl  = int(draw.textlength(preco_por, font=f_new))
    x0  = (W - pl - 16 - nl) // 2
    draw.text((x0, y + 22), por_lbl, font=f_lbl, fill=WHITE)
    # Sombra do preco
    draw.text((x0 + pl + 18, y + 2), preco_por, font=f_new, fill=(0, 100, 40, 120))
    draw.text((x0 + pl + 16, y), preco_por, font=f_new, fill=GREEN)
    y += 106

    # --- ESTRELAS + REVIEWS ---
    stars_val = float(cfg.get("stars", "4.5"))
    draw_stars(draw, W//2 - 80, y + 14, stars_val, r=16)
    rev_txt = f"  {cfg.get('stars','')}  -  {cfg.get('reviews','')}"
    draw.text((W//2 - 12, y + 2), rev_txt, font=f_rev, fill=GRAY)
    y += 46

    # --- BARRA DE URGENCIA ---
    urg_y1 = y + 10
    urg_y2 = urg_y1 + 56
    draw.rectangle([70, urg_y1, W-70, urg_y2], fill=D_RED, outline=RED, width=1)
    # Icone de relogio
    clk_x = 110
    clk_y = (urg_y1 + urg_y2) // 2
    draw_clock(draw, clk_x, clk_y, 14, (255, 130, 130), width=2)
    # Texto urgencia
    urg_txt = cfg.get("urgencia", "Ultimas horas")
    uw  = int(draw.textlength(urg_txt, font=f_urg))
    draw.text(((W - uw)//2 + 10, urg_y1 + 14), urg_txt, font=f_urg, fill=(255, 140, 140))
    y = urg_y2 + 16

    # --- BOTAO CTA ---
    cta_y1 = y
    cta_y2 = cta_y1 + 86
    # Sombra do botao
    shadow_btn = Image.new("RGBA", (W, H), (0, 0, 0, 0))
    sbd        = ImageDraw.Draw(shadow_btn)
    sbd.rectangle([55, cta_y1+6, W-55, cta_y2+6], fill=(0, 0, 0, 80))
    shadow_btn = shadow_btn.filter(ImageFilter.GaussianBlur(8))
    card.alpha_composite(shadow_btn)
    draw = ImageDraw.Draw(card)
    draw.rectangle([55, cta_y1, W-55, cta_y2], fill=RED)
    draw.rectangle([55, cta_y1, W-55, cta_y2], outline=(255, 70, 70), width=2)
    cta_txt = "GARANTIR MINHA OFERTA  >"
    cw      = int(draw.textlength(cta_txt, font=f_cta))
    draw.text(((W-cw)//2, cta_y1 + 22), cta_txt, font=f_cta, fill=WHITE)

    # --- FAIXA RODAPE ---
    draw.rectangle([0, H-10, W, H], fill=RED)

    # --- SALVA ---
    output = cfg.get("output", "card_clube_usa.png")
    card.convert("RGB").save(output, format="PNG", optimize=True)
    return os.path.abspath(output)


# ============================================================
#  EXECUCAO
# ============================================================
if __name__ == "__main__":
    print("Gerando card...")
    path = generate_card(CONFIG)
    print(f"\nCard salvo em: {path}")
    print("\n--- INSTRUCOES ---")
    print("Como rodar:        pip install pillow requests && python gerar_card.py")
    print("Como abrir:        Abra o arquivo .png gerado em qualquer visualizador de imagem")
    print()
    print("Como adicionar imagem do produto:")
    print("  Via URL:   edite img_url com o link da imagem do produto")
    print("             Ex: 'img_url': 'https://m.media-amazon.com/images/I/xxxx.jpg'")
    print("  Via local: edite img_url com o caminho no seu PC")
    print("             Ex: 'img_url': 'C:/Users/nome/Downloads/produto.jpg'")
    print()
    print("Como pegar URL da imagem na Amazon:")
    print("  1. Abra a pagina do produto na Amazon")
    print("  2. Clique na foto principal")
    print("  3. Botao direito na imagem ampliada > Abrir imagem em nova aba")
    print("  4. Copie a URL da barra de endereco")
