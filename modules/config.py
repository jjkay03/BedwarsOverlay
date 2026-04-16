# Loads and saves config.json inside the data/ folder.
import json
import os
from pathlib import Path

_DATA_DIR   = Path(__file__).parent.parent / "data"
CONFIG_FILE = _DATA_DIR / "config.json"

_APPDATA = os.getenv("APPDATA", "")
_HOME    = Path.home()


def _default_log_path() -> str:
    if _APPDATA:
        return str(Path(_APPDATA) / ".minecraft" / "logs" / "latest.log")
    mac = _HOME / "Library" / "Application Support" / ".minecraft" / "logs" / "latest.log"
    if mac.exists():
        return str(mac)
    return str(_HOME / ".minecraft" / "logs" / "latest.log")


DEFAULTS: dict = {
    "api_key":  "",
    "log_path": _default_log_path(),
    "pin":      True,
    "opacity":  "semi",
    "font":     "Segoe UI",
    "hotkey":   "j",
}


def load() -> dict:
    _DATA_DIR.mkdir(exist_ok=True)
    if CONFIG_FILE.exists():
        try:
            with CONFIG_FILE.open("r", encoding="utf-8") as f:
                cfg = json.load(f)
            for k, v in DEFAULTS.items():
                cfg.setdefault(k, v)
            return cfg
        except (json.JSONDecodeError, OSError):
            pass
    cfg = DEFAULTS.copy()
    save(cfg)
    return cfg


def save(cfg: dict) -> None:
    with CONFIG_FILE.open("w", encoding="utf-8") as f:
        json.dump(cfg, f, indent=2)
