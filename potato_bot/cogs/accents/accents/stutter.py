import random

from typing import Optional

from .accent import Match, Accent


# https://github.com/unitystation/unitystation/blob/cf3bfff6563f0b3d47752e19021ab145ae318736/UnityProject/Assets/Resources/ScriptableObjects/Speech/CustomMods/Stuttering.cs
class Stutter(Accent):
    def repeat_char(match: Match) -> Optional[str]:
        if random.random() > 0.8:
            return

        severity = random.randint(1, 4)

        return f"{'-'.join(match.original for _ in range(severity))}"

    REPLACEMENTS = {
        r"\b[a-z](?=[a-z]|\s)": repeat_char,
    }
