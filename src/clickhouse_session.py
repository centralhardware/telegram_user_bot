from __future__ import annotations

from datetime import datetime, timezone
from typing import List, Tuple, Dict, Any

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

        # Load session information (безопасно обрабатываем пустой результат)
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
        rows = getattr(result, "result_rows", [])
        if rows:
            dc_id, server_address, port, auth_key, takeout_id = rows[0]
            self._dc_id = dc_id
            self._server_address = server_address
            self._port = port
            if auth_key:
                # В ClickHouse тип String/Bytes хранит бинарник прозрачно
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
        for entity_id, hash_, username, phone, name in getattr(result, "result_rows", []):
            # структура как в MemorySession._entities
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
        for md5_digest, file_size, type_, file_id, file_hash in getattr(result, "result_rows", []):
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
        for entity_id, pts, qts, date, seq in getattr(result, "result_rows", []):
            # нормализуем timezone -> naive UTC (Telethon хранит naive)
            if date.tzinfo is None:
                # считаем, что это UTC-naive
                date_utc_naive = date
            else:
                date_utc_naive = date.astimezone(timezone.utc).replace(tzinfo=None)

            self._update_states[entity_id] = types.updates.State(
                pts=pts, qts=qts, date=date_utc_naive, seq=seq, unread_count=0
            )

    # ------------------------------------------------------------------
    # Saving
    # ------------------------------------------------------------------
    def save(self) -> None:  # type: ignore[override]
        client = get_clickhouse_client()
        # Используем UTC-naive как в Telethon
        now = datetime.utcnow()

        # Persist session information — всегда INSERT (ReplacingMergeTree поглотит дубликаты)
        client.insert(
            self._SESSION_TABLE,
            [[
                self._name,
                self._dc_id,
                self._server_address or "",
                self._port or 0,
                (self._auth_key.key if self._auth_key else b""),
                self._takeout_id,
                now,
                ]],
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
            rows_ent: List[List[object]] = []
            for entity_id, hash_, username, phone, name in self._entities:
                rows_ent.append([
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
                rows_ent,
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
            rows_files: List[List[object]] = []
            for (md5_digest, file_size, file_type), (file_id, file_hash) in self._files.items():
                rows_files.append([
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
                rows_files,
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
            rows_states: List[List[object]] = []
            for entity_id, state in self._update_states.items():
                # приводим к naive (UTC) для согласованности с загрузкой
                if state.date.tzinfo is None:
                    date_naive = state.date
                else:
                    date_naive = state.date.astimezone(timezone.utc).replace(tzinfo=None)
                rows_states.append([
                    self._name,
                    entity_id,
                    state.pts,
                    state.qts,
                    date_naive,
                    state.seq,
                    now,
                ])
            client.insert(
                self._UPDATE_STATE_TABLE,
                rows_states,
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
