import os

from dotenv import load_dotenv

load_dotenv()

PREFIX = os.environ["BOT_PREFIX"]
ADMIN_ROLE_ID = int(os.environ["ADMIN_ROLE_ID"])
