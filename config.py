import os
import json
from dotenv import load_dotenv
from typing import List, Dict

# Load .env file
load_dotenv()

# ---------------------------
# Credentials
# ---------------------------
USERNAME: str = os.getenv("EMAIL")
PASSWORD: str = os.getenv("PASSWORD")
EMAIL_MAIL: str = os.getenv("EMAIL_MAIL")
APP_PASSWORD: str = os.getenv("APP_PASSWORD")  # App password recommended
IMAP_SERVER: str = os.getenv("IMAP_SERVER", "imap.gmail.com")
IMAP_PORT: int = int(os.getenv("IMAP_PORT", "993"))
SMTP_SERVER: str = os.getenv("SMTP_SERVER", "smtp.gmail.com")
SMTP_PORT: int = int(os.getenv("SMTP_PORT", "587"))

# ---------------------------
# Multilogin API
# ---------------------------
MLX_BASE: str = os.getenv("MLX_BASE", "https://api.multilogin.com")
MLX_LAUNCHER_V2: str = os.getenv("MLX_LAUNCHER_V2", "https://launcher.mlx.yt:45001/api/v2")
HEADERS: Dict[str, str] = json.loads(os.getenv(
    "HEADERS",
    '{"Accept": "application/json", "Content-Type": "application/json"}'
))

# ---------------------------
# Folder and Profiles
# ---------------------------
FOLDER_ID: str = os.getenv("FOLDER_ID")

# PROFILE_IDS in .env as comma-separated string
PROFILE_IDS: List[str] = [
    pid.strip() for pid in os.getenv("PROFILE_IDS", "").split(",") if pid.strip()
]

# ---------------------------
# Websites and Emails
# ---------------------------
WEBSITES_FILE: str = os.getenv("WEBSITES_FILE", "/home/ezaan-amin/Documents/BitBash_Tasks/multi-login/failed_sites.txt")

# EMAIL_POOL in .env as comma-separated string
EMAIL_POOL: List[str] = [
    email.strip() for email in os.getenv("EMAIL_POOL", "").split(",") if email.strip()
]

# ---------------------------
# Debug info
# ---------------------------
print(f"Loaded {len(PROFILE_IDS)} profiles and {len(EMAIL_POOL)} emails")
