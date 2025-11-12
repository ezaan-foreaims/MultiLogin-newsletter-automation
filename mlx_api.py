# mlx_api.py
import hashlib
import json
import requests
import urllib3
from typing import Tuple, Optional, Dict, Any

# Disable SSL warnings
urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

# SSL verification disabled for local MultiLogin launcher
VERIFY_SSL = False

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
        r = requests.post(url, json=payload, headers=headers, timeout=30, verify=VERIFY_SSL)
        
        if r.status_code != 200:
            print(f"Auth failed: {r.status_code} - {r.text}")
            return None

        data = r.json()
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
    """
    headers = dict(headers or _default_headers())
    headers["Authorization"] = f"Bearer {token}"
    
    # Normalize the launcher_v2 URL - ensure it has /api/v2
    base_url = launcher_v2.rstrip("/")
    
    # If it doesn't have /api/v2, add it
    if not base_url.endswith("/api/v2"):
        if "/api/v2" not in base_url:
            base_url = base_url + "/api/v2"
    
    # Build the full URL
    url = f"{base_url}/profile/f/{folder_id}/p/{profile_id}/start"
    params = {"automation_type": "playwright", "headless_mode": "false"}

    print(f"🔗 Requesting: {url}")

    try:
        r = requests.get(url, headers=headers, params=params, timeout=120, verify=VERIFY_SSL, allow_redirects=False)
        
        # Handle redirects manually
        if r.status_code in [301, 302, 307, 308]:
            redirect_url = r.headers.get('Location')
            print(f"↪️ Redirected to: {redirect_url}")
            # Follow redirect with verify=False
            r = requests.get(redirect_url, headers=headers, params=params, timeout=120, verify=False)
        
        if r.status_code != 200:
            print(f"Start profile failed: {r.status_code} - {r.text}")
            return None, None

        resp = r.json()
        port = resp.get("data", {}).get("port") or resp.get("port")
        
        if not port:
            # Check for direct endpoint
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

    except requests.exceptions.SSLError as e:
        print(f"❌ SSL Error: {e}")
        print("💡 Trying with HTTP instead of HTTPS...")
        
        # Try HTTP fallback
        try:
            http_url = url.replace("https://", "http://").replace("launcher.mlx.yt", "127.0.0.1")
            print(f"🔗 Retrying with: {http_url}")
            r = requests.get(http_url, headers=headers, params=params, timeout=120, verify=False)
            
            if r.status_code != 200:
                print(f"Start profile failed: {r.status_code} - {r.text}")
                return None, None
            
            resp = r.json()
            port = resp.get("data", {}).get("port") or resp.get("port")
            
            if port:
                endpoint = f"http://127.0.0.1:{port}"
                print(f"✅ Profile started | CDP: {endpoint}")
                return resp, endpoint
            
            return resp, None
            
        except Exception as retry_error:
            print(f"❌ Retry failed: {retry_error}")
            return None, None
            
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
    
    # Normalize URL
    base_url = launcher_v2.rstrip("/")
    if not base_url.endswith("/api/v2"):
        if "/api/v2" not in base_url:
            base_url = base_url + "/api/v2"
    
    url = f"{base_url}/profile/stop"
    payload = {"profileId": profile_id}

    print(f"🔗 Stop request: {url}")

    try:
        r = requests.post(url, json=payload, headers=headers, timeout=30, verify=VERIFY_SSL, allow_redirects=False)
        
        # Handle redirects
        if r.status_code in [301, 302, 307, 308]:
            redirect_url = r.headers.get('Location')
            r = requests.post(redirect_url, json=payload, headers=headers, timeout=30, verify=False)
        
        if r.status_code in (200, 204):
            print("🛑 Profile stopped")
            return True
        elif r.status_code == 404:
            print("⚠️ Profile not running (404)")
            return True  # Consider this success since profile isn't running
        else:
            print(f"Stop profile returned {r.status_code}: {r.text}")
            return False
            
    except requests.exceptions.SSLError:
        # Try HTTP fallback
        try:
            http_url = url.replace("https://", "http://").replace("launcher.mlx.yt", "127.0.0.1")
            r = requests.post(http_url, json=payload, headers=headers, timeout=30, verify=False)
            
            if r.status_code in (200, 204, 404):
                print("🛑 Profile stopped")
                return True
            return False
        except:
            return False
            
    except requests.exceptions.RequestException as e:
        print(f"Stop profile request error: {e}")
        return False
    except Exception as e:
        print(f"Unexpected stop_profile error: {e}")
        return False