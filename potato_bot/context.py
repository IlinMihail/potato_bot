from __future__ import annotations

from typing import TYPE_CHECKING, Any, Union, Optional, Sequence

import aiohttp
import discord

from discord.ext import commands

from .db import DB

if TYPE_CHECKING:
    from .types import Accent


class Context(commands.Context):
    @property
    def prefix(self) -> str:
        return self._prefix

    @prefix.setter
    def prefix(self, value: Optional[str]):
        # because custom get_prefix can leave spaces
        self._prefix = None if value is None else value.rstrip()

    @property
    def db(self) -> DB:
        return self.bot.db

    @property
    def session(self) -> aiohttp.ClientSession:
        return self.bot.session

    async def send(
        self,
        content: Any = None,
        *,
        target: discord.abc.Messageable = None,
        register: bool = True,
        accents: Optional[Sequence[Accent]] = None,
        **kwargs: Any,
    ) -> discord.Message:
        if content is not None:
            if accents is None:
                accents = self.bot.accents

            content = str(content)

            for accent in accents:
                content = accent.apply(content)

        if target is None:
            message = await super().send(content, **kwargs)
        else:
            message = await target.send(content, **kwargs)

        if register:
            self.bot.dispatch("message_response_", self.message.id, message)

        return message

    async def reply(self, content: str = None, **kwargs: Any) -> discord.Message:
        return await self.send(content, reference=self.message, **kwargs)

    async def edit(
        self,
        message: discord.Message,
        *,
        accents: Optional[Sequence[Accent]] = None,
        content: Optional[str] = None,
        **kwargs: Any,
    ):
        if content is not None:
            if accents is None:
                accents = self.bot.accents

            content = str(content)

            for accent in accents:
                content = accent.apply(content)

        await message.edit(content=content, **kwargs)

    async def react(
        self,
        *emojis: Union[discord.Emoji, str],
        message: discord.Message = None,
        register: bool = True,
    ):
        if message is None:
            message = self.message

        for emoji in emojis:
            await message.add_reaction(emoji)

        if register:
            for emoji in emojis:
                self.bot.dispatch(
                    "reaction_response_",
                    message.id,
                    message,
                    emoji,
                )

    async def ok(self, message: discord.Message = None):
        if message is None:
            message = self.message

        return await self.react("\N{HEAVY CHECK MARK}", message=message)

    async def nope(self, message: discord.Message = None):
        if message is None:
            message = self.message

        return await self.react("\N{HEAVY MULTIPLICATION X}", message=message)
