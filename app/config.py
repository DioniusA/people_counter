import os
from dotenv import load_dotenv

load_dotenv()

# Database config
POSTGRES_CONFIG = {
    "host": os.getenv("POSTGRES_HOST"),
    "port": int(os.getenv("POSTGRES_PORT", 5432)),
    "dbname": os.getenv("POSTGRES_DB"),
    "user": os.getenv("POSTGRES_USER"),
    "password": os.getenv("POSTGRES_PASSWORD")
}

# Model config
MODEL_PATH = os.getenv("MODEL_PATH")
CONFIDENCE_THRESHOLD = float(os.getenv("CONFIDENCE_THRESHOLD", 0.4))
CHECK_INTERVAL = int(os.getenv("CHECK_INTERVAL", 60))

# Output directory
OUTPUT_DIR = os.getenv("OUTPUT_DIR", "output")
os.makedirs(OUTPUT_DIR, exist_ok=True)

# Dynamic cameras reading
CAMERAS = []
i = 1
while True:
    name = os.getenv(f"CAMERA_{i}_NAME")
    url = os.getenv(f"CAMERA_{i}_URL")
    if not name or not url:
        break
    CAMERAS.append((name, url))
    i += 1
