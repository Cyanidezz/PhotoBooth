#!/bin/bash
set -euo pipefail
cd "$(dirname "$0")"

if ! command -v gphoto2 >/dev/null 2>&1; then
  echo "ไม่พบ gphoto2 กรุณาติดตั้งด้วย: brew install gphoto2"
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

ADDRESS=$(ipconfig getifaddr en0 2>/dev/null || ipconfig getifaddr en1 2>/dev/null || true)
echo ""
echo "เปิด Photobooth บน iPad: http://${ADDRESS:-IP-ของเครื่องนี้}:8000/?token=${PAIRING_CODE}"
echo "รหัสจับคู่: ${PAIRING_CODE}"
echo "กด Control+C เพื่อปิด Camera Server"
echo ""
python run_server.py
