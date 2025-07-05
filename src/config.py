import os


class Config:
    def __init__(self):
        self.api_id = int(os.getenv("API_ID"))
        self.api_hash = os.getenv("API_HASH")
        self.telephone = os.getenv("TELEPHONE")
        # Optional second telephone number for an additional account that uses
        # the same API credentials as the primary account.
        self.telephone_second = os.getenv("TELEPHONE_SECOND")
        self.db_user = os.getenv("CLICKHOUSE_USER")
        self.db_password = os.getenv("CLICKHOUSE_PASSWORD")
        self.db_host = os.getenv("CLICKHOUSE_HOST")
        self.db_database = os.getenv("CLICKHOUSE_DATABASE")
        self.chat_ids = os.getenv("TELEGRAM_CHAT_IDS").split(",")


config = Config()
