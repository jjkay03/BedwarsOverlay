# Scrollable, sortable player stats table widget.
# Pre-allocates a pool of lightweight tk.Frame / tk.Label rows so resize stays smooth.

from typing import List
import tkinter as tk
import customtkinter as ctk

from .ui_theme import (
    C_BG, C_BAR, C_BORDER, C_HEADER, C_ROW_ODD, C_ROW_EVEN,
    C_TEXT, C_DIM, C_ACCENT, MC_RED, GHOST_BG,
    FONT_HEADER, ROW_H, SCROLLBAR_W,
    COLUMNS, fkdr_color, star_color, ws_color,
)

CELL_PAD = 4
MAX_ROWS = 16


# Sortable, scrollable grid of player BedWars stats
class PlayerTable(ctk.CTkFrame):
    def __init__(self, master, sort_col: str = "stars", sort_asc: bool = False,
                 font_family: str = "Segoe UI", **kw):
        super().__init__(master, fg_color=C_BG, corner_radius=0, **kw)
        self._sort_col    = sort_col
        self._sort_asc    = sort_asc
        self._ghost       = False
        self._font_family = font_family
        self._players: List[dict] = []
        self._pool: List[_PoolRow] = []
        self._build_header()
        self._build_body()

    # Builds the fixed header row using CTkLabels so text aligns with row cells
    def _build_header(self) -> None:
        self._hdr_frame = ctk.CTkFrame(self, fg_color=C_HEADER, corner_radius=0, height=32)
        self._hdr_frame.pack(fill="x", side="top")
        self._hdr_frame.pack_propagate(False)

        self._hdr_labels: list = []
        for key, label, min_w, stretch, anchor in COLUMNS:
            lbl = ctk.CTkLabel(
                self._hdr_frame, text=label,
                font=ctk.CTkFont(*FONT_HEADER), text_color=C_TEXT,
                width=min_w, anchor=anchor, cursor="hand2",
            )
            lbl.pack(side="left", fill="y", expand=stretch, padx=(CELL_PAD, 0))
            lbl.bind("<Button-1>", lambda e, k=key: self._on_header_click(k))
            self._hdr_labels.append(lbl)

        ctk.CTkFrame(self._hdr_frame, fg_color="transparent", width=SCROLLBAR_W).pack(side="right")

        self._hdr_border = ctk.CTkFrame(self, fg_color=C_BORDER, corner_radius=0, height=1)
        self._hdr_border.pack(fill="x", side="top")

    # Builds the scrollable body and pre-allocates the row pool
    def _build_body(self) -> None:
        self._scroll = ctk.CTkScrollableFrame(
            self, fg_color=C_BG,
            scrollbar_button_color=C_BAR,
            scrollbar_button_hover_color=C_ACCENT,
            corner_radius=0,
        )
        self._scroll.pack(fill="both", expand=True, side="top")
        for i in range(MAX_ROWS):
            self._pool.append(_PoolRow(self._scroll, i, self._font_family))

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

    # Updates the font family on header labels and all pool rows without recreating widgets
    def set_font(self, family: str) -> None:
        self._font_family = family
        for lbl in self._hdr_labels:
            lbl.configure(font=ctk.CTkFont(family=family, size=11))
        for row in self._pool:
            row.set_font(family)

    # Replaces the current player list and re-renders all rows
    def set_players(self, players: List[dict]) -> None:
        self._players = list(players)
        self.render()

    # Hides all rows then re-packs them in sorted order with updated data
    def render(self) -> None:
        def sort_key(p: dict):
            v = p.get(self._sort_col, 0)
            return str(v).lower() if isinstance(v, str) else v

        ordered = sorted(self._players, key=sort_key, reverse=not self._sort_asc)

        for row in self._pool:
            row.hide()

        for i, player in enumerate(ordered[:MAX_ROWS]):
            bg  = GHOST_BG if self._ghost else (C_ROW_ODD if i % 2 else C_ROW_EVEN)
            row = self._pool[i]
            row.set_bg(bg)
            row.update(player)
            row.show()

    # Handles a header click – toggles sort direction or changes sort column
    def _on_header_click(self, col: str) -> None:
        if self._sort_col == col:
            self._sort_asc = not self._sort_asc
        else:
            self._sort_col = col
            self._sort_asc = col == "name"
        self.render()


# Pre-allocated lightweight row; updated in-place to avoid widget churn on render
class _PoolRow:
    def __init__(self, parent, idx: int, font_family: str) -> None:
        bg         = C_ROW_ODD if idx % 2 else C_ROW_EVEN
        self._bg   = bg
        self.frame = tk.Frame(parent, bg=bg, height=ROW_H)
        self.frame.pack_propagate(False)
        self._cells: list = []

        for key, _, min_w, stretch, anchor in COLUMNS:
            if key == "head":
                cell = _HeadCell(self.frame, bg, min_w)
                cell.wrapper.pack(side="left", fill="y", padx=(CELL_PAD, 0))
            elif key == "name":
                cell = _NameCell(self.frame, bg, min_w, font_family)
                cell.frame.pack(side="left", fill="both", expand=True, padx=(CELL_PAD, 0))
            else:
                cell = _DataCell(self.frame, bg, min_w, anchor, font_family)
                cell.wrapper.pack(side="left", fill="y", padx=(CELL_PAD, 0))
            self._cells.append((key, cell))

    def update(self, player: dict) -> None:
        loading = player.get("loading", False)
        nicked  = player.get("nicked", False)
        error   = player.get("error")
        for key, cell in self._cells:
            if key == "head":
                if loading:
                    cell.set_loading(self._bg)
                else:
                    cell.set_image(player.get("head_path"), self._bg)
            elif key == "name":
                if loading:
                    cell.set_loading(self._bg)
                else:
                    cell.set_data(
                        player.get("name", "?"),
                        player.get("rank", ""),
                        player.get("rank_color", C_TEXT),
                        nicked, self._bg,
                    )
            else:
                text, color = _resolve(player, key, loading, error)
                cell.set_text(text, color)

    def set_bg(self, bg: str) -> None:
        if bg == self._bg:
            return
        self._bg = bg
        self.frame.configure(bg=bg)
        for _, cell in self._cells:
            cell.set_bg(bg)

    def set_font(self, family: str) -> None:
        for _, cell in self._cells:
            cell.set_font(family)

    def show(self) -> None:
        self.frame.pack(fill="x", side="top")

    def hide(self) -> None:
        self.frame.pack_forget()


