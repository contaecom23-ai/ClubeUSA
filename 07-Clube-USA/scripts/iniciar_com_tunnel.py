"""
Inicia a Clube USA API + tunel publico (ngrok).
Uso: python iniciar_com_tunnel.py

O tunel gera uma URL publica (ex: https://abc123.ngrok-free.app)
que deve ser configurada no Z-API como webhook URL.
"""
import os, sys, time, threading, subprocess
from pathlib import Path
from dotenv import load_dotenv

ROOT = Path(__file__).parent
load_dotenv(ROOT / ".env")
sys.path.insert(0, str(ROOT / "clubeusa"))

PORT = int(os.environ.get("PORT", 8000))

def start_tunnel():
    time.sleep(3)  # aguarda API subir
    try:
        from pyngrok import ngrok, conf

        # Token do ngrok — gerar em dashboard.ngrok.com (gratis)
        ngrok_token = os.environ.get("NGROK_TOKEN", "")
        if ngrok_token:
            conf.get_default().auth_token = ngrok_token

        tunnel = ngrok.connect(PORT, "http")
        public_url = tunnel.public_url.replace("http://", "https://")

        print("\n" + "="*60)
        print("  CLUBE USA — ACESSO PUBLICO ATIVO")
        print("="*60)
        print(f"\n  Site:        {public_url}")
        print(f"  API:         {public_url}/health")
        print(f"  Admin:       {public_url}/admin")
        print(f"\n  Z-API Webhook URL:")
        print(f"  {public_url}/webhook/group")
        print("\n  Configure essa URL no painel Z-API!")
        print("="*60 + "\n")

        # Salva URL publica no .env para referencia
        env_path = ROOT / ".env"
        content = env_path.read_text()
        if "NGROK_PUBLIC_URL=" in content:
            lines = [f"NGROK_PUBLIC_URL={public_url}" if l.startswith("NGROK_PUBLIC_URL=") else l
                     for l in content.splitlines()]
            env_path.write_text("\n".join(lines))
        else:
            env_path.write_text(content + f"\nNGROK_PUBLIC_URL={public_url}\n")

    except Exception as e:
        print(f"\n[AVISO] Tunel nao iniciado: {e}")
        print(f"        A API continua disponivel em http://localhost:{PORT}\n")

# Inicia tunnel em background
t = threading.Thread(target=start_tunnel, daemon=True)
t.start()

# Inicia API
print(f"\nIniciando Clube USA API na porta {PORT}...")
os.chdir(ROOT / "clubeusa")
import uvicorn
uvicorn.run(
    "api.main:app",
    host="0.0.0.0",
    port=PORT,
    reload=True,
    log_level="info",
)
