from discord.ext import commands

from .context import PotatoContext
from .constants import ADMIN_ROLE_ID, TECHADMIN_ROLE_ID


def is_owner():
    async def predicate(ctx: PotatoContext) -> bool:
        return ctx.author.id in ctx.bot.owner_ids

    return commands.check(predicate)


def owner_bypass(check):
    def inner(*args, **kwargs):
        owner_pred = is_owner().predicate
        original_pred = check(*args, **kwargs).predicate

        async def predicate(ctx: PotatoContext):
            if await owner_pred(ctx):
                return True

            return await original_pred(ctx)

        return commands.check(predicate)

    return inner


@owner_bypass
def is_admin():
    return commands.has_role(ADMIN_ROLE_ID)


@owner_bypass
def is_techadmin():
    return commands.has_role(TECHADMIN_ROLE_ID)
