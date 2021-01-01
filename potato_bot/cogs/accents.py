import re
import random

from base64 import b64encode
from typing import Any, Optional, Sequence
from hashlib import sha256

from discord.ext import commands

from potato_bot.types import Accent
from potato_bot.checks import is_admin

MESSAGE_START = r"\A(?!```)"
MESSAGE_END = r"(?<!```)\Z"


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

    def nya() -> str:
        return " ".join(random.choice(OwO.NYAS) for _ in range(random.randint(1, 2)))

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
        MESSAGE_START: {
            lambda m: f"{OwO.nya()} ": 1,
            None: 2,
        },
        MESSAGE_END: {
            lambda m: f" {OwO.nya()}": 1,
            None: 2,
        },
    }


class French(Accent):
    WORD_REPLACEMENTS = {
        r"a": (
            "un",
            "une",
        ),
        r"am": "suis",
        r"and": "et",
        r"the": (
            "les",
            "la",
            "le",
        ),
        r"for": "pour",
        r"of": "de",
        r"my": (
            "mon",
            "ma",
        ),
        r"very": "très",
        r"want": "vouloir",
        r"with": "avec",
        r"i'm": "je suis",
        r"i am": "je suis",
        r"i": "je",
        r"good": "bon",
        r"bad": "mal",
        r"spicy": (
            "épicé",
            "épicée",
        ),
        r"yes": "oui",
        r"no": "non",
        r"why": "pourquoi",
        r"what'?s": "quel est",
        r"who'?s": "qui est",
        r"hello": (
            "'allô",
            "bonjour",
            "salut",
        ),
        r"bye": (
            "bon voyage",
            "adieu",
            "au revoir",
        ),
        r"thanks": "merci",
        r"assistant": "ravageur",
        r"assistants": "ravageurs",
        r"captain": "capitaine",
        r"cook": (
            "cuisinier",
            "cuisinière",
        ),
        r"enemy": (
            "silly english dog",
            "ennemi",
            "ennemie",
        ),
        r"friend": "ami",
        r"friends": "amis",
        r"greytider?": "gitans",
        r"changeling": "changeur",
        r"wizard": "sorcier",
        r"(op|operative)": "boche",
        r"(op|operative)s": "boches",
        r"cheese": (
            "brie",
            "roquefort",
            "camembert",
        ),
        r"bread": "baguette",
        r"tomato": "tomate",
        r"wine": "vin",
        r"traitor": "traitre",
        r"maint": "banlieues",
        r"nuke": (
            "grand bombe",
            "la baguette ultime",
        ),
        r"shit": "merde",
        r"urity": "urite",
        r"security": "securite",
        r"shitsec": (
            "gendarmerie",
            "keufs",
        ),
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
        r"xc": "gg",
        r"c": "g",
        r"k": "g",
        r"t": "d",
        r"p": "b",
        r"x": "gs",
        r"\Bng\b": "gn",
        r":?\)+": lambda m: f":{'D' * len(m[0]) * random.randint(1, 5)}",
        MESSAGE_END: {
            lambda m: f" :{'D' * random.randint(1, 5)}": 1,
            None: 1,
        },
    }

    WORD_REPLACEMENTS = {
        r"epic": "ebin",
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


class Base64(Accent):
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
# Is pretty bad, needs rework
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


# https://www.rbth.com/education/327126-10-steps-to-get-russian-accent
class Slav(Accent):
    WORD_REPLACEMENTS = {
        r"(fuck|shit)": (
            "blyat",
            "cyka",
        ),
        r"usa": "американские захватчики",
        r"we are being attacked": "нас атакуют",
    }

    REPLACEMENTS = {
        r"\b(a|the) +": {
            "": 1,
            None: 1,
        },
        r"r": ("r", "я"),
        r"\bha": "ga",
        r"e(?!e)": "ye",
        r"th": ("z", "g"),
        r"\Bo?u": ("a", "oo"),
        r"w": "v",
        MESSAGE_END: {
            " blyat": 1,
            None: 1,
        },
    }


class Debug(Accent):
    REPLACEMENTS = {
        r"🐛": "█",
    }


class Dyslexic(Accent):
    REPLACEMENTS = {
        r"[a-z]{2}": lambda m: m[0] if random.random() < 0.90 else m[0][::-1]
    }


# https://github.com/unitystation/unitystation/blob/cf3bfff6563f0b3d47752e19021ab145ae318736/UnityProject/Assets/Resources/ScriptableObjects/Speech/Swedish.asset
class Swedish(Accent):
    def bork(m: re.Match) -> Optional[str]:
        if random.random() > 1 / 3:
            return

        return f" Bork{', bork' * random.randint(0, 2)}!"

    REPLACEMENTS = {
        r"w": "v",
        r"j": "y",
        r"a": (
            "å",
            "ä",
            "æ",
            "a",
        ),
        r"bo": "bjo",
        r"o": (
            "ö",
            "ø",
            "o",
        ),
        MESSAGE_END: bork,
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
            ctx.bot.accents = []
        else:
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
