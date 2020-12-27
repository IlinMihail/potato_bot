import json
import asyncio
import traceback

from datetime import datetime, timedelta

from discord.ext import commands

from potato_bot.utils import minutes_to_human_readable
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
        self.minutes = int(minutes)
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
            minutes=data["minutes"],
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


class UserEntry:
    def __init__(self, id, name, duration, ban_count):
        self.id = id
        self.name = name
        self.duration = int(duration)
        self.ban_count = ban_count


class Bans(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.db = bot.db

        self.source_file = SERVER_HOME / "admin" / "banlist.json"
        self.source_file_last_modified = None

    async def async_init(self):
        await self.db.ready.wait()

        asyncio.create_task(self._watch_task())

    @commands.command()
    async def bans(self, ctx, *, user_name=None):
        """List all bans or get bans for specific user from db"""

        if user_name is None:
            users = await self.fetch_all_users()
            if not users:
                return await ctx.send("No bans recorded yet")

            users = sorted(users, key=lambda u: u.name.lower())

            total_duration = minutes_to_human_readable(sum(u.duration for u in users))
            await ctx.send(
                f"Bans: **{sum(u.ban_count for u in users)}**\nDuration: **{total_duration}**"
            )
            paginator = commands.Paginator(
                prefix="```",
                suffix="```",
            )
            for i, user in enumerate(users):
                paginator.add_line(
                    f"{i + 1:>2}. {user.name}: {user.ban_count} bans, {minutes_to_human_readable(user.duration)}"
                )

            for page in paginator.pages:
                await ctx.send(page)

            return

        bans = await self.fetch_user_bans(user_name)
        if not bans:
            return await ctx.send("No bans recorded for user")

        total_duration = minutes_to_human_readable(sum(ban.minutes for ban in bans))
        result = "\n".join(
            f"{i + 1:>2}{'.' if ban.expired else '!'} {ban.admin_name}: {ban.title}"
            for i, ban in enumerate(bans)
        )

        await ctx.send(
            f"User has **{len(bans)}** ban(s) for **{total_duration}** in total```{result}```"
        )

    @property
    def source_file_modified(self):
        if (
            mtime := self.source_file.stat().st_mtime
        ) == self.source_file_last_modified:
            return False

        self.source_file_last_modified = mtime

        return True

    async def fetch_ban(self, user_id, date):
        cursor = await self.db.conn.execute(
            "SELECT * FROM bans WHERE userId=? AND dateTimeOfBan=?",
            (user_id, date),
        )

        fetched = await cursor.fetchone()
        if fetched is None:
            return None

        return BanEntry(*fetched)

    async def fetch_user_bans(self, user_name):
        cursor = await self.db.conn.execute(
            "SELECT * FROM bans WHERE userName=? COLLATE NOCASE",
            (user_name,),
        )
        return [BanEntry(*row) for row in await cursor.fetchall()]

    async def fetch_all_users(self):
        # TODO: sort by date of latest ban instead
        cursor = await self.db.conn.execute(
            """
            SELECT
                userId,
                userName,
                SUM(minutes),
                COUNT(userName)
            FROM
                bans
            GROUP BY
                userId
            """,
        )
        return [UserEntry(*row) for row in await cursor.fetchall()]

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
        await self.db.conn.executemany(
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
        await self.db.conn.commit()

    async def _watch_task(self):
        print(f"Started watching {self.source_file}")

        while True:
            await asyncio.sleep(60)
            try:
                await self._inner_watch_task()
            except Exception:
                traceback.print_exc()


def setup(bot):
    bot.add_cog(Bans(bot))
