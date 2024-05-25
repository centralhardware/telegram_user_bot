import logging
from admin_utils import get_admins


def _get_notify_count(raw_text):
    if raw_text == "!n":
        return 1
    else:
        return int(raw_text.replace("!n", ""))


def _get_admin_message(admins_list):
    admins = admins_list
    return ", ".join(admins)


async def notify_admins(event):
    admins_list = await get_admins(event.chat, event.client, _get_notify_count(event.raw_text))

    if admins_list:
        logging.info(f"Notify {_get_notify_count(event.raw_text)} admins in {event.chat.title} ({admins_list})")
        await event.client.delete_messages(event.chat, message_ids=[event.message.id])
        msg = _get_admin_message(admins_list)

        if event.message.reply_to_msg_id:
            await event.client.send_message(event.chat, msg, reply_to=event.message.reply_to_msg_id)
        else:
            await event.client.send_message(event.chat, msg)
