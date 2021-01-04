from typing import Union
from collections import OrderedDict

import discord

from discord.ext import commands

from potato_bot.bot import Bot

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


class ResponseTracker(commands.Cog):
    def __init__(self, bot: Bot):
        super().__init__()

        self.bot = bot

        self.responses = LRU(1024)

    @commands.Cog.listener()
    async def on_message_response_(self, message_id: int, message: discord.Message):
        self.register_response(message_id, MessageResponse(message))

    @commands.Cog.listener()
    async def on_reaction_response_(
        self, message_id: int, message: discord.Message, emoji: _EmojiType
    ):
        self.register_response(
            message_id, ReactionResponse(message, convert_emoji_reaction(emoji))
        )

    @commands.Cog.listener()
    async def on_response_delete_(self, message_id: int):
        await self.remove_responses(message_id)

    @commands.Cog.listener()
    async def on_message_edit(self, old: discord.Message, new: discord.Message):
        if new.author.bot:
            return

        # embed edit
        if old.content == new.content:
            return

        if old.pinned != new.pinned:
            return

        await self.remove_responses(new.id)

        await self.bot.process_commands(new)

    @commands.Cog.listener()
    async def on_message_delete(self, message: discord.Message):
        await self.remove_responses(message.id)

    def register_response(self, message_id: int, response: Response):
        existing = self.responses.get(message_id, [])
        existing.append(response)

        self.responses[message_id] = existing

    async def remove_responses(self, message_id):
        responses = self.responses.pop(message_id, [])

        for response in responses:
            await response.remove(self.bot)

        # race conditions, bad until command cancellation is done
        # asyncio.gather(*[r.remove(self) for r in responses])


def setup(bot: Bot):
    bot.add_cog(ResponseTracker(bot))
