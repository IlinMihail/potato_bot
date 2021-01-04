from discord.ext import commands

from potato_bot.bot import Bot


class Cog(commands.Cog):
    def __init__(self, bot: Bot):
        self.bot = bot

        self.bot.loop.create_task(self._setup())

    async def _setup(self):
        await self.bot.wait_until_ready()

        await self.setup()

    async def setup(self):
        pass
