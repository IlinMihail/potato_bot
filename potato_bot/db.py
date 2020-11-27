import json
import asyncio
import traceback

from datetime import datetime, timedelta

import aiosqlite

from potato_bot.constants import SERVER_HOME


class BanEntry:
    def __init__(
        self,
        user_id,
        user_name,
        minutes,
        date,
        reason,
        ip,
        client_id,
        admin_id,
        admin_name,
    ):
        self.user_id = user_id
        self.user_name = user_name
        self.minutes = minutes
        self.date = date
        self.reason = reason
        self.ip = ip
        self.client_id = client_id
        self.admin_id = admin_id
        self.admin_name = admin_name

    @classmethod
    def from_file(cls, data):
        return cls(
            user_id=data["userId"],
            user_name=data["userName"],
            minutes=int(data["minutes"]),
            date=data["dateTimeOfBan"],
            reason=data["reason"],
            ip=data["ipAddress"],
            client_id=data["clientId"],
            admin_id=data["adminId"],
            admin_name=data["adminName"],
        )

    def to_dict(self):
        return {
            "userId": self.user_id,
            "userName": self.user_name,
            "minutes": self.minutes,
            "dateTimeOfBan": self.date,
            "reason": self.reason,
            "ipAddress": self.ip,
            "clientId": self.client_id,
            "adminId": self.admin_id,
            "adminName": self.admin_name,
        }

    @property
    def title(self):
        return self.reason.split("\n")[0]

    @property
    def expired(self):
        date = self.date

        minutes = self.minutes

        # https://discord.com/channels/273774715741667329/312454684021620736/781461129427681310
        parsed_date = datetime.strptime(
            date.replace(" ", ""), "%Y-%m-%dT%H:%M:%S.%f0%z"
        )

        return parsed_date + timedelta(minutes=minutes) < datetime.now(
            tz=parsed_date.tzinfo
        )


class BansDB:
    def __init__(self):
        self.source_file = SERVER_HOME / "admin" / "banlist.json"
        self.source_file_last_modified = None

    async def connect(self):
        conn = await aiosqlite.connect(SERVER_HOME / "bans.db")

        await conn.execute(
            """
            CREATE TABLE IF NOT EXISTS bans
            (
                userId         text,
                userName       text,
                minutes        real,
                dateTimeOfBan  text,
                reason         text,
                ipAddress      text,
                clientId       text,
                adminId        text,
                adminName      text
            )
            """
        )
        await conn.execute(
            """
            CREATE INDEX IF NOT EXISTS bans_by_userId_and_dateTimeOfBan
            ON bans(userId, dateTimeOfBan)
            """
        )

        await conn.commit()

        print("initialized bans db")

        self.conn = conn

    @property
    def source_file_modified(self):
        if (
            mtime := self.source_file.stat().st_mtime
        ) == self.source_file_last_modified:
            return False

        self.source_file_last_modified = mtime

        return True

    async def fetch_ban(self, user_id, date):
        cursor = await self.conn.execute(
            "SELECT * FROM bans WHERE userId=? AND dateTimeOfBan=?",
            (user_id, date),
        )

        fetched = await cursor.fetchone()
        if fetched is None:
            return None

        return BanEntry(*fetched)

    async def fetch_user_bans(self, user_name):
        cursor = await self.conn.execute(
            "SELECT * FROM bans WHERE userName=?",
            (user_name,),
        )
        return [BanEntry(*row) for row in await cursor.fetchall()]

    async def watch(self):
        asyncio.create_task(self._watch_task())

    async def _inner_watch_task(self):
        if not self.source_file_modified:
            return

        print(f"{self.source_file} update detected at {self.source_file_last_modified}")

        with open(self.source_file) as f:
            bans = json.loads(f.read())["banEntries"]

        skipped = 0
        new_bans = []
        for obj in bans:
            ban = BanEntry.from_file(obj)

            if ban.expired:
                skipped += 1

            if await self.fetch_ban(ban.user_id, ban.date) is None:
                new_bans.append(ban.to_dict())

        if skipped:
            print(f"skipped {skipped}/{len(bans)} bans")

        if not new_bans:
            return

        print(f"Found {len(new_bans)} new ban(s), writing to db")
        await self.conn.executemany(
            """
            INSERT INTO bans (
                userId,
                userName,
                minutes,
                dateTimeOfBan,
                reason,
                ipAddress,
                clientId,
                adminId,
                adminName
            ) VALUES (
                :userId,
                :userName,
                :minutes,
                :dateTimeOfBan,
                :reason,
                :ipAddress,
                :clientId,
                :adminId,
                :adminName
            )
            """,
            new_bans,
        )
        await self.conn.commit()

    async def _watch_task(self):
        print(f"Started watching {self.source_file}")

        while True:
            await asyncio.sleep(5)
            try:
                await self._inner_watch_task()
            except Exception:
                traceback.print_exc()
