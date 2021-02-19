import random

from typing import Optional

from .accent import Match, Accent

HICCBURPS = (
    "- burp... ",
    "- hic- ",
    "- hic! ",
    "- buuuurp... ",
)


def duplicate_char(match: Match) -> Optional[str]:
    if random.random() > 0.8:
        return
    severity = random.randint(1, 6)

    return match.original * severity


def hiccburp(match: Match) -> Optional[str]:
    if random.random() > 0.1:
        return

    return random.choice(HICCBURPS)


# https://github.com/unitystation/unitystation/blob/cf3bfff6563f0b3d47752e19021ab145ae318736/UnityProject/Assets/Resources/ScriptableObjects/Speech/CustomMods/SlurredMod.cs
class Drunk(Accent):
    REPLACEMENTS = {
        r" +": hiccburp,
        r"[aeiouslnmr]": duplicate_char,
    }
