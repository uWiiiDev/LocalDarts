"""
Complete Dart Game Engine for LocalDarts supporting all 16 game modes:
  1.  x01           - X01 (301 / 501 / 701 / 901 / 170, Straight/Double In, Double/Single/Master Out)
  2.  cricket       - Cricket (Standard & Cut-Throat)
  3.  atc           - Around the Clock (1..20 + Bull, Standard & Fast-Forward)
  4.  shanghai      - Shanghai (Rounds 1..20 with instant Shanghai win)
  5.  highscore     - Freies Training / Highscore
  6.  elimination   - Elimination ("Mensch ärgere dich nicht" - 0 to 301/501, reset opponents on exact match)
  7.  killer        - Killer (Own target number, build up to 3 lives = KILLER, eliminate opponents)
  8.  halve_it      - Halve It (8 target rounds; missing round target with all 3 darts halves score)
  9.  gotcha        - Gotcha (0 to 301, opponent reset, milestone bust reset, Bullseye score swap)
  10. tictactoe     - Tic-Tac-Toe Darts (3x3 board of sectors with Bull center, 3 marks to claim cell)
  11. bermuda       - Bermuda Triangle (13 rounds: 12,13,14,D,15,16,17,T,18,19,20,25,BULL; miss halves score)
  12. bobs27        - Bob's 27 (Start at 27 pts, D1..D20 + DBull; hits add, 0 hits in turn subtracts)
  13. jdc_challenge - JDC Challenge (19 rounds: Shanghai 10-15, Doubles D1-DBull, Shanghai 15-20)
  14. catch40       - Catch 40 (Checkouts 61..100 with 6 darts each, 3/2/1 point scoring)
  15. checkout121   - 121 Checkout Ladder (Start at 121 with 9 darts; success -> +1, fail -> back to 121)
  16. scoring100    - Bulls-Eye / Scoring 100 (33 rounds / 99 darts on target sector 20, 19, 18, or Bull)
"""

from __future__ import annotations
import copy
import random
import time
from dataclasses import dataclass, field
from typing import Dict, List, Optional

from .board_geometry import DartHit, get_checkout_guide

CRICKET_NUMBERS = [20, 19, 18, 17, 16, 15, 25]
ATC_TARGETS = list(range(1, 21)) + [25]

HALVE_IT_STAGES = [
    {"id": "20", "label": "Feld 20", "type": "sector", "target": 20},
    {"id": "16", "label": "Feld 16", "type": "sector", "target": 16},
    {"id": "DOUBLE", "label": "Beliebiges Double", "type": "double", "target": 0},
    {"id": "14", "label": "Feld 14", "type": "sector", "target": 14},
    {"id": "TRIPLE", "label": "Beliebiges Triple", "type": "triple", "target": 0},
    {"id": "18", "label": "Feld 18", "type": "sector", "target": 18},
    {"id": "41_PTS", "label": "Mind. 41 Punkte", "type": "min_sum", "target": 41},
    {"id": "BULL", "label": "Single / Double Bull", "type": "sector", "target": 25},
]

BERMUDA_STAGES = [
    {"id": "12", "label": "Feld 12", "type": "sector", "target": 12},
    {"id": "13", "label": "Feld 13", "type": "sector", "target": 13},
    {"id": "14", "label": "Feld 14", "type": "sector", "target": 14},
    {"id": "DOUBLE", "label": "Beliebiges Double", "type": "double", "target": 0},
    {"id": "15", "label": "Feld 15", "type": "sector", "target": 15},
    {"id": "16", "label": "Feld 16", "type": "sector", "target": 16},
    {"id": "17", "label": "Feld 17", "type": "sector", "target": 17},
    {"id": "TRIPLE", "label": "Beliebiges Triple", "type": "triple", "target": 0},
    {"id": "18", "label": "Feld 18", "type": "sector", "target": 18},
    {"id": "19", "label": "Feld 19", "type": "sector", "target": 19},
    {"id": "20", "label": "Feld 20", "type": "sector", "target": 20},
    {"id": "SBULL", "label": "Single Bull (25)", "type": "sbull", "target": 25},
    {"id": "DBULL", "label": "Double Bull (50)", "type": "dbull", "target": 25},
]

TICTACTOE_LINES = [
    (0, 1, 2), (3, 4, 5), (6, 7, 8),  # rows
    (0, 3, 6), (1, 4, 7), (2, 5, 8),  # cols
    (0, 4, 8), (2, 4, 6),             # diagonals
]


@dataclass
class PlayerState:
    name: str
    score: int = 501
    legs_won: int = 0
    sets_won: int = 0
    darts_thrown_leg: int = 0
    darts_thrown_total: int = 0
    points_scored_total: int = 0
    first9_points: int = 0
    first9_darts: int = 0
    checkout_attempts: int = 0
    checkout_hits: int = 0
    count_180: int = 0
    count_140_plus: int = 0
    count_100_plus: int = 0
    count_60_plus: int = 0
    in_achieved: bool = True

    # Mode-specific player attributes
    cricket_marks: Dict[int, int] = field(default_factory=lambda: {n: 0 for n in CRICKET_NUMBERS})
    atc_index: int = 0

    # Killer state
    killer_number: int = 0
    killer_lives: int = 0
    is_killer: bool = False
    eliminated: bool = False

    # Bob's 27 state
    bobs27_failed: bool = False

    # Catch 40 / 121 Checkout state
    sub_target: int = 61
    sub_remaining: int = 61
    sub_darts_used: int = 0
    best_checkout: int = 0

    # Scoring 100 state
    target_hits: int = 0

    # Coordinate history for heatmap / dispersion
    hit_history: List[dict] = field(default_factory=list)

    @property
    def three_dart_avg(self) -> float:
        if self.darts_thrown_total == 0:
            return 0.0
        return round((self.points_scored_total / self.darts_thrown_total) * 3.0, 2)

    @property
    def first9_avg(self) -> float:
        if self.first9_darts == 0:
            return 0.0
        return round((self.first9_points / self.first9_darts) * 3.0, 2)

    @property
    def checkout_pct(self) -> float:
        if self.checkout_attempts == 0:
            return 0.0
        return round((self.checkout_hits / self.checkout_attempts) * 100.0, 1)

    def to_dict(
        self,
        current_turn_darts_left: int = 3,
        double_out: bool = True,
        mode: str = "x01",
        target_badge: Optional[str] = None,
    ) -> dict:
        checkout = None
        if mode == "x01":
            checkout = get_checkout_guide(self.score, darts_left=current_turn_darts_left, double_out=double_out)
        elif mode in ("catch40", "checkout121"):
            checkout = get_checkout_guide(self.sub_remaining, darts_left=current_turn_darts_left, double_out=True)

        atc_target = ATC_TARGETS[min(self.atc_index, len(ATC_TARGETS) - 1)] if self.atc_index < len(ATC_TARGETS) else 0
        return {
            "name": self.name,
            "score": self.score,
            "legs_won": self.legs_won,
            "sets_won": self.sets_won,
            "darts_thrown_leg": self.darts_thrown_leg,
            "darts_thrown_total": self.darts_thrown_total,
            "three_dart_avg": self.three_dart_avg,
            "first9_avg": self.first9_avg,
            "checkout_pct": self.checkout_pct,
            "checkout_attempts": self.checkout_attempts,
            "checkout_hits": self.checkout_hits,
            "count_180": self.count_180,
            "count_140_plus": self.count_140_plus,
            "count_100_plus": self.count_100_plus,
            "count_60_plus": self.count_60_plus,
            "in_achieved": self.in_achieved,
            "checkout_guide": checkout,
            "cricket_marks": {str(k): v for k, v in self.cricket_marks.items()},
            "atc_target": atc_target,
            "atc_index": self.atc_index,
            "killer_number": self.killer_number,
            "killer_lives": self.killer_lives,
            "is_killer": self.is_killer,
            "eliminated": self.eliminated,
            "sub_target": self.sub_target,
            "sub_remaining": self.sub_remaining,
            "sub_darts_used": self.sub_darts_used,
            "best_checkout": self.best_checkout,
            "target_hits": self.target_hits,
            "target_badge": target_badge,
            "hit_history": self.hit_history[-60:],
        }


