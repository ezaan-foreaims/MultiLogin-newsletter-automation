import requests, hashlib
from config import USERNAME, PASSWORD, MLX_BASE, MLX_LAUNCHER_V2, HEADERS, FOLDER_ID

def sign_in(username=USERNAME, password=PASSWORD):
    try:
        url = f"{MLX_BASE}/user/signin"
        payload = {"email": username, "password": hashlib.md5(password.encode()).hexdigest()}
        r = requests.post(url, json=payload, headers=HEADERS, timeout=15)
        r.raise_for_status()
        return r.json()["data"]["token"]
    except Exception as e:
        print(f"Auth failed: {e}")
        return None

def start_profile(token, folder_id, profile_id):
    headers = {**HEADERS, "Authorization": f"Bearer {token}"}
    url = f"{MLX_LAUNCHER_V2}/profile/f/{folder_id}/p/{profile_id}/start"
    params = {"automation_type":"playwright","headless_mode":"false"}
    r = requests.get(url, headers=headers, params=params, timeout=30, verify=False)
    r.raise_for_status()
    port = r.json().get("data", {}).get("port")
    if not port: return None, None
    return r.json(), f"http://127.0.0.1:{port}"

def stop_profile(token, profile_id):
    headers = {**HEADERS, "Authorization": f"Bearer {token}"}
    url = f"{MLX_LAUNCHER_V2}/profile/stop"
    requests.post(url, json={"profileId": profile_id}, headers=headers, timeout=10, verify=False)
