from __future__ import annotations

import os
import re

from typing import TYPE_CHECKING, Set, List
from collections import OrderedDict

import aiohttp
import discord

from discord.ext import commands

from potato_bot.db import DB

from .context import PotatoContext
from .response import Response

if TYPE_CHECKING:
    from .types import Accent

initial_extensions = (
    "potato_bot.cogs.accents",
    "potato_bot.cogs.admin",
    "potato_bot.cogs.bans",
    "potato_bot.cogs.fun",
    "potato_bot.cogs.meta",
    "potato_bot.cogs.techadmin",
)


# https://docs.python.org/3/library/collections.html#ordereddict-examples-and-recipes
class LRU(OrderedDict):
    def __init__(self, maxsize=128, /, *args, **kwds):
        self.maxsize = maxsize
        super().__init__(*args, **kwds)

    def __setitem__(self, key, value):
        if key in self:
            self.move_to_end(key)

        super().__setitem__(key, value)

        if len(self) > self.maxsize:
            oldest = next(iter(self))
            del self[oldest]


class Bot(commands.Bot):
    def __init__(self, **kwargs):
        super().__init__(
            command_prefix=commands.when_mentioned_or(os.environ["BOT_PREFIX"]),
            case_insensitive=True,
            allowed_mentions=discord.AllowedMentions(
                roles=False, everyone=False, users=True
            ),
            intents=discord.Intents(
                guilds=True,
                members=True,
                bans=True,
                emojis=True,
                messages=True,
                reactions=True,
            ),
            **kwargs,
        )

        self._first_on_ready = True

        self._responses = LRU(1024)

        self.db = DB()
        self.session = aiohttp.ClientSession()

        self.owner_ids: Set[int] = set()
        self.accents: List[Accent] = []

        for extension in initial_extensions:
            self.load_extension(extension)

    async def get_prefix(self, message: discord.Message):
        standard = await super().get_prefix(message)

        if message.guild is None:
            standard.append("")

        expr = re.compile(
            rf"^(({'|'.join(re.escape(p) for p in standard)})\s*)", re.IGNORECASE
        )

        if (match := expr.match(message.content)) is not None:
            return match.group(1)

        return []

    async def on_ready(self):
        if not self._first_on_ready:
            return

        self._first_on_ready = False

        print(f"Logged in as {self.user}!")
        print(f"Prefix: {os.environ['BOT_PREFIX']}")

        await self.db.connect()
        await self._fetch_owners()

    async def _fetch_owners(self):
        app_info = await self.application_info()
        if app_info.team is None:
            self.owner_ids = set((app_info.owner.id,))
        else:
            self.owner_ids = set(m.id for m in app_info.team.members)

    async def on_command_error(self, ctx, e):
        ignored = (commands.CommandNotFound,)
        if isinstance(e, ignored):
            return

        if isinstance(e, commands.MissingRole):
            await ctx.reply(f"You must have **{e.missing_role}** role to use this")
        elif isinstance(
            e,
            (
                commands.MissingRequiredArgument,
                commands.BadArgument,
                commands.NoPrivateMessage,
            ),
        ):
            await ctx.reply(f"Error: **{e}**")
        elif isinstance(e, commands.TooManyArguments):
            await ctx.send_help(ctx.command)
        elif isinstance(e, commands.ArgumentParsingError):
            await ctx.reply(f"Unable to process command arguments: {e}")
        else:
            if isinstance(e, commands.CommandInvokeError):
                e = e.original

            await ctx.reply(f"Unexpected error: **{e.__class__.__name__}**: `{e}`")

            raise e

    async def close(self):
        await super().close()

        await self.session.close()
        await self.db.close()

    async def get_context(self, message, *, cls=None):
        return await super().get_context(message, cls=cls or PotatoContext)

    async def on_message(self, message: discord.Message):
        if message.author.bot:
            return

        await self.process_commands(message)

    async def on_message_edit(self, old: discord.Message, new: discord.Message):
        if new.author.bot:
            return

        # embed edit
        if old.content == new.content:
            return

        if old.pinned != new.pinned:
            return

        await self.remove_responses(new.id)

        await self.process_commands(new)

    async def on_message_delete(self, message: discord.Message):
        await self.remove_responses(message.id)

    def register_responses(self, message_id: int, responses: List[Response]):
        existing = self._responses.get(message_id, [])
        existing.extend(responses)

        self._responses[message_id] = existing

    async def remove_responses(self, message_id):
        responses = self._responses.pop(message_id, [])

        for response in responses:
            await response.remove(self)

        # race conditions
        # asyncio.gather(*[r.remove(self) for r in responses])

        return responses
