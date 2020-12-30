import re
import random

from typing import Any, Optional, Sequence

from discord.ext import commands

from potato_bot.types import Accent
from potato_bot.checks import is_admin


class OwO(Accent):
    NYAS = (
        ":3",
        ">w<",
        "^w^",
        "uwu",
        "UwU",
        "owo",
        "OwO",
        "nya",
        "Nya",
        "nyan",
        "!!!",
        "(=^‥^=)",
        "(=；ｪ；=)",
        "ヾ(=｀ω´=)ノ”",
        "~~",
    )

    def nya(match: re.Match) -> Optional[str]:
        return f" {' '.join(random.choice(OwO.NYAS) for _ in range(random.randint(0, 2)))} "

    REPLACEMENTS = {
        r"[rlv]": "w",
        r"ove": "uv",
        r"(?<!ow)o(?!wo)": {"owo": 1, None: 4},
        # do not break mentions by avoiding @
        r"(?<!@)!": lambda m: f" {random.choice(OwO.NYAS)}!",
        r"ni": "nyee",
        r"na": "nya",
        r"ne": "nye",
        r"no": "nyo",
        r"nu": "nyu",
        r"^(?!```)": nya,
        r"(?<!```)$": nya,
    }


class French(Accent):
    WORD_REPLACEMENTS = {
        r"a": ("un", "une"),
        r"am": "suis",
        r"and": "et",
        r"bad": "mal",
        r"bye": ("bon voyage", "adieu", "au revoir"),
        r"bread": "baguette",
        r"for": "pour",
        r"good": "bon",
        r"hello": ("bonjour", "salut"),
        r"i": "je",
        r"i'm": "je suis",
        r"my": ("mon", "ma"),
        r"no": "non",
        r"of": "de",
        r"security": "securite",
        r"shit": "merde",
        r"thanks": "merci",
        r"the": ("les", "la", "le"),
        r"traitor": "collaborateur",
        r"very": "tres",
        r"want": "vouloir",
        r"with": "avec",
        r"why": "porquois",
        r"wizard": "sorcier",
        r"yes": "oui",
    }


# https://github.com/unitystation/unitystation/blob/cf3bfff6563f0b3d47752e19021ab145ae318736/UnityProject/Assets/Resources/ScriptableObjects/Speech/CustomMods/Stuttering.cs
class Stutter(Accent):
    def repeat_char(match: re.Match) -> Optional[str]:
        if random.random() > 0.8:
            return

        severity = random.randint(1, 4)

        return f"{'-'.join(match[0] for _ in range(severity))}"

    REPLACEMENTS = {
        r"\b[a-z](?=[a-z]|\s)": repeat_char,
    }


class Scotsman(Accent):
    REPLACEMENTS = {
        r"(?<!```)$": lambda m: " ye daft cunt" if random.random() > 0.5 else ""
    }


class E(Accent):
    REPLACEMENTS = {
        r"[a-z]": "e",
    }


class Spurdo(Accent):
    REPLACEMENTS = {
        r"c": "g",
        r"k": "g",
        r"t": "d",
        r"p": "b",
        r"x": "gs",
        r"(?<!```)$": {
            lambda m: f" :{'D' * random.randint(1, 5)}": 1,
            None: 1,
        },
    }

    WORD_REPLACEMENTS = {
        "epic": "ebin",
    }


# https://github.com/unitystation/unitystation/blob/cf3bfff6563f0b3d47752e19021ab145ae318736/UnityProject/Assets/Resources/ScriptableObjects/Speech/CustomMods/SlurredMod.cs
class Drunk(Accent):
    HICCBURPS = (
        "- burp... ",
        "- hic- ",
        "- hic! ",
        "- buuuurp... ",
    )

    def duplicate_char(match: re.Match) -> Optional[str]:
        if random.random() > 0.8:
            return

        severity = random.randint(1, 6)

        return match[0] * severity

    def hiccburp(match: re.Match) -> Optional[str]:
        if random.random() > 0.1:
            return

        return random.choice(Drunk.HICCBURPS)

    REPLACEMENTS = {
        r" +": hiccburp,
        r"[aeiouslnmr]": duplicate_char,
    }


