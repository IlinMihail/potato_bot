import importlib

from typing import Any, Optional, Sequence
from pathlib import Path

import discord

from discord.ext import commands

from potato_bot.bot import Bot
from potato_bot.cog import Cog
from potato_bot.checks import is_admin
from potato_bot.context import Context

from .accent import Accent


class AccentConvertable(Accent):
    @classmethod
    async def convert(cls, ctx: Context, argument: str) -> Accent:
        prepared = argument.lower().replace(" ", "_")
        try:
            return Accent.get_by_name(prepared)
        except KeyError:
            raise commands.BadArgument(f'Accent "{argument}" does not exist')


class Accents(Cog):
    """Commands for managing bot accents"""

    accents = []

    @commands.group(invoke_without_command=True, aliases=["accents"])
    async def accent(self, ctx):
        """Manage bot accents"""

        await ctx.send_help(ctx.command)

    @accent.command()
    async def list(self, ctx):
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
                sequence_find(Accents.accents, a, len(accents)),
                # sort the rest by names
                str(a).lower(),
            ),
        ):
            enabled = accent in Accents.accents

            body += f"{'+' if enabled else '-'} {accent}\n"

        await ctx.send(f"Bot accents: ```\n{body}```")

    async def _update_nick(self, ctx):
        new_nick = ctx.me.name
        for accent in Accents.accents:
            new_nick = accent.apply(ctx.me.name, limit=32).strip()

        await ctx.me.edit(nick=new_nick)

    @accent.command(aliases=["enable", "on"])
    @is_admin()
    async def add(self, ctx, *accents: AccentConvertable):
        """Enable accents"""

        if not accents:
            return await ctx.send("No accents provided")

        for accent in accents:
            if accent in self.accents:
                continue

            Accents.accents.append(accent)

        await self._update_nick(ctx)

        await ctx.send("Enabled accents")

    @accent.command(aliases=["disable", "off"])
    @is_admin()
    async def remove(self, ctx, *accents: AccentConvertable):
        """Disable accents

        Disables all if no accents provided
        """

        if not accents:
            Accents.accents = []
        else:
            for accent in accents:
                if accent not in Accents.accents:
                    continue

                Accents.accents.remove(accent)

        await self._update_nick(ctx)

        await ctx.send("Disabled accents")

    @accent.command()
    async def use(self, ctx, accent: AccentConvertable, *, text: str):
        """Apply specified accent to text"""

        await ctx.send(text, accents=[accent])

    @commands.command()
    async def owo(self, ctx):
        """OwO what's this"""

        owo = await AccentConvertable.convert(ctx, "owo")
        if owo in Accents.accents:
            Accents.accents.remove(owo)
        else:
            Accents.accents.append(owo)

        await self._update_nick(ctx)

        await ctx.send("owo toggled")

    @Context.hook()
    async def on_send(
        original,
        ctx: Context,
        content: Any = None,
        *,
        accents: Optional[Sequence[Accent]] = None,
        **kwargs: Any,
    ) -> discord.Message:
        if content is not None:
            if accents is None:
                accents = Accents.accents

            content = str(content)

            for accent in accents:
                content = accent.apply(content)

        return await original(ctx, content, **kwargs)

    @Context.hook()
    async def on_edit(
        original,
        ctx: Context,
        message: discord.Message,
        *,
        accents: Optional[Sequence[Accent]] = None,
        content: Optional[str] = None,
        **kwargs: Any,
    ):
        if content is not None:
            if accents is None:
                accents = Accents.accents

            content = str(content)

            for accent in accents:
                content = accent.apply(content)

        return await original(ctx, message, content=content, **kwargs)


def load_accents():
    this_file = Path(__file__)

    for child in this_file.parent.iterdir():
        if child.suffix != ".py":
            continue

        if child.name in (this_file.name, "accent.py"):
            continue

        importlib.import_module(f"{__name__}.{child.stem}")


def setup(bot: Bot):
    load_accents()

    bot.add_cog(Accents(bot))
