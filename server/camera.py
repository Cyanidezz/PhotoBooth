from __future__ import annotations

import asyncio
import subprocess
import threading
import time
from datetime import datetime
from pathlib import Path

import cv2
import numpy as np
from aiortc import VideoStreamTrack
from av import VideoFrame

from .config import Settings


class NikonCamera:
    """Owns the single USB connection used for Live View and still capture."""

    def __init__(self, settings: Settings):
        self.settings = settings
        self._process: subprocess.Popen | None = None
        self._reader: threading.Thread | None = None
        self._condition = threading.Condition()
        self._latest: np.ndarray | None = None
        self._sequence = 0
        self._stopping = False

    def start_preview(self) -> None:
        with self._condition:
            if self._process and self._process.poll() is None:
                return
            self._stopping = False
            self._process = subprocess.Popen(
                [self.settings.gphoto2, "--capture-movie", "--stdout"],
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                bufsize=0,
            )
            self._reader = threading.Thread(target=self._read_preview, daemon=True)
            self._reader.start()

    def _read_preview(self) -> None:
        process = self._process
        if not process or not process.stdout:
            return
        buffer = bytearray()
        while not self._stopping:
            chunk = process.stdout.read(65536)
            if not chunk:
                break
            buffer.extend(chunk)
            while True:
                start = buffer.find(b"\xff\xd8")
                if start < 0:
                    if len(buffer) > 1:
                        del buffer[:-1]
                    break
                end = buffer.find(b"\xff\xd9", start + 2)
                if end < 0:
                    if start:
                        del buffer[:start]
                    break
                jpeg = bytes(buffer[start : end + 2])
                del buffer[: end + 2]
                image = cv2.imdecode(np.frombuffer(jpeg, dtype=np.uint8), cv2.IMREAD_COLOR)
                if image is not None:
                    with self._condition:
                        self._latest = image
                        self._sequence += 1
                        self._condition.notify_all()
        with self._condition:
            self._condition.notify_all()

    def frame_after(self, sequence: int, timeout: float = 20) -> tuple[np.ndarray, int]:
        deadline = time.monotonic() + timeout
        with self._condition:
            while self._sequence <= sequence or self._latest is None:
                remaining = deadline - time.monotonic()
                if remaining <= 0:
                    detail = self.preview_error()
                    raise RuntimeError(detail or "ไม่ได้รับ Live View จาก Nikon ผ่าน USB")
                self._condition.wait(min(remaining, 1))
            return self._latest.copy(), self._sequence

    def preview_error(self) -> str:
        process = self._process
        if not process or process.poll() is None or not process.stderr:
            return ""
        try:
            detail = process.stderr.read().decode("utf-8", errors="replace").strip()
        except Exception:
            return ""
        return detail[-500:]

    def stop_preview(self) -> None:
        self._stopping = True
        process = self._process
        self._process = None
        if process and process.poll() is None:
            process.terminate()
            try:
                process.wait(timeout=3)
            except subprocess.TimeoutExpired:
                process.kill()
                process.wait(timeout=2)
        if self._reader and self._reader.is_alive():
            self._reader.join(timeout=2)
        self._reader = None

    def capture(self, session_dir: Path, shot_number: int) -> Path:
        self.stop_preview()
        timestamp = datetime.now().strftime("%Y%m%d-%H%M%S")
        destination = session_dir / f"shot-{shot_number}-{timestamp}.jpg"
        try:
            result = subprocess.run(
                [self.settings.gphoto2, "--capture-image-and-download", "--force-overwrite", "--filename", str(destination)],
                capture_output=True,
                text=True,
                timeout=45,
                check=False,
            )
            if result.returncode != 0 or not destination.exists():
                detail = (result.stderr or result.stdout or "gphoto2 ไม่ได้สร้างไฟล์ภาพ").strip()
                raise RuntimeError(detail[-500:])
            return destination
        finally:
            self.start_preview()

    def close(self) -> None:
        self.stop_preview()


class NikonPreviewTrack(VideoStreamTrack):
    def __init__(self, camera: NikonCamera):
        super().__init__()
        self.camera = camera
        self.sequence = -1
        self.camera.start_preview()

    async def recv(self) -> VideoFrame:
        pts, time_base = await self.next_timestamp()
        image, self.sequence = await asyncio.to_thread(self.camera.frame_after, self.sequence)
        frame = VideoFrame.from_ndarray(cv2.cvtColor(image, cv2.COLOR_BGR2RGB), format="rgb24")
        frame.pts, frame.time_base = pts, time_base
        return frame
