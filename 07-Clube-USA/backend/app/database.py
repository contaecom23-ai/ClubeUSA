import ssl
import asyncpg
from app.config import get_settings

_pool: asyncpg.Pool | None = None


async def _create_pool() -> asyncpg.Pool:
    settings = get_settings()
    dsn = settings.DATABASE_URL
    ssl_ctx: ssl.SSLContext | None = None
    if "supabase.co" in dsn:
        ssl_ctx = ssl.create_default_context()
    return await asyncpg.create_pool(dsn, ssl=ssl_ctx, min_size=2, max_size=10)


async def get_pool() -> asyncpg.Pool:
    global _pool
    if _pool is None:
        _pool = await _create_pool()
    return _pool


async def get_db():
    pool = await get_pool()
    async with pool.acquire() as conn:
        yield conn
