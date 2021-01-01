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
        "hamburger",
        "clownburger",
        "kitty ears",
        "o2 tank",
        "normal looking pen",
        "a water bucket",
        "a pair of shoes",
        "lizard",
        "beer",
        "porrly written computer program",
        "water balloon",
        "nothing",
        "chessboard",
        "bowl of rice",
        "mug",
        "egg",
        "up",
        "spear",
        "pea",
        "curses",
        "snowball",
        "sand",
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

        Target can be user, channel or just string.
        You can also attach file as target."""

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
            if ctx.message.attachments:
                item = ctx.message.attachments[0].url
            else:
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
                if ctx.channel.is_nsfw() and not target.is_nsfw():
                    return await ctx.send("Can't throw items from horny channel!")

                await ctx.send(
                    f"{item} from `{ctx.author}` in {ctx.channel.mention}!",
                    target=target,
                    allowed_mentions=discord.AllowedMentions(users=False),
                )
            else:
                await ctx.send(
                    f"{item} bounces back from {mention} and hits `{ctx.author}`!"
                )


def setup(bot):
    bot.add_cog(Fun(bot))
