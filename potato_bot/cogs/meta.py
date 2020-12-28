from discord.ext import commands


class CustomHelp(commands.DefaultHelpCommand):
    def get_destination(self):
        return self.context


class Meta(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.old_help_command = bot.help_command

        bot.help_command = CustomHelp()
        bot.help_command.cog = self

    def cog_unload(self):
        self.bot.help_command = self.old_help_command


def setup(bot):
    bot.add_cog(Meta(bot))
