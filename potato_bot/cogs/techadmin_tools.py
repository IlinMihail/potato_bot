from discord.ext import commands

from potato_bot.utils import run_process
from potato_bot.checks import is_techadmin


class TechAdminTools(commands.Cog, name="TechAdmin tools"):
    async def cog_check(self, ctx):
        return await is_techadmin().predicate(ctx)

    @commands.command()
    async def eval(self, ctx, program: str):
        await ctx.send("TBD")

    @commands.command()
    async def exec(self, ctx, pipeline: str):
        await ctx.send("TBD")
