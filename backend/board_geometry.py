"""
Dartboard geometry, coordinate conversion, calibration reference presets,
and checkout tables for LocalDarts.
"""

from __future__ import annotations
import math
from dataclasses import dataclass, asdict
from typing import Dict, List, Optional, Tuple

# Official tournament bristle dartboard dimensions in mm (WDF / PDC standard)
R_DOUBLE_OUTER_MM = 170.0
R_DOUBLE_INNER_MM = 160.0
R_TRIPLE_OUTER_MM = 107.4
R_TRIPLE_INNER_MM = 97.4
R_OUTER_BULL_MM = 15.9
R_INNER_BULL_MM = 6.35

# Normalized radii where Outer Double ring radius = 1.0
R_INNER_BULL = R_INNER_BULL_MM / R_DOUBLE_OUTER_MM      # ~0.03735
R_OUTER_BULL = R_OUTER_BULL_MM / R_DOUBLE_OUTER_MM      # ~0.09353
R_TRIPLE_INNER = R_TRIPLE_INNER_MM / R_DOUBLE_OUTER_MM  # ~0.57294
R_TRIPLE_OUTER = R_TRIPLE_OUTER_MM / R_DOUBLE_OUTER_MM  # ~0.63176
R_DOUBLE_INNER = R_DOUBLE_INNER_MM / R_DOUBLE_OUTER_MM  # ~0.94118
R_DOUBLE_OUTER = 1.0

# Clockwise sectors starting at 12 o'clock (0 deg)
SECTORS_CLOCKWISE: List[int] = [
    20, 1, 18, 4, 13, 6, 10, 15, 2, 17,
    3, 19, 7, 16, 8, 11, 14, 9, 12, 5
]


def polar_to_board_xy(radius_norm: float, angle_deg_from_top_cw: float) -> Tuple[float, float]:
    """
    Convert normalized polar coordinates (r, angle clockwise from 12 o'clock)
    into standard board Cartesian coordinates (x, y) where:
      - center is (0, 0)
      - +x is right (towards 6)
      - +y is down (towards 3) / image coordinate convention, or -y is up (towards 20).
    We use image-aligned board coordinates:
      x = r * sin(theta)   (+x right towards sector 6)
      y = -r * cos(theta)  (-y up towards sector 20, +y down towards sector 3)
    """
    rad = math.radians(angle_deg_from_top_cw)
    x = radius_norm * math.sin(rad)
    y = -radius_norm * math.cos(rad)
    return (round(x, 6), round(y, 6))


# Calibration reference point presets on the Outer Double wire (r = 1.0)
CALIBRATION_PRESETS: Dict[str, dict] = {
    "autodarts_wires_ccw": {
        "id": "autodarts_wires_ccw",
        "name": "Autodarts Standard-Drähte (5|20, 13|6, 17|3, 8|11)",
        "description": "Äußerer Double-Draht an den 4 Draht-Übergängen jeweils links/gegen den Uhrzeigersinn von 20, 6, 3 und 11.",
        "points": [
            {"label": "1. Draht 5 | 20 (Oben)", "angle_deg": -9.0, "xy": polar_to_board_xy(1.0, -9.0)},
            {"label": "2. Draht 13 | 6 (Rechts)", "angle_deg": 81.0, "xy": polar_to_board_xy(1.0, 81.0)},
            {"label": "3. Draht 17 | 3 (Unten)", "angle_deg": 171.0, "xy": polar_to_board_xy(1.0, 171.0)},
            {"label": "4. Draht 8 | 11 (Links)", "angle_deg": 261.0, "xy": polar_to_board_xy(1.0, 261.0)},
        ],
    },
    "wires_cw": {
        "id": "wires_cw",
        "name": "Draht-Übergänge rechts (20|1, 6|10, 3|19, 11|14)",
        "description": "Äußerer Double-Draht an den 4 Draht-Übergängen jeweils im Uhrzeigersinn von 20, 6, 3 und 11.",
        "points": [
            {"label": "1. Draht 20 | 1 (Oben)", "angle_deg": 9.0, "xy": polar_to_board_xy(1.0, 9.0)},
            {"label": "2. Draht 6 | 10 (Rechts)", "angle_deg": 99.0, "xy": polar_to_board_xy(1.0, 99.0)},
            {"label": "3. Draht 3 | 19 (Unten)", "angle_deg": 189.0, "xy": polar_to_board_xy(1.0, 189.0)},
            {"label": "4. Draht 11 | 14 (Links)", "angle_deg": 279.0, "xy": polar_to_board_xy(1.0, 279.0)},
        ],
    },
    "cardinal_centers": {
        "id": "cardinal_centers",
        "name": "12 / 3 / 6 / 9 Uhr Mitte (Außenkante D20, D6, D3, D11)",
        "description": "Exakte Mitte der Außenkante des Double-Feldes bei 20 (oben), 6 (rechts), 3 (unten) und 11 (links).",
        "points": [
            {"label": "1. Mitte Außenkante D20 (12 Uhr)", "angle_deg": 0.0, "xy": polar_to_board_xy(1.0, 0.0)},
            {"label": "2. Mitte Außenkante D6 (3 Uhr)", "angle_deg": 90.0, "xy": polar_to_board_xy(1.0, 90.0)},
            {"label": "3. Mitte Außenkante D3 (6 Uhr)", "angle_deg": 180.0, "xy": polar_to_board_xy(1.0, 180.0)},
            {"label": "4. Mitte Außenkante D11 (9 Uhr)", "angle_deg": 270.0, "xy": polar_to_board_xy(1.0, 270.0)},
        ],
    },
}


