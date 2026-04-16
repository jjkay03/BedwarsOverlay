# Fetches and caches Minecraft player head avatars from mc-heads.net.
import shutil
from pathlib import Path
from typing import Optional

import requests

_CACHE_DIR = Path(__file__).parent.parent / "data" / "heads"
_SIZE      = 24   # pixels – mc-heads.net accepts a size suffix
_TIMEOUT   = 5


# Wipes and recreates the head image cache directory
def clear_cache() -> None:
    try:
        if _CACHE_DIR.exists():
            shutil.rmtree(_CACHE_DIR)
        _CACHE_DIR.mkdir(parents=True, exist_ok=True)
    except Exception:
        pass


# Downloads a player head and saves it to the cache; returns the file path or None
def fetch_head(name: str) -> Optional[str]:
    try:
        resp = requests.get(
            f"https://mc-heads.net/avatar/{name}/{_SIZE}",
            timeout=_TIMEOUT,
        )
        if resp.status_code == 200:
            path = _CACHE_DIR / f"{name}.png"
            path.write_bytes(resp.content)
            return str(path)
    except Exception:
        pass
    return None
