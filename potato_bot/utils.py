import asyncio


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
