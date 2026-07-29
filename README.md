# AqilUstun Bridge — Hikvision Domofon & Google Gemini Live AI Ko'prigi

**AqilUstun Bridge** — Hikvision (KV6114) domofoni va **Google Gemini Live AI** (WebSocket BidiGenerateContent API) o'rtasidagi 24/7 ishlaydigan real-time ovozli SIP/RTP xizmati.

---

## 🏛 Arxitektura

```
 [Tashrifchi]
      │ (Tugma bosiladi)
      ▼
 [KV6114 Domofon]
      │
      ├─► (SIP UDP 5060 INVITE) ────► [ai_call_server.py (Server)]
      ├─► (RTP UDP 10000 G.711) ───► [audio_codec.py (u-law 8kHz ◄► PCM16)]
                                                │
                                                ▼ (wss:// 443 TCP)
                                      [Google Gemini Live API]
```

---

## 📂 Fayllar Tuzilishi

- **`ai_call_server.py`**: SIP server (port 5060) hamda RTP audio kanali (port 10000) ni boshqaruvchi va suhbat transkriptini saqlovchi asosiy server.
- **`audio_codec.py`**: Domofon va Gemini o'rtasida audioni real-time kechikishsiz va chirsillashlarsiz o'giruvchi modul (`audioop`).
- **`gemini_live.py`**: Google Gemini Live API bidi-stream WebSocket muloqot mijozi.
- **`enable_sip_server.py`**: Domofonga SIP server IP manzilini bir marta sozlab beruvchi yordamchi skript.
- **`config.example.py`**: Konfiguratsiya namuna fayli (`config.py` qilib nusxalanadi).
- **`aqilustun-bridge.service`**: Linux serverda Systemd orqali 24/7 fonda ishlatish fayli.

---

## 🚀 O'rnatish va Ishga Tushirish (Serverda)

### 1. Loyihani yuklash va kutubxonalarni o'rnatish

```bash
git clone <YOUR_GITHUB_REPO_URL> aqilustun-bridge
cd aqilustun-bridge

python3 -m venv venv
source venv/bin/activate
pip install -r requirements.txt
```

### 2. Portlarni ochish (UFW)

```bash
sudo ufw allow 5060/udp   # SIP Port
sudo ufw allow 10000/udp  # RTP Audio Port
```

### 3. Production Konfiguratsiyani Yaratish

`config.example.py` dan `config.py` yaratasiz:

```bash
cp config.example.py config.py
```

`config.py` ichini tahrirlang:
```python
SERVER_IP = "192.0.0.64"          # Serveringizning lokal IP si
KV6114_IP = "192.0.0.65"          # Domofon IP si
KV6114_USERNAME = "admin"
KV6114_PASSWORD = "YOUR_PASSWORD"

GEMINI_API_KEY = "YOUR_GEMINI_API_KEY"
```

### 4. Domofonni Sozlash (1 marta)

```bash
python3 enable_sip_server.py
```

### 5. Systemd Servis sifatida fonda ishga tushirish (24/7)

```bash
sudo cp aqilustun-bridge.service /etc/systemd/system/
sudo systemctl daemon-reload
sudo systemctl enable --now aqilustun-bridge

# Loglarni kuzatish:
sudo journalctl -u aqilustun-bridge -f
```

---

## 🔒 Xavfsizlik

`config.py` va `logs/` papkasi `.gitignore` fayliga kiritilgan. Shaxsiy API kalit va parollaringizni GitHub'ga yuklamang!
