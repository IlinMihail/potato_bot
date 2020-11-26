import json
import asyncio

from datetime import datetime, timedelta

import aiosqlite

from discord.ext import commands

from potato_bot.constants import SERVER_HOME


async def init_sqlite():
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

    return conn


async def watch_bans(bot):
    print("Starting watching bans file")

    bans_file = SERVER_HOME / "admin" / "banlist.json"
    last_modified = None

    while True:
        await asyncio.sleep(60)

        if (mtime := bans_file.stat().st_mtime) == last_modified:
            continue

        last_modified = mtime

        print(f"bans file update detected at {mtime}")

        with open(bans_file) as f:
            bans = json.loads(f.read())["banEntries"]

        skipped = 0
        new_bans = []
        for ban in bans:
            # these 2 seem enough to identify bans
            user_id = ban["userId"]
            date = ban["dateTimeOfBan"]

            minutes = int(ban["minutes"])

            # https://discord.com/channels/273774715741667329/312454684021620736/781461129427681310
            parsed_date = datetime.strptime(
                date.replace(" ", ""), "%Y-%m-%dT%H:%M:%S.%f0%z"
            )

            if parsed_date + timedelta(minutes=minutes) < datetime.now(
                tz=parsed_date.tzinfo
            ):
                skipped += 1

            cursor = await bot.bans_conn.execute(
                "SELECT EXISTS(SELECT * FROM bans WHERE userId=? AND dateTimeOfBan=?)",
                (user_id, date),
            )

            exists = (await cursor.fetchone())[0]

            if not exists:
                new_bans.append(ban)

        if skipped:
            print(f"skipped {skipped}/{len(bans)} bans")

        if new_bans:
            print(f"Found {len(new_bans)} new ban(s), writing to db")
            await bot.bans_conn.executemany(
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
            await bot.bans_conn.commit()


class Bot(commands.Bot):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

        self.first_on_ready = True

    async def on_ready(self):
        if not self.first_on_ready:
            return

        self.first_on_ready = False

        print(f"Logged in as {self.user}!")

        self.bans_conn = await init_sqlite()

        asyncio.create_task(watch_bans(self))

    async def on_command_error(self, ctx, e):
        ignored = (commands.CommandNotFound,)
        if isinstance(e, ignored):
            return

        if isinstance(e, commands.MissingRole):
            await ctx.send(f"You must have {e.missing_role} role to use this")
        elif isinstance(e, (commands.MissingRequiredArgument, commands.BadArgument)):
            await ctx.send(f"Error: {e}")
        else:
            await ctx.send(f"Unexpected error: {e.__class__.__name__}: {e}")

            raise e
