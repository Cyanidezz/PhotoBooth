from __future__ import annotations

import json
import secrets
from pathlib import Path

root = Path(__file__).resolve().parent
path = root / "config.json"
example = json.loads((root / "config.example.json").read_text(encoding="utf-8"))
current = json.loads(path.read_text(encoding="utf-8")) if path.exists() else {}
for key, value in example.items():
    current.setdefault(key, value)
if not current.get("access_token"):
    current["access_token"] = secrets.token_urlsafe(18)
path.write_text(json.dumps(current, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
print(current["access_token"])
