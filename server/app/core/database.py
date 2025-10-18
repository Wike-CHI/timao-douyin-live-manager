# -*- coding: utf-8 -*-
"""MongoDB connection and initialization helpers."""
from __future__ import annotations

import logging
from typing import Iterable, Type

from beanie import Document, init_beanie
from motor.motor_asyncio import AsyncIOMotorClient

from ..utils.settings import get_settings

logger = logging.getLogger(__name__)

_client: AsyncIOMotorClient | None = None


def get_mongo_client() -> AsyncIOMotorClient:
    global _client
    if _client is None:
        settings = get_settings()
        _client = AsyncIOMotorClient(settings.mongo_uri)
        logger.info("✅ 已创建 Mongo 客户端: %s", settings.mongo_uri)
    return _client


async def init_db(document_models: Iterable[Type[Document]]) -> None:
    """Initialise Beanie with the provided document models."""
    client = get_mongo_client()
    settings = get_settings()
    db = client[settings.mongo_db_name]
    await init_beanie(database=db, document_models=list(document_models))
    logger.info("✅ MongoDB 初始化完成 (数据库: %s)", settings.mongo_db_name)
