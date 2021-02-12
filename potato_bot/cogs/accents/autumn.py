import re
import random

from .accent import Accent


def brrrr(m: re.Match):
    forms_of_go = (
        ("e", "go"),
        ("es", "goes"),
        ("ed", "went"),
        ("ing", "going"),
    )
    for ending, _go_form in forms_of_go:
        if m[0].lower().endswith(ending):
            break
    else:
        _go_form = forms_of_go[0][1]

    return f"{_go_form} br{'r' * random.randint(1, 10)}"


class Autumn(Accent):
    WORD_REPLACEMENTS = {
        r"increas[a-z]+": (
            lambda m: brrrr(m),
            None,
        ),
        "them": "em",
        "well": "welp",
        "oh": (
            "er",
            None,
        ),
        "hey": "yo",
        "because": "cause",
        "let me": "lemme",
    }
    REPLACEMENTS = {
        # "who" does not work well with this
        r"\bwh(?!o)": "w",
        r"\bth": {"d": 1, None: 4},
        r"oo": "u",
        # !!contextual syntax is hell!!
        # I'm not sure how to describe this rule universally yet
        # some examples:
        # + something
        # + nothing
        # + doing
        # - thing
        # - wrong
        #
        # blacklisting all bad examples for now
        r"(?<!\b(?:thi|wro))ng\b": (
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
