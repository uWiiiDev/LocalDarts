"""
OpenCV Diff-Tracking, Multi-Camera Triangulation & Automatic Takeout Detector for LocalDarts.
"""

from __future__ import annotations
import math
import threading
import time
from typing import Callable, Dict, List, Optional, Tuple
import cv2
import numpy as np

from .board_geometry import DartHit, coords_to_hit
from .calibration import CalibrationManager
from .camera_manager import CameraManager


class CameraDartCandidate:
    """Represents a detected dart contour and its projected line/tip in one camera."""

    def __init__(
        self,
        cam_id: int,
        tip_px: Tuple[int, int],
        tail_px: Tuple[int, int],
        tip_board: Tuple[float, float],
        tail_board: Tuple[float, float],
        contour_area: float,
        contour: np.ndarray,
    ):
        self.cam_id = cam_id
        self.tip_px = tip_px
        self.tail_px = tail_px
        self.tip_board = tip_board
        self.tail_board = tail_board
        self.contour_area = contour_area
        self.contour = contour


class DartDetector:
    """
    Continuous background vision processor that monitors up to 3 cameras for:
      1. Motion (flying dart / player hand)
      2. Settled new dart (frame diff between previous settled state and current settled state)
      3. Multi-camera ray intersection & endpoint clustering to find the exact dart tip (x, y)
      4. Automatic Takeout detection when darts are pulled from the board -> auto-advances player!
    """

    def __init__(
        self,
        camera_manager: CameraManager,
        calibration_manager: CalibrationManager,
        on_dart_detected: Optional[Callable[[DartHit], None]] = None,
        on_takeout_detected: Optional[Callable[[], None]] = None,
        on_state_change: Optional[Callable[[str], None]] = None,
        is_turn_waiting_takeout: Optional[Callable[[], bool]] = None,
    ):
        self.camera_manager = camera_manager
        self.calibration_manager = calibration_manager
        self.on_dart_detected = on_dart_detected
        self.on_takeout_detected = on_takeout_detected
        self.on_state_change = on_state_change
        self.is_turn_waiting_takeout = is_turn_waiting_takeout

        # Tunable parameters
        self.enabled: bool = True
        self.auto_takeout_enabled: bool = True
        self.diff_threshold: int = 26
        self.min_contour_area: int = 120
        self.max_contour_area: int = 28000
        self.settle_time_ms: int = 260
        self.motion_threshold_px: int = 320
        self.hand_takeout_motion_px: int = 2400

        # Internal state
        self.state: str = "READY"  # READY, MOTION, SETTLING, TAKEOUT
        self.darts_in_board: int = 0
        self._empty_refs: Dict[int, np.ndarray] = {}
        self._prev_settled_refs: Dict[int, np.ndarray] = {}
        self._prev_loop_grays: Dict[int, np.ndarray] = {}
        self._last_diff_masks: Dict[int, np.ndarray] = {}
        self._last_candidates: Dict[int, CameraDartCandidate] = {}
        self._last_fused_hit: Optional[DartHit] = None
        self._peak_diff_vs_empty: float = 0.0

        self._motion_active: bool = False
        self._hand_motion_seen: bool = False
        self._motion_frames_count: int = 0
        self._settled_since: float = time.monotonic()
        self._cooldown_until: float = 0.0
        self._lock = threading.Lock()
        self._running = False
        self._thread: Optional[threading.Thread] = None

    def start(self) -> None:
        self.stop()
        self.capture_empty_reference()
        self._running = True
        self._thread = threading.Thread(target=self._vision_loop, daemon=True)
        self._thread.start()

    def stop(self) -> None:
        self._running = False
        if self._thread and self._thread.is_alive():
            self._thread.join(timeout=1.5)

    def _preprocess(self, frame: np.ndarray) -> np.ndarray:
        gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
        blurred = cv2.GaussianBlur(gray, (5, 5), 0)
        return blurred

    def capture_empty_reference(self) -> None:
        """Capture current frames as the clean, empty dartboard reference."""
        frames = self.camera_manager.get_all_frames()
        with self._lock:
            for cid, frame in frames.items():
                proc = self._preprocess(frame)
                self._empty_refs[cid] = proc
                self._prev_settled_refs[cid] = proc.copy()
                self._prev_loop_grays[cid] = proc.copy()
                self._last_diff_masks[cid] = np.zeros_like(proc)
            self._last_candidates.clear()
            self.darts_in_board = 0
            self._peak_diff_vs_empty = 0.0
            self._hand_motion_seen = False
            self._motion_frames_count = 0
            self._set_state("READY")

    def notify_board_cleared(self) -> None:
        """Reset simulated darts and recapture empty reference."""
        self.camera_manager.clear_simulated_darts()
        time.sleep(0.05)
        self.capture_empty_reference()

    def _set_state(self, new_state: str) -> None:
        if self.state != new_state:
            self.state = new_state
            if self.on_state_change:
                try:
                    self.on_state_change(new_state)
                except Exception:
                    pass

    def _vision_loop(self) -> None:
        while self._running:
            time.sleep(0.045)  # ~22 Hz
            if not self.enabled:
                continue

            now = time.monotonic()
            if now < self._cooldown_until:
                continue

            frames = self.camera_manager.get_all_frames()
            current_grays: Dict[int, np.ndarray] = {}
            total_motion_px = 0

            for cid, frame in frames.items():
                gray = self._preprocess(frame)
                current_grays[cid] = gray
                prev_loop = self._prev_loop_grays.get(cid)
                if prev_loop is not None and prev_loop.shape == gray.shape:
                    mot_diff = cv2.absdiff(gray, prev_loop)
                    _, mot_bin = cv2.threshold(mot_diff, 22, 255, cv2.THRESH_BINARY)
                    total_motion_px += int(cv2.countNonZero(mot_bin))
                self._prev_loop_grays[cid] = gray

            # Check if motion is happening right now
            if total_motion_px > self.motion_threshold_px:
                self._motion_active = True
                self._motion_frames_count += 1
                if total_motion_px > self.hand_takeout_motion_px or self._motion_frames_count >= 4:
                    self._hand_motion_seen = True
                self._settled_since = now
                self._set_state("MOTION")
                continue

            # If we recently saw motion, wait for settle_time_ms
            if self._motion_active:
                if (now - self._settled_since) * 1000.0 < self.settle_time_ms:
                    self._set_state("SETTLING")
                    continue
                # Motion has settled! Evaluate board state:
                self._motion_active = False
                hand_was_seen = self._hand_motion_seen
                self._hand_motion_seen = False
                self._motion_frames_count = 0
                self._evaluate_settled_board(frames, current_grays, hand_was_seen=hand_was_seen)

    def _measure_max_contour_vs_empty(self, current_grays: Dict[int, np.ndarray]) -> float:
        """
        Compute the average largest contour area when comparing current_grays against _empty_refs.
        Using morphological opening + contour area (instead of raw pixel count) ignores camera
        sensor noise and slight lighting drift while reliably measuring sticking darts.
        """
        kernel_open = cv2.getStructuringElement(cv2.MORPH_ELLIPSE, (3, 3))
        kernel_close = cv2.getStructuringElement(cv2.MORPH_ELLIPSE, (7, 7))
        max_areas: List[float] = []

        for cid, gray in current_grays.items():
            empty_ref = self._empty_refs.get(cid)
            if empty_ref is None or empty_ref.shape != gray.shape:
                continue
            d_empty = cv2.absdiff(gray, empty_ref)
            _, thresh = cv2.threshold(d_empty, self.diff_threshold, 255, cv2.THRESH_BINARY)
            cleaned = cv2.morphologyEx(thresh, cv2.MORPH_OPEN, kernel_open)
            cleaned = cv2.morphologyEx(cleaned, cv2.MORPH_CLOSE, kernel_close)
            contours, _ = cv2.findContours(cleaned, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
            largest = max((cv2.contourArea(c) for c in contours), default=0.0)
            max_areas.append(float(largest))

        return (sum(max_areas) / len(max_areas)) if max_areas else 0.0

    def _evaluate_settled_board(
        self,
        frames: Dict[int, np.ndarray],
        current_grays: Dict[int, np.ndarray],
        hand_was_seen: bool = False,
    ) -> None:
        waiting_takeout = False
        if self.is_turn_waiting_takeout:
            try:
                waiting_takeout = bool(self.is_turn_waiting_takeout())
            except Exception:
                waiting_takeout = False

        # 1. Check for Automatic Takeout (Pfeile herausgezogen)
        if self.auto_takeout_enabled and (self.darts_in_board > 0 or waiting_takeout):
            current_vs_empty = self._measure_max_contour_vs_empty(current_grays)

            # Case A: Board is back to clean/empty state (no dart-sized contour left vs empty_ref)
            board_is_clean = current_vs_empty < (self.min_contour_area * 0.85)

            # Case B: Significant drop (>55%) in sticking dart contour area compared to before takeout
            darts_disappeared = (
                self._peak_diff_vs_empty > self.min_contour_area
                and current_vs_empty < (self._peak_diff_vs_empty * 0.45)
            )

            # Case C: Turn already complete (3 darts thrown / bust / checkout) and player's hand
            # reached into the board and left, leaving fewer/no darts behind
            turn_done_hand_takeout = (
                (self.darts_in_board >= 3 or waiting_takeout)
                and hand_was_seen
                and (board_is_clean or darts_disappeared or current_vs_empty < self._peak_diff_vs_empty * 0.75)
            )

            if board_is_clean or darts_disappeared or turn_done_hand_takeout:
                with self._lock:
                    for cid, gray in current_grays.items():
                        self._empty_refs[cid] = gray.copy()
                        self._prev_settled_refs[cid] = gray.copy()
                    self._last_candidates.clear()
                    self.darts_in_board = 0
                    self._peak_diff_vs_empty = 0.0
                self._set_state("TAKEOUT")
                self._cooldown_until = time.monotonic() + 0.45
                if self.on_takeout_detected:
                    self.on_takeout_detected()
                self._set_state("READY")
                return

        # 2. Check for a newly landed dart (diff against _prev_settled_refs)
        if self.darts_in_board >= 3 or waiting_takeout:
            self._set_state("READY")
            return

        candidates: Dict[int, CameraDartCandidate] = {}
        for cid, gray in current_grays.items():
            cal = self.calibration_manager.cameras.get(cid)
            if cal is None or not cal.is_calibrated:
                continue
            prev_ref = self._prev_settled_refs.get(cid)
            if prev_ref is None or prev_ref.shape != gray.shape:
                self._prev_settled_refs[cid] = gray.copy()
                continue

            cand, mask = self._extract_dart_candidate(cid, gray, prev_ref, cal)
            with self._lock:
                self._last_diff_masks[cid] = mask
            if cand is not None:
                candidates[cid] = cand

        if not candidates:
            self._set_state("READY")
            return

        # Fuse candidates across cameras to determine exact (x, y) dart tip on board
        hit = self._fuse_candidates(candidates)
        if hit is not None:
            current_vs_empty = self._measure_max_contour_vs_empty(current_grays)
            with self._lock:
                for cid, gray in current_grays.items():
                    self._prev_settled_refs[cid] = gray.copy()
                self._last_candidates = candidates
                self._last_fused_hit = hit
                self.darts_in_board += 1
                self._peak_diff_vs_empty = max(self._peak_diff_vs_empty, current_vs_empty)
            self._cooldown_until = time.monotonic() + 0.35
            self._set_state("READY")
            if self.on_dart_detected:
                self.on_dart_detected(hit)
        else:
            self._set_state("READY")

    def _extract_dart_candidate(
        self,
        cam_id: int,
        current_gray: np.ndarray,
        prev_gray: np.ndarray,
        cal,
    ) -> Tuple[Optional[CameraDartCandidate], np.ndarray]:
        h, w = current_gray.shape[:2]
        diff = cv2.absdiff(current_gray, prev_gray)
        _, thresh = cv2.threshold(diff, self.diff_threshold, 255, cv2.THRESH_BINARY)

        kernel_open = cv2.getStructuringElement(cv2.MORPH_ELLIPSE, (3, 3))
        kernel_close = cv2.getStructuringElement(cv2.MORPH_ELLIPSE, (7, 7))
        cleaned = cv2.morphologyEx(thresh, cv2.MORPH_OPEN, kernel_open)
        cleaned = cv2.morphologyEx(cleaned, cv2.MORPH_CLOSE, kernel_close)

        contours, _ = cv2.findContours(cleaned, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
        if not contours:
            return None, cleaned

        valid_contours = [
            c for c in contours
            if self.min_contour_area <= cv2.contourArea(c) <= self.max_contour_area
        ]
        if not valid_contours:
            return None, cleaned

        best_cnt = max(valid_contours, key=cv2.contourArea)
        area = float(cv2.contourArea(best_cnt))
        pts = best_cnt.reshape(-1, 2).astype(np.float32)
        if len(pts) < 5:
            return None, cleaned

        line = cv2.fitLine(pts, cv2.DIST_L2, 0, 0.01, 0.01).flatten()
        vx, vy, x0, y0 = float(line[0]), float(line[1]), float(line[2]), float(line[3])

        projections = (pts[:, 0] - x0) * vx + (pts[:, 1] - y0) * vy
        min_idx = int(np.argmin(projections))
        max_idx = int(np.argmax(projections))
        end_a = (int(round(pts[min_idx, 0])), int(round(pts[min_idx, 1])))
        end_b = (int(round(pts[max_idx, 0])), int(round(pts[max_idx, 1])))

        span = float(projections[max_idx] - projections[min_idx])
        if span > 8.0:
            near_a = pts[projections <= projections[min_idx] + 0.25 * span]
            near_b = pts[projections >= projections[max_idx] - 0.25 * span]
            perp_a = np.std(-(near_a[:, 0] - x0) * vy + (near_a[:, 1] - y0) * vx) if len(near_a) > 2 else 1.0
            perp_b = np.std(-(near_b[:, 0] - x0) * vy + (near_b[:, 1] - y0) * vx) if len(near_b) > 2 else 1.0
        else:
            perp_a, perp_b = 1.0, 1.0

        if perp_a <= perp_b:
            tip_px, tail_px = end_a, end_b
        else:
            tip_px, tail_px = end_b, end_a

        tip_board = cal.image_px_to_board_xy(tip_px[0], tip_px[1], w, h)
        tail_board = cal.image_px_to_board_xy(tail_px[0], tail_px[1], w, h)
        if tip_board is None or tail_board is None:
            return None, cleaned

        return (
            CameraDartCandidate(
                cam_id=cam_id,
                tip_px=tip_px,
                tail_px=tail_px,
                tip_board=tip_board,
                tail_board=tail_board,
                contour_area=area,
                contour=best_cnt,
            ),
            cleaned,
        )

    def _fuse_candidates(self, candidates: Dict[int, CameraDartCandidate]) -> Optional[DartHit]:
        cam_list = list(candidates.values())
        n_cams = len(cam_list)
        if n_cams == 0:
            return None

        if n_cams == 1:
            c = cam_list[0]
            bx, by = c.tip_board
            return coords_to_hit(bx, by, confidence=0.78, cameras_used=1, source="camera")

        endpoint_options = [[c.tip_board, c.tail_board] for c in cam_list]
        best_spread = float("inf")
        best_combo: List[Tuple[float, float]] = [c.tip_board for c in cam_list]
        best_mask = 0

        for mask in range(1 << n_cams):
            combo = []
            for idx in range(n_cams):
                choice = (mask >> idx) & 1
                combo.append(endpoint_options[idx][choice])
            dist_sum = 0.0
            for i in range(n_cams):
                for j in range(i + 1, n_cams):
                    dist_sum += math.hypot(combo[i][0] - combo[j][0], combo[i][1] - combo[j][1])
            if dist_sum < best_spread:
                best_spread = dist_sum
                best_combo = combo
                best_mask = mask

        for idx, c in enumerate(cam_list):
            if ((best_mask >> idx) & 1) == 1:
                c.tip_px, c.tail_px = c.tail_px, c.tip_px
                c.tip_board, c.tail_board = c.tail_board, c.tip_board

        intersections: List[Tuple[float, float]] = []
        for i in range(n_cams):
            for j in range(i + 1, n_cams):
                pt_int = self._intersect_lines(
                    cam_list[i].tip_board,
                    cam_list[i].tail_board,
                    cam_list[j].tip_board,
                    cam_list[j].tail_board,
                )
                if pt_int is not None:
                    mean_tip_x = sum(p[0] for p in best_combo) / n_cams
                    mean_tip_y = sum(p[1] for p in best_combo) / n_cams
                    if math.hypot(pt_int[0] - mean_tip_x, pt_int[1] - mean_tip_y) < 0.08:
                        intersections.append(pt_int)

        all_points = list(best_combo) + intersections
        bx = sum(p[0] for p in all_points) / len(all_points)
        by = sum(p[1] for p in all_points) / len(all_points)

        avg_pair_dist = best_spread / max(1, (n_cams * (n_cams - 1)) // 2)
        confidence = max(0.65, min(0.99, 1.0 - avg_pair_dist * 2.5))

        return coords_to_hit(bx, by, confidence=confidence, cameras_used=n_cams, source="camera")

    @staticmethod
    def _intersect_lines(
        p1: Tuple[float, float],
        p2: Tuple[float, float],
        p3: Tuple[float, float],
        p4: Tuple[float, float],
    ) -> Optional[Tuple[float, float]]:
        x1, y1 = p1
        x2, y2 = p2
        x3, y3 = p3
        x4, y4 = p4
        denom = (x1 - x2) * (y3 - y4) - (y1 - y2) * (x3 - x4)
        if abs(denom) < 1e-6:
            return None
        px = ((x1 * y2 - y1 * x2) * (x3 - x4) - (x1 - x2) * (x3 * y4 - y3 * x4)) / denom
        py = ((x1 * y2 - y1 * x2) * (y3 - y4) - (y1 - y2) * (x3 * y4 - y3 * x4)) / denom
        return (px, py)

    def render_annotated_camera_frame(self, cam_id: int, show_spider: bool = True) -> np.ndarray:
        frame = self.camera_manager.get_frame(cam_id).copy()
        cal = self.calibration_manager.cameras.get(cam_id)
        if show_spider and cal is not None:
            cal.draw_perspective_spider_on_camera(frame)

        with self._lock:
            cand = self._last_candidates.get(cam_id)

        if cand is not None:
            cv2.drawContours(frame, [cand.contour], -1, (0, 255, 120), 2, cv2.LINE_AA)
            cv2.line(frame, cand.tail_px, cand.tip_px, (0, 230, 255), 2, cv2.LINE_AA)
            cv2.circle(frame, cand.tip_px, 7, (0, 40, 255), 2, cv2.LINE_AA)
            cv2.circle(frame, cand.tip_px, 2, (255, 255, 255), -1, cv2.LINE_AA)
            cv2.putText(
                frame,
                "TIP",
                (cand.tip_px[0] + 10, cand.tip_px[1] - 8),
                cv2.FONT_HERSHEY_SIMPLEX,
                0.5,
                (0, 80, 255),
                2,
                cv2.LINE_AA,
            )

        status_col = (0, 230, 110) if self.state == "READY" else (0, 190, 255)
        cv2.putText(
            frame,
            f"CAM {cam_id + 1} | {self.state} | Darts: {self.darts_in_board}/3",
            (12, 26),
            cv2.FONT_HERSHEY_SIMPLEX,
            0.58,
            status_col,
            2,
            cv2.LINE_AA,
        )
        return frame

    def render_diff_mask_frame(self, cam_id: int) -> np.ndarray:
        with self._lock:
            mask = self._last_diff_masks.get(cam_id)
        if mask is None:
            canvas = np.zeros((480, 640, 3), dtype=np.uint8)
            cv2.putText(canvas, "Noch keine Differenz-Maske", (150, 240), cv2.FONT_HERSHEY_SIMPLEX, 0.7, (160, 160, 160), 2)
            return canvas
        color_mask = cv2.cvtColor(mask, cv2.COLOR_GRAY2BGR)
        with self._lock:
            cand = self._last_candidates.get(cam_id)
        if cand is not None:
            cv2.drawContours(color_mask, [cand.contour], -1, (0, 255, 100), 2)
            cv2.circle(color_mask, cand.tip_px, 8, (0, 60, 255), 2)
        return color_mask

    def update_settings(
        self,
        enabled: Optional[bool] = None,
        auto_takeout_enabled: Optional[bool] = None,
        diff_threshold: Optional[int] = None,
        min_contour_area: Optional[int] = None,
        settle_time_ms: Optional[int] = None,
    ) -> dict:
        if enabled is not None:
            self.enabled = bool(enabled)
        if auto_takeout_enabled is not None:
            self.auto_takeout_enabled = bool(auto_takeout_enabled)
        if diff_threshold is not None:
            self.diff_threshold = max(8, min(120, int(diff_threshold)))
        if min_contour_area is not None:
            self.min_contour_area = max(20, min(5000, int(min_contour_area)))
        if settle_time_ms is not None:
            self.settle_time_ms = max(80, min(1500, int(settle_time_ms)))
        return self.get_status()

    def get_status(self) -> dict:
        return {
            "enabled": self.enabled,
            "auto_takeout_enabled": self.auto_takeout_enabled,
            "state": self.state,
            "darts_in_board": self.darts_in_board,
            "diff_threshold": self.diff_threshold,
            "min_contour_area": self.min_contour_area,
            "settle_time_ms": self.settle_time_ms,
            "last_hit": self._last_fused_hit.to_dict() if self._last_fused_hit else None,
        }
