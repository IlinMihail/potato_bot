import os

from .bot import Bot
from .cogs import load_cogs

if __name__ == "__main__":
    bot = Bot(command_prefix=os.environ["BOT_PREFIX"])

    load_cogs(bot)

    bot.run(os.environ["BOT_TOKEN"])
