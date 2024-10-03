import os


class Config:
    def __init__(self):
        self.api_id = int(os.getenv('API_ID'))
        self.api_hash = os.getenv('API_HASH')
        self.telephone = os.getenv('TELEPHONE')
        self.telephone2 = os.getenv('TELEPHONE2')
        self.db_user = os.getenv("CLICKHOUSE_USER")
        self.db_password = os.getenv("CLICKHOUSE_PASSWORD")
        self.db_host = os.getenv("CLICKHOUSE_HOST")
        self.db_database = os.getenv("CLICKHOUSE_DATABASE")


config = Config()
