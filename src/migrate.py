from pathlib import Path

from clickhouse_driver import Client
from clickhouse_migrations.migrator import Migrator
from clickhouse_migrations.migration import MigrationStorage

from config import config


def run() -> None:
    client = Client(
        host=config.db_host,
        user=config.db_user,
        password=config.db_password,
        database=config.db_database,
    )
    migrator = Migrator(client)
    migrator.init_schema()
    migrations_dir = Path(__file__).resolve().parent.parent / "migrations"
    storage = MigrationStorage(migrations_dir)
    migrations = storage.migrations()
    migrator.apply_migration(migrations, multi_statement=True)


if __name__ == "__main__":
    run()
