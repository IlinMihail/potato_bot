import importlib

from typing import Any, Dict, Optional, Sequence
from pathlib import Path

import discord

from discord.ext import commands

from potato_bot.bot import Bot
from potato_bot.cog import Cog
from potato_bot.checks import is_admin
from potato_bot.context import Context

from .accent import Accent


class AccentConvertable(Accent):
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

    @accent.group(name="bot")
    async def _bot_accent(self, ctx: Context):
        """Manage bot accents, lists accents without arguments"""

        formatted_list = self._format_accent_list(Accents.accents)

        await ctx.send(f"Bot accents: ```\n{formatted_list}```")

    @_bot_accent.command(name="add", aliases=["enable", "on"])
    @is_admin()
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
    @is_admin()
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

    @accent.command(name="force")
    @is_admin()
    async def accent_force(
        self, ctx: Context, user: discord.Member, *accents: AccentConvertable
    ):
        """Force user to talk with accent

        Forced accent cannot be removed by user
        """

        if not accents:
            return await ctx.send("No accents provided")

        if user.bot:
            return await ctx.send("Canot use force on bots")

        current_accents = self.get_user_accents(user.guild.id, user.id)

        to_add = set(accents).difference(current_accents)

        # sets are nice, but we must preserve order here
        to_add = sorted(to_add, key=lambda x: accents.index(x))

        current_accents.extend(to_add)

        self.accent_settings[user.guild.id][user.id] = current_accents

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
                [(user.guild.id, user.id, str(accent)) for accent in to_add],
            )

            # force all listed accents, not just previously added new ones
            #
            # i have no idea why IN ? does not work, so list is created manually
            unique_accents = set(accents)
            await cur.execute(
                f"""
                UPDATE user_accent
                SET forced = true
                WHERE
                    guild_id = ?
                    AND user_id = ?
                    AND accent IN ({",".join("?" for a in unique_accents)})
                """,
                (user.guild.id, user.id, *[str(a) for a in unique_accents]),
            )

        await ctx.send("Forced accents for user")

    @accent.command(name="unforce")
    @is_admin()
    async def accent_unforce(
        self, ctx: Context, user: discord.Member, *accents: AccentConvertable
    ):
        """Remove forced accent"""

        if not accents:
            accents = self.get_user_accents(user.guild.id, user.id)

        async with ctx.db.cursor(commit=True) as cur:
            # i have no idea why IN ? does not work, so list is created manually
            unique_accents = set(accents)
            await cur.execute(
                f"""
                UPDATE user_accent
                SET forced = false
                WHERE
                    guild_id = ?
                    AND user_id = ?
                    AND accent IN ({",".join("?" for a in unique_accents)})
                """,
                (user.guild.id, user.id, *[str(a) for a in accents]),
            )

        await ctx.send("Unforced accents for user")

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

        await ctx.send(f"Your accents: ```\n{formatted_list}```")

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

        async with ctx.db.cursor() as cur:
            await cur.execute(
                """
                SELECT accent
                FROM user_accent
                WHERE
                    guild_id = ?
                    AND user_id = ?
                    AND forced = true
                """,
                (
                    ctx.guild.id,
                    ctx.author.id,
                ),
            )
            if (forced := await cur.fetchall()) :
                return await ctx.send(
                    f"Accent(s) **{', '.join(i['accent'] for i in forced)}** are forced, cannot remove"
                )

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

            content = str(content)

            for accent in accents:
                content = accent.apply(content)

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

            content = str(content)

            for accent in accents:
                content = accent.apply(content)

        return await original(ctx, message, content=content, **kwargs)

    @Cog.listener()
    async def on_message(self, message: discord.Message):
        if message.author.bot:
            return

        if message.guild is None:
            return

        if not message.content:
            return

        accents = self.get_user_accents(message.guild.id, message.author.id)
        if not accents:
            return

        ctx = await self.bot.get_context(message)
        if ctx.valid:
            return

        perms = message.guild.me.guild_permissions
        if not (perms.manage_messages and perms.manage_webhooks):
            return await ctx.send("Missing permissions to apply accents")

        for webhook in await message.channel.webhooks():
            if webhook.name == "Accent Webhook":
                break
        else:
            webhook = await message.channel.create_webhook(name="Accent Webhook")

        await message.delete()
        await ctx.send(
            message.content,
            allowed_mentions=discord.AllowedMentions(
                everyone=message.author.guild_permissions.mention_everyone,
                users=True,
                roles=True,
            ),
            target=webhook,
            register=False,
            accents=accents,
            # webhook data
            username=message.author.display_name,
            avatar_url=message.author.avatar_url,
        )


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
