import logging
import threading

from flask import Flask, jsonify
from telethon import events

from config import config
from notify_admins import notify_admins
from scrapper import save_outgoing, save_incoming, save_deleted
from Top import top
from Deleted import deleted
from TelegramUtils import create_telegram_client

app = Flask(__name__)
@app.route("/health")
def health():
    resp = jsonify(health="healthy")
    resp.status_code = 200
    return resp

def run_flask():
    app.run(host='0.0.0.0', port=80)

def run_telegram_clients():
    client = create_telegram_client('session/alex', config.telephone)
    client2 = create_telegram_client('session/alex2', config.telephone2)

    # Добавляем обработчики событий для клиента 1
    client.add_event_handler(save_outgoing, events.NewMessage(outgoing=True))
    client.add_event_handler(save_deleted, events.MessageDeleted())
    client.add_event_handler(save_incoming, events.NewMessage(incoming=True))
    client.add_event_handler(notify_admins, events.NewMessage(outgoing=True, pattern='!n', forwards=False))

    # Добавляем обработчики событий для клиента 2
    client2.add_event_handler(top, events.NewMessage(outgoing=True, pattern='!top', forwards=False, chats=[-1001633660171]))
    client2.add_event_handler(top, events.NewMessage(incoming=True, pattern='!top', forwards=False, chats=[-1001633660171]))
    client2.add_event_handler(deleted, events.NewMessage(outgoing=True, pattern='!deleted', forwards=False, chats=[-1001633660171]))
    client2.add_event_handler(deleted, events.NewMessage(incoming=True, pattern='!deleted', forwards=False, chats=[-1001633660171]))

    # Запускаем клиентов и блокируем поток до их завершения
    client.start()
    client2.start()

    client.run_until_disconnected()
    client2.run_until_disconnected()

if __name__ == '__main__':
    logging.basicConfig(level=logging.INFO, format='%(message)s')
    logging.info('start application')

    # Создаем потоки для Flask и Telegram клиентов
    flask_thread = threading.Thread(target=run_flask)
    telegram_thread = threading.Thread(target=run_telegram_clients)

    # Запускаем потоки
    flask_thread.start()
    telegram_thread.start()

    # Ожидаем завершения потоков
    flask_thread.join()
    telegram_thread.join()