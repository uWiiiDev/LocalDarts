"""
FastAPI Backend, WebSocket Broadcaster, and MJPEG Camera Stream Server for LocalDarts.
"""

from __future__ import annotations
import asyncio
from contextlib import asynccontextmanager
from pathlib import Path
import sys
import time
from typing import List, Optional, Set
import cv2
from fastapi import FastAPI, Query, WebSocket, WebSocketDisconnect
from fastapi.responses import FileResponse, StreamingResponse
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel

from .board_geometry import coords_to_hit, sector_multiplier_to_coords
from .calibration import CalibrationManager
from .camera_manager import CameraManager
from .detector import DartDetector
from .game_engine import GameEngine

if getattr(sys, "frozen", False) and hasattr(sys, "_MEIPASS"):
    FRONTEND_DIR = Path(sys._MEIPASS) / "frontend"
else:
    FRONTEND_DIR = Path(__file__).resolve().parent.parent / "frontend"


class ConnectionManager:
    """Manages active WebSocket clients for instant push updates."""

    def __init__(self):
        self.active_connections: Set[WebSocket] = set()
        self.loop: Optional[asyncio.AbstractEventLoop] = None

    async def connect(self, websocket: WebSocket) -> None:
        await websocket.accept()
        self.active_connections.add(websocket)

    def disconnect(self, websocket: WebSocket) -> None:
        self.active_connections.discard(websocket)

    async def broadcast(self, message: dict) -> None:
        dead = []
        for ws in list(self.active_connections):
            try:
                await ws.send_json(message)
            except Exception:
                dead.append(ws)
        for ws in dead:
            self.active_connections.discard(ws)

    def broadcast_threadsafe(self, message: dict) -> None:
        if self.loop and self.loop.is_running():
            asyncio.run_coroutine_threadsafe(self.broadcast(message), self.loop)


ws_manager = ConnectionManager()
camera_manager = CameraManager(num_slots=3)
calibration_manager = CalibrationManager(num_cameras=3)
game_engine = GameEngine()

# If no calibration file exists yet, pre-populate simulation calibration for any simulated cameras
for _cid, _slot in camera_manager.slots.items():
    if not calibration_manager.cameras[_cid].is_calibrated and not _slot.is_physical_open:
        calibration_manager.apply_default_simulation_calibration(_cid)


def _on_vision_dart_detected(hit) -> None:
    state = game_engine.register_dart(hit)
    ws_manager.broadcast_threadsafe(
        {
            "event": "dart_detected",
            "hit": hit.to_dict(),
            "game": state,
            "detector": detector.get_status(),
        }
    )


def _on_vision_takeout_detected() -> None:
    state = game_engine.next_turn()
    ws_manager.broadcast_threadsafe(
        {
            "event": "takeout_detected",
            "game": state,
            "detector": detector.get_status(),
        }
    )


def _on_vision_state_change(new_state: str) -> None:
    ws_manager.broadcast_threadsafe(
        {
            "event": "detector_state",
            "detector": detector.get_status(),
        }
    )


detector = DartDetector(
    camera_manager=camera_manager,
    calibration_manager=calibration_manager,
    on_dart_detected=_on_vision_dart_detected,
    on_takeout_detected=_on_vision_takeout_detected,
    on_state_change=_on_vision_state_change,
)


@asynccontextmanager
async def lifespan(app: FastAPI):
    ws_manager.loop = asyncio.get_running_loop()
    camera_manager.start_all()
    time.sleep(0.15)
    detector.start()
    yield
    detector.stop()
    camera_manager.stop_all()


app = FastAPI(title="LocalDarts - Autodarts Local Edition", lifespan=lifespan)
app.mount("/static", StaticFiles(directory=str(FRONTEND_DIR)), name="static")


# --- Request Schemas ---

class NewGameRequest(BaseModel):
    mode: str = "x01"
    player_names: List[str] = ["Spieler 1", "Spieler 2"]
    x01_start_score: int = 501
    double_in: bool = False
    out_mode: str = "double"
    legs_to_win: int = 3
    cricket_variant: str = "standard"
    atc_fast_forward: bool = False
    max_rounds: int = 10
    training_target_sector: int = 20


class ThrowRequest(BaseModel):
    x: Optional[float] = None
    y: Optional[float] = None
    sector: Optional[int] = None
    multiplier: Optional[int] = 1
    via_vision: bool = False


