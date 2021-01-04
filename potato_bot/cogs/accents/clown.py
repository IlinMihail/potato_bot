import random

from .accent import Accent


# https://github.com/unitystation/unitystation/blob/cf3bfff6563f0b3d47752e19021ab145ae318736/UnityProject/Assets/Resources/ScriptableObjects/Speech/Clown.asset
class Clown(Accent):
    REPLACEMENTS = {
        r"[a-z]": lambda m: m[0].upper(),
        Accent.MESSAGE_END: lambda m: f"{' HONK' * random.randint(1, 4)}!",
    }
