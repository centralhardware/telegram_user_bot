from __future__ import annotations

from datetime import datetime, timezone
from typing import List

from telethon.crypto import AuthKey
from telethon.sessions import MemorySession
from telethon.sessions.memory import _SentFileType
from telethon.tl import types

from clickhouse_utils import get_clickhouse_client


class ClickHouseSession(MemorySession):
    """SQLite-like Telethon session persisted in ClickHouse."""

    _SESSION_TABLE = "telegram_user_bot.client_sessions"
    _ENTITY_TABLE = "telegram_user_bot.client_session_entities"
    _FILES_TABLE = "telegram_user_bot.client_session_sent_files"
    _UPDATE_STATE_TABLE = "telegram_user_bot.client_session_update_state"

    def __init__(self, name: str) -> None:
        super().__init__()
        self._name = name
        self._load()

    # ------------------------------------------------------------------
    # Loading
    # ------------------------------------------------------------------
    def _load(self) -> None:
        client = get_clickhouse_client()

        # Load session information
        result = client.query(
            f"""
            SELECT dc_id, server_address, port, auth_key, takeout_id
            FROM {self._SESSION_TABLE}
            WHERE name = %(name)s
            ORDER BY updated_at DESC
            LIMIT 1
            """,
            {"name": self._name},
        )
        row = result.first_row
        if row:
            dc_id, server_address, port, auth_key, takeout_id = row
            self._dc_id = dc_id
            self._server_address = server_address
            self._port = port
            if auth_key:
                self._auth_key = AuthKey(data=auth_key)
            self._takeout_id = takeout_id

        # Load cached entities
        result = client.query(
            f"""
            SELECT id, hash, username, phone, display_name
            FROM {self._ENTITY_TABLE}
            WHERE name = %(name)s
            """,
            {"name": self._name},
        )
        for entity_id, hash_, username, phone, name in result.result_rows:
            self._entities.add((entity_id, hash_, username, phone, name))

        # Load cached files
        result = client.query(
            f"""
            SELECT md5_digest, file_size, type, id, hash
            FROM {self._FILES_TABLE}
            WHERE name = %(name)s
            """,
            {"name": self._name},
        )
        for md5_digest, file_size, type_, file_id, file_hash in result.result_rows:
            key = (md5_digest, file_size, _SentFileType(type_))
            self._files[key] = (file_id, file_hash)

        # Load update states
        result = client.query(
            f"""
            SELECT id, pts, qts, date, seq
            FROM {self._UPDATE_STATE_TABLE}
            WHERE name = %(name)s
            """,
            {"name": self._name},
        )
        for entity_id, pts, qts, date, seq in result.result_rows:
            if date.tzinfo is None:
                date = date.replace(tzinfo=timezone.utc)
            self._update_states[entity_id] = types.updates.State(
                pts, qts, date, seq, unread_count=0
            )

    # ------------------------------------------------------------------
    # Saving
    # ------------------------------------------------------------------
    def save(self) -> None:  # type: ignore[override]
        client = get_clickhouse_client()
        now = datetime.utcnow()

        # Persist session information
        client.insert(
            self._SESSION_TABLE,
            [
                [
                    self._name,
                    self._dc_id,
                    self._server_address or "",
                    self._port or 0,
                    self._auth_key.key if self._auth_key else b"",
                    self._takeout_id,
                    now,
                ]
            ],
            column_names=[
                "name",
                "dc_id",
                "server_address",
                "port",
                "auth_key",
                "takeout_id",
                "updated_at",
            ],
        )

        # Persist cached entities
        if self._entities:
            rows: List[List[object]] = []
            for entity_id, hash_, username, phone, name in self._entities:
                rows.append([
                    self._name,
                    entity_id,
                    hash_,
                    username,
                    phone,
                    name,
                    now,
                ])
            client.insert(
                self._ENTITY_TABLE,
                rows,
                column_names=[
                    "name",
                    "id",
                    "hash",
                    "username",
                    "phone",
                    "display_name",
                    "updated_at",
                ],
            )

        # Persist cached files
        if self._files:
            rows: List[List[object]] = []
            for (md5_digest, file_size, file_type), (file_id, file_hash) in self._files.items():
                rows.append([
                    self._name,
                    md5_digest,
                    file_size,
                    file_type.value,
                    file_id,
                    file_hash,
                    now,
                ])
            client.insert(
                self._FILES_TABLE,
                rows,
                column_names=[
                    "name",
                    "md5_digest",
                    "file_size",
                    "type",
                    "id",
                    "hash",
                    "updated_at",
                ],
            )

        # Persist update states
        if self._update_states:
            rows: List[List[object]] = []
            for entity_id, state in self._update_states.items():
                date = state.date.replace(tzinfo=None) if state.date.tzinfo else state.date
                rows.append([
                    self._name,
                    entity_id,
                    state.pts,
                    state.qts,
                    date,
                    state.seq,
                    now,
                ])
            client.insert(
                self._UPDATE_STATE_TABLE,
                rows,
                column_names=[
                    "name",
                    "id",
                    "pts",
                    "qts",
                    "date",
                    "seq",
                    "updated_at",
                ],
            )

