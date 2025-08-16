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
    "outgoing": "\033[94m",  # blue
    "deleted": "\033[91m",   # red
    "edited": "\033[93m",    # yellow
}


def colorize(message_type: str, text: str) -> str:
    color = COLOR_MAP.get(message_type, "")
    reset = "\033[0m" if color else ""
    return f"{color}{text}{reset}"


def colorize_diff(diff: str) -> str:
    colored_lines = []
    for line in diff.splitlines():
        if line.startswith("+"):
            colored_lines.append(f"\033[92m{line}\033[0m")
        elif line.startswith("-"):
            colored_lines.append(f"\033[91m{line}\033[0m")
        else:
            colored_lines.append(line)
    return "\n".join(colored_lines)


__all__ = ["remove_empty_and_none", "colorize", "colorize_diff"]