@dataclass
class DartHit:
    """Represents a scored dart on the board."""
    x: float                 # Normalized board X (-1.2 .. +1.2, where 1.0 = outer double)
    y: float                 # Normalized board Y (-1.2 .. +1.2)
    r: float                 # Normalized radius from center
    angle_deg: float         # Angle clockwise from 12 o'clock (0..360)
    sector: int              # Base number (1..20, 25 for Bull, 0 for Miss)
    multiplier: int          # 1 (Single), 2 (Double), 3 (Triple), 0 (Miss)
    score: int               # Total points (e.g. 60 for T20, 50 for Bull, 0 for Miss)
    ring: str                # "DBULL", "SBULL", "INNER_SINGLE", "TRIPLE", "OUTER_SINGLE", "DOUBLE", "MISS"
    label: str               # Short display string e.g. "T20", "D16", "S19", "BULL", "25", "MISS"
    confidence: float = 1.0  # Detection confidence (0..1)
    cameras_used: int = 1    # Number of cameras that contributed to this hit
    source: str = "camera"   # "camera", "manual", or "simulation"

    def to_dict(self) -> dict:
        return asdict(self)


def coords_to_hit(
    x: float,
    y: float,
    confidence: float = 1.0,
    cameras_used: int = 1,
    source: str = "camera",
) -> DartHit:
    """
    Convert normalized board coordinates (x, y) into a DartHit with sector,
    multiplier, ring type, and score.
    Coordinate convention:
      (0, 0) = center of Bullseye
      (0, -1) = top of D20 (12 o'clock)
      (1, 0) = right of D6 (3 o'clock)
      (0, 1) = bottom of D3 (6 o'clock)
      (-1, 0) = left of D11 (9 o'clock)
    """
    r = math.hypot(x, y)
    # Angle clockwise from 12 o'clock (0, -1):
    angle_rad = math.atan2(x, -y)
    angle_deg = math.degrees(angle_rad) % 360.0

    # Check Bullseye first
    if r <= R_INNER_BULL:
        return DartHit(
            x=round(x, 4),
            y=round(y, 4),
            r=round(r, 4),
            angle_deg=round(angle_deg, 2),
            sector=25,
            multiplier=2,
            score=50,
            ring="DBULL",
            label="BULL",
            confidence=round(confidence, 3),
            cameras_used=cameras_used,
            source=source,
        )
    if r <= R_OUTER_BULL:
        return DartHit(
            x=round(x, 4),
            y=round(y, 4),
            r=round(r, 4),
            angle_deg=round(angle_deg, 2),
            sector=25,
            multiplier=1,
            score=25,
            ring="SBULL",
            label="25",
            confidence=round(confidence, 3),
            cameras_used=cameras_used,
            source=source,
        )

    # Determine clock sector (each sector is 18 deg wide, centered at index * 18 deg)
    sector_idx = int(((angle_deg + 9.0) % 360.0) // 18.0)
    sector = SECTORS_CLOCKWISE[sector_idx]

    if r > R_DOUBLE_OUTER:
        return DartHit(
            x=round(x, 4),
            y=round(y, 4),
            r=round(r, 4),
            angle_deg=round(angle_deg, 2),
            sector=0,
            multiplier=0,
            score=0,
            ring="MISS",
            label="MISS",
            confidence=round(confidence, 3),
            cameras_used=cameras_used,
            source=source,
        )

    if r >= R_DOUBLE_INNER:
        multiplier = 2
        ring = "DOUBLE"
        label = f"D{sector}"
    elif R_TRIPLE_INNER <= r <= R_TRIPLE_OUTER:
        multiplier = 3
        ring = "TRIPLE"
        label = f"T{sector}"
    elif r < R_TRIPLE_INNER:
        multiplier = 1
        ring = "INNER_SINGLE"
        label = f"S{sector}"
    else:
        multiplier = 1
        ring = "OUTER_SINGLE"
        label = f"S{sector}"

    return DartHit(
        x=round(x, 4),
        y=round(y, 4),
        r=round(r, 4),
        angle_deg=round(angle_deg, 2),
        sector=sector,
        multiplier=multiplier,
        score=sector * multiplier,
        ring=ring,
        label=label,
        confidence=round(confidence, 3),
        cameras_used=cameras_used,
        source=source,
    )


def sector_multiplier_to_coords(sector: int, multiplier: int) -> Tuple[float, float]:
    """
    Convert a (sector, multiplier) selection into representative normalized
    board coordinates (x, y) for visualization when manually entered.
    """
    if sector == 0 or multiplier == 0:
        return (0.0, -1.12)
    if sector == 25:
        if multiplier == 2:
            return (0.0, 0.0)
        return (0.0, -0.065)

    try:
        idx = SECTORS_CLOCKWISE.index(sector)
    except ValueError:
        return (0.0, -1.12)

    angle_deg = idx * 18.0
    if multiplier == 3:
        r = (R_TRIPLE_INNER + R_TRIPLE_OUTER) / 2.0
    elif multiplier == 2:
        r = (R_DOUBLE_INNER + R_DOUBLE_OUTER) / 2.0
    else:
        r = (R_TRIPLE_OUTER + R_DOUBLE_INNER) / 2.0
    return polar_to_board_xy(r, angle_deg)


# Comprehensive PDC/WDF Double-Out Checkout Table (scores 170 down to 2)
CHECKOUT_TABLE: Dict[int, List[str]] = {
    170: ["T20", "T20", "BULL"],
    167: ["T20", "T19", "BULL"],
    164: ["T20", "T18", "BULL"],
    161: ["T20", "T17", "BULL"],
    160: ["T20", "T20", "D20"],
    158: ["T20", "T20", "D19"],
    157: ["T20", "T19", "D20"],
    156: ["T20", "T20", "D18"],
    155: ["T20", "T19", "D19"],
    154: ["T20", "T18", "D20"],
    153: ["T20", "T19", "D18"],
    152: ["T20", "T20", "D16"],
    151: ["T20", "T17", "D20"],
    150: ["T20", "T18", "D18"],
    149: ["T20", "T19", "D16"],
    148: ["T20", "T16", "D20"],
    147: ["T20", "T17", "D18"],
    146: ["T20", "T18", "D16"],
    145: ["T20", "T15", "D20"],
    144: ["T20", "T20", "D12"],
    143: ["T20", "T17", "D16"],
    142: ["T20", "T14", "D20"],
    141: ["T20", "T19", "D12"],
    140: ["T20", "T16", "D16"],
    139: ["T19", "T14", "D20"],
    138: ["T20", "T18", "D12"],
    137: ["T19", "T16", "D16"],
    136: ["T20", "T20", "D8"],
    135: ["BULL", "T15", "D20"],
    134: ["T20", "T14", "D16"],
    133: ["T20", "T19", "D8"],
    132: ["BULL", "BULL", "D16"],
    131: ["T20", "T13", "D16"],
    130: ["T20", "T20", "D5"],
    129: ["T19", "T16", "D12"],
    128: ["T18", "T14", "D16"],
    127: ["T20", "T17", "D8"],
    126: ["T19", "T19", "D6"],
    125: ["25", "T20", "D20"],
    124: ["T20", "T16", "D8"],
    123: ["T19", "T16", "D9"],
    122: ["T18", "T20", "D4"],
    121: ["T20", "T11", "D14"],
    120: ["T20", "S20", "D20"],
    119: ["T19", "T12", "D13"],
    118: ["T20", "S18", "D20"],
    117: ["T20", "S17", "D20"],
    116: ["T20", "S16", "D20"],
    115: ["T20", "S15", "D20"],
    114: ["T20", "S14", "D20"],
    113: ["T20", "S13", "D20"],
    112: ["T20", "S12", "D20"],
    111: ["T20", "S19", "D16"],
    110: ["T20", "S18", "D16"],
    109: ["T20", "S17", "D16"],
    108: ["T20", "S16", "D16"],
    107: ["T19", "S18", "D16"],
    106: ["T20", "S14", "D16"],
    105: ["T20", "S13", "D16"],
    104: ["T18", "S18", "D16"],
    103: ["T20", "S11", "D16"],
    102: ["T20", "S10", "D16"],
    101: ["T20", "S9", "D16"],
    100: ["T20", "D20"],
    99: ["T19", "S10", "D16"],
    98: ["T20", "D19"],
    97: ["T19", "D20"],
    96: ["T20", "D18"],
    95: ["T19", "D19"],
    94: ["T18", "D20"],
    93: ["T19", "D18"],
    92: ["T20", "D16"],
    91: ["T17", "D20"],
    90: ["T20", "D15"],
    89: ["T19", "D16"],
    88: ["T20", "D14"],
    87: ["T17", "D18"],
    86: ["T18", "D16"],
    85: ["T15", "D20"],
    84: ["T20", "D12"],
    83: ["T17", "D16"],
    82: ["BULL", "D16"],
    81: ["T19", "D12"],
    80: ["T20", "D10"],
    79: ["T19", "D11"],
    78: ["T18", "D12"],
    77: ["T19", "D10"],
    76: ["T20", "D8"],
    75: ["T17", "D12"],
    74: ["T14", "D16"],
    73: ["T19", "D8"],
    72: ["T16", "D12"],
    71: ["T13", "D16"],
    70: ["T18", "D8"],
    69: ["T19", "D6"],
    68: ["T20", "D4"],
    67: ["T17", "D8"],
    66: ["T10", "D18"],
    65: ["25", "D20"],
    64: ["T16", "D8"],
    63: ["T13", "D12"],
    62: ["T10", "D16"],
    61: ["25", "D18"],
    60: ["S20", "D20"],
    59: ["S19", "D20"],
    58: ["S18", "D20"],
    57: ["S17", "D20"],
    56: ["S16", "D20"],
    55: ["S15", "D20"],
    54: ["S14", "D20"],
    53: ["S13", "D20"],
    52: ["S20", "D16"],
    51: ["S19", "D16"],
    50: ["BULL"],
    49: ["S17", "D16"],
    48: ["S16", "D16"],
    47: ["S15", "D16"],
    46: ["S14", "D16"],
    45: ["S13", "D16"],
    44: ["S12", "D16"],
    43: ["S11", "D16"],
    42: ["S10", "D16"],
    41: ["S9", "D16"],
}
for _even in range(40, 1, -2):
    CHECKOUT_TABLE[_even] = [f"D{_even // 2}"]


def get_checkout_guide(remaining_score: int, darts_left: int = 3, double_out: bool = True) -> Optional[List[str]]:
    """Return recommended checkout sequence for the remaining score and darts left in turn."""
    if remaining_score < 2 or remaining_score > 170:
        return None
    if not double_out:
        if remaining_score <= 60:
            if remaining_score <= 20:
                return [f"S{remaining_score}"]
            if remaining_score % 3 == 0:
                return [f"T{remaining_score // 3}"]
            if remaining_score % 2 == 0 and remaining_score <= 40:
                return [f"D{remaining_score // 2}"]
    guide = CHECKOUT_TABLE.get(remaining_score)
    if not guide:
        return None
    if len(guide) > darts_left:
        return None
    return guide
