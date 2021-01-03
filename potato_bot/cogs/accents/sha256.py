from hashlib import sha256

from .accent import Accent


class SHA256(Accent):
    REPLACEMENTS = {
        r"[\s\S]+": lambda m: sha256(m[0].encode()).hexdigest(),
    }
