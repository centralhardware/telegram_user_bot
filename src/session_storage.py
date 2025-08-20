from datetime import datetime
from typing import Optional

from clickhouse_utils import get_clickhouse_client


def load_session(name: str) -> Optional[str]:
    """Retrieve the stored session string for a given client name."""
    client = get_clickhouse_client()
    result = client.query(
        """
        SELECT session
        FROM telegram_user_bot.client_sessions
        WHERE name = %(name)s
        ORDER BY updated_at DESC
        LIMIT 1
        """,
        {"name": name},
    )
    rows = result.result_rows
    return rows[0][0] if rows else None


def save_session(name: str, session: str) -> None:
    """Persist the session string for a given client name."""
    client = get_clickhouse_client()
    client.insert(
        "telegram_user_bot.client_sessions",
        [[name, session, datetime.utcnow()]],
        column_names=["name", "session", "updated_at"],
    )
