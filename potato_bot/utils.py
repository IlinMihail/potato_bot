import asyncio

from collections import OrderedDict


async def run_process(cmd, *args):
    process = await asyncio.create_subprocess_exec(
        cmd,
        *args,
        stdout=asyncio.subprocess.PIPE,
        stderr=asyncio.subprocess.PIPE,
    )
    data = await process.communicate()

    return [stream.decode() if stream is not None else "" for stream in data]


async def run_process_shell(program):
    process = await asyncio.create_subprocess_shell(
        program,
        stdout=asyncio.subprocess.PIPE,
        stderr=asyncio.subprocess.PIPE,
    )
    data = await process.communicate()

    return [stream.decode() if stream is not None else "" for stream in data]


def minutes_to_human_readable(minutes: int) -> str:
    ranges = (
        (60, "m"),  # minutes/hour
        (24, "h"),  # hours/day
        (30, "d"),  # days/month
        (12, "mon"),  # months/year
        (1, "y"),  # stop at years
    )

    s = ""
    quotient = minutes

    for count, name in ranges:
        quotient, remainder = divmod(quotient, count)

        if count == 1:
            remainder = quotient  # terminating value

        if remainder:
            s = f"{remainder}{name} {s}"

        if not quotient:
            break

    return s.rstrip()


# https://docs.python.org/3/library/collections.html#ordereddict-examples-and-recipes
class LRU(OrderedDict):
    def __init__(self, maxsize=128, /, *args, **kwds):
        self.maxsize = maxsize
        super().__init__(*args, **kwds)

    def __setitem__(self, key, value):
        if key in self:
            self.move_to_end(key)

        super().__setitem__(key, value)

        if len(self) > self.maxsize:
            oldest = next(iter(self))
            del self[oldest]
