from .accent import Accent


class Slav(Accent):
    WORD_REPLACEMENTS = {
        r"my": "our",
        r"friend": "comrade",
        r"(enemy|foe)": "american pig",
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
        r"\bha": "ga",
        r"e(?!e)": "ye",
        r"th": ("z", "g"),
        r"\Bo?u": ("a", "oo"),
        r"w": "v",
        Accent.MESSAGE_END: {
            " blyat": 1,
            None: 1,
        },
    }
