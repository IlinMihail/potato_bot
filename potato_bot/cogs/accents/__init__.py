import importlib

from typing import Any, Dict, Optional, Sequence
from pathlib import Path

import discord

from discord.ext import commands

from potato_bot.bot import Bot
from potato_bot.cog import Cog
from potato_bot.utils import LRU
from potato_bot.checks import is_owner
from potato_bot.context import Context

from .accent import Accent

REQUIRED_PERMS = discord.Permissions(
    send_messages=True, manage_messages=True, manage_webhooks=True
)


class AccentConvertable(Accent, is_accent=False):
    @classmethod
    async def convert(cls, ctx: Context, argument: str) -> Accent:
        prepared = argument.replace(" ", "_")
        try:
            return Accent.get_by_name(prepared)
        except KeyError:
            raise commands.BadArgument(f'Accent "{argument}" does not exist')


class Accents(Cog):
    """Commands for managing accents"""

    accents = []

    MAX_ACCENTS_PER_USER = 10

    def __init__(self, bot: Bot):
        super().__init__(bot)

        # channel_id -> Webhook
        self._webhooks = LRU(50)

        # guild_id -> user_id -> accents
        self.accent_settings: Dict[int, Dict[int, Sequence[Accent]]] = {}

    async def setup(self):
        async with self.bot.db.cursor() as cur:
            await cur.execute("SELECT * FROM user_accent")
            accents = await cur.fetchall()

        for row in accents:
            accent = Accent.get_by_name(row["accent"])

            guild_id = row["guild_id"]
            user_id = row["user_id"]

            if guild_id in self.accent_settings:
                if user_id in self.accent_settings[guild_id]:
                    self.accent_settings[guild_id][user_id].append(accent)
                else:
                    self.accent_settings[guild_id][user_id] = [accent]
            else:
                self.accent_settings[guild_id] = {user_id: [accent]}

    @commands.group(
        invoke_without_command=True, ignore_extra=False, aliases=["accents"]
    )
    async def accent(self, ctx: Context):
        """Accent management"""

        await ctx.send_help(ctx.command)

    def _format_accent_list(self, accents: Sequence[Accent]) -> str:
        body = ""

        # I have no idea why this is not in stdlib, string has find method
        def sequence_find(seq: Sequence[Any], item: Any, default: int = -1) -> int:
            for i, j in enumerate(seq):
                if j == item:
                    return i

            return default

        all_accents = Accent.all_accents()
        for accent in sorted(
            all_accents,
            key=lambda a: (
                # sort by position in global accent list, leave missing at the end
                sequence_find(accents, a, len(all_accents)),
                # sort the rest by names
                str(a).lower(),
            ),
        ):
            enabled = accent in accents

            body += f"{'+' if enabled else '-'} {accent}\n"

        return body

    async def _update_nick(self, ctx: Context):
        new_nick = ctx.me.name
        for accent in Accents.accents:
            new_nick = accent.apply(ctx.me.name, limit=32).strip()

        await ctx.me.edit(nick=new_nick)

    @accent.group(name="bot", invoke_without_command=True, ignore_extra=False)
    async def _bot_accent(self, ctx: Context):
        """Manage bot accents, lists accents without arguments"""

        formatted_list = self._format_accent_list(Accents.accents)

        await ctx.send(
            f"Bot accents (applied from top to bottom): ```\n{formatted_list}```"
        )

    @_bot_accent.command(name="add", aliases=["enable", "on"])
    @is_owner()
    async def _bot_accent_add(self, ctx: Context, *accents: AccentConvertable):
        """Enable accents"""

        if not accents:
            return await ctx.send("No accents provided")

        for accent in accents:
            if accent in self.accents:
                continue

            Accents.accents.append(accent)

        await self._update_nick(ctx)

        await ctx.send("Enabled bot accents")

    @_bot_accent.command(name="remove", aliases=["disable", "off"])
    @is_owner()
    async def _bot_accent_remove(self, ctx: Context, *accents: AccentConvertable):
        """Disable accents

        Disables all if no accents provided
        """

        if not accents:
            Accents.accents = []
        else:
            for accent in accents:
                try:
                    Accents.accents.remove(accent)
                except ValueError:
                    pass

        await self._update_nick(ctx)

        await ctx.send("Disabled bot accents")

    @accent.command(name="use")
    async def accent_use(self, ctx: Context, accent: AccentConvertable, *, text: str):
        """Apply specified accent to text"""

        await ctx.send(text, accents=[accent])

    def get_user_accents(self, guild_id: int, user_id: int) -> Sequence[Accent]:
        if guild_id not in self.accent_settings:
            self.accent_settings[guild_id] = {}

        return self.accent_settings[guild_id].get(user_id, [])

    @accent.group(
        name="me",
        invoke_without_command=True,
        ignore_extra=False,
    )
    @commands.guild_only()
    async def my_accents(self, ctx: Context):
        """Manage your accents, lists accents without arguments"""

        accents = self.get_user_accents(ctx.guild.id, ctx.author.id)
        formatted_list = self._format_accent_list(accents)

        await ctx.send(
            f"Your accents (applied from top to bottom): ```\n{formatted_list}```"
        )

    @my_accents.command(name="add", aliases=["enable", "on"])
    @commands.guild_only()
    @commands.bot_has_permissions(manage_messages=True, manage_webhooks=True)
    async def add_my_accent(self, ctx, *accents: AccentConvertable):
        """Enable personal accents"""

        if not accents:
            return await ctx.send("No accents provided")

        current_accents = self.get_user_accents(ctx.guild.id, ctx.author.id)

        if not (to_add := set(accents).difference(current_accents)):
            return await ctx.send("Nothing to add")

        if len(current_accents) + len(to_add) > self.MAX_ACCENTS_PER_USER:
            return await ctx.send(
                f"Cannot have more than **{self.MAX_ACCENTS_PER_USER}** enabled at once"
            )

        # sets are nice, but we must preserve order here
        to_add = sorted(to_add, key=lambda x: accents.index(x))

        current_accents.extend(to_add)

        self.accent_settings[ctx.guild.id][ctx.author.id] = current_accents

        async with ctx.db.cursor(commit=True) as cur:
            await cur.executemany(
                """
                INSERT INTO user_accent (
                    guild_id,
                    user_id,
                    accent
                ) VALUES (
                    ?,
                    ?,
                    ?
                )
                """,
                [(ctx.guild.id, ctx.author.id, str(accent)) for accent in to_add],
            )

        await ctx.send("Enabled personal accents")

    @my_accents.command(name="remove", aliases=["disable", "off"])
    @commands.guild_only()
    async def remove_my_accent(self, ctx, *accents: AccentConvertable):
        """Disable personal accents

        Disables all if no accents provided
        """

        current_accents = self.get_user_accents(ctx.guild.id, ctx.author.id)

        if not accents:
            accents = current_accents

        if not (to_remove := set(current_accents).intersection(accents)):
            return await ctx.send("Nothing to remove")

        self.accent_settings[ctx.guild.id][ctx.author.id] = [
            a for a in current_accents if a not in to_remove
        ]

        async with ctx.db.cursor(commit=True) as cur:
            await cur.executemany(
                """
                DELETE FROM user_accent
                WHERE
                    guild_id = ? AND
                    user_id = ? AND
                    accent = ?
                """,
                [(ctx.guild.id, ctx.author.id, str(accent)) for accent in to_remove],
            )

        await ctx.send("Disabled personal accents")

    @commands.command()
    async def owo(self, ctx: Context):
        """OwO what's this"""

        owo = await AccentConvertable.convert(ctx, "owo")
        if owo in Accents.accents:
            Accents.accents.remove(owo)
        else:
            Accents.accents.append(owo)

        await self._update_nick(ctx)

        await ctx.send("owo toggled")

    @staticmethod
    def _apply_accents(content: str, accents: Sequence[Accent]) -> Optional[str]:
        for accent in accents:
            content = accent.apply(content)

        return content

    @Context.hook()
    async def on_send(
        original,
        ctx: Context,
        content: Any = None,
        *,
        accents: Optional[Sequence[Accent]] = None,
        **kwargs: Any,
    ) -> discord.Message:
        if content is not None:
            if accents is None:
                accents = Accents.accents

            content = Accents._apply_accents(str(content), accents)

        return await original(ctx, content, **kwargs)

    @Context.hook()
    async def on_edit(
        original,
        ctx: Context,
        message: discord.Message,
        *,
        accents: Optional[Sequence[Accent]] = None,
        content: Optional[str] = None,
        **kwargs: Any,
    ):
        if content is not None:
            if accents is None:
                accents = Accents.accents

            content = Accents._apply_accents(str(content), accents)

        return await original(ctx, message, content=content, **kwargs)

    async def _replace_message(self, message: discord.Message):
        if message.author.bot:
            return

        if message.guild is None:
            return

        if not message.content:
            return

        if not (accents := self.get_user_accents(message.guild.id, message.author.id)):
            return

        if not message.guild.me.guild_permissions.is_superset(REQUIRED_PERMS):
            return

        if (ctx := await self.bot.get_context(message)).valid:
            return

        if (
            content := self._apply_accents(message.content, accents)
        ) == message.content:
            return

        await message.delete()
        try:
            await self._send_new_message(ctx, content, message)
        except discord.NotFound:
            # cached webhook is missing, should invalidate cache
            del self._webhooks[message.channel.id]

            await self._send_new_message(ctx, content, message)

    async def _get_cached_webhook(
        self, channel: discord.TextChannel
    ) -> discord.Webhook:
        if (wh := self._webhooks.get(channel.id)) is None:
            wh_name = "PotatoBot accent Webhook"
            for wh in await channel.webhooks():
                if wh.name == wh_name:
                    break
            else:
                wh = await channel.create_webhook(name=wh_name)

            self._webhooks[channel.id] = wh

        return wh

    async def _send_new_message(
        self,
        ctx: Context,
        content: str,
        original: discord.Message,
    ) -> None:
        await ctx.send(
            content,
            allowed_mentions=discord.AllowedMentions(
                everyone=original.author.guild_permissions.mention_everyone,
                users=True,
                roles=True,
            ),
            target=await self._get_cached_webhook(original.channel),
            register=False,
            accents=[],
            # webhook data
            username=original.author.display_name,
            avatar_url=original.author.avatar_url,
            embeds=original.embeds,
        )

    @Cog.listener()
    async def on_message(self, message: discord.Message):
        await self._replace_message(message)

    # needed in case people use command and edit their message
    @Cog.listener()
    async def on_message_edit(self, old: discord.Message, new: discord.Message):
        await self._replace_message(new)


def load_accents():
    this_file = Path(__file__)

    for child in this_file.parent.iterdir():
        if child.suffix != ".py":
            continue

        if child.name in (this_file.name, "accent.py"):
            continue

        importlib.import_module(f"{__name__}.{child.stem}")


def setup(bot: Bot):
    load_accents()

    bot.add_cog(Accents(bot))
