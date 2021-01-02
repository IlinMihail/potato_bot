import os

import travitia_talk as tt

from discord.ext import commands

from potato_bot.bot import Bot


class Chat(commands.Cog):
    """ChatBot commands"""

    def __init__(self, bot: Bot):
        self.bot = bot

        self.chatbot = tt.ChatBot(os.environ["TRAVITIA_API_TOKEN"])
        self.emotion = tt.Emotion.neutral

    @commands.command()
    async def emotion(self, ctx, emotion: str = None):
        """Manage chatbot emotion globally"""

        if emotion is None:
            return await ctx.send(f"Current emotion is **{self.emotion.value}**")

        try:
            self.emotion = tt.Emotion(emotion)
        except ValueError:
            return await ctx.send(
                f"Must be one of `{', '.join(e.value for e in tt.Emotion)}`"
            )

        await ctx.ok()

    @commands.command(aliases=["cb", "talk"])
    async def ask(self, ctx, *, text: str):
        """Talk to PotatoBot"""

        async with ctx.typing():
            await self._ask(ctx, text)

    async def _ask(self, ctx, text: str):
        try:
            response = await self.chatbot.ask(
                text, id=ctx.author.id, emotion=self.emotion
            )
        except tt.APIError as e:
            return await ctx.send(f"Error: `{e}`")

        await ctx.send(response.text)


def setup(bot):
    bot.add_cog(Chat(bot))
