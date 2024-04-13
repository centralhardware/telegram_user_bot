import os


class Config:
    def __init__(self):
        self.api_id = int(os.getenv('API_ID'))
        self.api_hash = os.getenv('API_HASH')
        self.telephone = os.getenv('TELEPHONE')
        self.telephone2 = os.getenv('TELEPHONE2')
        self.db_user = os.getenv("DB_USER")
        self.db_password = os.getenv("DB_PASSWORD")
        self.db_host = os.getenv("DB_HOST")
        self.db_database = os.getenv("DB_DATABASE")
        self.redis_host = os.getenv("REDIS_HOST")
        self.redis_port = os.getenv('REDIS_PORT')