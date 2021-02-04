from __future__ import annotations

import logging

from typing import Any
from pathlib import Path

import aiosqlite

log = logging.getLogger(__name__)


class DB:
    def __init__(self, acquire_timeout=30):
        self._acquire_timeout = acquire_timeout

        self._conn = None

        self._db_path = Path("db.sqlite")

    async def connect(self):
        conn = await aiosqlite.connect(self._db_path)
        conn.row_factory = aiosqlite.Row

        self._conn = conn

        await self.migrate()

    async def migrate(self):
        migrations = [
            (f, int(f.stem)) for f in Path("migrations").iterdir() if f.is_file()
        ]  # tuples of path, version number

        db_version = (await self._conn.execute_fetchall("PRAGMA user_version"))[0][0]

        migrations = list(filter(lambda i: i[1] > db_version, migrations))
        if not migrations:
            log.debug("No pending migrations")

            return

        # sort by version number avoiding FS nonsense
        migrations.sort(key=lambda i: i[1])

        log.info(f"Pending migrations: {' -> '.join(str(i[1]) for i in migrations)}")

        for path, version in migrations:
            log.info(f"Running migration {version}")

            with open(path) as f:
                script = (
                    f"BEGIN;\n"
                    f"-- MIGRATION --\n"
                    f"{f.read()}\n"
                    f"-- MIGRATION --\n"
                    f"PRAGMA user_version = {version};\n"
                    f"COMMIT;"
                )

            await self._conn.executescript(script)

    async def close(self):
        if self._conn is not None:
            await self._conn.close()

    async def commit(self):
        await self._conn.commit()

    def cursor(self, *, commit: bool = False) -> _CursorContext:
        return _CursorContext(self, commit)

    def conn(self, *, commit: bool = False) -> _ConnContext:
        return _ConnContext(self, commit)


class _DBContext:
    def __init__(self, db: DB, commit: bool):
        self.db = db
        self.commit = commit

    async def __aenter__(self) -> Any:
        return await self.enter()

    async def __aexit__(self, exc_type, exc, tb):
        if exc_type is None and self.commit:
            await self.db.commit()

        await self.exit()

    async def enter(self) -> Any:
        pass

    async def exit(self):
        pass


class _CursorContext(_DBContext):
    async def enter(self) -> aiosqlite.Cursor:
        self.cursor = await self.db._conn.cursor()

        return self.cursor

    async def exit(self):
        await self.cursor.close()


class _ConnContext(_DBContext):
    async def enter(self) -> aiosqlite.Connection:
        return self.db._conn