class CorrectDartRequest(BaseModel):
    dart_index: int
    x: Optional[float] = None
    y: Optional[float] = None
    sector: Optional[int] = None
    multiplier: Optional[int] = 1


class AssignCameraRequest(BaseModel):
    slot_id: int
    device_index: int


class SetCameraFpsRequest(BaseModel):
    target_fps: int = 25


class SaveCalibrationRequest(BaseModel):
    cam_id: int
    preset_id: str = "autodarts_wires_ccw"
    points: List[List[float]]


class DetectorSettingsRequest(BaseModel):
    enabled: Optional[bool] = None
    diff_threshold: Optional[int] = None
    min_contour_area: Optional[int] = None
    settle_time_ms: Optional[int] = None


# --- Routes ---

@app.get("/")
async def index():
    return FileResponse(str(FRONTEND_DIR / "index.html"))


@app.websocket("/ws")
async def websocket_endpoint(websocket: WebSocket):
    await ws_manager.connect(websocket)
    try:
        await websocket.send_json(
            {
                "event": "init",
                "game": game_engine.get_state(),
                "cameras": camera_manager.get_status(),
                "calibration": calibration_manager.get_status(),
                "detector": detector.get_status(),
            }
        )
        while True:
            await websocket.receive_text()
    except WebSocketDisconnect:
        ws_manager.disconnect(websocket)


@app.get("/api/status")
async def api_status():
    return {
        "game": game_engine.get_state(),
        "cameras": camera_manager.get_status(),
        "calibration": calibration_manager.get_status(),
        "detector": detector.get_status(),
    }


@app.post("/api/game/new")
async def api_new_game(req: NewGameRequest):
    detector.notify_board_cleared()
    state = game_engine.new_game(
        mode=req.mode,
        player_names=req.player_names,
        x01_start_score=req.x01_start_score,
        double_in=req.double_in,
        out_mode=req.out_mode,
        legs_to_win=req.legs_to_win,
        cricket_variant=req.cricket_variant,
        atc_fast_forward=req.atc_fast_forward,
        max_rounds=req.max_rounds,
        training_target_sector=req.training_target_sector,
    )
    await ws_manager.broadcast({"event": "game_update", "game": state, "detector": detector.get_status()})
    return state


@app.post("/api/game/throw")
async def api_throw_dart(req: ThrowRequest):
    if req.x is not None and req.y is not None:
        bx, by = float(req.x), float(req.y)
    elif req.sector is not None:
        bx, by = sector_multiplier_to_coords(int(req.sector), int(req.multiplier or 1))
    else:
        bx, by = (0.0, 0.0)

    if req.via_vision:
        # Place the simulated 3D dart onto the board so the OpenCV camera pipeline detects it!
        if game_engine.turn_complete or len(game_engine.turn_darts) >= 3:
            detector.notify_board_cleared()
            game_engine.next_turn()
        camera_manager.add_simulated_dart(bx, by)
        return {"queued_for_vision": True, "x": bx, "y": by}

    hit = coords_to_hit(bx, by, confidence=1.0, cameras_used=0, source="manual")
    state = game_engine.register_dart(hit)
    await ws_manager.broadcast(
        {
            "event": "dart_detected",
            "hit": hit.to_dict(),
            "game": state,
            "detector": detector.get_status(),
        }
    )
    return state


@app.post("/api/game/correct")
async def api_correct_dart(req: CorrectDartRequest):
    if req.x is not None and req.y is not None:
        bx, by = float(req.x), float(req.y)
    elif req.sector is not None:
        bx, by = sector_multiplier_to_coords(int(req.sector), int(req.multiplier or 1))
    else:
        bx, by = (0.0, 0.0)

    new_hit = coords_to_hit(bx, by, confidence=1.0, cameras_used=0, source="manual")
    state = game_engine.correct_turn_dart(req.dart_index, new_hit)
    await ws_manager.broadcast({"event": "game_update", "game": state})
    return state


@app.post("/api/game/undo")
async def api_undo():
    if camera_manager.simulated_darts:
        camera_manager.simulated_darts.pop()
    state = game_engine.undo_last_dart()
    await ws_manager.broadcast({"event": "game_update", "game": state, "detector": detector.get_status()})
    return state


@app.post("/api/game/next")
async def api_next_turn():
    detector.notify_board_cleared()
    state = game_engine.next_turn()
    await ws_manager.broadcast(
        {
            "event": "takeout_detected",
            "game": state,
            "detector": detector.get_status(),
        }
    )
    return state


