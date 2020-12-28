from typing import Any, Union

import discord

from discord.ext import commands

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
                [
                    ReactionResponse(message, convert_emoji_reaction(emoji))
                    for emoji in emojis
                ],
            )
