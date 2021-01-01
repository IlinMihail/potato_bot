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
                mention = target.mention
            else:
                mention = f"`{target}`"

        elif isinstance(
            target,
            (
                discord.TextChannel,
                discord.CategoryChannel,
                discord.VoiceChannel,
            ),
        ):
            mention = target.mention
            preposition = "into"
        else:
            mention = target

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
            f"**{ctx.author}** {verb} {item} {preposition} **{mention}**{modifier}!"
        )

        if isinstance(target, discord.TextChannel) and target.guild == ctx.guild:
            if (
                target.permissions_for(ctx.author).send_messages
                and target.permissions_for(ctx.me).send_messages
            ):
                await ctx.send(
                    f"{item} from `{ctx.author}` in {ctx.channel.mention}!",
                    target=target,
                )
            else:
                await ctx.send(
                    f"{item} bounces back from {mention} and hits `{ctx.author}`!"
                )


def setup(bot):
    bot.add_cog(Fun(bot))
