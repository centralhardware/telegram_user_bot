import os
from dataclasses import dataclass, field
from typing import List, Optional


def _get_chat_ids() -> List[str]:
    chat_ids = os.getenv("TELEGRAM_CHAT_IDS", "")
    return [cid.strip() for cid in chat_ids.split(",") if cid.strip()]


@dataclass
class Config:
    api_id = int(os.getenv("API_ID"))
    api_hash = os.getenv("API_HASH")
    telephone = os.getenv("TELEPHONE")
    telephone_second = os.getenv("TELEPHONE_SECOND")
    db_user = os.getenv("CLICKHOUSE_USER")
    db_password = os.getenv("CLICKHOUSE_PASSWORD")
    db_host = os.getenv("CLICKHOUSE_HOST")
    db_database = os.getenv("CLICKHOUSE_DATABASE")
    chat_ids: List[str] = field(default_factory=_get_chat_ids)


config = Config()
