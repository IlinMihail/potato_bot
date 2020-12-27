import io
import asyncio
import textwrap
import traceback

from contextlib import redirect_stdout

import discord

from discord.ext import commands

from potato_bot.utils import run_process_shell
from potato_bot.checks import is_techadmin


class TechAdminTools(commands.Cog, name="TechAdmin tools"):
    def __init__(self, bot):
        self.bot = bot

    async def cog_check(self, ctx):
        return await is_techadmin().predicate(ctx)

    @commands.command()
    async def eval(self, ctx, *, program: str):
        """
        Evaluate code inside bot, with async support
        Has conveniece shortcuts like
        - ctx
        - discord

        To get result you can either print or return object.
        """

        if program.startswith("```") and program.endswith("```"):
            # strip codeblock
            program = program[:-3]
            program = "\n".join(program.split("\n")[1:])

        result = await self._eval(ctx, program)
        result = result.replace(self.bot.http.token, "TOKEN_LEAKED")

        await ctx.send(f"```python\n{result[-2000 - 1 + 14:]}```")

    async def _eval(self, ctx, program):
        # copied from https://github.com/Fogapod/KiwiBot/blob/49743118661abecaab86388cb94ff8a99f9011a8/modules/owner/module_eval.py
        # (originally copied from R. Danny bot)
        glob = {
            "self": self,
            "bot": self.bot,
            "ctx": ctx,
            "msg": ctx.message,
            "guild": ctx.guild,
            "author": ctx.author,
            "channel": ctx.channel,
            "discord": discord,
        }

        fake_stdout = io.StringIO()

        to_compile = "async def func():\n" + textwrap.indent(program, "  ")

        try:
            exec(to_compile, glob)
        except Exception as e:
            return f"{e.__class__.__name__}: {e}"

        func = glob["func"]

        try:
            with redirect_stdout(fake_stdout):
                returned = await func()
        except asyncio.CancelledError:
            raise
        except Exception:
            return f"{fake_stdout.getvalue()}{traceback.format_exc()}"
        else:
            from_stdout = fake_stdout.getvalue()

            if returned is None:
                if from_stdout:
                    return f"{from_stdout}"

                return "Evaluated"
            else:
                return f"{from_stdout}{returned}"

    @commands.command()
    async def exec(self, ctx, *, arguments: str):
        """Execute shell command"""

        stdout, stderr = await run_process_shell(arguments)

        result = ""
        if stderr:
            result += f"STDERR:\n{stderr}"
        if stdout:
            result += stdout

        result = result.replace(self.bot.http.token, "TOKEN_LEAKED")

        await ctx.send(f"```bash\n{result[-2000 - 1 + 12:]}```")


def setup(bot):
    bot.add_cog(TechAdminTools(bot))
