import asyncpg
from .config import get_settings

_pool: asyncpg.Pool | None = None


async def create_pool() -> asyncpg.Pool:
    s = get_settings()
    return await asyncpg.create_pool(
        s.database_url,
        min_size=2,
        max_size=10,
        command_timeout=30,
        ssl="require",  # Supabase exige SSL
    )


async def get_pool() -> asyncpg.Pool:
    global _pool
    if _pool is None:
        _pool = await create_pool()
    return _pool


async def close_pool() -> None:
    global _pool
    if _pool:
        await _pool.close()
        _pool = None


async def get_db():
    """FastAPI dependency — fornece uma conexão do pool."""
    pool = await get_pool()
    async with pool.acquire() as conn:
        yield conn
