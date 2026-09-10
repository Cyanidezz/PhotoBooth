from __future__ import annotations

import asyncio
import subprocess
import threading
from datetime import datetime
from pathlib import Path

import cv2
from aiortc import VideoStreamTrack
from av import VideoFrame

from .config import Settings


class CaptureCardTrack(VideoStreamTrack):
    kind = "video"

    def __init__(self, settings: Settings):
        super().__init__()
        source = settings.capture_device
        self.capture = cv2.VideoCapture(int(source) if str(source).isdigit() else source)
        self.capture.set(cv2.CAP_PROP_FRAME_WIDTH, settings.capture_width)
        self.capture.set(cv2.CAP_PROP_FRAME_HEIGHT, settings.capture_height)
        if not self.capture.isOpened():
            raise RuntimeError("เปิด Capture Card ไม่ได้ กรุณาตรวจ config.json และสาย HDMI")
        self._lock = threading.Lock()

    async def recv(self) -> VideoFrame:
        pts, time_base = await self.next_timestamp()
        ok, image = await asyncio.to_thread(self._read)
        if not ok:
            await asyncio.sleep(0.1)
            raise RuntimeError("ไม่ได้รับสัญญาณจาก Capture Card")
        frame = VideoFrame.from_ndarray(cv2.cvtColor(image, cv2.COLOR_BGR2RGB), format="rgb24")
        frame.pts, frame.time_base = pts, time_base
        return frame

    def _read(self):
        with self._lock:
            return self.capture.read()

    def stop(self) -> None:
        with self._lock:
            self.capture.release()
        super().stop()


def capture_full_resolution(settings: Settings, session_dir: Path, shot_number: int) -> Path:
    timestamp = datetime.now().strftime("%Y%m%d-%H%M%S")
    destination = session_dir / f"shot-{shot_number}-{timestamp}.jpg"
    command = [
        settings.gphoto2,
        "--capture-image-and-download",
        "--force-overwrite",
        "--filename",
        str(destination),
    ]
    result = subprocess.run(command, capture_output=True, text=True, timeout=45, check=False)
    if result.returncode != 0 or not destination.exists():
        detail = (result.stderr or result.stdout or "gphoto2 ไม่ได้สร้างไฟล์ภาพ").strip()
        raise RuntimeError(detail[-500:])
    return destination
