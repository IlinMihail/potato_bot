import asyncio

import aiosqlite

from potato_bot.constants import SERVER_HOME


class DB:
    def __init__(self):
        self.ready = asyncio.Event()

    @property
    def conn(self):
        if not self.ready.is_set():
            # the most basic way
            raise Exception("Database is not ready")

        return self._conn

    async def connect(self):
        conn = await aiosqlite.connect(SERVER_HOME / "db.sqlite")
        conn.row_factory = aiosqlite.Row

        self._conn = conn

        await self.migrate()
        self.ready.set()

    async def migrate(self):
        migrations = [
            (f, int(f.stem))
            for f in (SERVER_HOME / "migrations").iterdir()
            if f.is_file()
        ]  # tuples of path, version number

        db_version = (await self._conn.execute_fetchall("PRAGMA user_version"))[0][0]

        migrations = list(filter(lambda i: i[1] > db_version, migrations))
        if not migrations:
            print("No pending migrations")

            return

        # sort by version number avoiding FS nonsense
        migrations.sort(key=lambda i: i[1])

        print(f"Pending migrations: {' -> '.join(str(i[1]) for i in migrations)}")

        for path, version in migrations:
            print(f"Running migration {version}")

            with open(path) as f:
                script = f"{f.read()}\n\nPRAGMA user_version = {version};"

            await self._conn.executescript(script)
            await self._conn.commit()

    async def close(self):
        self.ready.clear()
        await self._conn.close()
