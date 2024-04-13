import logging


async def read_acknowledge(event):
    async for dialog in event.client.iter_dialogs():
        logging.info(f"mark {dialog.name} as read")
        await event.client.send_read_acknowledge(dialog, clear_mentions=True, clear_reactions=True)
