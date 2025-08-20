from __future__ import annotations

from datetime import datetime, timezone
from typing import List

from telethon.crypto import AuthKey
from telethon.sessions import MemorySession
from telethon.sessions.memory import _SentFileType
from telethon.tl import types

from clickhouse_utils import get_clickhouse_client


def _to_bytes(v) -> bytes:
    """Нормализует значение к bytes для двоичных полей из ClickHouse."""
    if v is None:
        return b""
    if isinstance(v, bytes):
        return v
    if isinstance(v, bytearray):
        return bytes(v)
    if isinstance(v, memoryview):
        return v.tobytes()
    if isinstance(v, str):
        # Если драйвер вернул str, кодируем без потерь в диапазоне 0..255.
        # Это корректно, если исходно было сохранено как raw bytes в String.
        return v.encode("latin1")
    # На всякий случай пытаемся сконвертить «как есть»
    return bytes(v)


class ClickHouseSession(MemorySession):
    """Telethon session, сохранённая в ClickHouse (аналог SQLite-сессии)."""

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

        # --- session info (безопасно обрабатываем пустой результат)
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
                # КЛЮЧЕВОЙ ФИКС: приводим к bytes прежде чем скормить AuthKey
                auth_key_bytes = _to_bytes(auth_key)
                self._auth_key = AuthKey(data=auth_key_bytes)
            self._takeout_id = takeout_id

        # --- cached entities
        result = client.query(
            f"""
            SELECT id, hash, username, phone, display_name
            FROM {self._ENTITY_TABLE}
            WHERE name = %(name)s
            """,
            {"name": self._name},
        )
        for entity_id, hash_, username, phone, name in getattr(result, "result_rows", []):
            self._entities.add((entity_id, hash_, username, phone, name))

        # --- cached files
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

        # --- update states
        result = client.query(
            f"""
            SELECT id, pts, qts, date, seq
            FROM {self._UPDATE_STATE_TABLE}
            WHERE name = %(name)s
            """,
            {"name": self._name},
        )
        for entity_id, pts, qts, date, seq in getattr(result, "result_rows", []):
            # нормализуем: Telethon использует naive UTC
            if date.tzinfo is None:
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
        now = datetime.utcnow()  # Telethon ожидает naive UTC

        # --- session info: всегда INSERT (ReplacingMergeTree «заменит» по updated_at)
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

        # --- cached entities
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

        # --- cached files
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

        # --- update states
        if self._update_states:
            rows_states: List[List[object]] = []
            for entity_id, state in self._update_states.items():
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
