from __future__ import annotations

import re
import random

from typing import Any, Dict, Union, Callable, Optional, Sequence

from discord.ext import commands

from .context import PotatoContext

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


class Job:
    # https://github.com/unitystation/unitystation/blob/699415ef6238f2135aac7f02b253c486a71a4473/UnityProject/Assets/Scripts/Systems/Occupations/JobType.cs#L12-L67
    jobs = {
        "NULL": 0,
        "AI": 1,
        "ASSISTANT": 2,
        "ATMOSTECH": 3,
        "BARTENDER": 4,
        "BOTANIST": 5,
        "CAPTAIN": 6,
        "CARGOTECH": 7,
        "CHAPLAIN": 8,
        "CHEMIST": 9,
        "CHIEF_ENGINEER": 10,
        "CIVILIAN": 11,
        "CLOWN": 12,
        "CMO": 13,
        "COOK": 14,
        "CURATOR": 15,
        "CYBORG": 16,
        "DETECTIVE": 17,
        "DOCTOR": 18,
        "ENGSEC": 19,
        "ENGINEER": 20,
        "GENETICIST": 21,
        "HOP": 22,
        "HOS": 23,
        "JANITOR": 24,
        "LAWYER": 25,
        "MEDSCI": 26,
        "MIME": 27,
        "MINER": 28,
        "QUARTERMASTER": 29,
        "RD": 30,
        "ROBOTICIST": 31,
        "SCIENTIST": 32,
        "SECURITY_OFFICER": 33,
        "VIROLOGIST": 34,
        "WARDEN": 35,
        "SYNDICATE": 36,
        "CENTCOMM_OFFICER": 37,
        "CENTCOMM_INTERN": 38,
        "CENTCOMM_COMMANDER": 39,
        "DEATHSQUAD": 40,
        "ERT_COMMANDER": 41,
        "ERT_SECURITY": 42,
        "ERT_MEDIC": 43,
        "ERT_ENGINEER": 44,
        "ERT_CHAPLAIN": 45,
        "ERT_JANITOR": 46,
        "ERT_CLOWN": 47,
        "TRAITOR": 48,
        "CARGONIAN": 49,
        "PRISONER": 50,
        "FUGITIVE": 51,
        "PARAMEDIC": 52,
        "PSYCHIATRIST": 53,
        "WIZARD": 54,
        "BLOB": 55,
    }

    reverse_jobs_map = {v: k for k, v in jobs.items()}

    def __init__(self, id: int):
        self.id = id
        self.name = self.reverse_jobs_map.get(id, "Unknown")

    @classmethod
    async def convert(cls, ctx: PotatoContext, argument: str):
        if argument.isdigit():
            return cls(int(argument))

        prepared = argument.upper().replace(" ", "_")
        if (id := cls.jobs.get(prepared)) is None:
            raise commands.BadArgument(
                "Job with this name does not exist. Try using id instead"
            )

        return cls(id)

    def __str__(self) -> str:
        return f"{self.name}[{self.id}]"


class UserID(str):
    @classmethod
    async def convert(cls, ctx: PotatoContext, argument: str) -> str:
        if len(argument) != 28:
            raise commands.BadArgument(
                f"User ID must be exactly 28 characters long, got {len(argument)}"
            )

        return argument


class Accent:
    _registered_accents: Dict[str, Accent] = {}

    REPLACEMENTS: Dict[Union[re.Pattern, str], Any] = {}
    WORD_REPLACEMENTS: Dict[Union[re.Pattern, str], Any] = {}

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
    async def convert(cls, ctx: PotatoContext, argument: str) -> Accent:
        prepared = argument.lower().replace(" ", "_")
        try:
            return cls._registered_accents[prepared]
        except KeyError:
            raise commands.BadArgument("Accent does not exist")

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
                if original.islower():
                    # if there are some case variations better leave string untouched
                    return replacement.title()

            elif original.isupper():
                return replacement.upper()

            return replacement

        for pattern in mapping.keys():
            text = pattern.sub(repl, text)

        return text

    def apply(self, text: str, limit: int = 2000) -> str:
        text = self._replace(text, limit, self.REPLACEMENTS)

        return self._replace(text, limit, self.WORD_REPLACEMENTS)

    def __str__(self) -> str:
        return self.__class__.__name__
