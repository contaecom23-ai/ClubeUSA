import asyncpg
from .config import settings

_pool: asyncpg.Pool | None = None


async def startup() -> None:
    global _pool
    if not settings.DATABASE_URL:
        return  # Permitir startup sem DB apenas em modo DEBUG
    _pool = await asyncpg.create_pool(
        settings.DATABASE_URL,
        min_size=2,
        max_size=10,
        command_timeout=30,
    )


async def shutdown() -> None:
    global _pool
    if _pool:
        await _pool.close()
        _pool = None


def get_pool() -> asyncpg.Pool:
    if _pool is None:
        raise RuntimeError("Pool de banco não inicializado. Verifique DATABASE_URL.")
    return _pool


async def fetchrow(query: str, *args):
    async with get_pool().acquire() as conn:
        return await conn.fetchrow(query, *args)


async def fetch(query: str, *args):
    async with get_pool().acquire() as conn:
        return await conn.fetch(query, *args)


async def execute(query: str, *args):
    async with get_pool().acquire() as conn:
        return await conn.execute(query, *args)
