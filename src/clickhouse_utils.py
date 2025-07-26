import contextvars
import clickhouse_connect

from config import config


# Store a client instance per async context to avoid concurrent queries within
# the same session. Each task will lazily create its own client on demand.
_client_var: contextvars.ContextVar = contextvars.ContextVar(
    "clickhouse_client",
    default=None,
)


def get_clickhouse_client():
    client = _client_var.get()
    if client is None:
        client = clickhouse_connect.get_client(
            host=config.db_host,
            database=config.db_database,
            port=8123,
            username=config.db_user,
            password=config.db_password,
            settings={"async_insert": "1", "wait_for_async_insert": "0"},
        )
        _client_var.set(client)
    return client
