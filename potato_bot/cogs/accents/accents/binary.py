from typing import Any

from .accent import Accent


class Binary(Accent):
    def apply(self, text: str, *, severity: int = 1, **kwargs: Any) -> str:
        if severity >= 1:
            return "".join(f"{ord(c):08b} " for c in text)

        return text
