from __future__ import annotations

import os
import re

from typing import TYPE_CHECKING, Set, List

import aiohttp
import discord

from discord.ext import commands

from potato_bot.db import DB

from .context import Context

if TYPE_CHECKING:
    from .types import Accent

initial_extensions = (
    "potato_bot.cogs.accents",
    "potato_bot.cogs.bans",
    "potato_bot.cogs.chat",
    "potato_bot.cogs.fun",
    "potato_bot.cogs.meta",
    "potato_bot.cogs.potatostation",
    "potato_bot.cogs.techadmin",
    "potato_bot.cogs.utils.errorhandler",
    "potato_bot.cogs.utils.responsetracker",
)


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

        self.db = DB()
        self.session = aiohttp.ClientSession()

        self.owner_ids: Set[int] = set()
        self.accents: List[Accent] = []

        self.loop.run_until_complete(self.critical_setup())
        self.loop.create_task(self.setup())

        for extension in initial_extensions:
            self.load_extension(extension)

    async def get_prefix(self, message: discord.Message):
        standard = await super().get_prefix(message)
        if isinstance(standard, str):
            standard = [standard]

        if message.guild is None:
            standard.append("")

        expr = re.compile(
            rf"^(?:{'|'.join(re.escape(p) for p in standard)})\s*", re.IGNORECASE
        )

        if (match := expr.match(message.content)) is not None:
            return match[0]

        # don't waste effort checking prefixes twice
        return []

    async def on_ready(self):
        print(f"Logged in as {self.user}!")
        print(f"Prefix: {os.environ['BOT_PREFIX']}")

    async def critical_setup(self):
        await self.db.connect()

    async def setup(self):
        await self.wait_until_ready()

        await self._fetch_owners()

    async def _fetch_owners(self):
        app_info = await self.application_info()
        if app_info.team is None:
            self.owner_ids = set((app_info.owner.id,))
        else:
            self.owner_ids = set(m.id for m in app_info.team.members)

    async def close(self):
        await super().close()

        await self.session.close()
        await self.db.close()

    async def get_context(self, message, *, cls=None):
        return await super().get_context(message, cls=cls or Context)

    async def on_message(self, message: discord.Message):
        if message.author.bot:
            return

        await self.process_commands(message)