# Compound name cell: [rank ]name[ (nick)]
class _NameCell:
    def __init__(self, parent, bg: str, width: int, font_family: str) -> None:
        self._font = (font_family, 12)
        self.frame = tk.Frame(parent, bg=bg, width=width)
        self.frame.pack_propagate(False)
        self._rank = tk.Label(self.frame, bg=bg, font=self._font, anchor="w")
        self._name = tk.Label(self.frame, bg=bg, font=self._font, anchor="w")
        self._nick = tk.Label(self.frame, text=" (nick)", bg=bg, fg=MC_RED, font=self._font)

    def set_loading(self, bg: str) -> None:
        self._reset(bg)
        self._name.configure(text="…", fg=C_DIM)
        self._name.pack(side="left")

    def set_data(self, name: str, rank: str, rank_color: str, nicked: bool, bg: str) -> None:
        self._reset(bg)
        if rank:
            self._rank.configure(text=f"{rank} {name}", fg=rank_color)
            self._rank.pack(side="left", fill="both", expand=True)
        else:
            self._name.configure(text=name, fg=C_TEXT)
            self._name.pack(side="left", fill="both", expand=True)
        if nicked:
            self._nick.pack(side="left")

    def set_bg(self, bg: str) -> None:
        self.frame.configure(bg=bg)
        for w in (self._rank, self._name, self._nick):
            w.configure(bg=bg)

    def set_font(self, family: str) -> None:
        self._font = (family, 12)
        for w in (self._rank, self._name, self._nick):
            w.configure(font=self._font)

    def _reset(self, bg: str) -> None:
        self.frame.configure(bg=bg)
        for w in (self._rank, self._name, self._nick):
            w.pack_forget()
            w.configure(bg=bg)


# Fixed-width cell that displays a player head avatar image
class _HeadCell:
    def __init__(self, parent, bg: str, width: int) -> None:
        self._photo = None  # hold reference to prevent GC
        self.wrapper = tk.Frame(parent, bg=bg, width=width)
        self.wrapper.pack_propagate(False)
        self.label = tk.Label(self.wrapper, bg=bg, anchor="center", bd=0, highlightthickness=0)
        self.label.pack(fill="both", expand=True)

    def set_image(self, path: "str | None", bg: str) -> None:
        self.wrapper.configure(bg=bg)
        self.label.configure(bg=bg)
        if path:
            try:
                photo = tk.PhotoImage(file=path)
                self._photo = photo
                self.label.configure(image=photo, text="")
                return
            except Exception:
                pass
        self._photo = None
        self.label.configure(image="", text="")

    def set_loading(self, bg: str) -> None:
        self.set_image(None, bg)

    def set_bg(self, bg: str) -> None:
        self.wrapper.configure(bg=bg)
        self.label.configure(bg=bg)

    def set_font(self, family: str) -> None:
        pass  # no text in this cell


# Fixed-width wrapper frame containing a single data label
class _DataCell:
    def __init__(self, parent, bg: str, width: int, anchor: str, font_family: str) -> None:
        self._font   = (font_family, 12)
        self.wrapper = tk.Frame(parent, bg=bg, width=width)
        self.wrapper.pack_propagate(False)
        self.label   = tk.Label(self.wrapper, bg=bg, fg=C_TEXT, font=self._font, anchor=anchor)
        self.label.pack(fill="both", expand=True)

    def set_text(self, text: str, color: str) -> None:
        self.label.configure(text=text, fg=color)

    def set_bg(self, bg: str) -> None:
        self.wrapper.configure(bg=bg)
        self.label.configure(bg=bg)

    def set_font(self, family: str) -> None:
        self._font = (family, 12)
        self.label.configure(font=self._font)


def _resolve(player: dict, key: str, loading: bool, error) -> tuple:
    if loading:
        return "…", C_DIM
    if player.get("nicked"):
        return "—", C_DIM
    if error:
        return (error[:14], MC_RED) if key == "fkdr" else ("—", C_DIM)
    return _fmt(player, key)


def _fmt(p: dict, key: str) -> tuple:
    if key == "stars":
        s = p.get("stars", 0)
        return f"[{s}✫]", star_color(s)
    if key == "fkdr":
        v = p.get("fkdr", 0.0)
        return f"{v:.2f}", fkdr_color(v)
    if key == "wins":
        return str(p.get("wins", 0)), C_TEXT
    if key == "winstreak":
        ws = p.get("winstreak", 0)
        return str(ws), ws_color(ws)
    return str(p.get(key, "")), C_TEXT
