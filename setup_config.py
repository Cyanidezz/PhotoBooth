from __future__ import annotations

import json
import secrets
import sys
from datetime import datetime
from pathlib import Path

root = Path(__file__).resolve().parent
path = root / "config.json"
example = json.loads((root / "config.example.json").read_text(encoding="utf-8"))
current = {}
if path.exists():
    try:
        current = json.loads(path.read_text(encoding="utf-8"))
    except json.JSONDecodeError as error:
        backup = root / f"config.invalid-{datetime.now().strftime('%Y%m%d-%H%M%S')}.json"
        path.replace(backup)
        print(
            f"config.json ไม่ถูกต้องที่บรรทัด {error.lineno} คอลัมน์ {error.colno} "
            f"สำรองไฟล์เดิมไว้ที่ {backup.name} และสร้างไฟล์ใหม่แล้ว",
            file=sys.stderr,
        )
for key, value in example.items():
    current.setdefault(key, value)
if not current.get("access_token"):
    current["access_token"] = secrets.token_urlsafe(18)
path.write_text(json.dumps(current, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
print(current["access_token"])
