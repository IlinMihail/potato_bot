from __future__ import annotations

import re
import random

from typing import Any, Dict, Sequence

from discord.ext import commands

from .context import PotatoContext


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

    ENDINGS: Sequence[str] = ()
    ACCCENT_MAP: Dict[str, Any] = {}

    def __init_subclass__(cls, **kwargs):
        super().__init_subclass__(**kwargs)

        instance = cls()
        cls._registered_accents[str(instance).lower()] = instance

    def __init__(self):
        self._prepare_data()

    def _prepare_data(self):
        for key in list(self.ACCCENT_MAP.keys()):
            self.ACCCENT_MAP[re.compile(key, re.IGNORECASE)] = self.ACCCENT_MAP[key]
            del self.ACCCENT_MAP[key]

    @classmethod
    def all_accents(cls) -> Sequence[Accent]:
        return cls._registered_accents.values()

    @classmethod
    async def convert(cls, ctx: PotatoContext, argument: str) -> Accent:
        prepared = argument.lower().replace(" ", "_")
        try:
            return cls._registered_accents[prepared]
        except KeyError:
            raise commands.BadArgument("Accent does not exist")

    def _replace(self, text: str, mapping: Dict[str, str], limit: int) -> str:
        result_len = len(text)

        def repl(match: re.Match) -> str:
            nonlocal result_len

            original = match[0]

            replacement = mapping[match.re]
            if not isinstance(replacement, str):
                if isinstance(replacement, dict):
                    replacement = random.choices(
                        list(replacement.keys()),
                        list(replacement.values()),
                    )[0]

                    # special value
                    if replacement is None:
                        return original
                else:  # assume sequence, no checks for perfomance
                    replacement = random.choice(replacement)

            result_len += len(replacement) - len(original)
            if result_len > limit:
                return original

            if original.islower():
                return replacement.lower()
            elif original.isupper():
                return replacement.upper()

            return replacement

        for pattern in mapping.keys():
            text = re.sub(pattern, repl, text, re.IGNORECASE)

        return text

    def _add_endings(self, text: str) -> str:
        if not self.ENDINGS:
            return text

        for _ in range(random.randint(0, 2)):
            text += f" {random.choice(self.ENDINGS)}"

        return text

    def apply(self, text: str, endings: bool = True, limit: int = 2000) -> str:
        replaced = self._replace(text, self.ACCCENT_MAP, limit)

        if not endings:
            return replaced

        return self._add_endings(replaced)

    def __str__(self) -> str:
        return self.__class__.__name__
