from typing import Any


def remove_empty_and_none(obj: Any):
    if isinstance(obj, dict):
        cleaned = {k: remove_empty_and_none(v) for k, v in obj.items() if v is not None}
        return {k: v for k, v in cleaned.items() if v not in (None, {}, [])}
    if isinstance(obj, list):
        cleaned = [remove_empty_and_none(v) for v in obj if v is not None]
        return [v for v in cleaned if v not in (None, {}, [])]
    return obj


COLOR_MAP = {
    "incoming": "\033[92m",  # green
    "outgoing": "\033[95m",  # magenta for better readability
    "deleted": "\033[91m",   # red
    "edited": "\033[93m",    # yellow
    "reactions": "\033[94m",  # blue
}


def colorize(message_type: str, text: str) -> str:
    color = COLOR_MAP.get(message_type, "")
    reset = "\033[0m" if color else ""
    return f"{color}{text}{reset}"


__all__ = ["remove_empty_and_none", "colorize"]
