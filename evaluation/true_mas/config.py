import os
from dotenv import load_dotenv

load_dotenv()

BASE_URL = os.environ["BASE_URL"]
API_KEY = os.environ["API_KEY"]

MODEL_NAME = "llama3.1:8b"
MAX_REPAIR_ATTEMPTS = 3
STRUCTURED_GENERATION_MAX_TOKENS = 1500
TEXT_GENERATION_MAX_TOKENS = 2000
TEMPERATURE = 0.0