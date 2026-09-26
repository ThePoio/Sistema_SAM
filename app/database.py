from collections.abc import AsyncIterator
from contextlib import asynccontextmanager
from typing import Any

from fastapi import FastAPI, Request
from motor.motor_asyncio import AsyncIOMotorClient, AsyncIOMotorDatabase
from pymongo import UpdateOne

from .config import settings
from .services import hash_password


def get_database(request: Request) -> AsyncIOMotorDatabase[Any]:
    return request.app.state.database


@asynccontextmanager
async def lifespan(app: FastAPI) -> AsyncIterator[None]:
    client = AsyncIOMotorClient(settings.mongo_uri, serverSelectionTimeoutMS=5000)
    app.state.mongo_client = client
    app.state.database = client[settings.db_name]
    try:
        await client.admin.command("ping")
        await app.state.database.users.create_index("username", unique=True)
        await app.state.database.evaluations.create_index("assigned_to")
        await app.state.database.users.bulk_write(
            [
                UpdateOne(
                    {"username": "admin"},
                    {"$setOnInsert": {"username": "admin", "password_hash": hash_password("admin123"), "email": "admin@organismo.gov", "role": "admin", "display_name": "Administrador"}},
                    upsert=True,
                ),
                UpdateOne(
                    {"username": "encargado"},
                    {"$setOnInsert": {"username": "encargado", "password_hash": hash_password("encargado123"), "email": "encargado@organismo.gov", "role": "encargado", "display_name": "Encargado de Area"}},
                    upsert=True,
                ),
            ]
        )
        yield
    finally:
        client.close()
