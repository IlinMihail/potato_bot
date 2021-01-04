import importlib

from typing import Any, Sequence
from pathlib import Path

from discord.ext import commands

from potato_bot.cog import Cog
from potato_bot.checks import is_admin

from .accent import Accent


class Accents(Cog):
    """Commands for managing bot accents"""

    def cog_unload(self):
        self.bot.accents = []

    @commands.group(invoke_without_command=True, aliases=["accents"])
    async def accent(self, ctx):
        """Manage bot accents"""

        await ctx.send_help(ctx.command)

    @accent.command()
    async def list(self, ctx, *accents: Accent):
        """List available accents"""

        body = ""

        # I have no idea why this is not in stdlib, string has find method
        def sequence_find(seq: Sequence[Any], item: Any, default: int = -1) -> int:
            for i, j in enumerate(seq):
                if j == item:
                    return i

            return default

        accents = Accent.all_accents()
        for accent in sorted(
            accents,
            key=lambda a: (
                # sort by position in global accent list, leave missing at the end
                sequence_find(ctx.bot.accents, a, len(accents)),
                # sort the rest by names
                str(a).lower(),
            ),
        ):
            enabled = accent in ctx.bot.accents

            body += f"{'+' if enabled else '-'} {accent}\n"

        await ctx.send(f"Bot accents: ```\n{body}```")

    async def _update_nick(self, ctx):
        new_nick = ctx.me.name
        for accent in ctx.bot.accents:
            new_nick = accent.apply(ctx.me.name, limit=32).strip()

        await ctx.me.edit(nick=new_nick)

    @accent.command(aliases=["enable", "on"])
    @is_admin()
    async def add(self, ctx, *accents: Accent):
        """Enable accents"""

        if not accents:
            return await ctx.send("No accents provided")

        for accent in accents:
            if accent in ctx.bot.accents:
                continue

            ctx.bot.accents.append(accent)

        await self._update_nick(ctx)

        await ctx.send("Enabled accents")

    @accent.command(aliases=["disable", "off"])
    @is_admin()
    async def remove(self, ctx, *accents: Accent):
        """Disable accents

        Disables all if no accents provided
        """

        if not accents:
            ctx.bot.accents = []
        else:
            for accent in accents:
                if accent not in ctx.bot.accents:
                    continue

                ctx.bot.accents.remove(accent)

        await self._update_nick(ctx)

        await ctx.send("Disabled accents")

    @accent.command()
    async def use(self, ctx, accent: Accent, *, text: str):
        """Apply specified accent to text"""

        await ctx.send(text, accents=[accent])

    @commands.command()
    async def owo(self, ctx):
        """OwO what's this"""

        owo = await Accent.convert(ctx, "owo")
        if owo in ctx.bot.accents:
            ctx.bot.accents.remove(owo)
        else:
            ctx.bot.accents.append(owo)

        await self._update_nick(ctx)

        await ctx.send("owo toggled")


def load_accents():
    this_file = Path(__file__)

    for child in this_file.parent.iterdir():
        if child.suffix != ".py":
            continue

        if child.name in (this_file.name, "accent.py"):
            continue

        importlib.import_module(f"{__name__}.{child.stem}")


def setup(bot):
    load_accents()

    bot.add_cog(Accents(bot))
