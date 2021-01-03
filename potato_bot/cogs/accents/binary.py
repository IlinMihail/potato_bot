import re

from typing import Optional

from .accent import Accent


class Binary(Accent):
    def char_to_binary(match: re.Match) -> Optional[str]:
        return f"{ord(match[0]):08b} "

    REPLACEMENTS = {
        r".": char_to_binary,
    }
