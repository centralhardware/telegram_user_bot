from telethon import TelegramClient


def create_telegram_client(session_name, phone):
    c = TelegramClient(session_name, config.api_id, config.api_hash)
    c.connect()
    c.start(phone=phone)
    return c