@app.post("/api/cameras/assign")
async def api_assign_camera(req: AssignCameraRequest):
    slot_status = camera_manager.assign_device(req.slot_id, req.device_index)
    detector.capture_empty_reference()
    status = camera_manager.get_status()
    await ws_manager.broadcast({"event": "cameras_update", "cameras": status})
    return {"slot": slot_status, "cameras": status}


@app.post("/api/cameras/rescan")
async def api_rescan_cameras():
    status = camera_manager.rescan_and_auto_assign()
    detector.capture_empty_reference()
    await ws_manager.broadcast({"event": "cameras_update", "cameras": status})
    return status


@app.post("/api/cameras/fps")
async def api_set_camera_fps(req: SetCameraFpsRequest):
    status = camera_manager.set_target_fps(req.target_fps)
    detector.capture_empty_reference()
    await ws_manager.broadcast({"event": "cameras_update", "cameras": status})
    return status


@app.post("/api/calibration/save")
async def api_save_calibration(req: SaveCalibrationRequest):
    pts = [(float(p[0]), float(p[1])) for p in req.points[:4]]
    cal_dict = calibration_manager.set_camera_points(req.cam_id, pts, preset_id=req.preset_id)
    detector.capture_empty_reference()
    status = calibration_manager.get_status()
    await ws_manager.broadcast({"event": "calibration_update", "calibration": status})
    return {"camera": cal_dict, "calibration": status}


@app.post("/api/calibration/auto_sim/{cam_id}")
async def api_auto_sim_calibration(cam_id: int):
    if cam_id < 0:
        for cid in range(3):
            calibration_manager.apply_default_simulation_calibration(cid)
    else:
        calibration_manager.apply_default_simulation_calibration(cam_id)
    detector.capture_empty_reference()
    status = calibration_manager.get_status()
    await ws_manager.broadcast({"event": "calibration_update", "calibration": status})
    return status


@app.post("/api/calibration/reset/{cam_id}")
async def api_reset_calibration(cam_id: int):
    calibration_manager.reset_camera(cam_id)
    status = calibration_manager.get_status()
    await ws_manager.broadcast({"event": "calibration_update", "calibration": status})
    return status


@app.post("/api/detector/settings")
async def api_detector_settings(req: DetectorSettingsRequest):
    status = detector.update_settings(
        enabled=req.enabled,
        diff_threshold=req.diff_threshold,
        min_contour_area=req.min_contour_area,
        settle_time_ms=req.settle_time_ms,
    )
    await ws_manager.broadcast({"event": "detector_state", "detector": status})
    return status


@app.post("/api/detector/reset_reference")
async def api_reset_reference():
    detector.notify_board_cleared()
    status = detector.get_status()
    await ws_manager.broadcast({"event": "detector_state", "detector": status})
    return status


def _render_camera_view(cam_id: int, view: str):
    if view == "raw":
        return camera_manager.get_frame(cam_id)
    if view == "warped":
        raw = camera_manager.get_frame(cam_id)
        cal = calibration_manager.cameras.get(cam_id)
        if cal:
            return cal.warp_frame_to_board_view(raw, out_size=460)
        return raw
    if view == "diff":
        return detector.render_diff_mask_frame(cam_id)
    # Default: "annotated" (camera view + perspective spider + tip marker)
    return detector.render_annotated_camera_frame(cam_id, show_spider=True)


@app.get("/api/stream/camera/{cam_id}")
async def stream_camera(
    cam_id: int,
    view: str = Query("annotated", pattern="^(raw|annotated|warped|diff)$"),
    snapshot: int = Query(0),
):
    if snapshot == 1:
        frame = _render_camera_view(cam_id, view)
        ok, buf = cv2.imencode(".jpg", frame, [int(cv2.IMWRITE_JPEG_QUALITY), 85])
        return StreamingResponse(iter([buf.tobytes() if ok else b""]), media_type="image/jpeg")

    async def frame_generator():
        while True:
            frame = _render_camera_view(cam_id, view)
            ok, buf = cv2.imencode(".jpg", frame, [int(cv2.IMWRITE_JPEG_QUALITY), 80])
            if ok:
                jpg_bytes = buf.tobytes()
                yield (
                    b"--frame\r\n"
                    b"Content-Type: image/jpeg\r\n\r\n" + jpg_bytes + b"\r\n"
                )
            await asyncio.sleep(0.08)

    return StreamingResponse(
        frame_generator(),
        media_type="multipart/x-mixed-replace; boundary=frame",
    )
