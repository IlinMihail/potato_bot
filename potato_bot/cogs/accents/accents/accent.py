from __future__ import annotations

import re
import random
import itertools

from typing import Any, Dict, Union, Callable, Optional, Sequence


class ReplacementContext:
    __slots__ = (
        "position",
        "data",
    )

    def __init__(self, position: int = 0, data: Any = None):
        self.position = position
        self.data = data

    def __repr__(self) -> str:
        return f"<{type(self).__name__} position={self.position} data={self.data}>"


class Match:
    __slots__ = (
        "match",
        "severity",
        "context",
    )

    def __init__(self, *, match: re.Match, severity: int, context: ReplacementContext):
        self.match = match
        self.severity = severity
        self.context = context

    @property
    def original(self):
        return self.match[0]

    def __repr__(self) -> str:
        return f"<{type(self).__name__} match={self.match} severity={self.severity} context={self.context}>"


_ReplacedType = Optional[str]
_ReplacementCallableType = Callable[[Match, int], _ReplacedType]
_ReplacementSequenceType = Sequence[Union[_ReplacedType, _ReplacementCallableType]]
_ReplacementDictType = Dict[
    Union[_ReplacedType, _ReplacementCallableType, _ReplacementSequenceType],
    int,
]
_ReplacementType = Union[
    str,
    _ReplacementSequenceType,
    _ReplacementDictType,
]


class Severity:
    pass


class Replacement:
    __slots__ = (
        "pattern",
        "callback",
    )

    def __init__(
        self, pattern: str, replacement: _ReplacementType, flags: Any = re.IGNORECASE
    ):
        self.pattern = re.compile(pattern, flags)

        self.callback = self._get_callback(replacement)

    def _get_callback(self, replacement: _ReplacementType) -> _ReplacementCallableType:
        if isinstance(replacement, str):

            def callback_static(match: Match):
                return replacement

            return callback_static

        elif isinstance(replacement, Sequence):
            # sequence of equally weighted items
            def callback_select_equal(match: Match) -> _ReplacedType:
                selected = random.choice(replacement)

                if isinstance(selected, str) or selected is None:
                    return selected

                return selected(match)

            return callback_select_equal

        elif isinstance(replacement, dict):
            # dict of weighted items
            keys = [*replacement.keys()]
            values = [*replacement.values()]

            computable_weights = []
            for i, v in enumerate(values):
                if not isinstance(v, (int, float)):
                    # assume is a callable
                    # TODO: proper check
                    computable_weights.append((i, v))

                    # compute for severity 1, fail early for ease of debugging
                    # also cleans values list from functions
                    values[i] = v(1)

            if not computable_weights:
                # inject None if total weight is < 1 for convenience
                # example: {"a": 0.25, "b": 0.5} -> {"a": 0.25, "b": 0.5, None: 0.25}
                if (values_sum := sum(values)) < 1:
                    keys.append(None)
                    values.append(1 - values_sum)

            # is only useful when there are no computable weights
            # computed as early optimization
            # https://docs.python.org/3/library/random.html#random.choices
            cum_weights = list(itertools.accumulate(values))

            def callback_select_weighted(match: Match) -> _ReplacedType:
                if computable_weights:
                    for index, fn in computable_weights:
                        # NOTE: is this racy? without threads it's fine I guess
                        values[index] = fn(match.severity)

                    selected = random.choices(keys, weights=values)[0]
                else:
                    selected = random.choices(keys, cum_weights=cum_weights)[0]

                if isinstance(selected, str) or selected is None:
                    return selected

                return selected(match)

            return callback_select_weighted
        else:
            # assume callable
            # TODO: check
            return replacement

    def apply(
        self, text: str, *, severity: int, limit: int, context: ReplacementContext
    ) -> str:
        result_len = len(text)

        def repl(match: re.Match) -> str:
            nonlocal result_len

            original = match[0]

            replacement = self.callback(
                Match(match=match, severity=severity, context=context)
            )
            if replacement is None:
                return original

            result_len += len(replacement) - len(original)
            if result_len > limit:
                return original

            context.position += 1

            if original.islower():
                return replacement

            if original.istitle():
                if replacement.islower():
                    # if there are some case variations better leave string untouched
                    return replacement.title()

            elif original.isupper():
                return replacement.upper()

            return replacement

        return self.pattern.sub(repl, text)

    def __repr__(self) -> str:
        return f"<{type(self).__name__} {self.pattern} => {self.callback}>"


class Accent:
    # public variables
    # shortcuts for common regexes
    MESSAGE_START = r"\A(?!```)"
    MESSAGE_END = r"(?<!```)\Z"

    # special value showing that chance depends on severity
    SEVERITY = Severity()

    # overridable variables
    WORD_REPLACEMENTS: Dict[Union[re.Pattern, str], Any] = {}
    REPLACEMENTS: Dict[Union[re.Pattern, str], Any] = {}

    # private class variables
    _registered_accents: Dict[str, Accent] = {}

    def __init_subclass__(cls, is_accent: bool = True, **kwargs: Any):
        super().__init_subclass__(**kwargs)

        if is_accent:
            instance = cls()
            cls._registered_accents[str(instance).lower()] = instance

    def __init__(self):
        self._replacemtns: Sequence[Replacement] = []

        for k, v in self.WORD_REPLACEMENTS.items():
            self._replacemtns.append(Replacement(rf"\b{k}\b", v))

        for k, v in self.REPLACEMENTS.items():
            self._replacemtns.append(Replacement(k, v))

    @classmethod
    def all_accents(cls) -> Sequence[Accent]:
        return list(cls._registered_accents.values())

    @classmethod
    def get_by_name(cls, name: str) -> Accent:
        return cls._registered_accents[name.lower()]

    def apply(
        self,
        text: str,
        *,
        severity: int = 1,
        limit: int = 2000,
        context_data: Any = None,
    ) -> str:
        if severity >= 1:
            context = ReplacementContext(data=context_data)
            for replacement in self._replacemtns:
                text = replacement.apply(
                    text,
                    severity=severity,
                    limit=limit,
                    context=context,
                )

        return text

    def __str__(self) -> str:
        return self.__class__.__name__
