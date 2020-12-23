from discord.ext import commands

from potato_bot.db import BansDB


class Bot(commands.Bot):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

        self._first_on_ready = True

        self.bans_db = BansDB()

    async def on_ready(self):
        if not self._first_on_ready:
            return

        self._first_on_ready = False

        print(f"Logged in as {self.user}!")
        print(f"Prefix: {self.command_prefix}")

        await self.bans_db.connect()
        await self.bans_db.watch()

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
