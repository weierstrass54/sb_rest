import asyncio
import asyncpg
import logging
import os
import sys

from api import Api
from yoyo import read_migrations, get_backend


def migrate(db_dsn):
    backend = get_backend(db_dsn)
    migrations = read_migrations('migrations')
    with backend.lock():
        backend.apply_migrations(migrations)


async def main():
    host = os.environ.get('SERVER_HOST', '0.0.0.0')
    port = os.environ.get('SERVER_PORT', 8081)
    db_dsn = os.environ.get('DB_DSN', 'postgres://sb_rest:sb_rest@127.0.0.1:5432/sb_rest')

    logging.basicConfig(stream=sys.stdout, level=logging.INFO)

    migrate(db_dsn)

    transactor = await asyncpg.create_pool(dsn=db_dsn)

    api = Api(host, port, transactor)
    await api.start()


if __name__ == '__main__':
    loop = asyncio.get_event_loop()
    loop.run_until_complete(main())
    loop.run_forever()