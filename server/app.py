from __future__ import annotations

import asyncio
import json
import os
import re
import shutil
import subprocess
import uuid
from dataclasses import dataclass, field
from pathlib import Path

import qrcode
from aiortc import RTCPeerConnection, RTCSessionDescription
from aiortc.contrib.media import MediaRelay
from fastapi import FastAPI, HTTPException, WebSocket, WebSocketDisconnect
from fastapi.responses import FileResponse
from fastapi.staticfiles import StaticFiles

from .camera import CaptureCardTrack, capture_full_resolution
from .config import ROOT, load_settings
from .frames import FRAMES, compose, transparent_overlay

settings = load_settings()
app = FastAPI(title="Retire Like a King Photobooth Camera Server")
peers: set[RTCPeerConnection] = set()
relay = MediaRelay()
source_track: CaptureCardTrack | None = None


@dataclass
class BoothSession:
    frame_id: str = ""
    photos: list[Path] = field(default_factory=list)
    result_id: str = ""


sessions: dict[str, BoothSession] = {}
camera_lock = asyncio.Lock()


def safe_id(value: str) -> str:
    if not re.fullmatch(r"[A-Za-z0-9-]{1,80}", value):
        raise HTTPException(400, "รหัสไม่ถูกต้อง")
    return value


@app.get("/api/health")
async def health():
    return {"ok": True, "gphoto2": shutil.which(settings.gphoto2) is not None}


@app.post("/api/offer")
async def offer(payload: dict):
    global source_track
    pc = RTCPeerConnection()
    peers.add(pc)
    if source_track is None or source_track.readyState == "ended":
        source_track = CaptureCardTrack(settings)
    pc.addTrack(relay.subscribe(source_track))

    @pc.on("connectionstatechange")
    async def state_changed():
        if pc.connectionState in {"failed", "closed", "disconnected"}:
            await pc.close()
            peers.discard(pc)

    await pc.setRemoteDescription(RTCSessionDescription(sdp=payload["sdp"], type=payload["type"]))
    answer = await pc.createAnswer()
    await pc.setLocalDescription(answer)
    return {"sdp": pc.localDescription.sdp, "type": pc.localDescription.type}


@app.get("/api/frame/{frame_id}.png")
async def prepared_frame(frame_id: str):
    if frame_id not in FRAMES:
        raise HTTPException(404, "ไม่พบเฟรม")
    path = settings.output_path / f"frame-{frame_id}.png"
    if not path.exists():
        await asyncio.to_thread(transparent_overlay(FRAMES[frame_id]).save, path, "PNG")
    return FileResponse(path, media_type="image/png")


async def send(websocket: WebSocket, event: str, **data):
    await websocket.send_json({"event": event, **data})


async def take_one(websocket: WebSocket, state: BoothSession, countdown: int):
    for remaining in range(countdown, 0, -1):
        await send(websocket, "countdown", value=remaining)
        await asyncio.sleep(1)
    await send(websocket, "shutter")
    session_dir = settings.output_path / "sessions" / websocket.state.session_id
    session_dir.mkdir(parents=True, exist_ok=True)
    async with camera_lock:
        photo = await asyncio.to_thread(capture_full_resolution, settings, session_dir, len(state.photos) + 1)
    state.photos.append(photo)
    await send(websocket, "shot_ready", count=len(state.photos), url=f"/media/sessions/{websocket.state.session_id}/{photo.name}")


async def finish(websocket: WebSocket, state: BoothSession):
    state.result_id = uuid.uuid4().hex
    destination = settings.output_path / f"{state.result_id}.jpg"
    await asyncio.to_thread(compose, state.frame_id, state.photos, destination)
    base = str(websocket.url).replace("ws://", "http://").replace("wss://", "https://").split("/ws/")[0]
    result_url = f"{base}/r/{state.result_id}"
    qrcode.make(result_url).save(settings.output_path / f"{state.result_id}.png")
    await send(websocket, "complete", image=f"/media/{state.result_id}.jpg", qr=f"/media/{state.result_id}.png", result=result_url)


@app.websocket("/ws/{session_id}")
async def control(websocket: WebSocket, session_id: str):
    try:
        safe_id(session_id)
    except HTTPException:
        await websocket.close(code=1008)
        return
    await websocket.accept()
    websocket.state.session_id = session_id
    state = sessions.setdefault(session_id, BoothSession())
    await send(websocket, "connected")
    try:
        while True:
            message = json.loads(await websocket.receive_text())
            action = message.get("action")
            if action == "reset":
                sessions[session_id] = state = BoothSession(frame_id=message.get("frame", ""))
                await send(websocket, "reset")
            elif action == "capture":
                frame_id = message.get("frame", "")
                if frame_id not in FRAMES:
                    raise RuntimeError("ไม่พบเฟรมที่เลือก")
                if state.frame_id != frame_id:
                    state = sessions[session_id] = BoothSession(frame_id=frame_id)
                required = len(FRAMES[frame_id].boxes)
                count = required - len(state.photos) if message.get("mode") == "continuous" else 1
                for index in range(count):
                    await take_one(websocket, state, max(0, min(15, int(message.get("countdown", 3)))))
                    if index < count - 1:
                        await send(websocket, "pose", next=len(state.photos) + 1)
                        await asyncio.sleep(1)
                if len(state.photos) == required:
                    await finish(websocket, state)
                else:
                    await send(websocket, "waiting", next=len(state.photos) + 1, total=required)
            else:
                await send(websocket, "error", message="คำสั่งไม่ถูกต้อง")
    except WebSocketDisconnect:
        pass
    except Exception as error:
        await send(websocket, "error", message=str(error))


@app.get("/r/{result_id}")
async def result(result_id: str):
    safe_id(result_id)
    path = settings.output_path / f"{result_id}.jpg"
    if not path.exists():
        raise HTTPException(404)
    return FileResponse(path)


@app.post("/api/print/{result_id}")
async def print_result(result_id: str):
    safe_id(result_id)
    path = settings.output_path / f"{result_id}.jpg"
    if not path.exists():
        raise HTTPException(404, "ไม่พบภาพ")
    if os.name == "nt":
        os.startfile(path, "print")
    else:
        command = ["lp"] + (["-d", settings.printer] if settings.printer else []) + [str(path)]
        result = await asyncio.to_thread(subprocess.run, command, capture_output=True, text=True, check=False)
        if result.returncode:
            raise HTTPException(500, (result.stderr or "สั่งพิมพ์ไม่สำเร็จ").strip())
    return {"ok": True}


app.mount("/media", StaticFiles(directory=settings.output_path), name="media")
app.mount("/", StaticFiles(directory=ROOT, html=True), name="web")


@app.on_event("shutdown")
async def shutdown():
    await asyncio.gather(*(peer.close() for peer in peers), return_exceptions=True)
    if source_track:
        source_track.stop()
