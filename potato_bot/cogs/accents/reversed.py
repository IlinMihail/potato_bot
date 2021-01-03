from .accent import Accent


class Reversed(Accent):
    REPLACEMENTS = {
        r".+": lambda m: m[0][::-1],
    }
