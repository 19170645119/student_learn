from core.mail import create_mail_instance
from fastapi_mail import FastMail
from sqlalchemy.ext.asyncio import AsyncSession
from models import AsyncSessionFactory
import redis.asyncio as aioredis
import settings

async def get_session() -> AsyncSession:
    session = AsyncSessionFactory()
    try:
        yield session
    finally:
        await session.close()

async def get_mail() -> FastMail:
    return create_mail_instance()

async def get_redis():
    redis_client = aioredis.from_url(
        f"redis://{settings.REDIS_HOST}:{settings.REDIS_PORT}/{settings.REDIS_DB}",
        encoding="utf-8",
        decode_responses=True
    )
    try:
        yield redis_client
    finally:
        await redis_client.close()
