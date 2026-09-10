# Nikon D7500 · iPad Photobooth

ระบบ Photobooth แบบ Camera Server สำหรับ Nikon D7500 ใช้ USB เส้นเดียวสำหรับ Live View และถ่ายภาพ JPEG ความละเอียดเต็ม

## การเชื่อมต่อ

```text
Nikon D7500 USB  ───────────────────────> Mac/PC
iPad             ── Wi-Fi / WebRTC ───> Camera Server
```

Camera Server รับ Live View ด้วย `gphoto2 --capture-movie --stdout` แล้วส่งไปหน้าเว็บผ่าน WebRTC เมื่อ iPad ส่งคำสั่งถ่ายผ่าน WebSocket ระบบจะหยุด Live View ชั่วคราว เรียก `gphoto2 --capture-image-and-download` ประกอบ JPEG เต็มความละเอียดเข้ากับ PNG frame แล้วเปิด Live View กลับอัตโนมัติ

## รองรับ

- เลือกเฟรม 1 Shot และ 3 Shot
- โหมด 3 Shot แบบต่อเนื่องหรือกดทีละช่อง
- เวลานับถอยหลัง 0–15 วินาที พร้อมเสียง
- Preview จาก Nikon ผ่าน USB และ WebRTC
- สั่ง Nikon D7500 ถ่ายผ่าน USB และใช้ JPEG ที่ดาวน์โหลดจริง
- ครอปภาพแบบเต็มช่องและวาง PNG โปร่งใส
- ถ่ายใหม่ ดาวน์โหลดผ่าน QR Code และสั่งพิมพ์จาก Camera Server

## ติดตั้งบน macOS

1. ติดตั้ง Python 3.11+ และ gphoto2:

   ```bash
   brew install python@3.11 gphoto2
   ```

2. ต่อ Nikon D7500 กับ Mac ด้วยสาย USB Data และถอด HDMI/Capture Card ออก
3. ปิด Photos, Image Capture และแอปอื่นที่จับกล้องอยู่ ตั้ง Nikon เป็น JPEG Fine และตั้ง Auto Off Timer ให้นานพอ
4. ดับเบิลคลิก `start.command` หรือเปิด Terminal แล้วรัน:

   ```bash
   chmod +x start.command
   ./start.command
   ```

5. ต่อ iPad กับ Wi-Fi เดียวกัน แล้วเปิด URL ที่โปรแกรมแสดง เช่น `http://192.168.1.50:8000`

## ตั้งค่า Nikon และเครื่องพิมพ์

ครั้งแรกโปรแกรมจะสร้าง `config.json` จาก `config.example.json`

```json
{
  "gphoto2": "gphoto2",
  "output_directory": "output",
  "printer": ""
}
```

- macOS ใช้คำสั่ง `lpstat -p` ดูชื่อเครื่องพิมพ์ แล้วใส่ชื่อใน `printer`
- เว้น `printer` ว่างไว้เพื่อใช้ Default Printer
- ผลลัพธ์และภาพต้นฉบับเก็บในโฟลเดอร์ `output`

## ตรวจกล้องก่อนเริ่มงาน

```bash
gphoto2 --auto-detect
gphoto2 --summary
```

ถ้า `gphoto2` ไม่เห็น Nikon ให้ตรวจสาย USB data, USB mode ของกล้อง และปิดโปรแกรมอื่นที่กำลังใช้งาน Nikon

## HTTPS

โหมดปกติใช้ HTTP ใน Wi-Fi เดียวกันและรองรับ Live View, ถ่าย, QR และพิมพ์ หากต้องการ Service Worker/PWA แบบเต็ม ให้สร้าง certificate ที่ iPad เชื่อถือ แล้วเปิดด้วย:

```bash
python run_server.py --cert cert.pem --key key.pem
```

จากนั้นเข้า `https://IP-ของเครื่อง:8000`

## เปิดผ่าน aero-photo.vercel.app จากอินเทอร์เน็ต

การเปิดจากภายนอกใช้ Cloudflare Tunnel สำหรับ HTTPS/WebSocket และใช้ TURN สำหรับส่งวิดีโอ WebRTC ข้ามเครือข่าย

1. ติดตั้ง Tunnel บน Mac:

   ```bash
   brew install cloudflared
   ```

2. สมัครบริการ TURN แล้วใส่ `urls`, `username` และ `credential` ใน `config.json` ตัวอย่างบริการที่ใช้ได้คือ Cloudflare Realtime TURN หรือ Metered TURN
3. เปิดระบบด้วย:

   ```bash
   git pull --ff-only
   chmod +x start-public.command
   ./start-public.command
   ```

4. คัดลอก URL รูปแบบ `https://...trycloudflare.com` จาก Terminal
5. เปิด `https://aero-photo.vercel.app/` เลือก **ตั้งค่า Camera Server** แล้วกรอก URL และรหัสจับคู่ที่ Terminal แสดง

Quick Tunnel จะได้ URL ใหม่เมื่อเปิดโปรแกรมใหม่ หากต้องการ URL เดิมทุกครั้ง ให้สร้าง Named Tunnel และกำหนด `public_base_url` ใน `config.json` เป็นโดเมนนั้น
