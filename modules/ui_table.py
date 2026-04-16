# Scrollable, sortable player stats table widget.
# Renders one CTkFrame row per player; re-renders on sort or data update.

from typing import List

import customtkinter as ctk

from .ui_theme import (
    C_BG, C_BAR, C_BORDER, C_HEADER, C_ROW_ODD, C_ROW_EVEN,
    C_TEXT, C_DIM, C_ACCENT, MC_RED, GHOST_BG,
    FONT_HEADER, FONT_ROW, ROW_H, SCROLLBAR_W,
    COLUMNS, fkdr_color, star_color,
)

CELL_PAD = 4


# Sortable, scrollable grid of player BedWars stats
class PlayerTable(ctk.CTkFrame):
    def __init__(self, master, sort_col: str = "fkdr", sort_asc: bool = False, **kw):
        super().__init__(master, fg_color=C_BG, corner_radius=0, **kw)
        self._sort_col = sort_col
        self._sort_asc = sort_asc
        self._ghost    = False
        self._players: List[dict] = []
        self._row_widgets: List[ctk.CTkFrame] = []
        self._build_header()
        self._build_body()

    # Builds the fixed header row using CTkLabels so text aligns with row cells
    def _build_header(self) -> None:
        self._hdr_frame = ctk.CTkFrame(self, fg_color=C_HEADER, corner_radius=0, height=32)
        self._hdr_frame.pack(fill="x", side="top")
        self._hdr_frame.pack_propagate(False)

        for key, label, min_w, stretch, anchor in COLUMNS:
            lbl = ctk.CTkLabel(
                self._hdr_frame,
                text=label,
                font=ctk.CTkFont(*FONT_HEADER),
                text_color=C_TEXT,
                width=min_w,
                anchor=anchor,
                cursor="hand2",
            )
            lbl.pack(side="left", fill="y", expand=stretch, padx=(CELL_PAD, 0))
            lbl.bind("<Button-1>", lambda e, k=key: self._on_header_click(k))

        ctk.CTkFrame(self._hdr_frame, fg_color="transparent", width=SCROLLBAR_W).pack(side="right")

        self._hdr_border = ctk.CTkFrame(self, fg_color=C_BORDER, corner_radius=0, height=1)
        self._hdr_border.pack(fill="x", side="top")

    # Builds the scrollable body frame that holds player rows
    def _build_body(self) -> None:
        self._scroll = ctk.CTkScrollableFrame(
            self,
            fg_color=C_BG,
            scrollbar_button_color=C_BAR,
            scrollbar_button_hover_color=C_ACCENT,
            corner_radius=0,
        )
        self._scroll.pack(fill="both", expand=True, side="top")

    # Enables or disables ghost mode (transparent background, opaque text)
    def set_ghost(self, enable: bool) -> None:
        self._ghost = enable
        bg = GHOST_BG if enable else C_BG
        self.configure(fg_color=bg)
        self._hdr_frame.configure(fg_color=bg)
        self._hdr_border.configure(fg_color=bg)
        self._scroll.configure(fg_color=bg, scrollbar_button_color=bg,
                               scrollbar_button_hover_color=bg)
        self.render()

    # Replaces the current player list and re-renders all rows
    def set_players(self, players: List[dict]) -> None:
        self._players = list(players)
        self.render()

    # Destroys existing row widgets and redraws them in sorted order
    def render(self) -> None:
        for w in self._row_widgets:
            w.destroy()
        self._row_widgets.clear()

        def sort_key(p: dict):
            v = p.get(self._sort_col, 0)
            return str(v).lower() if isinstance(v, str) else v

        ordered = sorted(self._players, key=sort_key, reverse=not self._sort_asc)
        for i, player in enumerate(ordered):
            row = self._make_row(player, i)
            row.pack(fill="x", side="top")
            self._row_widgets.append(row)

    # Builds one row frame for a single player dict
    def _make_row(self, player: dict, idx: int) -> ctk.CTkFrame:
        bg      = GHOST_BG if self._ghost else (C_ROW_ODD if idx % 2 else C_ROW_EVEN)
        row     = ctk.CTkFrame(self._scroll, fg_color=bg, corner_radius=0, height=ROW_H)
        loading = player.get("loading", False)
        nicked  = player.get("nicked", False)
        error   = player.get("error")
        row.pack_propagate(False)

        for key, _, min_w, stretch, anchor in COLUMNS:
            if key == "name" and not loading:
                cell = self._make_name_cell(row, player, min_w, nicked)
                cell.pack(side="left", fill="y", expand=stretch, padx=(CELL_PAD, 0))
            else:
                text, color = self._resolve_cell(player, key, loading, error)
                ctk.CTkLabel(
                    row, text=text, text_color=color,
                    font=ctk.CTkFont(*FONT_ROW), width=min_w, anchor=anchor,
                ).pack(side="left", fill="y", expand=stretch, padx=(CELL_PAD, 0))

        return row

    # Builds the name cell – handles rank prefix and (nick) indicator
    def _make_name_cell(self, parent, player: dict, width: int, nicked: bool) -> ctk.CTkFrame:
        frame = ctk.CTkFrame(parent, fg_color="transparent", width=width)
        frame.pack_propagate(False)

        name       = player.get("name", "?")
        rank       = player.get("rank", "")
        rank_color = player.get("rank_color", C_TEXT)

        if rank:
            ctk.CTkLabel(
                frame, text=f"{rank} {name}",
                text_color=rank_color,
                font=ctk.CTkFont(*FONT_ROW), anchor="w",
            ).pack(side="left", fill="both", expand=True)
        else:
            ctk.CTkLabel(
                frame, text=name,
                text_color=C_TEXT,
                font=ctk.CTkFont(*FONT_ROW), anchor="w",
            ).pack(side="left")

        if nicked:
            ctk.CTkLabel(
                frame, text=" (nick)",
                text_color=MC_RED,
                font=ctk.CTkFont(*FONT_ROW), anchor="w",
            ).pack(side="left")

        return frame

    # Returns (display_text, color) for a cell, handling loading and error states
    def _resolve_cell(self, player: dict, key: str, loading: bool, error) -> tuple:
        if loading:
            return "…", C_DIM
        if player.get("nicked"):
            return "—", C_DIM
        if error and not player.get("nicked"):
            if key == "fkdr":
                return error[:14], MC_RED
            return "—", C_DIM
        return self._data_cell(player, key)

    # Returns (display_text, color) for a normal data cell
    def _data_cell(self, p: dict, key: str) -> tuple:
        if key == "stars":
            s = p.get("stars", 0)
            return f"{s}✫", star_color(s)
        if key == "fkdr":
            v = p.get("fkdr", 0.0)
            return f"{v:.2f}", fkdr_color(v)
        if key == "wins":
            return str(p.get("wins", 0)), C_TEXT
        if key == "winstreak":
            ws = p.get("winstreak", 0)
            return str(ws), fkdr_color(ws / 5) if ws > 0 else (str(ws), C_DIM)
        return str(p.get(key, "")), C_TEXT

    # Handles a header click – toggles sort direction or changes sort column
    def _on_header_click(self, col: str) -> None:
        if self._sort_col == col:
            self._sort_asc = not self._sort_asc
        else:
            self._sort_col = col
            self._sort_asc = col == "name"
        self.render()
