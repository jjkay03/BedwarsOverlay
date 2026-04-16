# Tails Minecraft's latest.log in real time and fires callbacks on /who responses and game starts.
# Uses a polling loop instead of watchdog because Minecraft holds the file open on Windows,
# which prevents watchdog's on_modified event from firing reliably.

import re
import time
import threading
from typing import Callable, List

_ONLINE_RE = re.compile(r"ONLINE:\s*(.+)")

_GAME_START_RE = re.compile(
    r"Protect your Bed!"
    r"|The game starts in \d"
    r"|\[Bed Wars\]"
    r"|BED DESTRUCTION",
    re.IGNORECASE,
)

POLL_INTERVAL = 0.5  # seconds between reads


# Public interface for starting and stopping the log watcher
class LogWatcher:
    def __init__(
        self,
        path: str,
        on_players: Callable[[List[str]], None],
        on_game_start: Callable[[], None],
    ):
        self._path          = path
        self._on_players    = on_players
        self._on_game_start = on_game_start
        self._pos           = 0
        self._running       = False
        self._thread: threading.Thread | None = None
        self._seek_to_end()

    # Positions the read cursor at the end of the file so old lines are skipped on startup
    def _seek_to_end(self) -> None:
        try:
            with open(self._path, "r", encoding="utf-8", errors="replace") as fh:
                fh.seek(0, 2)
                self._pos = fh.tell()
        except OSError:
            self._pos = 0

    def start(self) -> None:
        self._running = True
        self._thread  = threading.Thread(target=self._poll_loop, daemon=True)
        self._thread.start()

    def stop(self) -> None:
        self._running = False
        if self._thread:
            self._thread.join(timeout=2)
            self._thread = None

    def change_path(self, new_path: str) -> None:
        self.stop()
        self._path = new_path
        self._seek_to_end()
        self.start()

    # Runs in background thread – polls the file every POLL_INTERVAL seconds
    def _poll_loop(self) -> None:
        while self._running:
            self._drain()
            time.sleep(POLL_INTERVAL)

    # Reads any new lines appended since the last poll and processes each one
    def _drain(self) -> None:
        try:
            with open(self._path, "r", encoding="utf-8", errors="replace") as fh:
                fh.seek(self._pos)
                lines = fh.readlines()
                self._pos = fh.tell()
            for line in lines:
                self._process(line)
        except OSError:
            pass

    # Checks a single line for a /who response or a game-start message
    def _process(self, line: str) -> None:
        m = _ONLINE_RE.search(line)
        if m:
            players = [p.strip() for p in m.group(1).split(",") if p.strip()]
            if players:
                self._on_players(players)
            return
        if _GAME_START_RE.search(line):
            self._on_game_start()
