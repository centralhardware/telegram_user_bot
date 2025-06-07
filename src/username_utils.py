"""Utility helpers for working with usernames."""

from typing import List


def extract_usernames(entity) -> List[str]:
    """Return list of usernames from a Telethon entity."""
    usernames: List[str] = []
    if hasattr(entity, "username") and entity.username:
        usernames.append(entity.username)
    if hasattr(entity, "usernames") and entity.usernames is not None:
        for username in entity.usernames:
            if isinstance(username, str):
                usernames.append(username)
            elif hasattr(username, "username") and username.username:
                usernames.append(username.username)
    return usernames
