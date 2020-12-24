import discord, json

from discord.ext import commands

from potato_bot.utils import run_process
from potato_bot.checks import is_admin
from potato_bot.constants import SERVER_HOME


class AdminTools(commands.Cog, name="Admin tools"):
    def __init__(self, bot):
        self.bot = bot

    async def cog_check(self, ctx):
        return await is_admin().predicate(ctx)

    @commands.command()
    async def searchahelp(self, ctx, *, text):
        """Grep chat logs"""

        output = await run_process("grep", "-lr", text, SERVER_HOME / "chatlogs")
        files = output[0].split("\n")
        files.remove("")

        if not files:
            return await ctx.send("Nothing found")

        if len(files) > 4:
            return await ctx.send("more than 4 files matched that pattern")

        for (i, filename) in enumerate(files):
            await ctx.send(i + 1, file=discord.File(filename, filename="logs.txt"))

    @commands.command()
    async def stop(self, ctx):
        await ctx.send("stopping server")
        await run_process("sudo", "supervisorctl", "stop", "serpot")

    @commands.command()
    async def start(self, ctx):
        await ctx.send("starting server")
        await run_process("sudo", "supervisorctl", "start", "serpot")

    # commands for ban management

    unbans_to_do = []
    unjobbans_to_do = []

    def do_unban_now(self, bans_json, unbannee):
        for index, i in enumerate(bans_json["banEntries"]):
            if unbannee == i["userName"]:
                bans_json["banEntries"].pop(index)
                return        raise Exception(unbannee + " was not found in the bans file")

    def do_unjobban_now(self, jobbans_json, unbannee):
        for index, i in enumerate(jobbans_json["jobBanEntries"]):
            if unbannee == i["userName"]:
                jobbans_json["jobBanEntries"].pop(index)
                return
        raise Exception(unbannee + " was not found in the jobbans file")

    @commands.command()
    async def unban(self, ctx, *, unbannee: str):
        await ctx.send(unbannee + " will be unbanned next !r")
        self.unbans_to_do.append(unbannee)

    @commands.command()
    async def unjobban(self, ctx, *, unbannee: str):
        await ctx.send(unbannee + " will be unjobbanned next !r")
        self.unjobbans_to_do.append(unbannee)

    @commands.command(aliases=["r"])
    async def restart(self, ctx):
        await ctx.send("restarting server")

        await self.stop(ctx)

        with open(SERVER_HOME / "admin" / "banlist.json", "r+") as bans_file:
            bans_json = json.load(bans_file)
            for i in self.unbans_to_do:
                await ctx.send("Unbanning " + i)
                try:
                    self.do_unban_now(bans_json, i)
                except:
                    await ctx.send("Unable to unban " + i)

            bans_fie.seek(0)
            json.dump(bans_json, bans_file, indent=1)
            bans_file.truncate()
            self.unbans_to_do = []

        with open(SERVER_HOME / "admin" / "jobBanlist.json", "r+") as jobbans_file:
            jobbans_json = json.load(jobbans_file)
            for i in self.unjobbans_to_do:
                await ctx.send("Unjobbanning " + i)
                try:
                    self.do_unjobban_now(jobbans_json, i)
                except:
                    await ctx.send("unable to unjobban " + i)
            jobbans_file.seek(0)
            json.dump(jobbans_json, jobbans_file, indent=1)
            jobbans_file.truncate()
            self.unjobbans_to_do = []

        await self.start(ctx)
