# Color palette, font tuples, column definitions, and stat-color helpers.
# All other UI files import from here so styling stays in one place.

import customtkinter as ctk

ctk.set_appearance_mode("dark")
ctk.set_default_color_theme("blue")

C_BG        = "#0e0e0e"
C_BAR       = "#161616"
C_ROW_ODD   = "#131313"
C_ROW_EVEN  = "#101010"
C_HEADER    = "#1a1a1a"
C_BORDER    = "#2a2a2a"
C_TEXT      = "#e0e0e0"
C_DIM       = "#666666"
C_ACCENT    = "#5865f2"
C_ACCENT_HV = "#4752c4"
MC_RED      = "#FF5555"   # §c – nick indicator, error

# Ghost mode punches the background out via Windows transparentcolor.
# All background frames are set to this colour; text pixels (different colour) stay visible.
GHOST_BG    = "#010101"

FONT_TITLE  = ("Segoe UI", 13, "bold")
FONT_HEADER = ("Segoe UI", 11, "bold")
FONT_ROW    = ("Segoe UI", 12)
FONT_STATUS = ("Segoe UI", 11)

ROW_H       = 30
SCROLLBAR_W = 14   # width reserved on header right to align with CTkScrollableFrame scrollbar

# Each column: (data key, header label, min width, stretch, text anchor)
COLUMNS = [
    ("name",      "Player", 140, True,  "w"),
    ("stars",     "Stars",   68, False, "center"),
    ("fkdr",      "FKDR",    68, False, "center"),
    ("wins",      "Wins",    68, False, "center"),
    ("winstreak", "WS",      52, False, "center"),
]

_FKDR_COLORS = [
    (5.0, "#ff2d55"),
    (3.0, "#ff9f0a"),
    (2.0, "#ffd60a"),
    (1.0, "#30d158"),
    (0.0, "#8e8e93"),
]

# Thresholds map to exact Minecraft §-code hex values.
# 1000+ uses a rotating rainbow cycle (one colour per 100-star prestige).
_STAR_COLORS = [
    (900, "#AA00AA"),   # §5  dark magenta
    (800, "#0000AA"),   # §1  dark blue
    (700, "#FF55FF"),   # §d  magenta
    (600, "#AA0000"),   # §4  dark red
    (500, "#00AAAA"),   # §3  dark aqua
    (400, "#00AA00"),   # §2  dark green
    (300, "#55FFFF"),   # §b  aqua
    (200, "#FFAA00"),   # §6  gold
    (100, "#FFFFFF"),   # §f  white
    (0,   "#AAAAAA"),   # §7  grey  (iron / no prestige)
]

_RAINBOW_CYCLE = [
    "#FF5555",  # §c  red
    "#FFAA00",  # §6  gold
    "#FFFF55",  # §e  yellow
    "#55FF55",  # §a  green
    "#55FFFF",  # §b  aqua
    "#5555FF",  # §9  blue
    "#FF55FF",  # §d  magenta
]

# Opacity presets shown in Settings.
# "ghost" uses transparentcolor so only background pixels disappear; text stays opaque.
OPACITY_VALUES = {"solid": 1.0,  "semi": 0.85, "ghost": 1.0}
OPACITY_LABELS = {"solid": "Solid", "semi": "Semi", "ghost": "Ghost"}


# Returns a hex color for a given FKDR value
def fkdr_color(v: float) -> str:
    for threshold, color in _FKDR_COLORS:
        if v >= threshold:
            return color
    return C_DIM


# Returns a hex color matching the player's star prestige tier
def star_color(s: int) -> str:
    if s >= 1000:
        return _RAINBOW_CYCLE[(s // 100) % len(_RAINBOW_CYCLE)]
    for threshold, color in _STAR_COLORS:
        if s >= threshold:
            return color
    return C_DIM
