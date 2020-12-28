import asyncio

from typing import List
from collections import OrderedDict

import aiohttp
import discord

from discord.ext import commands

from potato_bot.db import DB

from .context import PotatoContext
from .response import Response

initial_extensions = (
    "potato_bot.cogs.admin",
    "potato_bot.cogs.bans",
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

        for extension in initial_extensions:
            self.load_extension(extension)

    async def on_ready(self):
        if not self._first_on_ready:
            return

        self._first_on_ready = False

        print(f"Logged in as {self.user}!")
        print(f"Prefix: {self.command_prefix}")

        await self.db.connect()

        for cog in self.cogs.values():
            if hasattr(cog, "async_init"):
                await cog.async_init()

    async def on_command_error(self, ctx, e):
        ignored = (commands.CommandNotFound,)
        if isinstance(e, ignored):
            return

        if isinstance(e, commands.MissingRole):
            await ctx.send(f"You must have {e.missing_role} role to use this")
        elif isinstance(e, (commands.MissingRequiredArgument, commands.BadArgument)):
            await ctx.send(f"Error: {e}")
        else:
            if isinstance(e, commands.CommandInvokeError):
                e = e.original

            await ctx.send(f"Unexpected error: **{e.__class__.__name__}**: `{e}`")

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
