from discord.ext import commands

from potato_bot.constants import ADMIN_ROLE_ID


def is_techadmin():
    return commands.has_role(ADMIN_ROLE_ID)


def is_admin():
    return commands.has_role(ADMIN_ROLE_ID)
