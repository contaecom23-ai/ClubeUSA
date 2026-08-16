# ============================================================
#  deal_translator.py — Agente de localizacao de titulos
#  Usa Groq (gratis) para traduzir nomes de produtos para
#  PT e ES usando os termos que latinos realmente usam.
# ============================================================

import os
import json
import logging
import requests

log = logging.getLogger("translator")

GROQ_API_KEY = os.environ.get("GROQ_API_KEY", "")
GROQ_URL     = "https://api.groq.com/openai/v1/chat/completions"
GROQ_MODEL   = "llama-3.1-8b-instant"

_cache: dict = {}  # evita chamar API duas vezes para o mesmo produto


def _call_groq(prompt: str) -> str | None:
    if not GROQ_API_KEY:
        return None
    try:
        resp = requests.post(
            GROQ_URL,
            headers={"Authorization": f"Bearer {GROQ_API_KEY}", "Content-Type": "application/json"},
            json={
                "model":       GROQ_MODEL,
                "messages":    [{"role": "user", "content": prompt}],
                "max_tokens":  80,
                "temperature": 0.3,
            },
            timeout=8,
        )
        if resp.status_code == 200:
            return resp.json()["choices"][0]["message"]["content"].strip()
    except Exception as e:
        log.debug(f"Groq erro: {e}")
    return None


def translate_title(title: str, lang: str = "pt") -> str:
    """
    Retorna o titulo do produto no idioma e vocabulario do publico-alvo.
    PT: brasileiro. ES: latino americano (neutro).
    Mantem nomes de marca e modelos como estao.
    Se a API nao estiver disponivel, retorna o titulo original.
    """
    cache_key = f"{lang}:{title}"
    if cache_key in _cache:
        return _cache[cache_key]

    if lang == "es":
        prompt = (
            "Eres experto en productos americanos para latinoamericanos. "
            "Localiza este título usando los términos que la gente usa realmente en conversación, "
            "no traducciones literales que suenen raras. "
            "Mantén marca y modelo exactos. Máximo 80 caracteres. "
            "Responde SOLO con el título, sin explicaciones ni comillas.\n\n"
            "Ejemplos correctos:\n"
            "- 'Wireless Noise Canceling Headphones' → 'Audífonos inalámbricos con cancelación de ruido'\n"
            "- 'Electric Pressure Cooker' → 'Olla a presión eléctrica'\n"
            "- 'Cordless Drill' → 'Taladro inalámbrico'\n"
            "- 'Air Fryer' → 'Freidora de aire'\n"
            "- 'Robot Vacuum' → 'Aspiradora robot'\n\n"
            f"Producto: {title}"
        )
    else:
        prompt = (
            "Você é especialista em produtos americanos para brasileiros. "
            "Localize este título usando os termos que as pessoas usam no dia a dia no Brasil, "
            "NUNCA traduções literais que soem estranhas ou ridículas. "
            "Mantenha marca e modelo exatos. Máximo 80 caracteres. "
            "Responda APENAS com o título, sem explicações ou aspas.\n\n"
            "Exemplos CORRETOS (como brasileiro fala de verdade):\n"
            "- 'Wireless Noise Canceling Headphones' → 'Fone de ouvido sem fio com cancelamento de ruído'\n"
            "- 'Over-Ear Headphones' → 'Headphone over-ear' (não 'fones de cabeça'!)\n"
            "- 'Electric Pressure Cooker' → 'Panela de pressão elétrica'\n"
            "- 'Cordless Drill' → 'Furadeira sem fio'\n"
            "- 'Air Fryer' → 'Fritadeira airfryer'\n"
            "- 'Robot Vacuum' → 'Aspirador robô'\n"
            "- 'Blender' → 'Liquidificador'\n"
            "- 'Stand Mixer' → 'Batedeira planetária'\n"
            "- 'Dash Cam' → 'Câmera veicular'\n\n"
            f"Produto: {title}"
        )

    translated = _call_groq(prompt)

    if not translated or len(translated) > 120:
        return title  # fallback: original

    # Remove aspas que o modelo as vezes adiciona
    translated = translated.strip('"\'')
    _cache[cache_key] = translated
    return translated
