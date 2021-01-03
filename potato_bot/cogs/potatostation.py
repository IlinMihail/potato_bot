import json
import asyncio

import discord

from discord.ext import commands

from potato_bot.utils import run_process
from potato_bot.checks import is_admin
from potato_bot.constants import SERVER_HOME


class PotatoStation(commands.Cog):
    """PotatoStation UnityStation server management and info"""

    def __init__(self, bot):
        self.bot = bot

    @commands.command()
    @is_admin()
    async def ahelp(self, ctx, *, text):
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

    @commands.group(invoke_without_command=True, aliases=["sv"])
    async def server(self, ctx):
        """Manage and get PotatoStation info"""

        await ctx.send_help(ctx.command)

    @server.command()
    @is_admin()
    async def stop(self, ctx):
        """Stop server"""

        async with ctx.typing():
            await self.stop_server()
            await ctx.ok()

    @server.command()
    @is_admin()
    async def start(self, ctx):
        """Start server. Does not trigger unbans"""

        async with ctx.typing():
            await self.start_server()
            await ctx.ok()

    async def stop_server(self):
        return await self.sv_control("stop")

    async def start_server(self):
        return await self.sv_control("start")

    @server.command(aliases=["r"])
    @is_admin()
    async def restart(self, ctx):
        """Restart server. Triggers unbans"""

        async with ctx.typing():
            await self._restart(ctx)

    async def _restart(self, ctx):
        await self.stop_server()

        bans_cog = self.bot.get_cog("Bans")
        unbanned = await bans_cog.do_unbans()
        job_unbanned = await bans_cog.do_job_unbans()

        await self.start_server()
        await ctx.ok()

        nl = "\n"

        if unbanned:
            await ctx.send(f"Unbanned:\n{nl.join(unbanned)}")

        if job_unbanned:
            await ctx.send(f"Unbanned from jobs:\n{nl.join(job_unbanned)}")

    @server.command(aliases=["st"])
    async def status(self, ctx):
        """Get status of server"""

        result = await run_process("sudo", "supervisorctl", "status", "serpot")

        await ctx.send(f"```{result[0]}```")

    @commands.command()
    async def mem(self, ctx):
        """Get server memory info (free -h)"""

        result = await run_process("free", "-h")

        await ctx.send(f"```\n{result[0]}```")

    @commands.command(aliases=["spammem"])
    @is_admin()
    async def memspam(self, ctx):
        """Like mem but updates"""

        initial = await ctx.send("fetching")
        for _ in range(100):
            await asyncio.sleep(1)

            result = await run_process("free", "-h")
            await ctx.edit(initial, content=f"```\n{result[0]}```")

    @server.command(aliases=["cn"])
    @is_admin()
    async def changename(self, ctx, *, name):
        """Change the name of the server on the StationHub"""
        if len(name) < 5 or len(name) > 60 or not name.isascii():
            await ctx.send(
                "The server name should be between 5 and 60 characters, and should be fully ascii"
            )
            return
        with open(SERVER_HOME / "config" / "config.json", "r+") as sv_config:
            sv_config_json = json.load(sv_config)
            sv_config_json["ServerName"] = name
            sv_config.seek(0)
            json.dump(sv_config_json, sv_config)
            sv_config.truncate()


def setup(bot):
    bot.add_cog(PotatoStation(bot))
