import os

from pathlib import Path

from dotenv import load_dotenv

load_dotenv()

SERVER_HOME = Path(os.environ["SERVER_HOME"])
ADMIN_ROLE_ID = int(os.environ["ADMIN_ROLE_ID"])
TECHADMIN_ROLE_ID = int(os.environ["TECHADMIN_ROLE_ID"])