class Binary(Accent):
    def char_to_binary(char: str) -> Optional[str]:
        return f"{ord(char[0]):08b} "

    REPLACEMENTS = {
        r".": char_to_binary,
    }


class Leet(Accent):
    # note:
    # \ should be avoided because it renders differently in codeblocks and normal text
    REPLACEMENTS = {
        r"a": "4",
        r"b": "6",
        # r"c": "(",
        # r"d": "[)",
        r"e": "3",
        # r"f": "]]=",
        r"g": "&",
        # r"h": "#",
        r"i": "!",
        # r"j": ",|",
        # r"k": "]{",
        r"l": "1",
        # r"m": "(√)",
        # r"n": "(']",
        r"o": "0",
        # r"p": "|°",
        # r"q": "(,)",
        # r"r": "2",
        r"s": "$",
        r"t": "7",
        # r"u": "(_)",
        # r"v": "\/",
        # r"w": "'//",
        r"x": "%",
        # r"y": "'/",
        r"z": "2",
    }


class Accents(commands.Cog):
    """Commands for managing bot accents"""

    def __init__(self, bot):
        self.bot = bot

    def cog_unload(self):
        self.bot.accents = []

    @commands.group(invoke_without_command=True, aliases=["accents"])
    async def accent(self, ctx):
        """Manage bot accents"""

        await ctx.send_help(ctx.command)

    @accent.command()
    async def list(self, ctx, *accents: Accent):
        """List available accents"""

        body = ""

        # I have no idea why this is not in stdlib, string has find method
        def sequence_find(seq: Sequence[Any], item: Any, default: int = -1) -> int:
            for i, j in enumerate(seq):
                if j == item:
                    return i

            return default

        accents = Accent.all_accents()
        for accent in sorted(
            accents,
            key=lambda a: (
                # sort by position in global accent list, leave missing at the end
                sequence_find(ctx.bot.accents, a, len(accents)),
                # sort the rest by names
                str(a).lower(),
            ),
        ):
            enabled = accent in ctx.bot.accents

            body += f"{'+' if enabled else '-'} {accent}\n"

        await ctx.send(f"Bot accents: ```\n{body}```")

    async def _update_nick(self, ctx):
        new_nick = ctx.me.name
        for accent in ctx.bot.accents:
            new_nick = accent.apply(ctx.me.name, limit=32).strip()

        await ctx.me.edit(nick=new_nick)

    @accent.command(aliases=["enable", "on"])
    @is_admin()
    async def add(self, ctx, *accents: Accent):
        """Enable accents"""

        if not accents:
            return await ctx.send("No accents provided")

        for accent in accents:
            if accent in ctx.bot.accents:
                continue

            ctx.bot.accents.append(accent)

        await self._update_nick(ctx)

        await ctx.send("Enabled accents")

    @accent.command(aliases=["disable", "off"])
    @is_admin()
    async def remove(self, ctx, *accents: Accent):
        """Disable accents

        Disables all if no accents provided
        """

        if not accents:
            accents = ctx.bot.accents

        for accent in accents:
            if accent not in ctx.bot.accents:
                continue

            ctx.bot.accents.remove(accent)

        await self._update_nick(ctx)

        await ctx.send("Disabled accents")

    @accent.command()
    async def use(self, ctx, accent: Accent, *, text: str):
        """Apply specified accent to text"""

        await ctx.send(text, accents=[accent])

    @commands.command()
    async def owo(self, ctx):
        """OwO what's this"""

        owo = await Accent.convert(ctx, "owo")
        if owo in ctx.bot.accents:
            ctx.bot.accents.remove(owo)
        else:
            ctx.bot.accents.append(owo)

        await self._update_nick(ctx)

        await ctx.send("owo toggled")


def setup(bot):
    bot.add_cog(Accents(bot))
