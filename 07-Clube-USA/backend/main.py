from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from fastapi.staticfiles import StaticFiles

from .config import get_settings
from .routers import auth, profile


@asynccontextmanager
async def lifespan(app: FastAPI):
    get_settings()  # Validate required env vars at startup, not at first request
    yield


def create_app() -> FastAPI:
    settings = get_settings()

    app = FastAPI(
        title=settings.app_name,
        version="0.1.0",
        docs_url="/docs" if settings.environment == "development" else None,
        redoc_url=None,
        lifespan=lifespan,
    )

    app.add_middleware(
        CORSMiddleware,
        allow_origins=settings.allowed_origins,
        allow_credentials=True,
        allow_methods=["GET", "POST", "PATCH", "DELETE", "OPTIONS"],
        allow_headers=["Authorization", "Content-Type"],
        max_age=600,
    )

    app.include_router(auth.router, prefix="/api/v1")
    app.include_router(profile.router, prefix="/api/v1")

    @app.get("/health", tags=["infra"])
    async def health():
        return {"status": "ok", "service": settings.app_name}

    return app


app = create_app()
