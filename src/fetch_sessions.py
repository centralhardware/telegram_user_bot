import logging
from datetime import datetime

from telethon.tl.functions.account import GetAuthorizationsRequest

from clickhouse_utils import get_clickhouse_client


async def fetch_user_sessions(client):
    clickhouse = get_clickhouse_client()
    result = await client(GetAuthorizationsRequest())
    now = datetime.utcnow()

    all_data = []

    for session in result.authorizations:
        if session.current:
            continue

        all_data.append(
            [
                session.hash,
                session.device_model or "",
                session.platform or "",
                session.system_version or "",
                session.app_name or "",
                session.app_version or "",
                session.ip or "",
                session.country or "",
                session.region or "",
                session.date_created,
                session.date_active,
                now,
                client._self_id,
            ]
        )

    if all_data:
        clickhouse.insert(
            "telegram_user_bot.user_sessions",
            all_data,
            [
                "hash",
                "device_model",
                "platform",
                "system_version",
                "app_name",
                "app_version",
                "ip",
                "country",
                "region",
                "date_created",
                "date_active",
                "updated_at",
                "client_id",
            ],
        )