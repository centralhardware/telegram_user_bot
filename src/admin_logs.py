import json
import logging
from dataclasses import dataclass
from difflib import unified_diff
from typing import Any, Dict, Iterable, List, Tuple

from telethon.tl.functions.channels import GetAdminLogRequest

from username_utils import extract_usernames
from clickhouse_utils import get_clickhouse_client
from utils import remove_empty_and_none


@dataclass
class AdminLogRecord:
    """Container for a single admin log event."""

    event_id: int
    chat_id: int
    action_type: str
    user_id: int
    date: Any
    message: str
    usernames: List[str]
    chat_usernames: List[str]
    chat_title: str
    user_title: str


def format_log_output(action_type: str, action: Any, default_message: str) -> str:
    """Return a human friendly log message for an admin action."""
    if action_type == "EditMessage":
        prev = getattr(action, "prev_message", None)
        new = getattr(action, "new_message", None)
        prev_text = getattr(prev, "message", "") if prev else ""
        new_text = getattr(new, "message", "") if new else ""
        diff = "\n".join(
            unified_diff(
                prev_text.splitlines(),
                new_text.splitlines(),
                fromfile="prev",
                tofile="new",
                lineterm="",
            )
        )
        if not diff:
            diff = json.dumps({"prev": prev_text, "new": new_text}, ensure_ascii=False)
        return diff
    elif action_type == "DeleteMessage":
        msg = getattr(action, "message", None)
        if msg is not None:
            deleted_text = getattr(msg, "message", None)
            if deleted_text:
                return deleted_text
            try:
                return json.dumps(
                    remove_empty_and_none(msg.to_dict()),
                    default=str,
                    ensure_ascii=False,
                )
            except Exception:
                pass
    elif action_type in ("ParticipantJoin", "ParticipantLeave"):
        return ""
    return default_message


def get_last_id_from_clickhouse(chat_id: int) -> int:
    """Return the last processed event_id for the given chat."""
    clickhouse = get_clickhouse_client()
    result = clickhouse.query(
        """
        SELECT max(event_id) AS last_id
        FROM telegram_user_bot.admin_actions2
        WHERE chat_id = %(chat_id)s
    """,
        parameters={"chat_id": chat_id},
    ).result_rows
    return result[0][0] if result and result[0][0] is not None else 0


def build_event_maps(events: Any) -> Tuple[Dict[int, List[str]], Dict[int, str], Dict[int, List[str]]]:
    """Build helper maps for usernames and titles from admin log events."""
    usernames_map: Dict[int, List[str]] = {}
    title_map: Dict[int, str] = {}

    for user in events.users:
        title_map[user.id] = f"{user.first_name or ''} {user.last_name or ''}".strip()
        usernames_map[user.id] = extract_usernames(user)

    chat_map = {chat.id: extract_usernames(chat) for chat in events.chats}
    return usernames_map, title_map, chat_map


async def fetch_channel_actions(client, chat_id: int) -> None:
    """Fetch and store channel admin log events since the last processed ID."""
    last_id = get_last_id_from_clickhouse(chat_id)
    channel = await client.get_entity(chat_id)
    chat_usernames = extract_usernames(channel)
    max_id = last_id
    new_last_id = last_id
    all_data: List[List[Any]] = []

    while True:
        events = await client(
            GetAdminLogRequest(
                channel=channel, q="", min_id=max_id + 1, max_id=0, limit=100
            )
        )

        if not events.events:
            break

        usernames_map, title_map, chat_map = build_event_maps(events)

        for entry in events.events:
            eid = entry.id
            user_id = getattr(entry.user_id, "user_id", entry.user_id)
            action_type = type(entry.action).__name__.removeprefix(
                "ChannelAdminLogEventAction"
            )
            message = json.dumps(
                remove_empty_and_none(entry.action.to_dict()),
                default=str,
                ensure_ascii=False,
            )

            record = AdminLogRecord(
                event_id=eid,
                chat_id=chat_id,
                action_type=action_type,
                user_id=user_id or 0,
                date=entry.date,
                message=message,
                usernames=usernames_map.get(user_id) or chat_map.get(user_id, []),
                chat_usernames=chat_usernames,
                chat_title=channel.title,
                user_title=title_map.get(user_id, ""),
            )
            all_data.append(
                [
                    record.event_id,
                    record.chat_id,
                    record.action_type,
                    record.user_id,
                    record.date,
                    record.message,
                    record.usernames,
                    record.chat_usernames,
                    record.chat_title,
                    record.user_title,
                ]
            )

            log_text = format_log_output(record.action_type, entry.action, record.message)
            logging.info(
                "admin    %12d %-25s %-20s %-20s %s",
                record.event_id,
                channel.title[:25],
                record.action_type,
                record.user_title[:20],
                log_text,
            )

            if eid > new_last_id:
                new_last_id = eid

        if len(events.events) < 100:
            break
        else:
            max_id = max(e.id for e in events.events)

    if all_data:
        clickhouse = get_clickhouse_client()
        clickhouse.insert(
            "telegram_user_bot.admin_actions2",
            all_data,
            [
                "event_id",
                "chat_id",
                "action_type",
                "user_id",
                "date",
                "message",
                "usernames",
                "chat_usernames",
                "chat_title",
                "user_title",
            ],
        )
        logging.info(
            "[%s] Inserted %d entries. Last ID: %d",
            channel.title,
            len(all_data),
            new_last_id,
        )
