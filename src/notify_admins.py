import logging
from admin_utils import get_admins


def _get_notify_count(raw_text):
    if raw_text == "!n":
        return 1
    else:
        return int(raw_text.replace("!n", ""))


async def notify_admins(event):
    notify_count = _get_notify_count(event.raw_text)
    admins_list = await get_admins(event.chat, event.client, notify_count)

    if admins_list:
        logging.info(f"Notify {notify_count} admins in {event.chat.title} ({admins_list})")
        await event.client.delete_messages(event.chat, message_ids=[event.message.id])
        msg = ", ".join(admins_list)

        if event.message.reply_to_msg_id:
            await event.client.send_message(event.chat, msg, reply_to=event.message.reply_to_msg_id)
        else:
            await event.client.send_message(event.chat, msg)
