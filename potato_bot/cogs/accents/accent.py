from __future__ import annotations

import re
import random

from typing import Any, Dict, Union, Callable, Optional, Sequence

from potato_bot.types import Accent as AccentABC

_ReplacementCallableType = Callable[[re.Match], Optional[str]]
_ReplacementSequenceType = Sequence[Union[Optional[str], _ReplacementCallableType]]
_ReplacementDictType = Dict[
    Union[Optional[str], _ReplacementCallableType, _ReplacementSequenceType],
    int,
]
_ReplacementType = Union[
    str,
    _ReplacementSequenceType,
    _ReplacementDictType,
]


class Accent(AccentABC):
    MESSAGE_START = r"\A(?!```)"
    MESSAGE_END = r"(?<!```)\Z"

    REPLACEMENTS: Dict[Union[re.Pattern, str], Any] = {}
    WORD_REPLACEMENTS: Dict[Union[re.Pattern, str], Any] = {}

    _registered_accents: Dict[str, Accent] = {}

    def __init_subclass__(cls, **kwargs):
        super().__init_subclass__(**kwargs)

        instance = cls()
        cls._registered_accents[str(instance).lower()] = instance

    def __init__(self):
        self._format_word_replacements()

        self._compile_map(self.REPLACEMENTS)
        self._compile_map(self.WORD_REPLACEMENTS)

    def _format_word_replacements(self):
        for key in list(self.WORD_REPLACEMENTS.keys()):
            self.WORD_REPLACEMENTS[rf"\b{key}\b"] = self.WORD_REPLACEMENTS[key]
            del self.WORD_REPLACEMENTS[key]

    @staticmethod
    def _compile_map(mapping):
        for key in list(mapping.keys()):
            mapping[re.compile(key, re.IGNORECASE)] = mapping[key]
            del mapping[key]

    @classmethod
    def all_accents(cls) -> Sequence[Accent]:
        return list(cls._registered_accents.values())

    @classmethod
    def get_by_name(cls, name: str) -> Accent:
        return cls._registered_accents[name]

    @staticmethod
    def _get_replacement(candidate: _ReplacementType, match: re.Match) -> str:
        if isinstance(candidate, str):
            return candidate

        if isinstance(candidate, Sequence):
            # sequence of equally weighted items
            maybe_function = random.choice(candidate)
        elif isinstance(candidate, dict):
            # dict of weighted items
            maybe_function = random.choices(
                list(candidate.keys()),
                list(candidate.values()),
            )[0]
        else:
            # assume callable, no check for perfomance
            maybe_function = candidate

        original = match[0]

        if maybe_function is None:
            return original

        if isinstance(maybe_function, str):
            return maybe_function

        # assume callable, no check for perfomance
        result = maybe_function(match)
        if result is None:
            return original

        return result

    def _replace(
        self, text: str, limit: int, mapping: Dict[str, _ReplacementType]
    ) -> str:
        result_len = len(text)

        def repl(match: re.Match) -> str:
            nonlocal result_len

            replacement = self._get_replacement(mapping[match.re], match)

            original = match[0]

            result_len += len(replacement) - len(original)
            if result_len > limit:
                return original

            if original.islower():
                return replacement

            if original.istitle():
                if replacement.islower():
                    # if there are some case variations better leave string untouched
                    return replacement.title()

            elif original.isupper():
                return replacement.upper()

            return replacement

        for pattern in mapping.keys():
            text = pattern.sub(repl, text)

        return text

    def apply(self, text: str, limit: int = 2000) -> str:
        text = self._replace(text, limit, self.WORD_REPLACEMENTS)

        return self._replace(text, limit, self.REPLACEMENTS)
