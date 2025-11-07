import os, json
from dotenv import load_dotenv
from typing import List, Dict

load_dotenv()

USERNAME: str = os.getenv("USERNAME")
PASSWORD: str = os.getenv("PASSWORD")

MLX_BASE: str = os.getenv("MLX_BASE", "https://api.multilogin.com")
MLX_LAUNCHER_V2: str = os.getenv("MLX_LAUNCHER_V2", "https://launcher.mlx.yt:45001/api/v2")

HEADERS: Dict[str, str] = json.loads(os.getenv("HEADERS", '{"Accept":"application/json","Content-Type":"application/json"}'))

FOLDER_ID: str = os.getenv("FOLDER_ID")

PROFILE_IDS: List[str] = json.loads(os.getenv("PROFILE_IDS", "[]"))

WEBSITES_FILE: str = os.getenv("WEBSITES_FILE", "websites.txt")

EMAIL_POOL: List[str] = json.loads(os.getenv("EMAIL_POOL", "[]"))
