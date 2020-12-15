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
    async def exec(self, ctx, command: str, *arguments: str):
        stdout, stderr = await run_process(command, *arguments)

        result = ""
        if stderr:
            result += f"STDERR:\n{stderr}"
        if stdout:
            result += stdout

        await ctx.send(f"```bash\n{result[-2001 + 11:]}```")
