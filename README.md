# Nikon D7500 · iPad Photobooth

ระบบ Photobooth แบบ Camera Server สำหรับ Nikon D7500 ใช้ภาพ Live View จาก HDMI Capture Card และถ่ายภาพ JPEG ความละเอียดเต็มผ่าน USB

## การเชื่อมต่อ

```text
Nikon D7500 HDMI ──> UVC Capture Card ──> Mac/PC
Nikon D7500 USB  ───────────────────────> Mac/PC
iPad             ── Wi-Fi / WebRTC ───> Camera Server
```

หน้าเว็บบน iPad รับ Live View ผ่าน WebRTC และส่งคำสั่งถ่ายผ่าน WebSocket โปรแกรมบนเครื่อง Camera Server เรียก `gphoto2 --capture-image-and-download` แล้วประกอบ JPEG เต็มความละเอียดเข้ากับ PNG frame

## รองรับ

- เลือกเฟรม 1 Shot และ 3 Shot
- โหมด 3 Shot แบบต่อเนื่องหรือกดทีละช่อง
- เวลานับถอยหลัง 0–15 วินาที พร้อมเสียง
- Preview จาก HDMI Capture Card ผ่าน WebRTC
- สั่ง Nikon D7500 ถ่ายผ่าน USB และใช้ JPEG ที่ดาวน์โหลดจริง
- ครอปภาพแบบเต็มช่องและวาง PNG โปร่งใส
- ถ่ายใหม่ ดาวน์โหลดผ่าน QR Code และสั่งพิมพ์จาก Camera Server

## ติดตั้งบน macOS

1. ติดตั้ง Python 3.11+ และ gphoto2:

   ```bash
   brew install python@3.11 gphoto2
   ```

2. ต่อ Capture Card และ Nikon D7500 แล้วปิด Photos, Image Capture และแอปอื่นที่จับกล้องอยู่
3. ตั้ง Nikon เป็น JPEG Fine, เปิด Live View, เปิด Clean HDMI และตั้ง Auto Off Timer ให้นานพอ
4. ดับเบิลคลิก `start.command` หรือเปิด Terminal แล้วรัน:

   ```bash
   chmod +x start.command
   ./start.command
   ```

5. ต่อ iPad กับ Wi-Fi เดียวกัน แล้วเปิด URL ที่โปรแกรมแสดง เช่น `http://192.168.1.50:8000`

## ตั้งค่า Capture Card และเครื่องพิมพ์

ครั้งแรกโปรแกรมจะสร้าง `config.json` จาก `config.example.json`

```json
{
  "capture_device": 0,
  "capture_width": 1920,
  "capture_height": 1080,
  "gphoto2": "gphoto2",
  "output_directory": "output",
  "printer": ""
}
```

- ถ้ามี Video Device หลายตัว ให้เปลี่ยน `capture_device` เป็น `1`, `2` ตามลำดับ แล้วเปิดโปรแกรมใหม่
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
