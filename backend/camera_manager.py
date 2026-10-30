"""
Multi-camera capture manager (3 USB cameras + realistic synthetic camera fallback)
for LocalDarts.
"""

from __future__ import annotations
import glob
import json
import math
from pathlib import Path
import sys
import threading
import time
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
from .calibration import CalibrationManager, get_writable_config_dir

CONFIG_DIR = get_writable_config_dir()
CAMERA_CONFIG_FILE = CONFIG_DIR / "cameras.json"
IS_WINDOWS = sys.platform.startswith("win")


def _preferred_cv_backend() -> int:
    return cv2.CAP_DSHOW if IS_WINDOWS else cv2.CAP_V4L2


def discover_video_devices() -> List[dict]:
    """
    Scan video devices on Linux (/dev/video*) or Windows (DirectShow indices 0..5).
    """
    devices = []
    if IS_WINDOWS:
        for idx in range(6):
            cap = cv2.VideoCapture(idx, cv2.CAP_DSHOW)
            if cap.isOpened():
                devices.append(
                    {
                        "index": idx,
                        "path": f"CAM:{idx}",
                        "name": f"USB-Kamera #{idx} (Windows DirectShow)",
                    }
                )
            cap.release()
        return devices

    paths = sorted(glob.glob("/dev/video*"))
    for p in paths:
        try:
            idx = int(p.replace("/dev/video", ""))
        except ValueError:
            continue
        name = f"Video Device {idx} ({p})"
        sys_name_path = Path(f"/sys/class/video4linux/video{idx}/name")
        if sys_name_path.exists():
            try:
                name = f"{sys_name_path.read_text().strip()} ({p})"
            except Exception:
                pass
        devices.append({"index": idx, "path": p, "name": name})
    return devices


