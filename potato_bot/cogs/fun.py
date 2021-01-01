import random

from typing import Union

import discord

from discord.ext import commands


class Fun(commands.Cog):
    """Commands without practival use"""

    THROWABLE_ITEMS = (
        "dead bird",
        "potato",
        "rock",
        "stick",
        "divorce papers",
        "dice",
        "weird look",
        "sock",
        "apple",
        "car keys",
        "chair",
    )

    @commands.command()
    async def throw(
        self,
        ctx,
        target: Union[
            discord.User,
            discord.TextChannel,
            discord.CategoryChannel,
            discord.VoiceChannel,
            str,
        ],
        *,
        item: str = None,
    ):
        """Throw things, for FUN

        Target can be user, channel or just string."""

        preposition = "at"

        if isinstance(target, discord.User):
            if target in ctx.message.mentions:
                target = target.mention
            else:
                target = f"`{target}`"

        elif isinstance(
            target,
            (
                discord.TextChannel,
                discord.CategoryChannel,
                discord.VoiceChannel,
            ),
        ):
            target = target.mention
            preposition = "into"

        if item is None:
            item = random.choice(self.THROWABLE_ITEMS)

        verb = random.choice(
            (
                "throws",
                "threw",
                "is throwing",
            )
        )

        modifier = random.choice(
            (
                "",
                " angrily",
                " lazily",
                " weakly",
                " with a great force",
                " aiming for the kill",
                " and misses!!",
            )
        )

        await ctx.send(
            f"**{ctx.author}** {verb} {item} {preposition} **{target}**{modifier}!"
        )


def setup(bot):
    bot.add_cog(Fun(bot))
