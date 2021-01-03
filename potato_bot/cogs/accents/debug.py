from .accent import Accent


class Debug(Accent):
    REPLACEMENTS = {
        r"🐛": "█",
    }
