from typing import Any, Union

import discord

from potato_bot.bot import Bot
from potato_bot.cog import Cog
from potato_bot.utils import LRU
from potato_bot.context import Context

_EmojiType = Union[discord.Reaction, discord.Emoji, discord.PartialEmoji, str]


# https://github.com/Rapptz/discord.py/blob/5d75a0e7d613948245d1eb0353fb660f4664c9ed/discord/message.py#L56
def convert_emoji_reaction(emoji: _EmojiType):
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


class Response:
    async def remove(self, bot):
        raise NotImplementedError


class MessageResponse(Response):
    __slots__ = (
        "channel_id",
        "message_id",
    )

    def __init__(self, message: discord.Message):
        self.channel_id = message.channel.id
        self.message_id = message.id

    async def remove(self, bot):
        await bot.http.delete_message(self.channel_id, self.message_id)

    def __repr__(self) -> str:
        return f"<{self.__class__.__name__} channel={self.channel_id} message={self.message_id}>"


class ReactionResponse(Response):
    __slots__ = (
        "channel_id",
        "message_id",
        "emoji",
    )

    def __init__(
        self,
        message: discord.Message,
        emoji: str,
    ):
        self.channel_id = message.channel.id
        self.message_id = message.id
        self.emoji = emoji

    async def remove(self, bot):
        await bot.http.remove_own_reaction(self.channel_id, self.message_id, self.emoji)

    def __repr__(self) -> str:
        return f"<{self.__class__.__name__} channel={self.channel_id} message={self.message_id} emoji={self.emoji}>"


class ResponseTracker(Cog):
    responses = LRU(1024)

    @Context.hook()
    async def on_send(
        original, ctx: Context, *args: Any, register: bool = True, **kwargs: Any
    ):
        message = await original(ctx, *args, **kwargs)

        if register:
            ResponseTracker.register_response(ctx.message.id, MessageResponse(message))

        return message

    @Context.hook()
    async def on_react(
        original,
        ctx: Context,
        emoji: Union[discord.Emoji, str],
        register: bool = True,
        **kwargs: Any,
    ):
        message = await original(ctx, emoji, **kwargs)

        if register:
            ResponseTracker.register_response(
                ctx.message.id, ReactionResponse(message, convert_emoji_reaction(emoji))
            )

        return message

    @Cog.listener()
    async def on_message_edit(self, old: discord.Message, new: discord.Message):
        if new.author.bot:
            return

        # embed edit
        if old.content == new.content:
            return

        if old.pinned != new.pinned:
            return

        await self.remove_responses(new.id, self.bot)

        await self.bot.process_commands(new)

    @Cog.listener()
    async def on_message_delete(self, message: discord.Message):
        await self.remove_responses(message.id, self.bot)

    @classmethod
    def register_response(cls, message_id: int, response: Response):
        existing = cls.responses.get(message_id, [])
        existing.append(response)

        cls.responses[message_id] = existing

    @classmethod
    async def remove_responses(cls, message_id: int, bot: Bot):
        responses = cls.responses.pop(message_id, [])

        for response in responses:
            await response.remove(bot)

        # race conditions, bad until command cancellation is done
        # asyncio.gather(*[r.remove(bot) for r in responses])


def setup(bot: Bot):
    bot.add_cog(ResponseTracker(bot))
