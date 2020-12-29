from __future__ import annotations

import asyncio

from pathlib import Path

import aiosqlite

from potato_bot.constants import SERVER_HOME


class DB:
    def __init__(self, acquire_timeout=30):
        self._acquire_timeout = acquire_timeout

        self._ready = asyncio.Event()

    async def connect(self):
        conn = await aiosqlite.connect(SERVER_HOME / "db.sqlite")
        conn.row_factory = aiosqlite.Row

        self._conn = conn

        await self.migrate()
        self._ready.set()

    async def migrate(self):
        migrations = [
            (f, int(f.stem)) for f in Path("migrations").iterdir() if f.is_file()
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
        self._ready.clear()
        await self._conn.close()

    async def commit(self):
        await self._conn.commit()

    def cursor(self, *, commit: bool = False) -> _WaitCursor:
        return _WaitCursor(self, commit)

    async def conn(self, *, commit: bool = False) -> _WaitConn:
        return _WaitConn(self, commit)


class _WaitContext:
    def __init__(self, db: DB, commit: bool):
        self.db = db
        self.commit = commit

    async def __aenter__(self):
        if not self.db._ready.is_set():
            try:
                await asyncio.wait_for(self.db._ready.wait(), self.db._acquire_timeout)
            except asyncio.TimeoutError:
                raise Exception("Database is not ready")

        return await self.enter()

    async def __aexit__(self, exc_type, exc, tb):
        if self.exc_type is None and self.commit:
            await self.db.commit()

        await self.exit()

    async def enter(self):
        pass

    async def exit(self):
        pass


class _WaitCursor(_WaitContext):
    async def enter(self):
        self.cursor = await self.db._conn.cursor()

        return self.cursor

    async def exit(self):
        await self.cursor.close()


class _WaitConn(_WaitContext):
    async def enter(self):
        return self.db.conn
