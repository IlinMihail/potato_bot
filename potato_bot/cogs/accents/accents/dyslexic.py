from .accent import Accent


class Dyslexic(Accent):
    REPLACEMENTS = {
        # swap words with 5% chance
        r"\b(\w+?)(\s+)(\w+?)\b": {
            lambda m: f"{m.match[3]}{m.match[2]}{m.match[1]}": 0.05,
        },
        # swap letters with 5% chance
        # NOTE: lower() is used to let the replace function handle case
        r"[a-z]{2}": {
            lambda m: m.original[::-1].lower(): 0.05,
        },
    }
