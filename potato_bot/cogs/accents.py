import re
import random

from base64 import b64encode
from typing import Any, Optional, Sequence
from hashlib import sha256

from discord.ext import commands

from potato_bot.types import Accent
from potato_bot.checks import is_admin

MESSAGE_START = r"^\s*(?!```)"
MESSAGE_END = r"(?<!```)\s*$"


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
        MESSAGE_START: nya,
        MESSAGE_END: nya,
    }


class French(Accent):
    WORD_REPLACEMENTS = {
        r"a": ("un", "une"),
        r"am": "suis",
        r"and": "et",
        r"the": ("les", "la", "le"),
        r"for": "pour",
        r"of": "de",
        r"my": ("mon", "ma"),
        r"very": "tres",
        r"want": "vouloir",
        r"with": "avec",
        r"i'm": "je suis",
        r"i am": "je suis",
        r"i": "je",
        r"good": "bon",
        r"bad": "mal",
        r"yes": "oui",
        r"no": "non",
        r"why": "porquois",
        r"hello": ("bonjour", "salut"),
        r"bye": ("bon voyage", "adieu", "au revoir"),
        r"wizard": "sorcier",
        r"bread": "baguette",
        r"traitor": "collaborateur",
        r"shit": "merde",
        r"thanks": "merci",
        r"security": "securite",
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
        MESSAGE_END: lambda m: " ye daft cunt" if random.random() > 0.5 else ""
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
        MESSAGE_END: {
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


class Based64(Accent):
    REPLACEMENTS = {
        r"[\s\S]+": lambda m: b64encode(m[0].encode()).decode(),
    }


class SHA256(Accent):
    REPLACEMENTS = {
        r"[\s\S]+": lambda m: sha256(m[0].encode()).hexdigest(),
    }


class Reversed(Accent):
    REPLACEMENTS = {
        r".+": lambda m: m[0][::-1],
    }


# https://en.m.wikipedia.org/wiki/Texan_English
# https://lingojam.com/CowboyTalkTranslator
class Cowboy(Accent):
    def yeehaw(chance: float) -> Optional[str]:
        if random.random() > chance:
            return

        return f"y{'e'* random.randint(1,6)}haw"

    REPLACEMENTS = {
        r"\bo\B": "aw",
        # "the" excluded
        r"\b(th|t)(?!h?e\b)\B": "'",
        r"\Bng\b": "n'",
        r"\Bd\b": "",
        r"\Bht\b": "hyt",
        # exclude "hey"
        r"\B(?<!\bh)ey\b": "ay",
        r"(?<=g)r\B": "uh-r",
        r"(?<!h-)re": "hr",
        MESSAGE_END: lambda m: f" {Cowboy.yeehaw(1.0)}",
    }
    WORD_REPLACEMENTS = {
        r"the": "thuh",
        r"hey": ("heya", "ee", "hay"),
        r"you": ("cha", "chu", "ya"),
        r"buzzard": "vulture",
        r"dogie": "calf",
        r"about to": "fixin' to",
        r"(hello|hi|how do you do)": "howdy",
        r"you all": "y'all",
        r"bull": "toro",
        r"(freezer|refrigerator)": "ice box",
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
