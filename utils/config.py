import os
from dotenv import load_dotenv

load_dotenv()

GROQ_API_KEY = os.getenv("GROQ_API_KEY", "")
GROQ_MODEL = os.getenv("GROQ_MODEL", "llama-3.3-70b-versatile")

HINDSIGHT_API_KEY = os.getenv("HINDSIGHT_API_KEY", "")
HINDSIGHT_BANK_ID = os.getenv("HINDSIGHT_BANK_ID", "vaulty-ap-memory")
HINDSIGHT_API_URL = os.getenv("HINDSIGHT_API_URL", os.getenv("HINDSIGHT_BASE_URL", "https://api.hindsight.ai/v1"))
HINDSIGHT_BASE_URL = HINDSIGHT_API_URL

BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
DATA_DIR = os.path.join(BASE_DIR, "data")
