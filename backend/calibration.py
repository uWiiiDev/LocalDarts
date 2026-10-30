"""
Camera calibration and perspective transformation (Homography) for LocalDarts.
"""

from __future__ import annotations
import json
import math
from pathlib import Path
import sys
from typing import Dict, List, Optional, Tuple
import cv2
import numpy as np

from .board_geometry import (
    CALIBRATION_PRESETS,
    R_INNER_BULL,
    R_OUTER_BULL,
    R_TRIPLE_INNER,
    R_TRIPLE_OUTER,
    R_DOUBLE_INNER,
    R_DOUBLE_OUTER,
    SECTORS_CLOCKWISE,
    polar_to_board_xy,
)


def get_writable_config_dir() -> Path:
    """Return writable config directory next to the executable (PyInstaller) or project root."""
    if getattr(sys, "frozen", False):
        return Path(sys.executable).resolve().parent / "config"
    return Path(__file__).resolve().parent.parent / "config"


CONFIG_DIR = get_writable_config_dir()
CALIBRATION_FILE = CONFIG_DIR / "calibration.json"


class CameraCalibration:
    """Stores 4-point calibration and computes perspective transforms for a single camera."""

    def __init__(
        self,
        cam_id: int,
        preset_id: str = "autodarts_wires_ccw",
        image_points_norm: Optional[List[Tuple[float, float]]] = None,
        tip_offset_px: float = 0.0,
        camera_angle_hint_deg: Optional[float] = None,
    ):
        self.cam_id = cam_id
        self.preset_id = preset_id if preset_id in CALIBRATION_PRESETS else "autodarts_wires_ccw"
        # Normalized image coordinates [(u, v), ...] in [0.0, 1.0] x [0.0, 1.0]
        self.image_points_norm: List[Tuple[float, float]] = image_points_norm or []
        self.tip_offset_px: float = tip_offset_px
        # Default mounting angles for 3 cameras: Cam 0 = Top (0 deg), Cam 1 = Bottom-Right (120 deg), Cam 2 = Bottom-Left (240 deg)
        default_angles = {0: 0.0, 1: 120.0, 2: 240.0}
        self.camera_angle_hint_deg: float = (
            camera_angle_hint_deg if camera_angle_hint_deg is not None else default_angles.get(cam_id, 0.0)
        )
        self._H_norm_to_board: Optional[np.ndarray] = None
        self._H_board_to_norm: Optional[np.ndarray] = None
        self._recompute_homography()

    @property
    def is_calibrated(self) -> bool:
        return self._H_norm_to_board is not None and len(self.image_points_norm) == 4

    def get_reference_board_points(self) -> np.ndarray:
        preset = CALIBRATION_PRESETS[self.preset_id]
        pts = [pt["xy"] for pt in preset["points"]]
        return np.array(pts, dtype=np.float32)

    def _recompute_homography(self) -> None:
        if len(self.image_points_norm) != 4:
            self._H_norm_to_board = None
            self._H_board_to_norm = None
            return
        src = np.array(self.image_points_norm, dtype=np.float32)
        dst = self.get_reference_board_points()
        try:
            self._H_norm_to_board = cv2.getPerspectiveTransform(src, dst)
            self._H_board_to_norm = cv2.getPerspectiveTransform(dst, src)
        except cv2.error:
            self._H_norm_to_board = None
            self._H_board_to_norm = None

    def set_points(
        self,
        image_points_norm: List[Tuple[float, float]],
        preset_id: Optional[str] = None,
    ) -> bool:
        if preset_id and preset_id in CALIBRATION_PRESETS:
            self.preset_id = preset_id
        self.image_points_norm = [(float(u), float(v)) for u, v in image_points_norm[:4]]
        self._recompute_homography()
        return self.is_calibrated

    def image_px_to_board_xy(self, u_px: float, v_px: float, width: int, height: int) -> Optional[Tuple[float, float]]:
        """Transform pixel coordinates (u_px, v_px) into normalized board coordinates (x, y)."""
        if not self.is_calibrated or self._H_norm_to_board is None or width <= 0 or height <= 0:
            return None
        u_norm = u_px / float(width)
        v_norm = v_px / float(height)
        pt = np.array([[[u_norm, v_norm]]], dtype=np.float32)
        transformed = cv2.perspectiveTransform(pt, self._H_norm_to_board)
        bx, by = float(transformed[0, 0, 0]), float(transformed[0, 0, 1])
        return (bx, by)

    def board_xy_to_image_px(self, bx: float, by: float, width: int, height: int) -> Optional[Tuple[int, int]]:
        """Transform normalized board coordinates (bx, by) into image pixel coordinates (u_px, v_px)."""
        if not self.is_calibrated or self._H_board_to_norm is None or width <= 0 or height <= 0:
            return None
        pt = np.array([[[bx, by]]], dtype=np.float32)
        transformed = cv2.perspectiveTransform(pt, self._H_board_to_norm)
        u_px = int(round(float(transformed[0, 0, 0]) * width))
        v_px = int(round(float(transformed[0, 0, 1]) * height))
        return (u_px, v_px)

    def warp_frame_to_board_view(self, frame: np.ndarray, out_size: int = 480) -> np.ndarray:
        """
        Warp a camera frame into a flat top-down view of the dartboard,
        including spider wire overlay for visual verification.
        Board coordinates [-1.20, +1.20] map to [0, out_size].
        """
        h, w = frame.shape[:2]
        if not self.is_calibrated or self._H_norm_to_board is None:
            canvas = np.zeros((out_size, out_size, 3), dtype=np.uint8)
            cv2.putText(
                canvas,
                f"Kamera {self.cam_id + 1} nicht kalibriert",
                (45, out_size // 2),
                cv2.FONT_HERSHEY_SIMPLEX,
                0.7,
                (120, 180, 255),
                2,
                cv2.LINE_AA,
            )
            return canvas

        # Build pixel-to-canvas homography:
        # 1) scale image pixels (u_px, v_px) -> (u_norm, v_norm)
        S_px_to_norm = np.array(
            [[1.0 / w, 0.0, 0.0], [0.0, 1.0 / h, 0.0], [0.0, 0.0, 1.0]],
            dtype=np.float64,
        )
        # 2) scale board coords [-1.2, +1.2] -> [0, out_size]
        scale = out_size / 2.4
        offset = out_size / 2.0
        S_board_to_canvas = np.array(
            [[scale, 0.0, offset], [0.0, scale, offset], [0.0, 0.0, 1.0]],
            dtype=np.float64,
        )
        H_total = S_board_to_canvas @ self._H_norm_to_board.astype(np.float64) @ S_px_to_norm
        warped = cv2.warpPerspective(frame, H_total, (out_size, out_size))
        self.draw_topdown_spider_overlay(warped, out_size)
        return warped

    @staticmethod
    def draw_topdown_spider_overlay(canvas: np.ndarray, out_size: int = 480) -> None:
        """Draw the mathematical dartboard rings and sector wires on a top-down warped image."""
        scale = out_size / 2.4
        center = (out_size // 2, out_size // 2)

        for r_norm, color, thickness in [
            (R_INNER_BULL, (0, 255, 120), 1),
            (R_OUTER_BULL, (0, 220, 100), 1),
            (R_TRIPLE_INNER, (0, 220, 255), 1),
            (R_TRIPLE_OUTER, (0, 220, 255), 1),
            (R_DOUBLE_INNER, (0, 180, 255), 1),
            (R_DOUBLE_OUTER, (0, 255, 100), 2),
        ]:
            cv2.circle(canvas, center, int(round(r_norm * scale)), color, thickness, cv2.LINE_AA)

        # Draw 20 sector dividing wires (at -9, +9, +27, ... degrees)
        for i in range(20):
            angle_deg = i * 18.0 - 9.0
            x_in, y_in = polar_to_board_xy(R_OUTER_BULL, angle_deg)
            x_out, y_out = polar_to_board_xy(R_DOUBLE_OUTER, angle_deg)
            p1 = (int(round(center[0] + x_in * scale)), int(round(center[1] + y_in * scale)))
            p2 = (int(round(center[0] + x_out * scale)), int(round(center[1] + y_out * scale)))
            cv2.line(canvas, p1, p2, (180, 240, 180), 1, cv2.LINE_AA)

        # Draw sector numbers around the outside
        for i, num in enumerate(SECTORS_CLOCKWISE):
            angle_deg = i * 18.0
            nx, ny = polar_to_board_xy(1.10, angle_deg)
            px = int(round(center[0] + nx * scale)) - 10
            py = int(round(center[1] + ny * scale)) + 5
            cv2.putText(
                canvas,
                str(num),
                (px, py),
                cv2.FONT_HERSHEY_SIMPLEX,
                0.42,
                (255, 255, 255),
                1,
                cv2.LINE_AA,
            )

    def draw_perspective_spider_on_camera(self, frame: np.ndarray) -> None:
        """Draw the projected dartboard spider and calibration points onto the raw tilted camera frame."""
        h, w = frame.shape[:2]

        # Draw clicked calibration points
        colors = [(0, 80, 255), (0, 220, 255), (0, 255, 100), (255, 140, 0)]
        for idx, (u_norm, v_norm) in enumerate(self.image_points_norm):
            px, py = int(round(u_norm * w)), int(round(v_norm * h))
            color = colors[idx % len(colors)]
            cv2.circle(frame, (px, py), 7, color, 2, cv2.LINE_AA)
            cv2.circle(frame, (px, py), 2, (255, 255, 255), -1, cv2.LINE_AA)
            cv2.putText(
                frame,
                f"P{idx + 1}",
                (px + 9, py - 6),
                cv2.FONT_HERSHEY_SIMPLEX,
                0.5,
                color,
                2,
                cv2.LINE_AA,
            )

        if not self.is_calibrated:
            return

        # Draw rings projected back into camera space
        for r_norm, color in [
            (R_OUTER_BULL, (0, 255, 140)),
            (R_TRIPLE_INNER, (0, 210, 255)),
            (R_TRIPLE_OUTER, (0, 210, 255)),
            (R_DOUBLE_INNER, (0, 160, 255)),
            (R_DOUBLE_OUTER, (0, 255, 100)),
        ]:
            ring_pts = []
            for step in range(72):
                ang = step * 5.0
                bx, by = polar_to_board_xy(r_norm, ang)
                img_pt = self.board_xy_to_image_px(bx, by, w, h)
                if img_pt is not None:
                    ring_pts.append(img_pt)
            if len(ring_pts) > 2:
                pts_arr = np.array(ring_pts, dtype=np.int32).reshape((-1, 1, 2))
                cv2.polylines(frame, [pts_arr], isClosed=True, color=color, thickness=1, lineType=cv2.LINE_AA)

        # Draw 20 sector dividing lines projected back into camera space
        for i in range(20):
            angle_deg = i * 18.0 - 9.0
            bx1, by1 = polar_to_board_xy(R_OUTER_BULL, angle_deg)
            bx2, by2 = polar_to_board_xy(R_DOUBLE_OUTER, angle_deg)
            p1 = self.board_xy_to_image_px(bx1, by1, w, h)
            p2 = self.board_xy_to_image_px(bx2, by2, w, h)
            if p1 and p2:
                cv2.line(frame, p1, p2, (120, 230, 120), 1, cv2.LINE_AA)

    def to_dict(self) -> dict:
        return {
            "cam_id": self.cam_id,
            "preset_id": self.preset_id,
            "image_points_norm": self.image_points_norm,
            "is_calibrated": self.is_calibrated,
            "tip_offset_px": self.tip_offset_px,
            "camera_angle_hint_deg": self.camera_angle_hint_deg,
        }


class CalibrationManager:
    """Manages calibration state for all 3 cameras and persists to disk."""

    def __init__(self, num_cameras: int = 3):
        self.num_cameras = num_cameras
        self.cameras: Dict[int, CameraCalibration] = {
            i: CameraCalibration(cam_id=i) for i in range(num_cameras)
        }
        self.load()

    def load(self) -> None:
        if not CALIBRATION_FILE.exists():
            return
        try:
            data = json.loads(CALIBRATION_FILE.read_text(encoding="utf-8"))
            for cam_key, cam_data in data.get("cameras", {}).items():
                cid = int(cam_key)
                if cid in self.cameras:
                    pts = [tuple(p) for p in cam_data.get("image_points_norm", [])]
                    self.cameras[cid] = CameraCalibration(
                        cam_id=cid,
                        preset_id=cam_data.get("preset_id", "autodarts_wires_ccw"),
                        image_points_norm=pts,
                        tip_offset_px=float(cam_data.get("tip_offset_px", 0.0)),
                        camera_angle_hint_deg=cam_data.get("camera_angle_hint_deg"),
                    )
        except Exception as exc:
            print(f"[CalibrationManager] Warnung beim Laden der Kalibrierung: {exc}")

    def save(self) -> None:
        CONFIG_DIR.mkdir(parents=True, exist_ok=True)
        payload = {
            "cameras": {str(cid): cal.to_dict() for cid, cal in self.cameras.items()}
        }
        CALIBRATION_FILE.write_text(json.dumps(payload, indent=2), encoding="utf-8")

    def set_camera_points(
        self,
        cam_id: int,
        image_points_norm: List[Tuple[float, float]],
        preset_id: Optional[str] = None,
    ) -> dict:
        if cam_id not in self.cameras:
            self.cameras[cam_id] = CameraCalibration(cam_id=cam_id)
        cal = self.cameras[cam_id]
        cal.set_points(image_points_norm, preset_id=preset_id)
        self.save()
        return cal.to_dict()

    def reset_camera(self, cam_id: int) -> dict:
        if cam_id in self.cameras:
            self.cameras[cam_id].set_points([])
            self.save()
            return self.cameras[cam_id].to_dict()
        return {}

    def apply_default_simulation_calibration(self, cam_id: int) -> dict:
        """
        Provide an instant 4-point calibration matching the synthetic 3-camera simulator
        so users can test the full pipeline immediately.
        """
        sim_Configs = self.get_simulation_quads()
        quad = sim_Configs.get(cam_id, sim_Configs[0])
        return self.set_camera_points(cam_id, quad, preset_id="autodarts_wires_ccw")

    @staticmethod
    def get_simulation_quads() -> Dict[int, List[Tuple[float, float]]]:
        """Return the exact normalized 4-point quads used by the synthetic camera renderer."""
        return {
            0: [(0.452, 0.145), (0.818, 0.448), (0.538, 0.855), (0.172, 0.542)],
            1: [(0.435, 0.165), (0.835, 0.460), (0.555, 0.840), (0.155, 0.525)],
            2: [(0.468, 0.160), (0.842, 0.472), (0.522, 0.848), (0.162, 0.535)],
        }

    def get_status(self) -> dict:
        return {
            "presets": CALIBRATION_PRESETS,
            "cameras": {cid: cal.to_dict() for cid, cal in self.cameras.items()},
        }
