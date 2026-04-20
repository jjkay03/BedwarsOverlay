# Logging module – writes timestamped lines to console and a per-session log file.
from datetime import datetime
from pathlib import Path

_DATA_DIR = Path(__file__).parent.parent / "data"
_LOGS_DIR = _DATA_DIR / "logs"

_log_file: Path | None = None


def _get_log_file() -> Path:
    global _log_file
    if _log_file is None:
        _LOGS_DIR.mkdir(parents=True, exist_ok=True)
        stamp = datetime.now().strftime("%Y-%m-%d_%H-%M-%S")
        _log_file = _LOGS_DIR / f"{stamp}.log"
        _log_file.touch()
    return _log_file


def _write(message: str) -> None:
    timestamp = datetime.now().strftime("%H:%M:%S")
    line = f"[{timestamp}] {message}"
    print(line)
    with _get_log_file().open("a", encoding="utf-8") as f:
        f.write(line + "\n")


# Log a /who detection: player list and the Minecraft log file it came from
def who_detected(players: list[str], source_log: str) -> None:
    _write(f"/who detected {len(players)} player(s) from {source_log}")


# Log a successful Hypixel API fetch with the player's BedWars stats
def api_player_fetched(stats: dict) -> None:
    name      = stats.get("name", "?")
    stars     = stats.get("stars", 0)
    fkdr      = stats.get("fkdr", 0.0)
    wins      = stats.get("wins", 0)
    winstreak = stats.get("winstreak", 0)
    _write(f"Fetched {name} - Stars: {stars}  FKDR: {fkdr}  Wins: {wins}  WS: {winstreak}")


# Log an API error (rate limit, invalid key, timeout, etc.) for a player lookup
def api_error(name: str, error: str) -> None:
    _write(f"API error for {name}: {error}")
