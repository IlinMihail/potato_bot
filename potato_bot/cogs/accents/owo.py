import random

from typing import Optional

from .accent import Accent

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
    "*wings their tail*",
    "\N{PAW PRINTS}",
)


def nya() -> Optional[str]:
    return " ".join(random.choice(NYAS) for _ in range(random.randint(1, 2)))


class OwO(Accent):
    REPLACEMENTS = {
        r"[rlv]": "w",
        r"ove": "uv",
        r"(?<!ow)o(?!wo)": {"owo": 1, None: 4},
        # do not break mentions by avoiding @
        r"(?<!@)!": lambda m: f" {random.choice(NYAS)}!",
        r"ni": "nyee",
        r"na": "nya",
        r"ne": "nye",
        r"no": "nyo",
        r"nu": "nyu",
        Accent.MESSAGE_START: {
            lambda m: f"{nya()} ": 1,
            None: 2,
        },
        Accent.MESSAGE_END: {
            lambda m: f" {nya()}": 1,
            None: 2,
        },
    }
