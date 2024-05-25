from telethon.tl.types import ChatParticipantCreator


def build_username(user):
    if user.username is not None:
        return "@" + user.username
    else:
        return "@" + user.usernames[0].username


# The function retrieves administrators from a chat
async def get_admins(chat, client, limit):
    admins = []
    async for user in client.iter_participants(chat):
        try:
            if user.bot:
                continue
            if isinstance(user.participant, ChatParticipantCreator) or user.participant.admin_rights.delete_messages:
                admins.append(build_username(user))
            if len(admins) == limit:
                return admins
        except Exception:
            pass
    return admins


# Add this method after line 23
async def get_participant_count(chat, client):
    return await client.get_participant_count(chat)
