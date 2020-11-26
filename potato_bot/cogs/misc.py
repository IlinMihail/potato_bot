import asyncio

from aiohttp import ClientSession
from discord.ext import commands

from potato_bot.utils import run_process
from potato_bot.checks import is_techadmin


class Misc(commands.Cog):
    @commands.command()
    async def serverlist(self, ctx):
        """List hub servers"""

        async with ClientSession() as sess:
            async with sess.get("https://api.unitystation.org/serverlist") as r:
                # they send json with html mime type
                data = await r.json(content_type=None)

        result = "\n".join(
            f"{i['ServerName']}- playercount:{i['PlayerCount']}- Fork is {i['ForkName']}- Build is {i['BuildVersion']}- Fps:{i['fps']}"
            for i in data["servers"]
        )
        await ctx.send(f"```{result}```")

    @commands.command()
    async def fig(self, ctx, *, text):
        """Big ASCII characters"""

        result = await run_process("figlet", *text.split())
        stdout = result[0].rstrip()[:1994]
        await ctx.send(f"```{stdout}```")

    @commands.command()
    async def mem(self, ctx):
        """Get memory usage (free -h)"""

        result = await run_process("free", "-h")

        await ctx.send(f"mem is ```{result[0]}```")

    @commands.command()
    @is_techadmin()
    async def memspam(self, ctx):
        """Like mem but updates"""

        initial = await ctx.send("fetching")
        for _ in range(100):
            await asyncio.sleep(1)

            result = await run_process("free", "-h")
            await initial.edit(content=f"mem is ```{result[0]}```")
