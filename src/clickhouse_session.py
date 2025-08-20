from __future__ import annotations

import base64
import binascii
import logging
from datetime import datetime, timezone
from typing import List, Tuple, Optional, Any, Iterable

from telethon.crypto import AuthKey
from telethon.sessions import MemorySession
from telethon.sessions.memory import _SentFileType
from telethon.tl import types

from clickhouse_utils import get_clickhouse_client

"""
ClickHouse-backed Telethon session.

Ключевые отличия от исходной версии:
- Правильная загрузка auth_key из ClickHouse: поддержка RAW bytes, HEX-строк и base64.
- Запрещаем сохранять "пустой" ключ: пишем NULL в Nullable(String).
- Не используем недоступные для clickhouse-connect settings.
- Нормализуем даты к naive UTC (как ожидает Telethon).
"""

log = logging.getLogger(__name__)


def _decode_auth_key(raw: Any) -> Optional[bytes]:
    """
    Превращает значение из ClickHouse в bytes для AuthKey.
    Поддерживает bytes/bytearray/memoryview, hex-строку (512/384 символов), base64-строку,
    а также крайний случай "raw-байты в String" через latin1.
    Возвращает None, если ключ невалиден.
    """
    if raw is None:
        return None

    # Уже bytes?
    if isinstance(raw, (bytes, bytearray, memoryview)):
        data = bytes(raw)

    elif isinstance(raw, str):
        s = raw.strip()

        # 1) base64
        try:
            data = base64.b64decode(s, validate=True)
        except Exception:
            # 2) hex (512 симв. = 256 байт; 384 = 192 байта)
            try:
                s_hex = s.removeprefix("0x").removeprefix("0X").replace(" ", "")
                data = binascii.unhexlify(s_hex)
            except Exception:
                # 3) fallback: интерпретируем как "сырые байты" через latin1
                try:
                    data = s.encode("latin1")
                    log.warning("auth_key decoded via latin1 fallback — check storage format")
                except Exception:
                    return None
    else:
        try:
            data = bytes(raw)
        except Exception:
            return None

    # Telethon обычно ожидает 256 байт (2048 бит), допустимы и 192 на старых ключах
    if len(data) not in (256, 192):
        log.error("Invalid auth_key length: %s bytes", len(data))
        return None
    return data


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

            # Корректно декодируем ключ и не принимаем пустышки
            auth = _decode_auth_key(auth_key)
            if auth:
                self._auth_key = AuthKey(data=auth)
            else:
                self._auth_key = None

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
            # Telethon использует naive UTC
            if date is None:
                continue
            if getattr(date, "tzinfo", None) is None:
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

        # Не сохраняем "пустой" ключ — пишем NULL в Nullable(String)
        auth_bytes: Optional[bytes] = None
        if getattr(self, "_auth_key", None) and getattr(self._auth_key, "key", None):
            auth_bytes = self._auth_key.key  # bytes

        # --- session info: всегда INSERT (ReplacingMergeTree «заменит» по updated_at)
        client.insert(
            self._SESSION_TABLE,
            [[
                self._name,
                self._dc_id,
                self._server_address or "",
                self._port or 0,
                (auth_bytes if auth_bytes is not None else None),
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
                    md5_digest,           # ожидаем RAW 16 байт (FixedString(16) или String)
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
