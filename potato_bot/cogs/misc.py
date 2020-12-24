import asyncio

from aiohttp import ClientSession
from discord.ext import commands

from potato_bot.utils import run_process, minutes_to_human_readable
from potato_bot.checks import is_admin


class Misc(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    @commands.command()
    async def serverlist(self, ctx):
        """List hub servers"""

        async with ClientSession() as sess:
            async with sess.get("https://api.unitystation.org/serverlist") as r:
                # they send json with html mime type
                data = await r.json(content_type=None)

        result = "\n".join(
            f"{i['ServerName']}- playercount:{i['PlayerCount']}- Fork is {i['ForkName']}- Build is {i['BuildVersion']}- Fps:{i['fps']}"
            for i in data["servers"]
        )
        await ctx.send(f"```{result}```")

    @commands.command()
    async def fig(self, ctx, *, text):
        """Big ASCII characters"""

        result = await run_process("figlet", "-d", "/home/potato/font", *text.split())
        stdout = result[0].rstrip()[:1994]
        await ctx.send(f"```{stdout}```")

    @commands.command()
    async def mem(self, ctx):
        """Get memory usage (free -h)"""

        result = await run_process("free", "-h")

        await ctx.send(f"mem is ```{result[0]}```")

    @commands.command()
    @is_admin()
    async def memspam(self, ctx):
        """Like mem but updates"""

        initial = await ctx.send("fetching")
        for _ in range(100):
            await asyncio.sleep(1)

            result = await run_process("free", "-h")
            await initial.edit(content=f"mem is ```{result[0]}```")

    @commands.command()
    async def bans(self, ctx, *, user_name=None):
        """List all bans or get bans for specific user from db"""

        if user_name is None:
            users = await self.bot.bans_db.fetch_all_users()
            if not users:
                return await ctx.send("No bans recorded yet")

            users = sorted(users, key=lambda u: u.name.lower())

            total_duration = minutes_to_human_readable(sum(u.duration for u in users))
            result = "\n".join(
                f"{i + 1:>2}. {user.name}: {user.ban_count} bans, {minutes_to_human_readable(user.duration)}"
                for i, user in enumerate(users)
            )

            title = f"Bans: **{sum(u.ban_count for u in users)}**\nDuration: **{total_duration}**"
            return await ctx.send(f"{title}```{result}```")

        bans = await self.bot.bans_db.fetch_user_bans(user_name)
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
