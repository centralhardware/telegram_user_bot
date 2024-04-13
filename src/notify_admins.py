import logging
from src.admin_utils import get_admins

def _get_notify_count(raw_text):
    if raw_text == "!n":
        return 1
    else:
        return int(raw_text.replace("!n", ""))


def _get_admin_message(admins_list, notify_count):
    admins = admins_list[:notify_count]
    return ", ".join(admins)


async def notify_admins(event):
    notify_count = _get_notify_count(event.raw_text)
    admins_list, _ = await get_admins(event.chat, event.client)

    if admins_list:
        logging.info(f"Notify {notify_count} admins in {event.chat.title} ({admins_list})")
        await event.client.delete_messages(event.chat, message_ids=[event.message.id])
        msg = _get_admin_message(admins_list, notify_count)

        if event.message.reply_to_msg_id:
            await event.client.send_message(event.chat, msg, reply_to=event.message.reply_to_msg_id)
        else:
            await event.client.send_message(event.chat, msg)
