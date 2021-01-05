from discord.ext import commands

from .context import Context


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
    async def convert(cls, ctx: Context, argument: str):
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
    async def convert(cls, ctx: Context, argument: str) -> str:
        if len(argument) != 28:
            raise commands.BadArgument(
                f"User ID must be exactly 28 characters long, got {len(argument)}"
            )

        return argument
