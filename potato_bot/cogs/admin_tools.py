import json

import discord

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

    async def sv_control(self, command):
        await run_process("sudo", "supervisorctl", command, "serpot")

    @commands.command()
    async def stop(self, ctx):
        await ctx.send("stopping server")
        await self.sv_control("stop")

    @commands.command()
    async def start(self, ctx):
        await ctx.send("starting server")
        await self.sv_control("start")

    # commands for ban management

    unbans_to_do = []
    unjobbans_to_do = []

    def do_unban_now(self, bans_json, unbannee, key):
        for index, i in enumerate(bans_json[key]):
            if unbannee == i["userName"]:
                bans_json[key].pop(index)
                return
        raise Exception(unbannee + " was not found in the bans file")

    @commands.command()
    async def unban(self, ctx, *, unbannee: str):
        await ctx.send(unbannee + " will be unbanned next !r")
        self.unbans_to_do.append(unbannee)

    @commands.command()
    async def unjobban(self, ctx, *, unbannee: str):
        await ctx.send(unbannee + " will be unjobbanned next !r")
        self.unjobbans_to_do.append(unbannee)

    async def modify_ban_file(self, filename, people_to_unban, key):
        with open(SERVER_HOME / "admin" / filename, "r+") as file:
            bans_json = json.load(file)
            for i in people_to_unban:
                try:
                    self.do_unban_now(bans_json, i, key)
                except Exception as e:
                    print(e)

            file.seek(0)
            json.dump(bans_json, file, indent=1)
            file.truncate()
            people_to_unban = []

    @commands.command(aliases=["r"])
    async def restart(self, ctx):
        await ctx.send("restarting server")
        await self.sv_control("stop")

        await self.modify_ban_file("banlist.json", self.unbans_to_do, "banEntries")
        await self.modify_ban_file(
            "jobBanlist.json", self.unjobbans_to_do, "jobBanEntries"
        )

        await self.sv_control("start")
