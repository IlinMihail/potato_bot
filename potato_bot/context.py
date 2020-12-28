from typing import Any, Union

import discord

from discord.ext import commands

from .response import MessageResponse, ReactionResponse


class PotatoContext(commands.Context):
    async def send(
        self, *args: Any, register: bool = True, **kwargs: Any
    ) -> discord.Message:
        message = await super().send(*args, **kwargs)

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
                [ReactionResponse(message, str(emoji)) for emoji in emojis],
            )
