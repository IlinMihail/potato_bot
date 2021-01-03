import random

from .accent import Accent


class Dyslexic(Accent):
    REPLACEMENTS = {
        r"[a-z]{2}": lambda m: m[0] if random.random() < 0.90 else m[0][::-1]
    }
