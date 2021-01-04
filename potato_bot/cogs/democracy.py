from discord.ext import commands

from potato_bot.bot import Bot
from potato_bot.cog import Cog


class Democracy(Cog):
    """Automatic democracy tools"""

    def __init__(self, bot: Bot):
        self.bot = bot

    @commands.command()
    async def peng(self, ctx):
        await ctx.send("pong!")


def setup(bot):
    bot.add_cog(Democracy(bot))
