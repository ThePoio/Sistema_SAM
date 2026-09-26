from collections.abc import AsyncIterator
from contextlib import asynccontextmanager
from typing import Any

from fastapi import FastAPI
from motor.motor_asyncio import AsyncIOMotorClient, AsyncIOMotorDatabase

from .config import settings


def get_database(app: FastAPI) -> AsyncIOMotorDatabase[Any]:
    return app.state.database


@asynccontextmanager
async def lifespan(app: FastAPI) -> AsyncIterator[None]:
    client = AsyncIOMotorClient(settings.mongo_uri, serverSelectionTimeoutMS=5000)
    app.state.mongo_client = client
    app.state.database = client[settings.db_name]
    try:
        await client.admin.command("ping")
        yield
    finally:
        client.close()
