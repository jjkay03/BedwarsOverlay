# Main overlay window. Wires together the log watcher, API calls, and UI widgets.

import threading
import tkinter as tk
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path
from typing import List

import customtkinter as ctk

from . import api_hypixel as api
from . import api_heads
from . import config
from . import parser as bw_parser
from .hotkey import HotkeyManager
from .log_watcher import LogWatcher
from .ui_table import PlayerTable
from .ui_settings import SettingsDialog
from .ui_theme import (
    C_BG, C_BAR, C_BORDER, C_HEADER, C_TEXT, C_DIM, GHOST_BG,
    FONT_TITLE, FONT_STATUS, OPACITY_VALUES, ROW_H,
)


def _set_taskbar_icon() -> None:
    try:
        import ctypes
        ctypes.windll.shell32.SetCurrentProcessExplicitAppUserModelID(
            "BedwarsOverlay.App"
        )
    except Exception:
        pass


# Always-on-top overlay window
class App(ctk.CTk):
    def __init__(self) -> None:
        _set_taskbar_icon()
        super().__init__()
        self._cfg      = config.load()
        self._players: List[dict] = []
        self._executor = ThreadPoolExecutor(max_workers=8)
        self._watcher: LogWatcher | None = None
        self._bg_frames: List[ctk.CTkFrame] = []   # background frames toggled in ghost mode

        self._hotkey = HotkeyManager(self._toggle_minimize)

        self._setup_window()
        self._build_topbar()
        self._table = PlayerTable(self, font_family=self._cfg.get("font", "Segoe UI"))
        self._table.pack(fill="both", expand=True, side="top")
        self._build_statusbar()
        self._apply_window_attrs()
        self._apply_font(self._cfg.get("font", "Segoe UI"))
        self._start_watcher()
        self._hotkey.set_key(self._cfg.get("hotkey", "j"))

    # Configures the root window geometry
    def _setup_window(self) -> None:
        self.title("BedWars Overlay")
        self.geometry("490x380")
        self.minsize(360, 200)
        self.configure(fg_color=C_BG)
        self.protocol("WM_DELETE_WINDOW", self._on_close)
        _ico = Path(__file__).parent.parent / "assets" / "bed.ico"
        if _ico.exists():
            self.iconbitmap(str(_ico))

    # Builds the top bar with title, Clear and Settings buttons
    def _build_topbar(self) -> None:
        bar = ctk.CTkFrame(self, fg_color=C_BAR, corner_radius=0, height=42)
        bar.pack(fill="x", side="top")
        bar.pack_propagate(False)
        self._bg_frames.append(bar)

        self._title_lbl = ctk.CTkLabel(
            bar, text="BedWars Overlay",
            font=ctk.CTkFont(*FONT_TITLE), text_color=C_TEXT,
        )
        self._title_lbl.pack(side="left", padx=14)

        _btn = dict(height=28, corner_radius=6, fg_color=C_HEADER,
                    hover_color=C_BORDER, font=ctk.CTkFont(*FONT_STATUS))

        self._settings_btn = ctk.CTkButton(bar, text="⚙  Settings", width=100, **_btn,
                                           command=self._open_settings)
        self._settings_btn.pack(side="right", padx=(0, 10), pady=7)
        self._clear_btn = ctk.CTkButton(bar, text="Clear", width=58, **_btn,
                                        command=self._clear)
        self._clear_btn.pack(side="right", padx=(0, 4), pady=7)

        border = ctk.CTkFrame(self, fg_color=C_BORDER, corner_radius=0, height=1)
        border.pack(fill="x", side="top")
        self._bg_frames.append(border)

    # Builds the status bar at the bottom of the window
    def _build_statusbar(self) -> None:
        btmborder = ctk.CTkFrame(self, fg_color=C_BORDER, corner_radius=0, height=1)
        btmborder.pack(fill="x", side="bottom")
        self._bg_frames.append(btmborder)

        sb = ctk.CTkFrame(self, fg_color=C_BAR, corner_radius=0, height=26)
        sb.pack(fill="x", side="bottom")
        sb.pack_propagate(False)
        self._bg_frames.append(sb)

        self._status_var = tk.StringVar(value="Starting…")
        self._status_lbl = ctk.CTkLabel(
            sb, textvariable=self._status_var,
            font=ctk.CTkFont(*FONT_STATUS), text_color=C_DIM, anchor="w",
        )
        self._status_lbl.pack(side="left", padx=10)

    # Applies pin, alpha, and ghost mode from the current config
    def _apply_window_attrs(self) -> None:
        opacity = self._cfg.get("opacity", "solid")
        pin     = self._cfg.get("pin", True)

        self.attributes("-topmost", pin)

        if opacity == "ghost":
            # Make all background frames the chromakey colour, then punch through
            self.configure(fg_color=GHOST_BG)
            for frame in self._bg_frames:
                frame.configure(fg_color=GHOST_BG)
            self._table.set_ghost(True)
            self.attributes("-alpha", 1.0)
            self.wm_attributes("-transparentcolor", GHOST_BG)
        else:
            self.configure(fg_color=C_BG)
            self._bg_frames[0].configure(fg_color=C_BAR)   # topbar
            self._bg_frames[1].configure(fg_color=C_BORDER) # top border
            self._bg_frames[2].configure(fg_color=C_BORDER) # bottom border
            self._bg_frames[3].configure(fg_color=C_BAR)   # statusbar
            self._table.set_ghost(False)
            self.wm_attributes("-transparentcolor", "")
            self.attributes("-alpha", OPACITY_VALUES.get(opacity, 1.0))

    # Creates and starts the LogWatcher for the configured log path
    def _start_watcher(self) -> None:
        path = self._cfg.get("log_path", "")
        if not path:
            self._set_status("No log path set – open Settings")
            return
        try:
            self._watcher = LogWatcher(path, self._on_players_detected, self._on_game_start)
            self._watcher.start()
            self._set_status("Watching log – type /who in BedWars")
        except Exception as exc:
            self._set_status(f"Watcher error: {exc}")

    # Stops any existing watcher and starts a fresh one
    def _restart_watcher(self) -> None:
        if self._watcher:
            try:
                self._watcher.stop()
            except Exception:
                pass
            self._watcher = None
        self._start_watcher()

    # Called by the log watcher thread when a /who response is detected
    def _on_players_detected(self, names: List[str]) -> None:
        self.after(0, lambda: self._load_players(names))

    # Called by the log watcher thread when a BedWars game start is detected
    def _on_game_start(self) -> None:
        self.after(0, lambda: self._set_status("BedWars game detected – type /who in chat!"))

    # Resizes the window height to exactly fit n player rows plus the fixed chrome
    def _fit_to_players(self, count: int) -> None:
        _CHROME_H = 103  # topbar(43) + table header(33) + statusbar(27)
        h = max(_CHROME_H + count * ROW_H, 180)
        h = min(h, int(self.winfo_screenheight() * 0.9))
        self.geometry(f"{self.winfo_width()}x{h}")

    # Starts fetching stats for all detected players in parallel
    def _load_players(self, names: List[str]) -> None:
        if self.state() == "iconic":
            self.deiconify()
            self.lift()
        api_key = self._cfg.get("api_key", "").strip()
        if not api_key:
            self._set_status("No API key – open Settings first")
            return

        api_heads.clear_cache()
        self._players = [{"name": n, "loading": True} for n in names]
        self._table.set_players(self._players)
        self._fit_to_players(len(names))
        self._set_status(f"Fetching stats for {len(names)} player(s)…")

        def fetch_all() -> None:
            for name in names:
                future = self._executor.submit(self._fetch_one, api_key, name)
                future.add_done_callback(
                    lambda f, n=name: self.after(0, lambda: self._on_fetched(n, f))
                )

        threading.Thread(target=fetch_all, daemon=True).start()

    # Fetches and parses stats for a single player (runs in thread pool)
    def _fetch_one(self, api_key: str, name: str) -> dict:
        player_data, err = api.fetch_player(api_key, name)
        if err:
            result = {"name": name, "error": err, "nicked": False}
        else:
            stats = bw_parser.parse_bedwars(player_data)
            stats["name"] = name
            result = stats

        head_path = api_heads.fetch_head(name)
        if head_path:
            result["head_path"] = head_path

        return result

    # Called on the main thread when a single player's fetch completes
    def _on_fetched(self, name: str, future) -> None:
        try:
            stats = future.result()
        except Exception as exc:
            stats = {"name": name, "error": str(exc), "nicked": False}

        for i, p in enumerate(self._players):
            if p.get("name", "").lower() == name.lower():
                self._players[i] = stats
                break

        self._table.set_players(self._players)

        pending = sum(1 for p in self._players if p.get("loading"))
        if pending == 0:
            self._set_status(f"Loaded {len(self._players)} player(s) – type /who to refresh")

    # Clears the table and resets status
    def _clear(self) -> None:
        self._players = []
        self._table.set_players([])
        self._fit_to_players(0)
        self._set_status("Cleared – waiting for /who…")

    # Thread-safe status bar update
    def _set_status(self, msg: str) -> None:
        self.after(0, lambda: self._status_var.set(msg))

    # Opens the settings dialog
    def _open_settings(self) -> None:
        SettingsDialog(self, self._cfg, self._on_settings_saved)

    # Toggles the window between minimized and normal; called from the hotkey thread
    def _toggle_minimize(self) -> None:
        self.after(0, self._do_toggle_minimize)

    def _do_toggle_minimize(self) -> None:
        if self.state() == "iconic":
            self.deiconify()
            self.lift()
            self.focus_force()
        else:
            self.iconify()

    # Applies the chosen font family to every text widget in the overlay
    def _apply_font(self, family: str) -> None:
        self._title_lbl.configure(font=ctk.CTkFont(family=family, size=13))
        self._settings_btn.configure(font=ctk.CTkFont(family=family, size=11))
        self._clear_btn.configure(font=ctk.CTkFont(family=family, size=11))
        self._status_lbl.configure(font=ctk.CTkFont(family=family, size=11))
        self._table.set_font(family)

    # Saves new config, re-applies window attributes, and restarts the log watcher
    def _on_settings_saved(self, new_cfg: dict) -> None:
        self._cfg = new_cfg
        self._apply_window_attrs()
        self._restart_watcher()
        self._apply_font(new_cfg.get("font", "Segoe UI"))
        self._hotkey.set_key(new_cfg.get("hotkey", "j"))
        self._set_status("Settings saved.")

    # Cleans up background resources before the window closes
    def _on_close(self) -> None:
        self._hotkey.stop()
        if self._watcher:
            try:
                self._watcher.stop()
            except Exception:
                pass
        self._executor.shutdown(wait=False)
        self.destroy()
