import discord


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
