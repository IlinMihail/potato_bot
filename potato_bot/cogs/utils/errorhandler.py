from discord.ext import commands

from potato_bot.bot import Bot
from potato_bot.context import PotatoContext


class ErrorHandler(commands.Cog):
    def __init__(self, bot: Bot):
        self.bot = Bot

    @commands.Cog.listener()
    async def on_command_error(self, ctx: PotatoContext, e: Exception):
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

            await ctx.reply(f"Unexpected error: **{e.__class__.__name__}**: `{e}`")


def setup(bot: Bot):
    bot.add_cog(ErrorHandler(bot))
