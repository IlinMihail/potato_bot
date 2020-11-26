from .misc import Misc
from .admin_tools import AdminTools
from .techadmin_tools import TechAdminTools


def load_cogs(bot):
    for cog in (AdminTools, Misc, TechAdminTools):
        bot.add_cog(cog(bot))
