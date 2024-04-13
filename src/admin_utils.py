from telethon.tl.types import ChatParticipantCreator


def build_username(user):
    if user.username is not None:
        return "@" + user.username
    else:
        return "@" + user.usernames[0].username


# The function retrieves administrators from a chat
async def get_admins(chat, client):
    admins = []
    count = 0
    async for user in client.iter_participants(chat):
        try:
            count += 1
            if user.bot:
                continue
            if isinstance(user.participant, ChatParticipantCreator) or user.participant.admin_rights.delete_messages:
                admins.append(build_username(user))
        except AttributeError as e:
            print(f'AttributeError occurred: {str(e)}')
        except TypeError as e:
            print(f'TypeError occurred: {str(e)}')
    return [admins, count]
