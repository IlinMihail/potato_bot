import json
import asyncio
import traceback

from datetime import datetime, timedelta

from discord.ext import commands

from potato_bot.utils import minutes_to_human_readable
from potato_bot.checks import is_admin
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

        self.bans_file = SERVER_HOME / "admin" / "banlist.json"
        self.job_bans_file = SERVER_HOME / "admin" / "jobBanlist.json"

    async def async_init(self):
        await self.db.ready.wait()

        asyncio.create_task(self._watch_task(self.bans_file, self._bans_file_modified))
        asyncio.create_task(
            self._watch_task(self.job_bans_file, self._job_bans_file_modified)
        )

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
        user_id = bans[0].user_id

        result = "\n".join(
            f"{i + 1:>2}{'.' if ban.expired else '!'} {ban.admin_name}: {ban.title}"
            for i, ban in enumerate(bans)
        )

        await ctx.send(
            f"`{user_id}` has **{len(bans)}** ban(s) for **{total_duration}** in total```\n{result}```"
        )

    @commands.command(aliases=["ub"])
    @is_admin()
    async def unban(self, ctx, user_id: str):
        """
        Add unban to queue
        Unban is only be done after restarting server
        """

        await self.bot.db.conn.execute_insert(
            "INSERT INTO unban_queue (user_id) VALUES (?)", (user_id,)
        )
        await self.bot.db.conn.commit()

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

        await self.bot.db.conn.executemany(
            "INSERT INTO job_unban_queue (user_id, job) VALUES (?, ?)",
            [(user_id, job) for job in jobs],
        )
        await self.bot.db.conn.commit()

        await ctx.send(
            f"Added `{user_id}` to job unban queue for jobs: **{', '.join(str(i) for i in jobs)}**"
        )

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
        async with self.bot.db.conn.cursor() as cur:
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

        await self.db.conn.commit()

        return [str(i) for i in user_ids]

    async def do_job_unbans(self):
        async with self.bot.db.conn.cursor() as cur:
            await cur.execute(
                "SELECT user_id, job FROM job_unban_queue GROUP BY user_id"
            )

            bans = await cur.fetchall()

            await cur.execute("DELETE FROM job_unban_queue")

        await self.db.conn.commit()


def setup(bot):
    bot.add_cog(Bans(bot))
