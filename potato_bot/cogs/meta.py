import asyncio

from discord.ext import commands

from potato_bot.bot import Bot
from potato_bot.utils import run_process
from potato_bot.checks import is_admin


class CustomHelp(commands.DefaultHelpCommand):
    def get_destination(self):
        return self.context


class Meta(commands.Cog):
    def __init__(self, bot: Bot):
        self.bot = bot
        self.old_help_command = bot.help_command

        bot.help_command = CustomHelp()
        bot.help_command.cog = self

    def cog_unload(self):
        self.bot.help_command = self.old_help_command

    @commands.command(aliases=["list"])
    async def servers(self, ctx, *, server_name: str = None):
        """List hub servers"""

        async with ctx.bot.session.get("https://api.unitystation.org/serverlist") as r:
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

    @commands.command()
    async def fig(self, ctx, *, text):
        """Big ASCII characters"""

        result = await run_process("figlet", "-d", "/home/potato/font", *text.split())
        stdout = result[0].rstrip()[:1994]
        await ctx.send(f"```{stdout}```")

    @commands.command()
    async def mem(self, ctx):
        """Get memory usage (free -h)"""

        result = await run_process("free", "-h")

        await ctx.send(f"mem is ```{result[0]}```")

    @commands.command()
    @is_admin()
    async def memspam(self, ctx):
        """Like mem but updates"""

        initial = await ctx.send("fetching")
        for _ in range(100):
            await asyncio.sleep(1)

            result = await run_process("free", "-h")
            await initial.edit(content=f"mem is ```{result[0]}```")

    @commands.command(aliases=["st"])
    async def status(self, ctx):
        """Prints status of server"""

        result = await run_process("sudo", "supervisorctl", "status", "serpot")

        await ctx.send(f"```{result[0]}```")

    @commands.command(aliases=["p"])
    async def ping(self, ctx, *args):
        await ctx.send(f"{' '.join(reversed(args))} pong{ctx.prefix}")


def setup(bot):
    bot.add_cog(Meta(bot))
