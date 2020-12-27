import os
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
        await self.stop_server()

    @commands.command()
    async def start(self, ctx):
        await ctx.send("starting server")
        await self.start_server()

    async def stop_server(self):
        return await self.sv_control("stop")

    async def start_server(self):
        return await self.sv_control("start")

    @commands.command(aliases=["r"])
    async def restart(self, ctx):
        await ctx.send("restarting server")

        await self.stop_server()

        bans_cog = self.bot.get_cog("Bans")
        unbanned = await bans_cog.do_unbans()
        job_unbanned = await bans_cog.do_job_unbans()

        await self.start_server()

        nl = "\n"

        if unbanned:
            await ctx.send(f"Unbanned:\n{nl.join(unbanned)}")

        if job_unbanned:
            await ctx.send(f"Unbanned from jobs:\n{nl.join(job_unbanned)}")


def setup(bot):
    bot.add_cog(AdminTools(bot))
