import discord

from discord.ext import commands

from potato_bot.utils import run_process
from potato_bot.checks import is_admin
from potato_bot.constants import SERVER_HOME


class AdminTools(commands.Cog, name="Admin tools"):
    def __init__(self, bot):
        self.bot = bot

    async def cog_check(self, ctx):
        return await is_admin().predicate(ctx)

    @commands.command(aliases=["bans", "banlist"])
    async def getbans(self, ctx, *, user_name=None):
        """List all bans or get bans for specific user from db"""

        if user_name is None:
            users = await self.bot.bans_db.fetch_all_users()
            if not users:
                return await ctx.send("No bans recorded yet")

            result = "\n".join(
                f"{i + 1:>2}. {user.name}: {user.ban_count} bans, {user.duration} minutes"
                for i, user in enumerate(users)
            )

            title = f"Bans: {sum(u.ban_count for u in users)}\nDuration: {sum(u.duration for u in users)}"
            return await ctx.send(f"{title}```{result}```")

        bans = await self.bot.bans_db.fetch_user_bans(user_name)
        if not bans:
            return await ctx.send("No bans recorded for user")

        total_duration = sum(ban.minutes for ban in bans)
        result = "\n".join(
            f"{i + 1:>2}{'.' if ban.expired else '!'} {ban.admin_name}: {ban.title}"
            for i, ban in enumerate(bans)
        )

        await ctx.send(
            f"User has {len(bans)} ban(s) for {total_duration} minutes in total```{result}```"
        )

    @commands.command()
    async def searchahelp(self, ctx, *, text):
        """Grep chat logs"""

        output = await run_process("grep", "-lr", text, SERVER_HOME / "chatlogs")
        files = output[0].split("\n")
        files.remove("")

        if not files:
            return await ctx.send("Nothing found")

        if len(files) > 4:
            return await ctx.send("more than 4 files matched that pattern")

        for (i, filename) in enumerate(files):
            await ctx.send(i + 1, file=discord.File(filename, filename="logs.txt"))
