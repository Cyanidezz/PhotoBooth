#!/bin/bash
set -euo pipefail
cd "$(dirname "$0")"

if ! command -v gphoto2 >/dev/null 2>&1; then
  echo "ไม่พบ gphoto2 กรุณาติดตั้งด้วย: brew install gphoto2"
  read -r
  exit 1
fi
if ! command -v cloudflared >/dev/null 2>&1; then
  echo "ไม่พบ cloudflared กรุณาติดตั้งด้วย: brew install cloudflared"
  read -r
  exit 1
fi
if [ ! -d .venv ]; then
  python3 -m venv .venv
fi
. .venv/bin/activate
python -m pip install --upgrade pip setuptools wheel
python -m pip install --only-binary=av -r requirements.txt
PAIRING_CODE=$(python setup_config.py)

echo ""
echo "รหัสจับคู่สำหรับ aero-photo.vercel.app: ${PAIRING_CODE}"
echo "คัดลอก URL https://...trycloudflare.com ที่จะแสดงด้านล่างไปกรอกในหน้าเว็บ"
echo "กด Control+C เพื่อปิด Camera Server และ Tunnel"
echo ""

python run_server.py &
SERVER_PID=$!
trap 'kill "$SERVER_PID" 2>/dev/null || true' EXIT INT TERM
cloudflared tunnel --url http://127.0.0.1:8000
