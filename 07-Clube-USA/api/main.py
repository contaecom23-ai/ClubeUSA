from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from .config import settings
from .routers import profiles

app = FastAPI(
    title="Clube USA API",
    version="0.1.0",
    # Em produção: docs_url=None, redoc_url=None
    docs_url="/docs",
    redoc_url=None,
)

_origins = [o.strip() for o in settings.allowed_origins.split(",") if o.strip()]

app.add_middleware(
    CORSMiddleware,
    allow_origins=_origins,
    allow_credentials=True,
    allow_methods=["GET", "POST", "PUT", "DELETE"],
    allow_headers=["Authorization", "Content-Type"],
    max_age=3600,
)

app.include_router(profiles.router)


@app.get("/health", tags=["meta"])
def health() -> dict:
    return {"status": "ok", "service": "clube-usa-api", "version": "0.1.0"}