class GameEngine:
    """Manages game rules, turns, undo stack, and dart corrections across all 16 modes."""

    def __init__(self):
        self.mode: str = "x01"
        self.x01_start_score: int = 501
        self.double_in: bool = False
        self.out_mode: str = "double"
        self.legs_to_win: int = 3
        self.cricket_variant: str = "standard"
        self.atc_fast_forward: bool = False
        self.max_rounds: int = 10
        self.training_target_sector: int = 20

        self.players: List[PlayerState] = []
        self.current_player_idx: int = 0
        self.leg_starter_idx: int = 0
        self.round_number: int = 1

        # Current turn tracking
        self.turn_darts: List[DartHit] = []
        self.turn_start_snapshot: Optional[dict] = None
        self.turn_busted: bool = False
        self.turn_complete: bool = False
        self.waiting_for_takeout: bool = False
        self.winner_name: Optional[str] = None
        self.last_announcement: str = "Neues Spiel gestartet"
        self.last_caller_speech: str = "Game on!"

        # Tic-Tac-Toe 3x3 board state
        self.ttt_numbers: List[int] = [20, 19, 18, 17, 25, 16, 15, 14, 13]
        self.ttt_owners: List[Optional[int]] = [None] * 9
        self.ttt_marks: List[Dict[int, int]] = [{} for _ in range(9)]

        # Turn-specific hit counter for Halve It / Bermuda / Bob's 27
        self.turn_stage_hits: int = 0
        self.turn_stage_points: int = 0

        # Undo stack
        self._undo_stack: List[dict] = []

        self.new_game(mode="x01", player_names=["Spieler 1", "Spieler 2"], x01_start_score=501)

    def _save_undo_snapshot(self) -> None:
        snapshot = {
            "players": copy.deepcopy(self.players),
            "current_player_idx": self.current_player_idx,
            "leg_starter_idx": self.leg_starter_idx,
            "round_number": self.round_number,
            "turn_darts": copy.deepcopy(self.turn_darts),
            "turn_start_snapshot": copy.deepcopy(self.turn_start_snapshot),
            "turn_busted": self.turn_busted,
            "turn_complete": self.turn_complete,
            "waiting_for_takeout": self.waiting_for_takeout,
            "winner_name": self.winner_name,
            "last_announcement": self.last_announcement,
            "ttt_owners": copy.deepcopy(self.ttt_owners),
            "ttt_marks": copy.deepcopy(self.ttt_marks),
            "turn_stage_hits": self.turn_stage_hits,
            "turn_stage_points": self.turn_stage_points,
        }
        self._undo_stack.append(snapshot)
        if len(self._undo_stack) > 60:
            self._undo_stack.pop(0)

    def _capture_turn_start(self) -> None:
        p = self.players[self.current_player_idx]
        self.turn_stage_hits = 0
        self.turn_stage_points = 0
        self.turn_start_snapshot = {
            "score": p.score,
            "in_achieved": p.in_achieved,
            "darts_thrown_leg": p.darts_thrown_leg,
            "darts_thrown_total": p.darts_thrown_total,
            "points_scored_total": p.points_scored_total,
            "first9_points": p.first9_points,
            "first9_darts": p.first9_darts,
            "checkout_attempts": p.checkout_attempts,
            "cricket_marks": copy.deepcopy(p.cricket_marks),
            "atc_index": p.atc_index,
            "sub_target": p.sub_target,
            "sub_remaining": p.sub_remaining,
            "sub_darts_used": p.sub_darts_used,
        }

    def new_game(
        self,
        mode: str = "x01",
        player_names: Optional[List[str]] = None,
        x01_start_score: int = 501,
        double_in: bool = False,
        out_mode: str = "double",
        legs_to_win: int = 3,
        cricket_variant: str = "standard",
        atc_fast_forward: bool = False,
        max_rounds: int = 10,
        training_target_sector: int = 20,
    ) -> dict:
        self.mode = mode
        self.x01_start_score = int(x01_start_score)
        self.double_in = bool(double_in)
        self.out_mode = out_mode
        self.legs_to_win = max(1, int(legs_to_win))
        self.cricket_variant = cricket_variant
        self.atc_fast_forward = bool(atc_fast_forward)
        self.training_target_sector = int(training_target_sector)

        # Set default max_rounds per mode
        if mode == "halve_it":
            self.max_rounds = len(HALVE_IT_STAGES)
        elif mode == "bermuda":
            self.max_rounds = len(BERMUDA_STAGES)
        elif mode == "bobs27":
            self.max_rounds = 21
        elif mode == "jdc_challenge":
            self.max_rounds = 19
        elif mode == "catch40":
            self.max_rounds = 80
        elif mode == "scoring100":
            self.max_rounds = 33
        else:
            self.max_rounds = max(1, int(max_rounds))

        names = [n.strip() for n in (player_names or ["Spieler 1"]) if n.strip()][:6]
        if not names:
            names = ["Spieler 1"]

        # Assign distinct random Killer numbers if mode == "killer"
        available_nums = list(range(1, 21))
        random.shuffle(available_nums)

        self.players = []
        for idx, name in enumerate(names):
            if mode == "x01":
                init_score = self.x01_start_score
            elif mode == "bobs27":
                init_score = 27
            else:
                init_score = 0

            p = PlayerState(
                name=name,
                score=init_score,
                in_achieved=(not self.double_in if mode == "x01" else True),
                killer_number=available_nums[idx % 20] if mode == "killer" else 0,
                killer_lives=0,
                is_killer=False,
                sub_target=61 if mode == "catch40" else (121 if mode == "checkout121" else 0),
                sub_remaining=61 if mode == "catch40" else (121 if mode == "checkout121" else 0),
                sub_darts_used=0,
            )
            self.players.append(p)

        # Initialize Tic-Tac-Toe 3x3 board (8 random sectors 1..20 + 25 in center index 4)
        pool = random.sample(range(1, 21), 8)
        self.ttt_numbers = pool[:4] + [25] + pool[4:]
        self.ttt_owners = [None] * 9
        self.ttt_marks = [{i: 0 for i in range(len(self.players))} for _ in range(9)]

        self.current_player_idx = 0
        self.leg_starter_idx = 0
        self.round_number = 1
        self.turn_darts = []
        self.turn_busted = False
        self.turn_complete = False
        self.waiting_for_takeout = False
        self.winner_name = None
        self._undo_stack.clear()
        self._capture_turn_start()
        self.last_announcement = f"Spiel gestartet: {self._get_mode_title()}"
        self.last_caller_speech = "Game on!"
        return self.get_state()

    def _get_mode_title(self) -> str:
        titles = {
            "x01": f"X01 ({self.x01_start_score})",
            "cricket": f"Cricket ({self.cricket_variant.capitalize()})",
            "atc": "Around the Clock",
            "shanghai": "Shanghai",
            "highscore": "Highscore / Training",
            "elimination": f"Elimination ({self.x01_start_score})",
            "killer": "Killer",
            "halve_it": "Halve It (Halbieren)",
            "gotcha": f"Gotcha ({self.x01_start_score})",
            "tictactoe": "Tic-Tac-Toe Darts",
            "bermuda": "Bermuda Triangle",
            "bobs27": "Bob's 27 (Doppel-Training)",
            "jdc_challenge": "JDC Challenge",
            "catch40": "Catch 40 (Checkout 61–100)",
            "checkout121": "121 Checkout-Leiter",
            "scoring100": f"Scoring 100 (Ziel {self.training_target_sector})",
        }
        return titles.get(self.mode, self.mode.upper())

    def _get_player_target_badge(self, player_idx: int) -> Optional[str]:
        p = self.players[player_idx]
        if self.mode == "atc":
            t = ATC_TARGETS[min(p.atc_index, len(ATC_TARGETS) - 1)]
            return f"Ziel: {'BULL' if t == 25 else t}"
        if self.mode == "shanghai":
            return f"Runden-Ziel: {min(20, self.round_number)}"
        if self.mode in ("elimination", "gotcha"):
            rem = max(0, self.x01_start_score - p.score)
            return f"Ziel: {self.x01_start_score} (Rest {rem})"
        if self.mode == "killer":
            if p.eliminated:
                return "☠️ Ausgeschieden"
            status = "🔪 KILLER" if p.is_killer else "Aufbau (Doppel)"
            return f"Zahl: D{p.killer_number} | ❤️ {p.killer_lives}/3 | {status}"
        if self.mode == "halve_it":
            st = HALVE_IT_STAGES[min(self.round_number - 1, len(HALVE_IT_STAGES) - 1)]
            return f"Runde {self.round_number}/8: {st['label']}"
        if self.mode == "bermuda":
            st = BERMUDA_STAGES[min(self.round_number - 1, len(BERMUDA_STAGES) - 1)]
            return f"Runde {self.round_number}/13: {st['label']}"
        if self.mode == "bobs27":
            if p.eliminated:
                return "☠️ Unter 0 gefallen"
            t = ATC_TARGETS[min(self.round_number - 1, 20)]
            return f"Runde {self.round_number}/21: {'DBULL' if t == 25 else f'D{t}'}"
        if self.mode == "jdc_challenge":
            return self._get_jdc_round_description(self.round_number)
        if self.mode == "catch40":
            return f"Checkout {p.sub_target}: Rest {p.sub_remaining} ({6 - p.sub_darts_used} Darts)"
        if self.mode == "checkout121":
            return f"Ziel {p.sub_target}: Rest {p.sub_remaining} ({9 - p.sub_darts_used} Darts) | Best: {p.best_checkout}"
        if self.mode == "scoring100":
            lbl = "BULL" if self.training_target_sector == 25 else str(self.training_target_sector)
            return f"Ziel: {lbl} | Treffer-Marks: {p.target_hits}"
        return None

    def register_dart(self, hit: DartHit) -> dict:
        """Process a newly thrown dart in the active game."""
        if self.winner_name is not None:
            return self.get_state()

        if self.turn_complete or len(self.turn_darts) >= 3:
            self.next_turn()

        self._save_undo_snapshot()
        if len(self.turn_darts) == 0:
            self._capture_turn_start()

        player = self.players[self.current_player_idx]
        self.turn_darts.append(hit)
        player.darts_thrown_leg += 1
        player.darts_thrown_total += 1
        player.hit_history.append(
            {
                "x": hit.x,
                "y": hit.y,
                "label": hit.label,
                "score": hit.score,
                "round": self.round_number,
                "ts": round(time.time(), 1),
            }
        )

        # Dispatch to active mode handler
        dispatch = {
            "x01": self._process_x01_dart,
            "cricket": self._process_cricket_dart,
            "atc": self._process_atc_dart,
            "shanghai": self._process_shanghai_dart,
            "highscore": self._process_highscore_dart,
            "elimination": self._process_elimination_dart,
            "killer": self._process_killer_dart,
            "halve_it": self._process_halve_it_dart,
            "gotcha": self._process_gotcha_dart,
            "tictactoe": self._process_tictactoe_dart,
            "bermuda": self._process_bermuda_dart,
            "bobs27": self._process_bobs27_dart,
            "jdc_challenge": self._process_jdc_dart,
            "catch40": self._process_catch40_dart,
            "checkout121": self._process_checkout121_dart,
            "scoring100": self._process_scoring100_dart,
        }
        handler = dispatch.get(self.mode, self._process_highscore_dart)
        handler(player, hit)

        if len(self.turn_darts) >= 3 and not self.turn_complete:
            self.turn_complete = True
            self.waiting_for_takeout = True
            self._on_three_darts_completed(player)

        return self.get_state()

    def _on_three_darts_completed(self, player: PlayerState) -> None:
        """Called when the 3rd dart of a turn has been thrown."""
        if self.mode == "x01":
            self._finalize_Three_dart_stats(player)
        elif self.mode == "halve_it":
            self._finalize_halve_it_turn(player)
        elif self.mode == "bermuda":
            self._finalize_bermuda_turn(player)
        elif self.mode == "bobs27":
            self._finalize_bobs27_turn(player)
        elif self.mode == "jdc_challenge":
            self._finalize_jdc_turn(player)

    # --- 1. X01 ---
    def _is_valid_checkout_dart(self, hit: DartHit) -> bool:
        if self.out_mode == "single":
            return True
        if self.out_mode == "master":
            return hit.multiplier in (2, 3)
        return hit.multiplier == 2

    def _is_checkout_attempt_score(self, remaining_before: int) -> bool:
        if self.out_mode == "double":
            return remaining_before == 50 or (2 <= remaining_before <= 40 and remaining_before % 2 == 0)
        if self.out_mode == "master":
            return (
                remaining_before == 50
                or (2 <= remaining_before <= 40 and remaining_before % 2 == 0)
                or (3 <= remaining_before <= 60 and remaining_before % 3 == 0)
            )
        return 1 <= remaining_before <= 60

    def _process_x01_dart(self, player: PlayerState, hit: DartHit) -> None:
        if not player.in_achieved:
            if hit.multiplier == 2:
                player.in_achieved = True
            else:
                self.last_announcement = f"{player.name}: {hit.label} (Double-In benötigt)"
                self.last_caller_speech = "No score"
                return

        rem_before = player.score
        if self._is_checkout_attempt_score(rem_before):
            player.checkout_attempts += 1

        new_rem = rem_before - hit.score
        if new_rem == 0 and self._is_valid_checkout_dart(hit):
            player.score = 0
            player.checkout_hits += 1
            player.points_scored_total += hit.score
            if player.darts_thrown_leg <= 9:
                player.first9_points += hit.score
                player.first9_darts += 1
            self._finalize_Three_dart_stats(player)
            self._handle_leg_win(player, hit)
            return

        min_remaining = 2 if self.out_mode in ("double", "master") else 1
        if new_rem < min_remaining:
            snap = self.turn_start_snapshot or {}
            player.score = snap.get("score", player.score)
            player.in_achieved = snap.get("in_achieved", player.in_achieved)
            player.points_scored_total = snap.get("points_scored_total", player.points_scored_total)
            player.first9_points = snap.get("first9_points", player.first9_points)
            self.turn_busted = True
            self.turn_complete = True
            self.waiting_for_takeout = True
            self.last_announcement = f"BUST! {player.name} bleibt bei {player.score}"
            self.last_caller_speech = "No score!"
            return

        player.score = new_rem
        player.points_scored_total += hit.score
        if player.darts_thrown_leg <= 9:
            player.first9_points += hit.score
            player.first9_darts += 1
        self.last_announcement = f"{player.name}: {hit.label} ({hit.score}) → Rest {player.score}"
        self.last_caller_speech = f"{hit.score}"

    def _finalize_Three_dart_stats(self, player: PlayerState) -> None:
        if self.turn_busted:
            return
        turn_sum = sum(d.score for d in self.turn_darts)
        if turn_sum == 180:
            player.count_180 += 1
            self.last_caller_speech = "One hundred and eighty!"
        elif turn_sum >= 140:
            player.count_140_plus += 1
            self.last_caller_speech = f"{turn_sum}!"
        elif turn_sum >= 100:
            player.count_100_plus += 1
            self.last_caller_speech = f"{turn_sum}"
        elif turn_sum >= 60:
            player.count_60_plus += 1
            self.last_caller_speech = f"{turn_sum}"
        else:
            self.last_caller_speech = f"{turn_sum}"

    def _handle_leg_win(self, player: PlayerState, winning_hit: DartHit) -> None:
        player.legs_won += 1
        self.turn_complete = True
        self.waiting_for_takeout = True
        if player.legs_won >= self.legs_to_win:
            player.sets_won += 1
            self.winner_name = player.name
            self.last_announcement = f"🏆 {player.name} gewinnt das Match mit {winning_hit.label}!"
            self.last_caller_speech = f"Game, shot, and the match, {player.name}!"
        else:
            self.last_announcement = f"🎯 Leg gewonnen von {player.name} mit {winning_hit.label}! ({player.legs_won}/{self.legs_to_win})"
            self.last_caller_speech = f"Game shot, {player.name}!"

    # --- 2. Cricket ---
    def _process_cricket_dart(self, player: PlayerState, hit: DartHit) -> None:
        target = hit.sector
        if target not in CRICKET_NUMBERS or hit.multiplier == 0:
            self.last_announcement = f"{player.name}: {hit.label} (Kein Cricket-Feld)"
            return

        marks_to_add = hit.multiplier
        current_marks = player.cricket_marks.get(target, 0)
        new_total = current_marks + marks_to_add
        player.cricket_marks[target] = min(3, new_total)
        overflow = max(0, new_total - 3)

        if overflow > 0:
            open_opponents = [
                op for op in self.players if op is not player and op.cricket_marks.get(target, 0) < 3
            ]
            pts = overflow * target
            if open_opponents or len(self.players) == 1:
                if self.cricket_variant == "cutthroat" and open_opponents:
                    for op in open_opponents:
                        op.score += pts
                else:
                    player.score += pts
                    player.points_scored_total += pts

        self.last_announcement = f"{player.name}: {hit.label} (Marks auf {target}: {player.cricket_marks[target]}/3)"
        self.last_caller_speech = f"{hit.label}"

        all_closed = all(player.cricket_marks[n] >= 3 for n in CRICKET_NUMBERS)
        if all_closed:
            if self.cricket_variant == "cutthroat":
                best_score = all(player.score <= op.score for op in self.players if op is not player)
            else:
                best_score = all(player.score >= op.score for op in self.players if op is not player)
            if best_score:
                self.winner_name = player.name
                self.turn_complete = True
                self.waiting_for_takeout = True
                self.last_announcement = f"🏆 {player.name} gewinnt Cricket!"
                self.last_caller_speech = f"Game shot, {player.name}!"

    # --- 3. Around the Clock ---
    def _process_atc_dart(self, player: PlayerState, hit: DartHit) -> None:
        if player.atc_index >= len(ATC_TARGETS):
            return
        expected_target = ATC_TARGETS[player.atc_index]
        if hit.sector == expected_target and hit.multiplier > 0:
            step = hit.multiplier if self.atc_fast_forward else 1
            player.atc_index = min(len(ATC_TARGETS), player.atc_index + step)
            player.score = player.atc_index
            player.points_scored_total += hit.score
            if player.atc_index >= len(ATC_TARGETS):
                self.winner_name = player.name
                self.turn_complete = True
                self.waiting_for_takeout = True
                self.last_announcement = f"🏆 {player.name} hat Around the Clock geschafft!"
                self.last_caller_speech = f"Winner, {player.name}!"
            else:
                next_t = ATC_TARGETS[player.atc_index]
                next_lbl = "BULL" if next_t == 25 else str(next_t)
                self.last_announcement = f"✅ Treffer {hit.label}! Nächstes Ziel für {player.name}: {next_lbl}"
                self.last_caller_speech = f"Hit! Next {next_lbl}"
        else:
            exp_lbl = "BULL" if expected_target == 25 else str(expected_target)
            self.last_announcement = f"{player.name}: {hit.label} (Ziel bleibt {exp_lbl})"

    # --- 4. Shanghai ---
    def _process_shanghai_dart(self, player: PlayerState, hit: DartHit) -> None:
        target = min(20, self.round_number)
        if hit.sector == target and hit.multiplier > 0:
            pts = target * hit.multiplier
            player.score += pts
            player.points_scored_total += pts
            self.last_announcement = f"{player.name}: {hit.label} (+{pts} Punkte in Runde {target})"
            mults_hit = {d.multiplier for d in self.turn_darts if d.sector == target and d.multiplier > 0}
            if mults_hit == {1, 2, 3}:
                self.winner_name = player.name
                self.turn_complete = True
                self.waiting_for_takeout = True
                self.last_announcement = f"⚡ SHANGHAI auf der {target}! {player.name} gewinnt sofort!"
                self.last_caller_speech = f"Shanghai! {player.name} wins!"
        else:
            self.last_announcement = f"{player.name}: {hit.label} (Runde {target} zählt nur auf {target})"

    # --- 5. Highscore ---
    def _process_highscore_dart(self, player: PlayerState, hit: DartHit) -> None:
        player.score += hit.score
        player.points_scored_total += hit.score
        self.last_announcement = f"{player.name}: {hit.label} (+{hit.score}) → Gesamt {player.score}"
        self.last_caller_speech = f"{hit.score}"

    # --- 6. Elimination ("Mensch ärgere dich nicht") ---
    def _process_elimination_dart(self, player: PlayerState, hit: DartHit) -> None:
        target_goal = self.x01_start_score
        new_score = player.score + hit.score

        if new_score > target_goal or (
            new_score == target_goal and self.out_mode == "double" and hit.multiplier != 2
        ):
            snap = self.turn_start_snapshot or {}
            player.score = snap.get("score", player.score)
            self.turn_busted = True
            self.turn_complete = True
            self.waiting_for_takeout = True
            self.last_announcement = f"BUST! {player.name} überwirft {target_goal} und bleibt bei {player.score}"
            self.last_caller_speech = "No score!"
            return

        player.score = new_score
        player.points_scored_total += hit.score

        # Check if any opponent stands on the exact same score -> eliminate back to 0!
        eliminated_names = []
        if player.score > 0:
            for op in self.players:
                if op is not player and op.score == player.score:
                    op.score = 0
                    eliminated_names.append(op.name)

        if player.score == target_goal:
            self.winner_name = player.name
            self.turn_complete = True
            self.waiting_for_takeout = True
            self.last_announcement = f"🏆 {player.name} erreicht exakt {target_goal} und gewinnt Elimination!"
            self.last_caller_speech = f"Winner, {player.name}!"
            return

        if eliminated_names:
            victims = ", ".join(eliminated_names)
            self.last_announcement = f"💥 ELIMINATED! {player.name} trifft {player.score} und schickt {victims} zurück auf 0!"
            self.last_caller_speech = "Eliminated!"
        else:
            self.last_announcement = f"{player.name}: {hit.label} → {player.score}/{target_goal}"
            self.last_caller_speech = f"{hit.score}"

    # --- 7. Killer ---
    def _process_killer_dart(self, player: PlayerState, hit: DartHit) -> None:
        if hit.multiplier not in (2, 3):
            self.last_announcement = f"{player.name}: {hit.label} (Bei Killer zählen Double/Triple)"
            return

        lives_delta = 1 if hit.multiplier == 2 else 2

        # Hitting own number builds up lives to 3 (becomes Killer)
        if hit.sector == player.killer_number:
            if not player.is_killer:
                player.killer_lives = min(3, player.killer_lives + lives_delta)
                player.score = player.killer_lives
                if player.killer_lives >= 3:
                    player.is_killer = True
                    self.last_announcement = f"🔪 {player.name} hat 3 Leben erreicht und ist jetzt KILLER!"
                    self.last_caller_speech = f"{player.name} is a Killer!"
                else:
                    self.last_announcement = f"{player.name} baut Leben auf: {player.killer_lives}/3"
            else:
                # Self-hit while already Killer removes own life!
                player.killer_lives = max(0, player.killer_lives - 1)
                player.score = player.killer_lives
                if player.killer_lives == 0:
                    player.is_killer = False
                self.last_announcement = f"⚠️ Eigentreffer! {player.name} verliert 1 Leben ({player.killer_lives}/3)"
            return

        # Hitting an opponent's number while player is a Killer!
        if player.is_killer:
            for op in self.players:
                if op is not player and not op.eliminated and op.killer_number == hit.sector:
                    op.killer_lives = max(0, op.killer_lives - lives_delta)
                    op.score = op.killer_lives
                    if op.killer_lives == 0 and op.is_killer:
                        op.eliminated = True
                        self.last_announcement = f"☠️ {player.name} eliminiert {op.name}!"
                        self.last_caller_speech = f"{op.name} eliminated!"
                    else:
                        self.last_announcement = f"🔪 {player.name} zieht {op.name} {lives_delta} Leben ab! (Rest: {op.killer_lives})"
                        self.last_caller_speech = "Hit!"

                    # Check if only 1 player remains alive
                    alive = [p for p in self.players if not p.eliminated]
                    if len(self.players) > 1 and len(alive) == 1:
                        self.winner_name = alive[0].name
                        self.turn_complete = True
                        self.waiting_for_takeout = True
                        self.last_announcement = f"🏆 {alive[0].name} überlebt als letzter Killer und gewinnt!"
                        self.last_caller_speech = f"Winner, {alive[0].name}!"
                    return

        self.last_announcement = f"{player.name}: {hit.label}"

    # --- 8. Halve It (Halbieren) ---
    def _process_halve_it_dart(self, player: PlayerState, hit: DartHit) -> None:
        stage = HALVE_IT_STAGES[min(self.round_number - 1, len(HALVE_IT_STAGES) - 1)]
        stype = stage["type"]
        starget = stage["target"]

        matched = False
        if stype == "sector" and hit.sector == starget and hit.multiplier > 0:
            matched = True
        elif stype == "double" and hit.multiplier == 2:
            matched = True
        elif stype == "triple" and hit.multiplier == 3:
            matched = True
        elif stype == "min_sum":
            self.turn_stage_points += hit.score
            self.last_announcement = f"{player.name}: {hit.label} (Summe dieser Aufnahme: {self.turn_stage_points}/41)"
            return

        if matched:
            self.turn_stage_hits += 1
            player.score += hit.score
            player.points_scored_total += hit.score
            self.last_announcement = f"✅ {player.name} trifft {hit.label} (+{hit.score}) → {player.score}"
            self.last_caller_speech = f"{hit.score}"
        else:
            self.last_announcement = f"{player.name}: {hit.label} (Ziel: {stage['label']})"

    def _finalize_halve_it_turn(self, player: PlayerState) -> None:
        stage = HALVE_IT_STAGES[min(self.round_number - 1, len(HALVE_IT_STAGES) - 1)]
        if stage["type"] == "min_sum":
            if self.turn_stage_points >= stage["target"]:
                player.score += self.turn_stage_points
                player.points_scored_total += self.turn_stage_points
                self.last_announcement = f"✅ {player.name} schafft {self.turn_stage_points} Punkte! Gesamt: {player.score}"
            else:
                player.score = player.score // 2
                self.last_announcement = f"✂️ HALBIERT! Nur {self.turn_stage_points}/41 Pkt – {player.name} fällt auf {player.score}!"
                self.last_caller_speech = "Halved!"
            return

        if self.turn_stage_hits == 0:
            player.score = player.score // 2
            self.last_announcement = f"✂️ HALBIERT! Kein Treffer auf {stage['label']} – {player.name} fällt auf {player.score}!"
            self.last_caller_speech = "Halved!"

    # --- 9. Gotcha ---
    def _process_gotcha_dart(self, player: PlayerState, hit: DartHit) -> None:
        target_goal = self.x01_start_score
        # Special Gotcha rule: Double Bull swaps score with the leader if behind!
        if hit.ring == "DBULL" and len(self.players) > 1:
            leader = max(self.players, key=lambda p: p.score)
            if leader is not player and leader.score > player.score and leader.score < target_goal:
                player.score, leader.score = leader.score, player.score
                self.last_announcement = f"🔄 GOTCHA BULLSEYE! {player.name} tauscht Punktestand mit {leader.name} ({player.score})!"
                self.last_caller_speech = "Gotcha swap!"
                return

        new_score = player.score + hit.score
        if new_score > target_goal:
            # Bust resets to last 100-milestone (0, 100, 200)
            milestone = (player.score // 100) * 100
            player.score = milestone
            self.turn_busted = True
            self.turn_complete = True
            self.waiting_for_takeout = True
            self.last_announcement = f"BUST! {player.name} fällt zurück auf den Meilenstein {milestone}!"
            self.last_caller_speech = "Bust!"
            return

        player.score = new_score
        player.points_scored_total += hit.score

        reset_ops = []
        for op in self.players:
            if op is not player and op.score == player.score and player.score > 0:
                op.score = 0
                reset_ops.append(op.name)

        if player.score == target_goal:
            self.winner_name = player.name
            self.turn_complete = True
            self.waiting_for_takeout = True
            self.last_announcement = f"🏆 GOTCHA! {player.name} erreicht exakt {target_goal} und gewinnt!"
            self.last_caller_speech = f"Winner, {player.name}!"
        elif reset_ops:
            self.last_announcement = f"💥 GOTCHA! {', '.join(reset_ops)} wird auf 0 zurückgesetzt!"
            self.last_caller_speech = "Gotcha!"
        else:
            self.last_announcement = f"{player.name}: {hit.label} → {player.score}/{target_goal}"

    # --- 10. Tic-Tac-Toe Darts ---
    def _process_tictactoe_dart(self, player: PlayerState, hit: DartHit) -> None:
        if hit.sector not in self.ttt_numbers or hit.multiplier == 0:
            self.last_announcement = f"{player.name}: {hit.label} (Nicht im Tic-Tac-Toe Raster)"
            return

        cell_idx = self.ttt_numbers.index(hit.sector)
        if self.ttt_owners[cell_idx] is not None:
            self.last_announcement = f"Feld {hit.sector} gehört bereits {self.players[self.ttt_owners[cell_idx]].name}!"
            return

        p_idx = self.current_player_idx
        prev_marks = self.ttt_marks[cell_idx].get(p_idx, 0)
        new_marks = min(3, prev_marks + hit.multiplier)
        self.ttt_marks[cell_idx][p_idx] = new_marks

        if new_marks >= 3:
            self.ttt_owners[cell_idx] = p_idx
            player.score += 1
            self.last_announcement = f"❌⭕ {player.name} erobert Feld {'BULL' if hit.sector == 25 else hit.sector}!"
            self.last_caller_speech = "Field claimed!"
            self._check_tictactoe_winner()
        else:
            self.last_announcement = f"{player.name}: {new_marks}/3 Marks auf Feld {'BULL' if hit.sector == 25 else hit.sector}"

    def _check_tictactoe_winner(self) -> None:
        for a, b, c in TICTACTOE_LINES:
            owner = self.ttt_owners[a]
            if owner is not None and self.ttt_owners[b] == owner and self.ttt_owners[c] == owner:
                w_name = self.players[owner].name
                self.winner_name = w_name
                self.turn_complete = True
                self.waiting_for_takeout = True
                self.last_announcement = f"🏆 3 IN EINER REIHE! {w_name} gewinnt Tic-Tac-Toe!"
                self.last_caller_speech = f"Winner, {w_name}!"
                return

        if all(o is not None for o in self.ttt_owners):
            best_p = max(self.players, key=lambda p: p.score)
            self.winner_name = best_p.name
            self.turn_complete = True
            self.waiting_for_takeout = True
            self.last_announcement = f"🏆 Alle Felder belegt! {best_p.name} gewinnt nach Feldern!"

    # --- 11. Bermuda Triangle ---
    def _process_bermuda_dart(self, player: PlayerState, hit: DartHit) -> None:
        stage = BERMUDA_STAGES[min(self.round_number - 1, len(BERMUDA_STAGES) - 1)]
        stype = stage["type"]
        starget = stage["target"]

        matched = False
        if stype == "sector" and hit.sector == starget and hit.multiplier > 0:
            matched = True
        elif stype == "double" and hit.multiplier == 2:
            matched = True
        elif stype == "triple" and hit.multiplier == 3:
            matched = True
        elif stype == "sbull" and hit.ring == "SBULL":
            matched = True
        elif stype == "dbull" and hit.ring == "DBULL":
            matched = True

        if matched:
            self.turn_stage_hits += 1
            player.score += hit.score
            player.points_scored_total += hit.score
            self.last_announcement = f"✅ Bermuda-Treffer {hit.label} (+{hit.score}) → {player.score}"
            self.last_caller_speech = f"{hit.score}"
        else:
            self.last_announcement = f"{player.name}: {hit.label} (Bermuda-Ziel: {stage['label']})"

    def _finalize_bermuda_turn(self, player: PlayerState) -> None:
        stage = BERMUDA_STAGES[min(self.round_number - 1, len(BERMUDA_STAGES) - 1)]
        if self.turn_stage_hits == 0:
            player.score = player.score // 2
            self.last_announcement = f"🔺 BERMUDA-DREIECK! Kein Treffer auf {stage['label']} – {player.name} halbiert auf {player.score}!"
            self.last_caller_speech = "Halved!"

    # --- 12. Bob's 27 ---
    def _process_bobs27_dart(self, player: PlayerState, hit: DartHit) -> None:
        if player.eliminated:
            return
        target = ATC_TARGETS[min(self.round_number - 1, 20)]
        is_hit = (target == 25 and hit.ring == "DBULL") or (target != 25 and hit.sector == target and hit.multiplier == 2)
        if is_hit:
            self.turn_stage_hits += 1
            pts = 50 if target == 25 else target * 2
            player.score += pts
            player.points_scored_total += pts
            self.last_announcement = f"✅ Bob's 27 Treffer {hit.label}! +{pts} → {player.score}"
            self.last_caller_speech = f"{pts}"
        else:
            lbl = "DBULL" if target == 25 else f"D{target}"
            self.last_announcement = f"{player.name}: {hit.label} (Ziel: {lbl})"

    def _finalize_bobs27_turn(self, player: PlayerState) -> None:
        if player.eliminated:
            return
        target = ATC_TARGETS[min(self.round_number - 1, 20)]
        if self.turn_stage_hits == 0:
            penalty = 50 if target == 25 else target * 2
            player.score -= penalty
            if player.score < 0:
                player.eliminated = True
                self.last_announcement = f"☠️ {player.name} fällt auf {player.score} (unter 0) – Game Over bei Bob's 27!"
                self.last_caller_speech = "Game over"
                alive = [p for p in self.players if not p.eliminated]
                if not alive:
                    best = max(self.players, key=lambda p: p.score)
                    self.winner_name = best.name
            else:
                self.last_announcement = f"➖ Kein Doppel getroffen (-{penalty}) → {player.name} steht bei {player.score}"

    # --- 13. JDC Challenge ---
    @staticmethod
    def _get_jdc_round_description(r: int) -> str:
        if 1 <= r <= 6:
            return f"Phase 1 (R{r}/19): Shanghai auf {9 + r}"
        if 7 <= r <= 13:
            idx = (r - 7) * 3
            t1, t2, t3 = ATC_TARGETS[idx], ATC_TARGETS[idx + 1], ATC_TARGETS[idx + 2]
            l3 = "DBULL" if t3 == 25 else f"D{t3}"
            return f"Phase 2 (R{r}/19): 1 Dart je auf D{t1}, D{t2}, {l3}"
        s_num = 15 + (r - 14)
        return f"Phase 3 (R{r}/19): Shanghai auf {min(20, s_num)}"

    def _process_jdc_dart(self, player: PlayerState, hit: DartHit) -> None:
        r = self.round_number
        if 1 <= r <= 6 or 14 <= r <= 19:
            target = (9 + r) if r <= 6 else min(20, 15 + (r - 14))
            if hit.sector == target and hit.multiplier > 0:
                player.score += hit.score
                player.points_scored_total += hit.score
                self.last_announcement = f"✅ JDC Treffer {hit.label} (+{hit.score}) → {player.score}"
            else:
                self.last_announcement = f"{player.name}: {hit.label} (Ziel: Sektor {target})"
        else:
            # Phase 2: Dart 1 -> target_idx, Dart 2 -> target_idx+1, Dart 3 -> target_idx+2
            dart_slot = len(self.turn_darts) - 1
            t_idx = (r - 7) * 3 + dart_slot
            target = ATC_TARGETS[min(t_idx, 20)]
            is_double_hit = (target == 25 and hit.ring == "DBULL") or (
                target != 25 and hit.sector == target and hit.multiplier == 2
            )
            if is_double_hit:
                bonus = 100 if target == 25 else 50
                player.score += bonus
                player.points_scored_total += bonus
                self.last_announcement = f"🎯 JDC Double-Treffer {hit.label}! +{bonus} Punkte → {player.score}"
                self.last_caller_speech = f"{bonus}"
            else:
                lbl = "DBULL" if target == 25 else f"D{target}"
                self.last_announcement = f"{player.name}: {hit.label} (Gefordert für Dart {dart_slot + 1}: {lbl})"

    def _finalize_jdc_turn(self, player: PlayerState) -> None:
        r = self.round_number
        if 1 <= r <= 6 or 14 <= r <= 19:
            target = (9 + r) if r <= 6 else min(20, 15 + (r - 14))
            mults = {d.multiplier for d in self.turn_darts if d.sector == target and d.multiplier > 0}
            if mults == {1, 2, 3}:
                player.score += 100
                self.last_announcement = f"⚡ JDC SHANGHAI-BONUS auf {target}! +100 Extrapunkte für {player.name}!"
                self.last_caller_speech = "Shanghai bonus!"

    # --- 14. Catch 40 ---
    def _process_catch40_dart(self, player: PlayerState, hit: DartHit) -> None:
        player.sub_darts_used += 1
        new_rem = player.sub_remaining - hit.score

        if new_rem == 0 and hit.multiplier == 2:
            # Checked out!
            used = player.sub_darts_used
            if used == 2:
                pts = 10 if player.sub_target == 99 else 3
            elif used == 3:
                pts = 2
            else:
                pts = 1
            player.score += pts
            player.checkout_hits += 1
            old_t = player.sub_target
            player.sub_target = min(100, player.sub_target + 1)
            player.sub_remaining = player.sub_target
            player.sub_darts_used = 0
            self.turn_complete = True
            self.waiting_for_takeout = True
            self.last_announcement = f"🎯 Catch 40: {old_t} gecheckt in {used} Darts (+{pts} Pkt)! Nächstes Ziel: {player.sub_target}"
            self.last_caller_speech = "Game shot!"
            if old_t >= 100:
                self.winner_name = player.name
            return

        if new_rem < 2 or player.sub_darts_used >= 6:
            # Bust or 6 darts exhausted
            if player.sub_darts_used >= 6:
                old_t = player.sub_target
                player.sub_target = min(100, player.sub_target + 1)
                player.sub_remaining = player.sub_target
                player.sub_darts_used = 0
                self.turn_complete = True
                self.waiting_for_takeout = True
                self.last_announcement = f"❌ {old_t} nicht in 6 Darts gecheckt. Weiter mit {player.sub_target}!"
            else:
                # Bust on visit 1 -> reset remaining to start of visit and advance to visit 2
                snap = self.turn_start_snapshot or {}
                player.sub_remaining = snap.get("sub_remaining", player.sub_target)
                player.sub_darts_used = 3
                self.turn_busted = True
                self.turn_complete = True
                self.waiting_for_takeout = True
                self.last_announcement = f"BUST bei {player.sub_target}! Noch 3 Darts im nächsten Durchgang."
            return

        player.sub_remaining = new_rem
        self.last_announcement = f"{player.name}: {hit.label} → Rest {player.sub_remaining} ({6 - player.sub_darts_used} Darts übrig)"

    # --- 15. 121 Checkout Ladder ---
    def _process_checkout121_dart(self, player: PlayerState, hit: DartHit) -> None:
        player.sub_darts_used += 1
        new_rem = player.sub_remaining - hit.score

        if new_rem == 0 and hit.multiplier == 2:
            checked = player.sub_target
            player.best_checkout = max(player.best_checkout, checked)
            player.score = player.best_checkout
            player.checkout_hits += 1
            player.sub_target += 1
            player.sub_remaining = player.sub_target
            player.sub_darts_used = 0
            self.turn_complete = True
            self.waiting_for_takeout = True
            self.last_announcement = f"🔥 {checked} gecheckt in {player.sub_darts_used or len(self.turn_darts)} Darts! Neues Ziel: {player.sub_target}"
            self.last_caller_speech = "Game shot!"
            return

        if new_rem < 2 or player.sub_darts_used >= 9:
            if player.sub_darts_used >= 9:
                old_t = player.sub_target
                player.sub_target = max(121, player.sub_target - 1)
                player.sub_remaining = player.sub_target
                player.sub_darts_used = 0
                self.turn_complete = True
                self.waiting_for_takeout = True
                self.last_announcement = f"❌ 9 Darts für {old_t} aufgebraucht – Ziel geht auf {player.sub_target}"
            else:
                snap = self.turn_start_snapshot or {}
                player.sub_remaining = snap.get("sub_remaining", player.sub_target)
                player.sub_darts_used = ((player.sub_darts_used - 1) // 3 + 1) * 3
                self.turn_busted = True
                self.turn_complete = True
                self.waiting_for_takeout = True
                self.last_announcement = f"BUST! Rest bleibt {player.sub_remaining}"
            return

        player.sub_remaining = new_rem
        self.last_announcement = f"{player.name}: {hit.label} → Rest {player.sub_remaining} ({9 - player.sub_darts_used} Darts übrig)"

    # --- 16. Bulls-Eye / Scoring 100 ---
    def _process_scoring100_dart(self, player: PlayerState, hit: DartHit) -> None:
        target = self.training_target_sector
        if hit.sector == target and hit.multiplier > 0:
            player.target_hits += hit.multiplier
            pts = hit.score if target == 25 else hit.multiplier
            player.score += pts
            player.points_scored_total += hit.score
            self.last_announcement = f"🎯 Treffer {hit.label}! Marks: {player.target_hits} ({player.darts_thrown_total}/99 Darts)"
            self.last_caller_speech = f"{hit.label}"
        else:
            lbl = "BULL" if target == 25 else str(target)
            self.last_announcement = f"{player.name}: {hit.label} (Zielsektor: {lbl} | {player.darts_thrown_total}/99 Darts)"

    # --- Turn Progression & Undo ---
    def next_turn(self) -> dict:
        if self.winner_name is not None:
            return self.get_state()

        current_player = self.players[self.current_player_idx]
        if self.mode == "x01" and current_player.score == 0:
            self._start_next_leg()
            return self.get_state()

        # If player finished turn early (with < 3 darts via Next button), still apply end-of-turn rules
        if len(self.turn_darts) < 3 and not self.turn_complete:
            self._on_three_darts_completed(current_player)

        self.turn_darts = []
        self.turn_busted = False
        self.turn_complete = False
        self.waiting_for_takeout = False

        # Find next non-eliminated player
        n_players = len(self.players)
        next_idx = (self.current_player_idx + 1) % n_players
        for _ in range(n_players):
            if not self.players[next_idx].eliminated:
                break
            next_idx = (next_idx + 1) % n_players

        if next_idx <= self.current_player_idx or n_players == 1:
            self.round_number += 1
            if self.mode in (
                "shanghai", "highscore", "halve_it", "bermuda", "bobs27", "jdc_challenge", "scoring100"
            ) and self.round_number > self.max_rounds:
                best_p = max(self.players, key=lambda p: p.score)
                self.winner_name = best_p.name
                self.last_announcement = f"🏆 Spielende! {best_p.name} gewinnt mit {best_p.score} Punkten!"
                self.last_caller_speech = f"Match over! Winner {best_p.name}"
                return self.get_state()

        self.current_player_idx = next_idx
        self._capture_turn_start()
        active_name = self.players[self.current_player_idx].name
        self.last_announcement = f"{active_name} ist am Wurf"
        self.last_caller_speech = f"{active_name} to throw"
        return self.get_state()

    def _start_next_leg(self) -> None:
        self.leg_starter_idx = (self.leg_starter_idx + 1) % len(self.players)
        self.current_player_idx = self.leg_starter_idx
        self.round_number = 1
        for p in self.players:
            p.score = self.x01_start_score
            p.darts_thrown_leg = 0
            p.in_achieved = not self.double_in
        self.turn_darts = []
        self.turn_busted = False
        self.turn_complete = False
        self.waiting_for_takeout = False
        self._capture_turn_start()
        starter_name = self.players[self.current_player_idx].name
        self.last_announcement = f"Neues Leg! {starter_name} beginnt."
        self.last_caller_speech = f"New leg. {starter_name} to throw."

    def undo_last_dart(self) -> dict:
        if not self._undo_stack:
            return self.get_state()
        snap = self._undo_stack.pop()
        self.players = snap["players"]
        self.current_player_idx = snap["current_player_idx"]
        self.leg_starter_idx = snap["leg_starter_idx"]
        self.round_number = snap["round_number"]
        self.turn_darts = snap["turn_darts"]
        self.turn_start_snapshot = snap["turn_start_snapshot"]
        self.turn_busted = snap["turn_busted"]
        self.turn_complete = snap["turn_complete"]
        self.waiting_for_takeout = snap["waiting_for_takeout"]
        self.winner_name = snap["winner_name"]
        self.last_announcement = "Letzter Wurf rückgängig gemacht"
        self.ttt_owners = snap["ttt_owners"]
        self.ttt_marks = snap["ttt_marks"]
        self.turn_stage_hits = snap["turn_stage_hits"]
        self.turn_stage_points = snap["turn_stage_points"]
        self.last_caller_speech = "Correction"
        return self.get_state()

    def correct_turn_dart(self, dart_index: int, new_hit: DartHit) -> dict:
        if dart_index < 0 or dart_index >= len(self.turn_darts):
            return self.get_state()

        updated_darts = list(self.turn_darts)
        updated_darts[dart_index] = new_hit

        num_to_pop = len(self.turn_darts)
        snap = None
        for _ in range(num_to_pop):
            if self._undo_stack:
                snap = self._undo_stack.pop()
        if snap is not None:
            self.players = snap["players"]
            self.current_player_idx = snap["current_player_idx"]
            self.leg_starter_idx = snap["leg_starter_idx"]
            self.round_number = snap["round_number"]
            self.turn_darts = []
            self.turn_start_snapshot = snap["turn_start_snapshot"]
            self.turn_busted = False
            self.turn_complete = False
            self.waiting_for_takeout = False
            self.winner_name = None
            self.ttt_owners = snap["ttt_owners"]
            self.ttt_marks = snap["ttt_marks"]
            self.turn_stage_hits = 0
            self.turn_stage_points = 0

        for d in updated_darts:
            self.register_dart(d)

        self.last_announcement = f"Dart {dart_index + 1} korrigiert auf {new_hit.label}"
        return self.get_state()

    def get_state(self) -> dict:
        darts_left = max(0, 3 - len(self.turn_darts)) if not self.turn_complete else 0
        double_out = self.out_mode in ("double", "master")
        ttt_cells = []
        if self.mode == "tictactoe":
            for i in range(9):
                owner_idx = self.ttt_owners[i]
                ttt_cells.append(
                    {
                        "sector": self.ttt_numbers[i],
                        "label": "BULL" if self.ttt_numbers[i] == 25 else str(self.ttt_numbers[i]),
                        "owner_idx": owner_idx,
                        "owner_name": self.players[owner_idx].name if owner_idx is not None else None,
                        "marks": {str(k): v for k, v in self.ttt_marks[i].items()},
                    }
                )

        return {
            "mode": self.mode,
            "mode_title": self._get_mode_title(),
            "x01_start_score": self.x01_start_score,
            "double_in": self.double_in,
            "out_mode": self.out_mode,
            "legs_to_win": self.legs_to_win,
            "cricket_variant": self.cricket_variant,
            "atc_fast_forward": self.atc_fast_forward,
            "max_rounds": self.max_rounds,
            "training_target_sector": self.training_target_sector,
            "round_number": self.round_number,
            "current_player_idx": self.current_player_idx,
            "players": [
                p.to_dict(
                    current_turn_darts_left=(darts_left if idx == self.current_player_idx else 3),
                    double_out=double_out,
                    mode=self.mode,
                    target_badge=self._get_player_target_badge(idx),
                )
                for idx, p in enumerate(self.players)
            ],
            "tictactoe_board": ttt_cells,
            "turn_darts": [d.to_dict() for d in self.turn_darts],
            "turn_score": 0 if self.turn_busted else sum(d.score for d in self.turn_darts),
            "turn_busted": self.turn_busted,
            "turn_complete": self.turn_complete,
            "waiting_for_takeout": self.waiting_for_takeout,
            "winner_name": self.winner_name,
            "last_announcement": self.last_announcement,
            "last_caller_speech": self.last_caller_speech,
            "can_undo": len(self._undo_stack) > 0,
        }
