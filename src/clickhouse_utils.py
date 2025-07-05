import clickhouse_connect

from config import config

_clickhouse_client = None


def get_clickhouse_client():
    global _clickhouse_client
    if _clickhouse_client is None:
        _clickhouse_client = clickhouse_connect.get_client(
            host=config.db_host,
            database=config.db_database,
            port=8123,
            username=config.db_user,
            password=config.db_password,
            settings={"async_insert": "1", "wait_for_async_insert": "0", "async_insert_flush_interval_milliseconds": "10000"},
        )
    return _clickhouse_client
