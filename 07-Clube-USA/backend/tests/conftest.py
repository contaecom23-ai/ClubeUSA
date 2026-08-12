"""
Set required env vars before any module import so that db.py / security.py
do not raise RuntimeError at collection time.
"""
import os

os.environ.setdefault(
    "SECRET_KEY", "test-secret-key-xxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx"
)
os.environ.setdefault("SUPABASE_URL", "http://localhost:54321")
os.environ.setdefault("SUPABASE_SERVICE_KEY", "test-service-key")
os.environ.setdefault("ALLOWED_ORIGINS", "http://localhost:8000")
os.environ.setdefault("COOKIE_SECURE", "false")