class SyntheticBoardRenderer:
    """
    Renders a realistic perspective-tilted bristle dartboard for each of the 3 camera slots,
    plus any simulated darts currently sticking in the board so the OpenCV diff detector
    can be tested end-to-end even when fewer than 3 physical cameras are plugged in.
    """

    def __init__(self, width: int = 640, height: int = 480):
        self.width = width
        self.height = height
        self._base_topdown = self._create_topdown_board(600)
        self._warped_backgrounds: Dict[int, Tuple[np.ndarray, np.ndarray]] = {}
        self._build_camera_perspectives()

    def _create_topdown_board(self, size: int = 600) -> np.ndarray:
        """Render a clean top-down bristle dartboard in [-1.2, +1.2] board space."""
        img = np.full((size, size, 3), (28, 30, 34), dtype=np.uint8)
        center = (size // 2, size // 2)
        scale = size / 2.4

        # Outer surround
        cv2.circle(img, center, int(round(1.16 * scale)), (22, 22, 25), -1, cv2.LINE_AA)

        # Draw 20 sectors
        for i, num in enumerate(SECTORS_CLOCKWISE):
            start_ang = i * 18.0 - 9.0 - 90.0
            end_ang = start_ang + 18.0
            is_dark = (i % 2 == 0)
            single_col = (26, 28, 30) if is_dark else (195, 212, 225)
            ring_col = (35, 35, 210) if is_dark else (45, 145, 35)

            # Double ring
            cv2.ellipse(
                img, center,
                (int(round(R_DOUBLE_OUTER * scale)), int(round(R_DOUBLE_OUTER * scale))),
                0, start_ang, end_ang, ring_col, -1, cv2.LINE_AA
            )
            # Outer single
            cv2.ellipse(
                img, center,
                (int(round(R_DOUBLE_INNER * scale)), int(round(R_DOUBLE_INNER * scale))),
                0, start_ang, end_ang, single_col, -1, cv2.LINE_AA
            )
            # Triple ring
            cv2.ellipse(
                img, center,
                (int(round(R_TRIPLE_OUTER * scale)), int(round(R_TRIPLE_OUTER * scale))),
                0, start_ang, end_ang, ring_col, -1, cv2.LINE_AA
            )
            # Inner single
            cv2.ellipse(
                img, center,
                (int(round(R_TRIPLE_INNER * scale)), int(round(R_TRIPLE_INNER * scale))),
                0, start_ang, end_ang, single_col, -1, cv2.LINE_AA
            )

        # Outer & Inner Bull
        cv2.circle(img, center, int(round(R_OUTER_BULL * scale)), (45, 145, 35), -1, cv2.LINE_AA)
        cv2.circle(img, center, int(round(R_INNER_BULL * scale)), (35, 35, 210), -1, cv2.LINE_AA)

        # Spider wires
        for r_norm in [R_INNER_BULL, R_OUTER_BULL, R_TRIPLE_INNER, R_TRIPLE_OUTER, R_DOUBLE_INNER, R_DOUBLE_OUTER]:
            cv2.circle(img, center, int(round(r_norm * scale)), (190, 195, 200), 1, cv2.LINE_AA)

        for i in range(20):
            ang = i * 18.0 - 9.0
            x1, y1 = polar_to_board_xy(R_OUTER_BULL, ang)
            x2, y2 = polar_to_board_xy(R_DOUBLE_OUTER, ang)
            p1 = (int(round(center[0] + x1 * scale)), int(round(center[1] + y1 * scale)))
            p2 = (int(round(center[0] + x2 * scale)), int(round(center[1] + y2 * scale)))
            cv2.line(img, p1, p2, (190, 195, 200), 1, cv2.LINE_AA)

        # Numbers on wire ring
        for i, num in enumerate(SECTORS_CLOCKWISE):
            ang = i * 18.0
            nx, ny = polar_to_board_xy(1.08, ang)
            px = int(round(center[0] + nx * scale)) - 10
            py = int(round(center[1] + ny * scale)) + 6
            cv2.putText(img, str(num), (px, py), cv2.FONT_HERSHEY_SIMPLEX, 0.48, (235, 235, 235), 1, cv2.LINE_AA)

        return img

    def _build_camera_perspectives(self) -> None:
        size = self._base_topdown.shape[0]
        scale = size / 2.4
        offset = size / 2.0

        preset_pts = CALIBRATION_PRESETS["autodarts_wires_ccw"]["points"]
        board_quad = np.array([pt["xy"] for pt in preset_pts], dtype=np.float32)

        S_board_to_topdown = np.array(
            [[scale, 0.0, offset], [0.0, scale, offset], [0.0, 0.0, 1.0]],
            dtype=np.float32,
        )
        S_topdown_to_board = np.linalg.inv(S_board_to_topdown)

        sim_quads = CalibrationManager.get_simulation_quads()
        for cid, norm_quad in sim_quads.items():
            dst_px = np.array(
                [(u * self.width, v * self.height) for u, v in norm_quad],
                dtype=np.float32,
            )
            H_board_to_cam = cv2.getPerspectiveTransform(board_quad, dst_px)
            H_topdown_to_cam = H_board_to_cam @ S_topdown_to_board
            warped_bg = cv2.warpPerspective(
                self._base_topdown,
                H_topdown_to_cam,
                (self.width, self.height),
                borderValue=(18, 20, 24),
            )
            self._warped_backgrounds[cid] = (warped_bg, H_board_to_cam)

    def render_frame(
        self,
        cam_id: int,
        simulated_darts: List[Tuple[float, float]],
    ) -> np.ndarray:
        """
        Render a camera frame for cam_id with any active simulated darts drawn
        so that their tip touches the exact board coordinate (bx, by) and their
        shaft/flight extends outward according to the camera perspective.
        """
        bg, H_board_to_cam = self._warped_backgrounds.get(cam_id, self._warped_backgrounds[0])
        frame = bg.copy()

        # Camera viewing angle influences direction of protruding dart barrel in 2D projection
        cam_mounting_angles = {0: -35.0, 1: 85.0, 2: 205.0}
        angle_rad = math.radians(cam_mounting_angles.get(cam_id, -35.0))
        dx_tail = math.sin(angle_rad) * 58.0
        dy_tail = -math.cos(angle_rad) * 58.0

        for bx, by in simulated_darts:
            pt = np.array([[[bx, by]]], dtype=np.float32)
            tip_px_arr = cv2.perspectiveTransform(pt, H_board_to_cam)
            tx = int(round(float(tip_px_arr[0, 0, 0])))
            ty = int(round(float(tip_px_arr[0, 0, 1])))
            tail_x = int(round(tx + dx_tail))
            tail_y = int(round(ty + dy_tail))

            # Draw dart shadow, metallic barrel, shaft, and bright flight
            cv2.line(frame, (tx, ty), (tail_x, tail_y), (235, 240, 245), 4, cv2.LINE_AA)
            cv2.line(
                frame,
                (int(round(tx + dx_tail * 0.45)), int(round(ty + dy_tail * 0.45))),
                (tail_x, tail_y),
                (40, 210, 255),
                6,
                cv2.LINE_AA,
            )
            # Flight polygon at tail
            perp_x = -dy_tail * 0.22
            perp_y = dx_tail * 0.22
            flight_pts = np.array(
                [
                    [int(round(tx + dx_tail * 0.72)), int(round(ty + dy_tail * 0.72))],
                    [int(round(tail_x + perp_x)), int(round(tail_y + perp_y))],
                    [int(round(tail_x + dx_tail * 0.18)), int(round(tail_y + dy_tail * 0.18))],
                    [int(round(tail_x - perp_x)), int(round(tail_y - perp_y))],
                ],
                dtype=np.int32,
            )
            cv2.fillConvexPoly(frame, flight_pts, (20, 180, 255), cv2.LINE_AA)

        return frame


class CameraStreamSlot:
    """Represents one of the 3 camera slots (physical USB camera or synthetic simulator)."""

    def __init__(self, slot_id: int, device_index: Optional[int], renderer: SyntheticBoardRenderer):
        self.slot_id = slot_id
        self.device_index: Optional[int] = device_index  # None or -1 means synthetic simulator
        self.renderer = renderer
        self.width = 640
        self.height = 480
        self.fps = 0.0
        self.is_physical_open = False
        self._cap: Optional[cv2.VideoCapture] = None
        self._latest_frame: Optional[np.ndarray] = None
        self._lock = threading.Lock()
        self._running = False
        self._thread: Optional[threading.Thread] = None

    def start(self) -> None:
        self.stop()
        self._running = True
        self._thread = threading.Thread(target=self._capture_loop, daemon=True)
        self._thread.start()

    def stop(self) -> None:
        self._running = False
        if self._thread and self._thread.is_alive():
            self._thread.join(timeout=1.5)
        self._release_cap()

    def set_device(self, device_index: Optional[int]) -> None:
        self.device_index = device_index
        self.start()

    def _open_cap(self) -> bool:
        self._release_cap()
        if self.device_index is None or self.device_index < 0:
            self.is_physical_open = False
            return False
        try:
            cap = cv2.VideoCapture(self.device_index, _preferred_cv_backend())
            if not cap.isOpened():
                cap = cv2.VideoCapture(self.device_index)
            if not cap.isOpened():
                self.is_physical_open = False
                return False
            # Set MJPG to save USB 2.0 bandwidth when running 3 cameras simultaneously
            cap.set(cv2.CAP_PROP_FOURCC, cv2.VideoWriter_fourcc(*"MJPG"))
            cap.set(cv2.CAP_PROP_FRAME_WIDTH, self.width)
            cap.set(cv2.CAP_PROP_FRAME_HEIGHT, self.height)
            cap.set(cv2.CAP_PROP_FPS, 30)
            ok, frame = cap.read()
            if not ok or frame is None:
                cap.release()
                self.is_physical_open = False
                return False
            with self._lock:
                self._latest_frame = frame
            self._cap = cap
            self.is_physical_open = True
            return True
        except Exception:
            self.is_physical_open = False
            return False

    def _release_cap(self) -> None:
        if self._cap is not None:
            try:
                self._cap.release()
            except Exception:
                pass
            self._cap = None
        self.is_physical_open = False

    def _capture_loop(self) -> None:
        self._open_cap()
        last_time = time.monotonic()
        frames_count = 0

        while self._running:
            if self.is_physical_open and self._cap is not None:
                ok, frame = self._cap.read()
                if ok and frame is not None:
                    with self._lock:
                        self._latest_frame = frame
                    frames_count += 1
                else:
                    time.sleep(0.05)
            else:
                # Synthetic mode frame pacing (~25 FPS)
                time.sleep(0.04)
                frames_count += 1

            now = time.monotonic()
            if now - last_time >= 1.0:
                self.fps = round(frames_count / (now - last_time), 1)
                frames_count = 0
                last_time = now

    def get_frame(self, simulated_darts: List[Tuple[float, float]]) -> np.ndarray:
        if self.is_physical_open:
            with self._lock:
                if self._latest_frame is not None:
                    return self._latest_frame.copy()
        return self.renderer.render_frame(self.slot_id, simulated_darts)

    def get_status(self) -> dict:
        return {
            "slot_id": self.slot_id,
            "device_index": self.device_index,
            "mode": "usb" if self.is_physical_open else "simulation",
            "is_physical_open": self.is_physical_open,
            "fps": self.fps,
            "resolution": f"{self.width}x{self.height}",
        }


class CameraManager:
    """Manages 3 camera stream slots and simulated board darts for testing."""

    def __init__(self, num_slots: int = 3):
        self.num_slots = num_slots
        self.renderer = SyntheticBoardRenderer(width=640, height=480)
        self.simulated_darts: List[Tuple[float, float]] = []
        self._sim_lock = threading.Lock()

        # Auto-assign discovered cameras or simulation fallback
        saved_map = self._load_saved_mapping()
        discovered = discover_video_devices()
        usable_indices = self._probe_usable_devices(discovered)

        self.slots: Dict[int, CameraStreamSlot] = {}
        for slot_id in range(num_slots):
            if slot_id in saved_map:
                dev_idx = saved_map[slot_id]
            elif slot_id < len(usable_indices):
                dev_idx = usable_indices[slot_id]
            else:
                dev_idx = -1  # Simulation fallback
            slot = CameraStreamSlot(slot_id=slot_id, device_index=dev_idx, renderer=self.renderer)
            self.slots[slot_id] = slot

    @staticmethod
    def _probe_usable_devices(discovered: List[dict]) -> List[int]:
        usable = []
        for dev in discovered:
            idx = dev["index"]
            try:
                cap = cv2.VideoCapture(idx, _preferred_cv_backend())
                if cap.isOpened():
                    ok, frame = cap.read()
                    if ok and frame is not None:
                        usable.append(idx)
                cap.release()
            except Exception:
                pass
        return usable

    def _load_saved_mapping(self) -> Dict[int, int]:
        if not CAMERA_CONFIG_FILE.exists():
            return {}
        try:
            data = json.loads(CAMERA_CONFIG_FILE.read_text(encoding="utf-8"))
            return {int(k): int(v) for k, v in data.get("slots", {}).items()}
        except Exception:
            return {}

    def save_mapping(self) -> None:
        CONFIG_DIR.mkdir(parents=True, exist_ok=True)
        payload = {
            "slots": {
                str(sid): (slot.device_index if slot.device_index is not None else -1)
                for sid, slot in self.slots.items()
            }
        }
        CAMERA_CONFIG_FILE.write_text(json.dumps(payload, indent=2), encoding="utf-8")

    def start_all(self) -> None:
        for slot in self.slots.values():
            slot.start()

    def stop_all(self) -> None:
        for slot in self.slots.values():
            slot.stop()

    def assign_device(self, slot_id: int, device_index: int) -> dict:
        if slot_id in self.slots:
            self.slots[slot_id].set_device(device_index)
            self.save_mapping()
            return self.slots[slot_id].get_status()
        return {}

    def add_simulated_dart(self, bx: float, by: float) -> None:
        with self._sim_lock:
            if len(self.simulated_darts) >= 3:
                self.simulated_darts.clear()
            self.simulated_darts.append((float(bx), float(by)))

    def clear_simulated_darts(self) -> None:
        with self._sim_lock:
            self.simulated_darts.clear()

    def get_frame(self, slot_id: int) -> np.ndarray:
        with self._sim_lock:
            sim_darts = list(self.simulated_darts)
        slot = self.slots.get(slot_id, self.slots[0])
        return slot.get_frame(sim_darts)

    def get_all_frames(self) -> Dict[int, np.ndarray]:
        with self._sim_lock:
            sim_darts = list(self.simulated_darts)
        return {sid: slot.get_frame(sim_darts) for sid, slot in self.slots.items()}

    def get_status(self) -> dict:
        return {
            "available_devices": discover_video_devices(),
            "slots": {sid: slot.get_status() for sid, slot in self.slots.items()},
            "simulated_darts_count": len(self.simulated_darts),
        }
