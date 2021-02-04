from time import perf_counter
from typing import Optional

from discord.ext import commands

from potato_bot.bot import Bot
from potato_bot.cog import Cog
from potato_bot.context import Context

POTATO_ART = r"""   ___      _        _
  / _ \___ | |_ __ _| |_ ___
 / /_)/ _ \| __/ _` | __/ _ \
/ ___/ (_) | || (_| | || (_) |
\/    \___/ \__\__,_|\__\___/"""


class CustomHelp(commands.DefaultHelpCommand):
    def get_destination(self):
        return self.context


class Meta(Cog):
    """Uncategorized commands"""

    def __init__(self, bot: Bot):
        super().__init__(bot)

        self.old_help_command = bot.help_command

        bot.help_command = CustomHelp()
        bot.help_command.cog = self

    def cog_unload(self):
        self.bot.help_command = self.old_help_command

    @commands.command(aliases=["list"])
    async def servers(self, ctx: Context, *, server_name: str = None):
        """List hub servers"""

        async with ctx.typing():
            await self._servers(ctx, server_name)

    async def _servers(self, ctx, server_name: Optional[str]):
        async with ctx.session.get("https://api.unitystation.org/serverlist") as r:
            # they send json with html mime type
            data = await r.json(content_type=None)

        servers = data["servers"]
        if not servers:
            return await ctx.send("No servers online")

        if server_name is not None:
            server_name = server_name.lower()

            for server in servers:
                if server["ServerName"].lower() == server_name:
                    break
            else:
                return await ctx.send("No servers with this name")

            # basic info
            aliases = {
                "name": "ServerName",
                "fork": "ForkName",
                "build": "BuildVersion",
                "map": "CurrentMap",
                "gamemode": "GameMode",
                "time": "IngameTime",
                "players": "PlayerCount",
                "fps": "fps",
            }
            longest_alias = len(sorted(aliases.keys(), key=lambda x: len(x))[-1])

            result = "\n".join(
                f"{alias:<{longest_alias}} : {server.get(key, 'unknown')}"
                for alias, key in aliases.items()
            )

            # compose address from 2 variables
            ip = server.get("ServerIP", "unknown")
            port = server.get("ServerPort", "unknown")

            result += f"\n{'address':<{longest_alias}} : {ip}:{port}\n"

            # downloads
            result += "\nDownloads\n"
            download_aliases = {
                "windows": "WinDownload",
                "linux": "LinuxDownload",
                "osx": "OSXDownload",
            }
            longest_download_alias = len(
                sorted(download_aliases.keys(), key=lambda x: len(x))[-1]
            )

            result += "\n".join(
                f"{alias:<{longest_download_alias}} : {server.get(key, 'unknown')}"
                for alias, key in download_aliases.items()
            )

            return await ctx.send(f"```\n{result}```")

        # sort using player count and name fields, player count is reversed and is more
        # significant
        servers.sort(key=lambda x: (-x["PlayerCount"], x["ServerName"]))
        columns = {
            "Server": "ServerName",
            "Build": "BuildVersion",
            "Players": "PlayerCount",
        }

        column_widths = {}

        for col_name, col_key in columns.items():
            longest_value = str(
                sorted(servers, key=lambda x: len(str(x[col_key])))[-1][col_key]
            )

            column_widths[col_name] = max((len(longest_value), len(col_name)))

        header = " | ".join(
            f"{col_name:<{column_widths[col_name]}}" for col_name in columns.keys()
        )
        separator = " + ".join("-" * i for i in column_widths.values())

        body = ""
        for server in servers:
            for col_name, col_key in columns.items():
                # newlines are allowed in server names
                value = str(server.get(col_key, "unknown")).replace("\n", " ")

                body += f"| {value:<{column_widths[col_name]}} "

            body += "|\n"

        await ctx.send(f"```\n| {header} |\n| {separator} |\n{body}```")

    @commands.command(aliases=["p"])
    async def ping(self, ctx: Context, *args):
        """Check bot latency"""

        start = perf_counter()
        m = await ctx.send("pinging")
        send_diff = round((perf_counter() - start) * 1000)

        latency = round(self.bot.latency * 1000)

        await m.edit(content=f"Pong, **{send_diff}ms**\n\nLatency: **{latency}ms**")

    @commands.command(aliases=["info"])
    async def about(self, ctx: Context):
        owners = [await self.bot.fetch_user(oid) for oid in self.bot.owner_ids]

        authors = f"Author{'s' if len(owners) > 1 else ''}: {', '.join(str(o) for o in owners)}"

        return await ctx.send(
            f"```\n"
            f"{POTATO_ART}\n"
            f"\n"
            f"Potato art by: patorjk.com/software/taag\n"
            f"\n"
            f"This bot was originally made for PotatoStation server for UnityStation.\n"
            f"\n"
            f"Source code: github.com/Fogapod/potato_bot\n"
            f"{authors}\n"
            f"```"
        )


def setup(bot):
    bot.add_cog(Meta(bot))
