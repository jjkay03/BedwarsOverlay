# Modal settings dialog for API key, log path, pin, hotkey, font, and opacity.

import tkinter as tk
import tkinter.font as tkfont
from tkinter import filedialog
from pathlib import Path

import customtkinter as ctk

from . import config
from .ui_theme import (
    C_BG, C_BAR, C_BORDER, C_HEADER, C_TEXT, C_DIM, C_ACCENT, C_ACCENT_HV,
    FONT_TITLE, FONT_STATUS, OPACITY_LABELS,
)

_OP_KEYS = {v: k for k, v in OPACITY_LABELS.items()}


# Modal window for editing API key, log path, always-on-top, and opacity
class SettingsDialog(ctk.CTkToplevel):
    def __init__(self, parent: ctk.CTk, cfg: dict, on_save):
        super().__init__(parent)
        self._cfg     = dict(cfg)
        self._on_save = on_save

        self.title("Settings")
        self.geometry("460x540")
        self.resizable(False, False)
        self.configure(fg_color=C_BG)
        self.attributes("-topmost", True)
        self.grab_set()
        self.focus()
        self.after(50, self.lift)
        _ico = Path(__file__).parent.parent / "assets" / "bed.ico"
        if _ico.exists():
            self.after(200, lambda: self.iconbitmap(str(_ico)))
        self._build()

    # Constructs all widgets inside the dialog
    def _build(self) -> None:
        PAD = {"padx": 18, "pady": 5}

        ctk.CTkLabel(
            self, text="Settings",
            font=ctk.CTkFont(*FONT_TITLE), text_color=C_TEXT, anchor="w",
        ).pack(fill="x", padx=18, pady=(18, 8))

        # API key
        ctk.CTkLabel(self, text="Hypixel API Key",
                     font=ctk.CTkFont(*FONT_STATUS), text_color=C_DIM, anchor="w",
                     ).pack(fill="x", **PAD)
        self._key_var = tk.StringVar(value=self._cfg.get("api_key", ""))
        ctk.CTkEntry(
            self, textvariable=self._key_var, show="•",
            placeholder_text="xxxxxxxx-xxxx-xxxx-xxxx-xxxxxxxxxxxx",
            font=ctk.CTkFont(*FONT_STATUS),
            fg_color=C_BAR, border_color=C_BORDER, height=34,
        ).pack(fill="x", padx=18)

        # Log path
        ctk.CTkLabel(self, text="Minecraft latest.log path",
                     font=ctk.CTkFont(*FONT_STATUS), text_color=C_DIM, anchor="w",
                     ).pack(fill="x", **PAD)
        path_row = ctk.CTkFrame(self, fg_color="transparent")
        path_row.pack(fill="x", padx=18)
        self._path_var = tk.StringVar(value=self._cfg.get("log_path", ""))
        ctk.CTkEntry(
            path_row, textvariable=self._path_var,
            font=ctk.CTkFont(*FONT_STATUS),
            fg_color=C_BAR, border_color=C_BORDER, height=34,
        ).pack(side="left", fill="x", expand=True)
        ctk.CTkButton(
            path_row, text="Browse", width=72, height=34,
            fg_color=C_BAR, hover_color=C_ACCENT_HV,
            font=ctk.CTkFont(*FONT_STATUS),
            command=self._browse,
        ).pack(side="left", padx=(8, 0))

        # Divider
        ctk.CTkFrame(self, fg_color=C_BORDER, corner_radius=0, height=1).pack(
            fill="x", padx=18, pady=(16, 0)
        )

        # Pin checkbox
        self._pin_var = tk.BooleanVar(value=self._cfg.get("pin", True))
        ctk.CTkCheckBox(
            self, text="Always on top", variable=self._pin_var,
            onvalue=True, offvalue=False,
            checkbox_width=16, checkbox_height=16,
            font=ctk.CTkFont(*FONT_STATUS),
        ).pack(anchor="w", padx=18, pady=(12, 0))

        # Hotkey – label + small entry on the same row
        hot_row = ctk.CTkFrame(self, fg_color="transparent")
        hot_row.pack(fill="x", padx=18, pady=(8, 0))
        ctk.CTkLabel(
            hot_row, text="Toggle hotkey",
            font=ctk.CTkFont(*FONT_STATUS), text_color=C_DIM, anchor="w",
        ).pack(side="left")
        self._hotkey_var = tk.StringVar(value=self._cfg.get("hotkey", "j"))
        ctk.CTkEntry(
            hot_row, textvariable=self._hotkey_var, width=40, height=28,
            font=ctk.CTkFont(*FONT_STATUS),
            fg_color=C_BAR, border_color=C_BORDER,
        ).pack(side="left", padx=(10, 0))

        # Font – label above, combobox below
        ctk.CTkLabel(self, text="Table font",
                     font=ctk.CTkFont(*FONT_STATUS), text_color=C_DIM, anchor="w",
                     ).pack(fill="x", padx=18, pady=(10, 4))
        _fonts = sorted(f for f in tkfont.families() if not f.startswith("@"))
        self._font_box = ctk.CTkComboBox(
            self, values=_fonts,
            font=ctk.CTkFont(*FONT_STATUS),
            fg_color=C_BAR, border_color=C_BORDER,
            button_color=C_HEADER, button_hover_color=C_BORDER,
            dropdown_fg_color=C_BAR, dropdown_hover_color=C_HEADER,
            height=34,
        )
        self._font_box.set(self._cfg.get("font", "Segoe UI"))
        self._font_box.pack(fill="x", padx=18)

        # Opacity – its own row below font
        ctk.CTkLabel(self, text="Opacity",
                     font=ctk.CTkFont(*FONT_STATUS), text_color=C_DIM, anchor="w",
                     ).pack(fill="x", padx=18, pady=(10, 4))

        current_op_label = OPACITY_LABELS.get(self._cfg.get("opacity", "solid"), "Solid")
        self._opacity_btn = ctk.CTkSegmentedButton(
            self,
            values=list(OPACITY_LABELS.values()),
            font=ctk.CTkFont(*FONT_STATUS),
            fg_color=C_BAR,
            selected_color=C_ACCENT,
            selected_hover_color=C_ACCENT_HV,
            unselected_color=C_BAR,
            unselected_hover_color=C_HEADER,
        )
        self._opacity_btn.set(current_op_label)
        self._opacity_btn.pack(fill="x", padx=18)

        # Save / Cancel
        btn_row = ctk.CTkFrame(self, fg_color="transparent")
        btn_row.pack(fill="x", padx=18, pady=(16, 16))

        ctk.CTkButton(
            btn_row, text="Cancel", width=80, height=34,
            fg_color=C_BAR, hover_color=C_HEADER,
            font=ctk.CTkFont(*FONT_STATUS),
            command=self.destroy,
        ).pack(side="right", padx=(8, 0))

        ctk.CTkButton(
            btn_row, text="Save", width=80, height=34,
            fg_color=C_ACCENT, hover_color=C_ACCENT_HV,
            font=ctk.CTkFont(*FONT_STATUS, "bold"),
            command=self._save,
        ).pack(side="right")

    # Opens a file picker and fills the path entry
    def _browse(self) -> None:
        path = filedialog.askopenfilename(
            title="Select latest.log",
            filetypes=[("Log files", "*.log"), ("All files", "*.*")],
        )
        if path:
            self._path_var.set(path)

    # Writes edited values to config.json and calls the save callback
    def _save(self) -> None:
        raw = self._hotkey_var.get().strip().lower()
        self._cfg["api_key"]  = self._key_var.get().strip()
        self._cfg["log_path"] = self._path_var.get().strip()
        self._cfg["pin"]      = self._pin_var.get()
        self._cfg["hotkey"]   = raw[0] if raw and raw[0].isalpha() else "j"
        self._cfg["font"]     = self._font_box.get() or "Segoe UI"
        self._cfg["opacity"]  = _OP_KEYS.get(self._opacity_btn.get(), "solid")
        config.save(self._cfg)
        self._on_save(self._cfg)
        self.destroy()
