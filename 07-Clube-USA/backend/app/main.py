from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.config import get_settings
from app.database import build_db_client
from app.routes import auth, profile


@asynccontextmanager
async def lifespan(app: FastAPI):
    app.state.db = build_db_client()
    yield


def create_app() -> FastAPI:
    s = get_settings()

    app = FastAPI(
        title="Clube USA API",
        version="0.1.0",
        lifespan=lifespan,
        docs_url=None if s.is_production else "/docs",
        redoc_url=None if s.is_production else "/redoc",
    )

    app.add_middleware(
        CORSMiddleware,
        allow_origins=s.cors_origins_list,
        allow_credentials=True,
        allow_methods=["GET", "POST", "PATCH", "DELETE", "OPTIONS"],
        allow_headers=["Authorization", "Content-Type"],
    )

    app.include_router(auth.router)
    app.include_router(profile.router)

    @app.get("/health", tags=["health"])
    def health():
        return {"status": "ok"}

    return app


app = create_app()
