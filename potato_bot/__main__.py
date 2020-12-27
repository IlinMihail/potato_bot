import os

from .bot import Bot

if __name__ == "__main__":
    bot = Bot(command_prefix=os.environ["BOT_PREFIX"])

    bot.run(os.environ["BOT_TOKEN"])
