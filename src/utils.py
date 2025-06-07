"""Common utility functions used across modules."""

from typing import Any


def remove_empty_and_none(obj: Any):
    """Recursively remove ``None`` values and empty containers from ``obj``.

    Dictionaries and lists are traversed and cleaned from ``None`` values or
    empty dictionaries/lists.
    """
    if isinstance(obj, dict):
        cleaned = {
            k: remove_empty_and_none(v)
            for k, v in obj.items()
            if v is not None
        }
        return {k: v for k, v in cleaned.items() if v not in (None, {}, [])}
    if isinstance(obj, list):
        cleaned = [remove_empty_and_none(v) for v in obj if v is not None]
        return [v for v in cleaned if v not in (None, {}, [])]
    return obj

__all__ = ["remove_empty_and_none"]
