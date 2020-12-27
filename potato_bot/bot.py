import aiohttp
import discord

from discord.ext import commands

from potato_bot.db import DB

initial_extensions = (
    "potato_bot.cogs.admin_tools",
    "potato_bot.cogs.bans",
    "potato_bot.cogs.misc",
    "potato_bot.cogs.techadmin_tools",
)


class Bot(commands.Bot):
    def __init__(self, **kwargs):
        super().__init__(
            allowed_mentions=discord.AllowedMentions(
                roles=False, everyone=False, users=True
            ),
            **kwargs,
        )

        self._first_on_ready = True

        self.db = DB()
        self.session = aiohttp.ClientSession()

        for extension in initial_extensions:
            self.load_extension(extension)

    async def on_ready(self):
        if not self._first_on_ready:
            return

        self._first_on_ready = False

        print(f"Logged in as {self.user}!")
        print(f"Prefix: {self.command_prefix}")

        await self.db.connect()

        for cog in self.cogs.values():
            if hasattr(cog, "async_init"):
                await cog.async_init()

    async def on_command_error(self, ctx, e):
        ignored = (commands.CommandNotFound,)
        if isinstance(e, ignored):
            return

        if isinstance(e, commands.MissingRole):
            await ctx.send(f"You must have {e.missing_role} role to use this")
        elif isinstance(e, (commands.MissingRequiredArgument, commands.BadArgument)):
            await ctx.send(f"Error: {e}")
        else:
            if isinstance(e, commands.CommandInvokeError):
                e = e.original

            await ctx.send(f"Unexpected error: **{e.__class__.__name__}**: `{e}`")

            raise e

    async def close(self):
        await super().close()

        await self.session.close()
        await self.db.close()
