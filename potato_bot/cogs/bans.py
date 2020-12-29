import json
import asyncio
import traceback

from typing import Sequence
from datetime import datetime, timedelta

import aiosqlite

from discord.ext import commands

from potato_bot.bot import Bot
from potato_bot.utils import minutes_to_human_readable
from potato_bot.checks import is_admin
from potato_bot.constants import SERVER_HOME


# TODO: remove these
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
    """Ban related commands"""

    def __init__(self, bot: Bot):
        self.bot = bot

        self.bans_file = SERVER_HOME / "admin" / "banlist.json"
        self.job_bans_file = SERVER_HOME / "admin" / "jobBanlist.json"

        self._start_tasks()

    def _start_tasks(self):
        self.bot.loop.create_task(
            self._watch_task(self.bans_file, self._bans_file_modified)
        )
        self.bot.loop.create_task(
            self._watch_task(self.job_bans_file, self._job_bans_file_modified)
        )

    @commands.group(invoke_without_command=True, ignore_extra=False)
    async def bans(self, ctx):
        """List bans"""

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

    def _ban_expired(self, date: str, minutes: int):
        # https://discord.com/channels/273774715741667329/312454684021620736/781461129427681310
        parsed_date = datetime.strptime(
            date.replace(" ", ""), "%Y-%m-%dT%H:%M:%S.%f0%z"
        )

        return parsed_date + timedelta(minutes=minutes) < datetime.now(
            tz=parsed_date.tzinfo
        )

    def _bans_to_paginator(self, bans: Sequence[aiosqlite.Row]) -> commands.Paginator:
        user_id = bans[0]["userId"]
        total_duration = minutes_to_human_readable(
            int(sum(ban["minutes"] for ban in bans))
        )

        paginator = commands.Paginator(
            prefix=f"`{user_id}` has **{len(bans)}** ban(s) for **{total_duration}** in total```"
        )

        longest_index = len(str(len(bans)))

        for i, ban in enumerate(bans):
            title = ban["reason"].split("\n")[0]
            ban_expired = self._ban_expired(ban["dateTimeOfBan"], ban["minutes"])

            paginator.add_line(
                f"{i + 1:>{longest_index}}{'.' if ban_expired else '!'} {ban['adminName']}: {title}"
            )

        return paginator

    @bans.command(name="name")
    async def _name_bans(self, ctx, user_name: str):
        """Fetch user bans using name"""

        async with ctx.db.cursor() as cur:
            await cur.execute(
                """
                SELECT a.userId
                FROM bans a
                INNER JOIN bans b
                ON
                    a.userName = b.userName AND a.userId != b.userId AND a.userName = ?
                GROUP BY a.userId
                """,
                (user_name,),
            )

            conflicts = await cur.fetchall()

            nl = "\n"
            if conflicts:
                return await ctx.send(
                    f"Conflicting IDs detected for name **{user_name}**: ```{nl.join(c[0] for c in conflicts)}```"
                )

            await cur.execute(
                """
                SELECT
                    userId,
                    userName,
                    dateTimeOfBan,
                    minutes,
                    reason,
                    adminName
                FROM bans
                WHERE userName = ?
                """,
                (user_name,),
            )

            bans = await cur.fetchall()

        if not bans:
            return await ctx.send("No bans recorded for name")

        paginator = self._bans_to_paginator(bans)
        for page in paginator.pages:
            await ctx.send(page)

    @bans.command(name="id")
    async def _id_bans(self, ctx, user_id: str):
        """Fetch user bans using id"""

        async with ctx.db.cursor() as cur:
            await cur.execute(
                """
                SELECT
                    userId,
                    userName,
                    dateTimeOfBan,
                    minutes,
                    reason,
                    adminName
                FROM bans
                WHERE userId = ?
                """,
                (user_id,),
            )

            bans = await cur.fetchall()

        if not bans:
            return await ctx.send("No bans recorded for id")

        paginator = self._bans_to_paginator(bans)
        for page in paginator.pages:
            await ctx.send(page)

    @commands.command(aliases=["ub"])
    @is_admin()
    async def unban(self, ctx, user_id: str):
        """
        Add unban to queue
        Unban is only be done after restarting server
        """

        async with ctx.db.cursor(commit=True) as cur:
            await cur.execute(
                "INSERT INTO unban_queue (user_id) VALUES (?)", (user_id,)
            )

        await ctx.send(f"Added `{user_id}` to unban queue")

    @commands.command(aliases=["ujb"])
    @is_admin()
    async def unjobban(self, ctx, user_id: str, *jobs: int):
        """
        Add job unbans to queue
        Unban is only be done after restarting server
        """
        if not jobs:
            return await ctx.send("No jobs provided")

        # TODO: overwrite file in do_job_unbans
        return await ctx.send("Not yet ready")

        async with ctx.db.cursor(commit=True) as cur:
            await cur.executemany(
                "INSERT INTO job_unban_queue (user_id, job) VALUES (?, ?)",
                [(user_id, job) for job in jobs],
            )

        await ctx.send(
            f"Added `{user_id}` to job unban queue for jobs: **{', '.join(str(i) for i in jobs)}**"
        )

    async def fetch_ban(self, user_id, date):
        async with self.bot.db.cursor() as cur:
            await cur.execute(
                "SELECT * FROM bans WHERE userId=? AND dateTimeOfBan=?",
                (user_id, date),
            )

            fetched = await cur.fetchone()

        if fetched is None:
            return None

        return BanEntry(*fetched)

    async def fetch_all_users(self):
        # TODO: sort by date of latest ban instead
        async with self.bot.db.cursor() as cur:
            await cur.execute(
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
            return [UserEntry(*row) for row in await cur.fetchall()]

    async def _bans_file_modified(self):
        with open(self.bans_file) as f:
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
        async with self.bot.db.cursor(commit=True) as cur:
            await cur.executemany(
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

    async def _job_bans_file_modified(self):
        pass

    async def _watch_task(self, path, callback):
        print(f"Started watching {path}")

        last_modified = None

        while True:
            await asyncio.sleep(60)

            try:
                if (mtime := path.stat().st_mtime) == last_modified:
                    continue

                last_modified = mtime

                print(f"{path} update detected at {last_modified}")

                await callback()
            except Exception:
                traceback.print_exc()

    async def do_unbans(self):
        async with self.bot.db.cursor(commit=True) as cur:
            await cur.execute("SELECT user_id FROM unban_queue")
            user_ids = set(i[0] for i in await cur.fetchall())

            if not user_ids:
                return []

            with open(self.bans_file) as f:
                data = json.loads(f.read())

            data["banEntries"] = list(
                filter(lambda b: b["userId"] not in user_ids, data["banEntries"])
            )

            # dump early to avoid exceptions and losing file contents
            dumped = json.dumps(data)
            with open(self.bans_file, "w") as f:
                f.write(dumped)

            await cur.execute("DELETE FROM unban_queue")

        return [str(i) for i in user_ids]

    async def do_job_unbans(self):
        async with self.bot.db.cursor(commit=True) as cur:
            await cur.execute(
                "SELECT user_id, job FROM job_unban_queue GROUP BY user_id"
            )

            bans = await cur.fetchall()
            print(bans)

            await cur.execute("DELETE FROM job_unban_queue")


def setup(bot):
    bot.add_cog(Bans(bot))
