from discord.ext import commands

from potato_bot.bot import Bot


class Democracy(commands.Cog):
    def __init__(self, bot: Bot):
        self.bot = bot

    @commands.command()
    async def peng(self, ctx):
        await ctx.send("pong!")


def setup(bot):
    bot.add_cog(Democracy(bot))
