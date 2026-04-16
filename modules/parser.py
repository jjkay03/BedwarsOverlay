# Extracts BedWars stats and Hypixel rank from a raw Hypixel player dict.
from typing import Optional

# Minecraft §-code hex equivalents used for rank colours
_MC_GREEN = "#55FF55"   # §a  VIP, VIP+
_MC_AQUA  = "#55FFFF"   # §b  MVP, MVP+
_MC_GOLD  = "#FFAA00"   # §6  MVP++ (SUPERSTAR)
_MC_RED   = "#FF5555"   # §c  staff / special ranks


# Returns (bracket_label, hex_color) for a player's Hypixel rank
def _rank_info(player: dict) -> tuple:
    rank    = player.get("rank", "NORMAL")
    monthly = player.get("monthlyPackageRank", "NONE")
    package = player.get("newPackageRank", "NONE")

    # Staff / special ranks take priority over purchased ones
    if rank and rank not in ("NORMAL", "NONE", ""):
        label = {"YOUTUBER": "YOUTUBE", "MODERATOR": "MOD"}.get(rank, rank)
        return f"[{label}]", _MC_RED

    if monthly == "SUPERSTAR":
        return "[MVP++]", _MC_GOLD

    if package == "MVP_PLUS":
        return "[MVP+]", _MC_AQUA
    if package == "MVP":
        return "[MVP]", _MC_AQUA
    if package == "VIP_PLUS":
        return "[VIP+]", _MC_GREEN
    if package == "VIP":
        return "[VIP]", _MC_GREEN

    return "", ""


# Returns a stats dict with keys: name, stars, fkdr, wins, winstreak, rank, rank_color, nicked, error
def parse_bedwars(player: Optional[dict]) -> dict:
    if player is None:
        return _stub()

    bw    = player.get("stats", {}).get("Bedwars", {})
    stars = player.get("achievements", {}).get("bedwars_level", 0)

    fk   = bw.get("final_kills_bedwars", 0)
    fd   = bw.get("final_deaths_bedwars", 0)
    fkdr = round(fk / fd, 2) if fd > 0 else float(fk)

    rank_label, rank_color = _rank_info(player)

    return {
        "name":       player.get("displayname", "Unknown"),
        "stars":      int(stars),
        "fkdr":       fkdr,
        "wins":       int(bw.get("wins_bedwars", 0)),
        "winstreak":  int(bw.get("winstreak", 0)),
        "rank":       rank_label,
        "rank_color": rank_color,
        "nicked":     False,
        "error":      None,
    }


def _stub() -> dict:
    return {
        "name": "?", "stars": 0, "fkdr": 0.0, "wins": 0, "winstreak": 0,
        "rank": "", "rank_color": "", "nicked": True, "error": "Nicked / not found",
    }
