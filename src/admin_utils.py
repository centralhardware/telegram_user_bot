from telethon.tl.types import ChatParticipantCreator


def build_username(user):
    if user.username is not None:
        return "@" + user.username
    else:
        return "@" + user.usernames[0].username


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
