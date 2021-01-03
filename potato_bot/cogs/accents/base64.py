from base64 import b64encode

from .accent import Accent


class Base64(Accent):
    REPLACEMENTS = {
        r"[\s\S]+": lambda m: b64encode(m[0].encode()).decode(),
    }
