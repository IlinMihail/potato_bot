from typing import Any, Union, Optional

import discord

from discord.ext import commands

from .db import DB
from .response import MessageResponse, ReactionResponse


# https://github.com/Rapptz/discord.py/blob/5d75a0e7d613948245d1eb0353fb660f4664c9ed/discord/message.py#L56
def convert_emoji_reaction(emoji):
    if isinstance(emoji, discord.Reaction):
        emoji = emoji.emoji

    if isinstance(emoji, discord.Emoji):
        return "%s:%s" % (emoji.name, emoji.id)
    if isinstance(emoji, discord.PartialEmoji):
        return emoji._as_reaction()
    if isinstance(emoji, str):
        # Reactions can be in :name:id format, but not <:name:id>.
        # No existing emojis have <> in them, so this should be okay.
        return emoji.strip("<>")

    raise discord.errors.InvalidArgument(
        "emoji argument must be str, Emoji, or Reaction not {.__class__.__name__}.".format(
            emoji
        )
    )


class PotatoContext(commands.Context):
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

    async def send(
        self,
        content: Any = None,
        *,
        register: bool = True,
        accents=None,
        **kwargs: Any,
    ) -> discord.Message:
        if content is not None:
            if accents is None:
                accents = self.bot.accents

            content = str(content)

            for accent in self.bot.accents:
                content = accent.apply(content)

        message = await super().send(content, **kwargs)

        if register:
            self.bot.register_responses(
                self.message.id,
                [MessageResponse(message)],
            )

        return message

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
            self.bot.register_responses(
                message.id,
                [
                    ReactionResponse(message, convert_emoji_reaction(emoji))
                    for emoji in emojis
                ],
            )

    async def ok(self, message: discord.Message = None):
        if message is None:
            message = self.message

        return await self.react("\N{HEAVY CHECK MARK}", message=message)

    async def nope(self, message: discord.Message = None):
        if message is None:
            message = self.message

        return await self.react("\N{HEAVY MULTIPLICATION X}", message=message)
