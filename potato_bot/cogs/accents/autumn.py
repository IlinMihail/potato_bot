import random

from .accent import Accent


class Autumn(Accent):
    WORD_REPLACEMENTS = {
        r"increases?": (
            lambda m: f"go br{'r' * random.randint(1, 10)}",
            None,
        ),
        "them": "em",
        "well": "welp",
        "oh": (
            "er",
            "crap",
            None,
        ),
        "hey": "yo",
    }
    REPLACEMENTS = {
        r"t m": "mm",
        r"wh": "w",
        r"oo": "u",
        r"ng\b": (
            "n",
            "n'",
        ),
        r"'?ve been": "da",
        r"disappear": "poof",
        Accent.MESSAGE_END: {
            " ye daft cunt": 1,
            None: 50,
        },
    }
