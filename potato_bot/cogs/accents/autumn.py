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
        "because": "cause",
    }
    REPLACEMENTS = {
        r"t m": "mm",
        # "who" does not work well with this
        r"\bwh(?!o)": "w",
        r"\bth": {"d": 1, None: 4},
        r"oo": "u",
        # !!contextual syntax is hell!!
        # I'm not yet sure how to describe this rule universally yet
        # some examples:
        # + something
        # + nothing
        # + doing
        # - thing
        #
        # blacklisting "thing" for now
        r"(?<!\bthi)ng\b": (
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
