import random

from .accent import Accent


class Dyslexic(Accent):
    REPLACEMENTS = {
        # swap words with 5% chance
        r"\b(\w+?)(\s+)(\w+?)\b": lambda m: m[0]
        if random.random() < 0.95
        else f"{m[3]}{m[2]}{m[1]}",
        # swap letters with 5% chance
        # NOTE: lower() is used to let the replace function handle case
        r"[a-z]{2}": lambda m: m[0] if random.random() < 0.95 else m[0][::-1].lower(),
    }
