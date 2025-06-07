from telethon.tl.types import ChatParticipantCreator

from username_utils import extract_usernames


def build_username(user):
    """Return formatted username for a user."""
    usernames = extract_usernames(user)
    return f"@{usernames[0]}" if usernames else ""


# The function retrieves administrators from a chat
async def get_admins(chat, client, limit=50):
    admins = []
    async for user in client.iter_participants(chat):
        try:
            if user.bot:
                continue
            if isinstance(user.participant, ChatParticipantCreator) or user.participant.admin_rights.delete_messages:
                admins.append(build_username(user))
        except Exception:
            pass
        if len(admins) >= limit:
            return admins
    return admins
