# mlx_api.py
import hashlib
import json
import requests
from typing import Tuple, Optional, Dict, Any

# If you prefer SSL verification, set this True and configure CA bundle
VERIFY_SSL = False

# Keep default headers minimal; token will be added by caller where needed
def _default_headers() -> Dict[str, str]:
    return {"Accept": "application/json", "Content-Type": "application/json"}


def sign_in(username: str, password: str, mlx_base: str, headers: Dict[str, str] = None) -> Optional[str]:
    """
    Sign in to Multilogin API and return token (string) or None on failure.
    The API expects MD5(password).
    """
    headers = headers or _default_headers()
    url = mlx_base.rstrip("/") + "/user/signin"
    payload = {"email": username, "password": hashlib.md5(password.encode()).hexdigest()}

    try:
        r = requests.post(url, json=payload, headers=headers, timeout=15, verify=VERIFY_SSL)
        # Helpful debug on failure
        if r.status_code != 200:
            print(f"Auth failed: {r.status_code} - {r.text}")
            return None

        data = r.json()
        # Response structure may vary; try common locations
        token = None
        if isinstance(data, dict):
            token = data.get("data", {}).get("token") or data.get("token") or data.get("access_token")
        if not token:
            print("Auth response did not contain token. Full response:")
            print(json.dumps(data, indent=2))
            return None

        print("✅ Authenticated successfully (token received)")
        return token

    except requests.exceptions.RequestException as e:
        print(f"Auth request error: {e}")
        return None
    except Exception as e:
        print(f"Unexpected auth error: {e}")
        return None


def start_profile(token: str, folder_id: str, profile_id: str, launcher_v2: str, headers: Dict[str, str] = None) -> Tuple[Optional[Dict[str, Any]], Optional[str]]:
    """
    Start profile via launcher API and return (json_response, cdp_endpoint_url) on success.
    On success the launcher often returns a port; we convert it to http://127.0.0.1:<port>
    """
    headers = dict(headers or _default_headers())
    headers["Authorization"] = f"Bearer {token}"
    url = launcher_v2.rstrip("/") + f"/profile/f/{folder_id}/p/{profile_id}/start"
    params = {"automation_type": "playwright", "headless_mode": "false"}

    try:
        r = requests.get(url, headers=headers, params=params, timeout=30, verify=VERIFY_SSL)
        if r.status_code != 200:
            print(f"Start profile failed: {r.status_code} - {r.text}")
            return None, None

        resp = r.json()
        port = resp.get("data", {}).get("port")
        if not port:
            # Some launcher versions may return endpoint directly
            endpoint = resp.get("data", {}).get("endpoint") or resp.get("endpoint")
            if endpoint:
                print(f"✅ Profile started | CDP endpoint: {endpoint}")
                return resp, endpoint

            print("❌ Start response did not include port/endpoint. Full response:")
            print(json.dumps(resp, indent=2))
            return resp, None

        endpoint = f"http://127.0.0.1:{port}"
        print(f"✅ Profile started | CDP: {endpoint}")
        return resp, endpoint

    except requests.exceptions.RequestException as e:
        print(f"Start profile request error: {e}")
        return None, None
    except Exception as e:
        print(f"Unexpected start_profile error: {e}")
        return None, None


def stop_profile(token: str, profile_id: str, launcher_v2: str, headers: Dict[str, str] = None) -> bool:
    """
    Stop a running profile via launcher API. Returns True if request succeeded (status 200/204).
    """
    headers = dict(headers or _default_headers())
    headers["Authorization"] = f"Bearer {token}"
    url = launcher_v2.rstrip("/") + "/profile/stop"
    payload = {"profileId": profile_id}

    try:
        r = requests.post(url, json=payload, headers=headers, timeout=10, verify=VERIFY_SSL)
        if r.status_code in (200, 204):
            print("🛑 Profile stopped")
            return True
        else:
            print(f"Stop profile returned {r.status_code}: {r.text}")
            return False
    except requests.exceptions.RequestException as e:
        print(f"Stop profile request error: {e}")
        return False
    except Exception as e:
        print(f"Unexpected stop_profile error: {e}")
        return False
