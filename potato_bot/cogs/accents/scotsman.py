import random

from .accent import Accent


class Scotsman(Accent):
    REPLACEMENTS = {
        Accent.MESSAGE_END: lambda m: " ye daft cunt" if random.random() > 0.5 else ""
    }
