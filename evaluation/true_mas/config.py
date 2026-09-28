import os
from dotenv import load_dotenv

load_dotenv()

BASE_URL = os.environ["BASE_URL"]
API_KEY = os.environ["API_KEY"]

MAX_REPAIR_ATTEMPTS = 3
STRUCTURED_GENERATION_MAX_TOKENS = 3000
TEXT_GENERATION_MAX_TOKENS = 3000
TEMPERATURE = 0.0

# Set to False when running without an NVIDIA GPU or without VRAM tracking.
MEASURE_VRAM = True

# Physical NVML GPU index or UUID used by Ollama.
GPU_METRICS_DEVICE = "0"

# Server country, not the client location. For example, "FIN" for Finland.
# Leave unset to disable emissions tracking until the location is known.
CODECARBON_COUNTRY_ISO_CODE = "FIN"
