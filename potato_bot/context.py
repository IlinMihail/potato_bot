import re
import random

from typing import Any, Dict, Union, Optional

import discord

from discord.ext import commands

from .db import DB
from .response import MessageResponse, ReactionResponse


# https://github.com/Rapptz/discord.py/blob/5d75a0e7d613948245d1eb0353fb660f4664c9ed/discord/message.py#L56
def convert_emoji_reaction(emoji):
    if isinstance(emoji, discord.Reaction):
        emoji = emoji.emoji

    if isinstance(emoji, discord.Emoji):
        return "%s:%s" % (emoji.name, emoji.id)
    if isinstance(emoji, discord.PartialEmoji):
        return emoji._as_reaction()
    if isinstance(emoji, str):
        # Reactions can be in :name:id format, but not <:name:id>.
        # No existing emojis have <> in them, so this should be okay.
        return emoji.strip("<>")

    raise discord.errors.InvalidArgument(
        "emoji argument must be str, Emoji, or Reaction not {.__class__.__name__}.".format(
            emoji
        )
    )


# https://github.com/unitystation/unitystation/blob/cf3bfff6563f0b3d47752e19021ab145ae318736/UnityProject/Assets/Resources/ScriptableObjects/Speech/UwU.asset
OWO_PASSIVE = {
    r"r": "w",
    r"R": "W",
    r"l": "w",
    r"L": "W",
    r"v": "w",
    r"V": "W",
    r"ove": "uv",
}

OWO_AGGRESSIVE = {
    r"!": "! owo",
    r"ni": "nyee",
    r"na": "nya",
    r"ne": "nye",
    r"no": "nyo",
    r"nu": "nyu",
    **OWO_PASSIVE,
}

OWO_ENDINGS = (
    "OwO",
    "Nya",
    "owo",
    "nya",
    "nyan",
    "!!!",
    "(=^‥^=)",
    "(=；ｪ；=)",
    "ヾ(=｀ω´=)ノ”",
    "(p`ω´) q",
    "ฅ(´-ω-`)ฅ",
)


def replace_with_map(text: str, mapping: Dict[str, str]) -> str:
    for original, replacement in mapping.items():
        text = re.sub(original, replacement, text)

    return text


def owoify(text: str) -> str:
    """Default owoify"""

    text = replace_with_map(text, OWO_AGGRESSIVE)

    if not text.endswith("```"):
        for _ in range(random.randint(0, 2)):
            text += f" {random.choice(OWO_ENDINGS)}"

    return text


def owoify_stable(text: str) -> str:
    """OwOify but do not increase text length"""

    return replace_with_map(text, OWO_PASSIVE)


class PotatoContext(commands.Context):
    @property
    def prefix(self) -> str:
        return self._prefix

    @prefix.setter
    def prefix(self, value: Optional[str]):
        # because custom get_prefix can leave spaces
        self._prefix = None if value is None else value.rstrip()

    @property
    def db(self) -> DB:
        return self.bot.db

    async def send(
        self, content: Any = None, *, register: bool = True, **kwargs: Any
    ) -> discord.Message:
        if content is not None:
            if self.bot.owo:
                content = str(content)

                owoified = owoify(content)

                if len(owoified) > 2000:
                    owoified = owoify_stable(content)

                content = owoified

        message = await super().send(content, **kwargs)

        if register:
            self.bot.register_responses(
                self.message.id,
                [MessageResponse(message)],
            )

        return message

    async def react(
        self,
        *emojis: Union[discord.Emoji, str],
        message: discord.Message = None,
        register: bool = True,
    ):
        if message is None:
            message = self.message

        for emoji in emojis:
            await message.add_reaction(emoji)

        if register:
            self.bot.register_responses(
                message.id,
                [
                    ReactionResponse(message, convert_emoji_reaction(emoji))
                    for emoji in emojis
                ],
            )

    async def ok(self, message: discord.Message = None):
        if message is None:
            message = self.message

        return await self.react("\N{HEAVY CHECK MARK}", message=message)

    async def nope(self, message: discord.Message = None):
        if message is None:
            message = self.message

        return await self.react("\N{HEAVY MULTIPLICATION X}", message=message)
