import os
from dotenv import load_dotenv

load_dotenv()

DB_URL = os.getenv("DB_URL", "")
REDIS_URL = os.getenv("REDIS_URL", "")
HOST = os.getenv("HOST", "0.0.0.0")
PORT = int(os.getenv("PORT", "8080"))
