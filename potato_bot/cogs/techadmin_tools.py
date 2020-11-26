from discord.ext import commands

from potato_bot.utils import run_process
from potato_bot.checks import is_techadmin


class TechAdminTools(commands.Cog, name="TechAdmin tools"):
    async def cog_check(self, ctx):
        return await is_techadmin().predicate(ctx)

    @commands.command(aliases=["r"])
    async def restart(self, ctx):
        await ctx.send("restarting server")
        await run_process("sudo", "supervisorctl", "restart", "serpot")

    @commands.command()
    async def stop(self, ctx):
        await ctx.send("stopping server")
        await run_process("sudo", "supervisorctl", "stop", "serpot")

    @commands.command()
    async def start(self, ctx):
        await ctx.send("starting server")
        await run_process("sudo", "supervisorctl", "start", "serpot")
