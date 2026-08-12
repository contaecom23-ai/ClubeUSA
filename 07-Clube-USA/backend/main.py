import os
from contextlib import asynccontextmanager

from dotenv import load_dotenv
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse
from fastapi.staticfiles import StaticFiles
from slowapi import _rate_limit_exceeded_handler
from slowapi.errors import RateLimitExceeded

load_dotenv()

from auth import router as auth_router
from limiter import limiter


@asynccontextmanager
async def lifespan(app: FastAPI):
    yield


app = FastAPI(title="Clube USA API", version="0.1.0", lifespan=lifespan)

app.state.limiter = limiter
app.add_exception_handler(RateLimitExceeded, _rate_limit_exceeded_handler)

allowed_origins = [
    o.strip()
    for o in os.environ.get("ALLOWED_ORIGINS", "http://localhost:8000").split(",")
    if o.strip()
]

app.add_middleware(
    CORSMiddleware,
    allow_origins=allowed_origins,
    allow_credentials=True,
    allow_methods=["GET", "POST", "PUT", "DELETE", "OPTIONS"],
    allow_headers=["Content-Type", "Authorization"],
)

app.include_router(auth_router, prefix="/api/auth", tags=["auth"])

# Serve frontend static files
_frontend_dir = os.path.join(os.path.dirname(__file__), "..", "frontend")
if os.path.isdir(_frontend_dir):
    app.mount("/static", StaticFiles(directory=_frontend_dir), name="static")

    @app.get("/", include_in_schema=False)
    async def index():
        return FileResponse(os.path.join(_frontend_dir, "index.html"))

    @app.get("/register", include_in_schema=False)
    async def register_page():
        return FileResponse(os.path.join(_frontend_dir, "register.html"))

    @app.get("/login", include_in_schema=False)
    async def login_page():
        return FileResponse(os.path.join(_frontend_dir, "login.html"))

    @app.get("/profile", include_in_schema=False)
    async def profile_page():
        return FileResponse(os.path.join(_frontend_dir, "profile.html"))


@app.get("/status", tags=["health"])
async def status():
    return {"status": "ok", "service": "clube-usa-api"}
