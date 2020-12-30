import re
import random

from discord.ext import commands

from potato_bot.types import Accent
from potato_bot.checks import is_admin


class OwO(Accent):
    ENDINGS = (
        "OwO",
        "Nya",
        "owo",
        "nya",
        "nyan",
        "!!!",
        "(=^‥^=)",
        "(=；ｪ；=)",
        "ヾ(=｀ω´=)ノ”",
        "(p`ω´) q",
        "ฅ(´-ω-`)ฅ",
        "~",
        "~~",
    )
    REPLACEMENTS = {
        r"r": "w",
        r"l": "w",
        r"v": "w",
        r"ove": "uv",
        r"o": {"owo": 1, None: 4},
        r"!": "! owo ",
        r"ni": "nyee",
        r"na": "nya",
        r"ne": "nye",
        r"no": "nyo",
        r"nu": "nyu",
    }


class French(Accent):
    REPLACEMENTS = {
        r"\ba\b": ("un", "une"),
        r"\bam\b": "suis",
        r"\band\b": "et",
        r"\bbad\b": "mal",
        r"\bbye\b": ("bon voyage", "adieu", "au revoir"),
        r"\bbread\b": "baguette",
        r"\bfor\b": "pour",
        r"\bgood\b": "bon",
        r"\bhello\b": ("bonjour", "salut"),
        r"\bi\b": "je",
        r"\bi'm\b": "je suis",
        r"\bmy\b": ("mon", "ma"),
        r"\bno\b": "non",
        r"\bof\b": "de",
        r"\bsecurity\b": "securite",
        r"\bshit\b": "merde",
        r"\bthanks\b": "merci",
        r"\bthe\b": ("les", "la", "le"),
        r"\btraitor\b": "collaborateur",
        r"\bvery\b": "tres",
        r"\bwant\b": "vouloir",
        r"\bwith\b": "avec",
        r"\bwhy\b": "porquois",
        r"\bwizard\b": "sorcier",
        r"\byes\b": "oui",
    }


class Stutter(Accent):
    # https://github.com/unitystation/unitystation/blob/cf3bfff6563f0b3d47752e19021ab145ae318736/UnityProject/Assets/Resources/ScriptableObjects/Speech/CustomMods/Stuttering.cs
    def repet_char(match: re.Match) -> str:
        if random.random() > 0.8:
            return match[0]

        severity = random.randint(1, 4)
        return f"{'-'.join(match[0] for _ in range(severity))}"

    REPLACEMENTS = {
        r"\b[a-z](?=[a-z]|\s)": repet_char,
    }


class Accents(commands.Cog):
    """Commands for managing bot accents"""

    def __init__(self, bot):
        self.bot = bot

    async def cog_unload(self):
        self.bot.accents = []

    @commands.group(invoke_without_command=True)
    async def accent(self, ctx):
        """Manage bot accents"""

        await ctx.send_help(ctx.command)

    @accent.command()
    async def list(self, ctx, *accents: Accent):
        """List available accents"""

        body = ""
        for accent in Accent.all_accents():
            enabled = accent in ctx.bot.accents

            body += f"{'+' if enabled else '-'} {accent}\n"

        await ctx.send(f"Bot accents: ```\n{body}```")

    @accent.command(aliases=["enable", "on"])
    @is_admin()
    async def add(self, ctx, *accents: Accent):
        """Enable accent"""

        for accent in accents:
            if accent in ctx.bot.accents:
                continue

            ctx.bot.accents.append(accent)

        await ctx.send("Enabled accents")

    @accent.command(aliases=["disable", "off"])
    @is_admin()
    async def remove(self, ctx, *accents: Accent):
        """Disable accent"""

        for accent in accents:
            if accent not in ctx.bot.accents:
                continue

            ctx.bot.accents.remove(accent)

        await ctx.send("Disabled accents")

    @accent.command()
    async def use(self, ctx, accent: Accent, *, text: str):
        """Apply specified accent to text"""

        await ctx.send(accent.apply(text), accents=None)

    @commands.command()
    async def owo(self, ctx):
        """OwO what's this"""

        owo = await Accent.convert(ctx, "owo")
        if owo in ctx.bot.accents:
            ctx.bot.accents.remove(owo)
        else:
            ctx.bot.accents.append(owo)

        await ctx.send("owo toggled")


def setup(bot):
    bot.add_cog(Accents(bot))
