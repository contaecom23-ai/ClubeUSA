"""
Configura variáveis de ambiente antes de qualquer import do app,
pois pydantic-settings lê as vars na instanciação do módulo config.
"""
import os

os.environ.setdefault("SUPABASE_URL", "https://test.supabase.co")
os.environ.setdefault("SUPABASE_SERVICE_ROLE_KEY", "test-service-role-key-xxxxxxxxxx")
os.environ.setdefault("SUPABASE_JWT_SECRET", "test-jwt-secret-32-chars-xxxxxxxxx!")
os.environ.setdefault("ALLOWED_ORIGINS", "http://localhost:8000")
