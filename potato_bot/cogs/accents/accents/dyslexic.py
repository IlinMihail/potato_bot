import random

from .accent import Accent


class Dyslexic(Accent):
    REPLACEMENTS = {
        # swap words with 5% chance
        r"\b(\w+?)(\s+)(\w+?)\b": lambda m: m.original
        if random.random() < 0.95
        else f"{m.match[3]}{m.match[2]}{m.match[1]}",
        # swap letters with 5% chance
        # NOTE: lower() is used to let the replace function handle case
        r"[a-z]{2}": lambda m: m.original
        if random.random() < 0.95
        else m.original[::-1].lower(),
    }
