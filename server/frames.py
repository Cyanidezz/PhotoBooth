from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path

from PIL import Image, ImageDraw

ROOT = Path(__file__).resolve().parent.parent


@dataclass(frozen=True)
class Frame:
    image: str
    boxes: tuple[tuple[int, int, int, int], ...]
    seeds: tuple[tuple[int, int], ...] = ()


FRAMES = {
    "1shot-1": Frame("1shot-1.png", ((169, 237, 1203, 508),), ((760, 480),)),
    "1shot-2": Frame("1shot-2.png", ((68, 178, 697, 560),), ((410, 450),)),
    "3shot-1": Frame("3shot-1.png", ((98, 199, 397, 405), (98, 760, 396, 403), (98, 1260, 396, 346)), ((290, 400), (290, 940), (290, 1450))),
    "3shot-2": Frame("3shot-2.png", ((0, 0, 541, 608), (0, 652, 537, 610), (0, 1308, 536, 612))),
}


def cover(image: Image.Image, size: tuple[int, int]) -> Image.Image:
    target_w, target_h = size
    source = image.convert("RGB")
    scale = max(target_w / source.width, target_h / source.height)
    resized = source.resize((round(source.width * scale), round(source.height * scale)), Image.Resampling.LANCZOS)
    left = (resized.width - target_w) // 2
    top = (resized.height - target_h) // 2
    return resized.crop((left, top, left + target_w, top + target_h))


def transparent_overlay(frame: Frame) -> Image.Image:
    overlay = Image.open(ROOT / frame.image).convert("RGBA")
    for seed in frame.seeds:
        ImageDraw.floodfill(overlay, seed, (255, 255, 255, 0), thresh=35)
    return overlay


def compose(frame_id: str, photos: list[Path], destination: Path) -> None:
    frame = FRAMES[frame_id]
    overlay = transparent_overlay(frame)
    result = Image.new("RGB", overlay.size, "#162d3d")
    for photo_path, (x, y, width, height) in zip(photos, frame.boxes, strict=True):
        with Image.open(photo_path) as photo:
            result.paste(cover(photo, (width, height)), (x, y))
    result.paste(overlay, (0, 0), overlay)
    result.save(destination, "JPEG", quality=95, subsampling=0)
