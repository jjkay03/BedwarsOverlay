# Thin wrapper around the Hypixel REST API player endpoint.
import requests
from typing import Optional, Tuple

_BASE_URL = "https://api.hypixel.net/player"
_TIMEOUT  = 10


# Returns (player_dict, None) on success or (None, error_str) on failure
def fetch_player(api_key: str, name: str) -> Tuple[Optional[dict], Optional[str]]:
    try:
        resp = requests.get(
            _BASE_URL,
            params={"key": api_key, "name": name},
            timeout=_TIMEOUT,
        )
        if resp.status_code == 403:
            return None, "Invalid API key"
        if resp.status_code == 429:
            return None, "Rate limited"
        resp.raise_for_status()
        data = resp.json()
        if not data.get("success"):
            return None, data.get("cause", "Unknown API error")
        return data.get("player"), None
    except requests.Timeout:
        return None, "Timed out"
    except requests.ConnectionError:
        return None, "No connection"
    except Exception as exc:
        return None, str(exc)
