import os
import logging
import traceback

from discord.ext import commands

from potato_bot.bot import Bot
from potato_bot.cog import Cog
from potato_bot.context import Context

log = logging.getLogger(__name__)


class ErrorHandler(Cog):
    def __init__(self, bot: Bot):
        super().__init__(bot)

        self.error_channel = None

    async def setup(self):
        if "ERROR_CHANNEL" not in os.environ:
            log.warn("error channel not set")
        else:
            self.error_channel = await self.bot.fetch_channel(
                os.environ["ERROR_CHANNEL"]
            )

    @Cog.listener()
    async def on_command_error(self, ctx: Context, e: Exception):
        ignored = (commands.CommandNotFound,)
        if isinstance(e, ignored):
            return

        if isinstance(e, commands.MissingRole):
            if isinstance(e.missing_role, int):
                role = f"<@&{e.missing_role}>"
            else:
                role = f"named **{e.missing_role}**"

            await ctx.reply(f"You must have {role} role to use this")
        elif isinstance(e, commands.CheckFailure):
            # all other checks
            error = str(e)
            if not error:
                error = f"**{e.__class__.__name__}**"

            await ctx.reply(f"Check failed: {error}")
        elif isinstance(
            e,
            (
                commands.MissingRequiredArgument,
                commands.BadArgument,
                commands.NoPrivateMessage,
            ),
        ):
            await ctx.reply(f"Error: **{e}**")
        elif isinstance(e, commands.TooManyArguments):
            await ctx.send_help(ctx.command)
        elif isinstance(e, (commands.ArgumentParsingError, commands.BadUnionArgument)):
            await ctx.reply(f"Unable to process command arguments: {e}")
        else:
            if isinstance(e, commands.CommandInvokeError):
                e = e.original

            await ctx.reply(f"Unexpected error: **{type(e).__name__}**: `{e}`")

            await self.send_error(e)

    async def send_error(self, e: Exception):
        if self.error_channel is None:
            return

        tb = "".join(traceback.format_exception(None, e, e.__traceback__, limit=20))

        await self.error_channel.send(f"**{type(e).__name__}**: {e}```\n{tb}```")


def setup(bot: Bot):
    bot.add_cog(ErrorHandler(bot))
