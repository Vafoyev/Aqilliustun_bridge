# 🛠 AqilUstun Bridge — DevOps & System Administrator Deployment Guide

Dastur **Hikvision KV6114** domofoni va **Google Gemini Live AI API** hamda **Urganch Shahar Webhook API** o'rtasidagi 24/7 ishlaydigan real-time ovozli SIP/RTP xizmatidir.

---

## 🏛 1. Arxitektura va Muloqot Oqimi

```
 [Tashrifchi]
      │ (Tugma bosiladi)
      ▼
 [Hikvision KV6114 Domofon]
      │
      ├─► (SIP UDP 5060 INVITE) ────► [ai_call_server.py (Linux Server)]
      ├─► (RTP UDP 10000 G.711u) ───► [audio_codec.py (u-law 8kHz ◄► PCM16)]
                                                │
                                                ├─► (wss:// 443 TCP) ──► [Google Gemini Live API]
                                                └─► (https:// 443 TCP) ─► [Urganch Shahar Webhook]
```

---

## 🌐 2. Tarmoq va Portlar Sozlamasi (Firewall)

DevOps / Server Administratori quyidagi portlarni ochiq bo'lishini ta'minlashi shart:

### Kiruvchi Portlar (Inbound / Server Firewall)
* **`5060 / UDP`**: SIP Signalling (Domofon chaqiruvlari uchun).
* **`10000 / UDP`**: RTP Audio Stream (Ovoz paketlarini uzatish uchun).
* **`8000 / TCP`**: Web Admin Dashboard (AI Prompt va Gemini API Key boshqaruvi uchun).
* **`22 / TCP`**: SSH Masofaviy ulanish.

### Chiquvchi Portlar (Outbound / External Network)
* **`443 / TCP (WSS/HTTPS)`**: Google Gemini Live API (`generativelanguage.googleapis.com`) va Urganch Shahar API (`app.urganchshahar.uz`).
* **`80 / TCP (HTTP)`**: Hikvision ISAPI konfiguratsiya uchun (`http://<KV6114_IP>`).

### UFW Firewall Sozlash (Ubuntu/Debian):
```bash
sudo ufw allow 5060/udp
sudo ufw allow 10000/udp
sudo ufw allow 8000/tcp
sudo ufw reload
```

---

## 🚀 3. Serverga O'rnatish va Ishga Tushirish (Deployment Steps)

### ⚡ Option A: Avtomatik Bash Skript Orqali (Tavsiya etiladi - 1 Click)

Serveringizda loyihani yuklab olgach, `deploy.sh` skripti orqali venv, kutubxonalar, systemd servislar va UFW firewall sozlamalarini 1 ta buyruq bilan o'rnatishingiz mumkin:

```bash
git clone https://github.com/Vafoyev/Aqilliustun_bridge.git
cd Aqilliustun_bridge

# Izoh: Faylga ijro (executable) huquqini berish:
chmod +x deploy.sh

# To'liq serverga o'rnatish va servislarni sozlash:
sudo ./deploy.sh setup

# Keyinchalik `config.py` faylida kalitlarni sozlang:
nano config.py
```

#### `deploy.sh` Boshqaruv Buyruqlari:
* `sudo ./deploy.sh setup` — Barcha paketlar, venv, systemd servislari va firewallni sozlash.
* `./deploy.sh update` — Loyihani git pull va venv yangilash hamda servislarni qayta yurgizish.
* `./deploy.sh status` — Bridge va Dashboard servislarining holatini ko'rish.
* `./deploy.sh logs bridge` — Bridge server jonli loglarini kuzatish.
* `./deploy.sh logs dashboard` — Dashboard jonli loglarini kuzatish.
* `./deploy.sh enable-sip` — Hikvision domofoniga SIP sozlamalarini yuborish.

---

### 🛠 Option B: Qo'lda (Manual) O'rnatish

### 1-Qadam: Loyihani yuklab olish va virtual muhit yaratish
```bash
git clone https://github.com/Vafoyev/Aqilliustun_bridge.git
cd Aqilliustun_bridge

python3 -m venv venv
source venv/bin/activate
pip install -r requirements.txt
```

### 2-Qadam: Konfiguratsiyani yaratish (`config.py`)
```bash
cp config.example.py config.py
nano config.py
```
`config.py` tarkibi:
```python
SERVER_IP = "195.158.8.44"        # Serveringizning Tashqi (Public) IP adresi
KV6114_IP = "192.0.0.65"        # Domofon IP adresi
KV6114_USERNAME = "admin"
KV6114_PASSWORD = "Q112233q"

GEMINI_API_KEY = "YOUR_GEMINI_API_KEY"
```

### 3-Qadam: Systemd Service orqali 24/7 fonda ishga tushirish
```bash
# 1. SIP/RTP Ovozli Bridge Server servisi:
sudo cp aqilustun-bridge.service /etc/systemd/system/

# 2. Web Admin Dashboard servisi (Port 8000):
sudo cp aqilustun-dashboard.service /etc/systemd/system/

# Servislarni faollashtirish va ishga tushirish:
sudo systemctl daemon-reload
sudo systemctl enable --now aqilustun-bridge
sudo systemctl enable --now aqilustun-dashboard
```

---

## 📊 4. Monitoring va Loglarni Kuzatish

```bash
# Servis holati:
sudo systemctl status aqilustun-bridge

# Jonli loglarni kuzatish (Tail logs):
sudo journalctl -u aqilustun-bridge -f

# Servisni qayta ishga tushirish:
sudo systemctl restart aqilustun-bridge
```

---

## 📞 5. Hikvision Domofonda SIP Serverni Sozlash

### Option A: Avtomatik Skript Orqali (Recomended)
`config.py` to'g'ri to'ldirilgach, 1 marta ushbu skript yurgiziladi:
```bash
python3 enable_sip_server.py
```

### Option B: Hikvision Web GUI orqali (`http://<KV6114_IP>`)
1. **Network -> SIP Settings:**
   * Standard SIP: **Enable**
   * Server IP / Proxy: **`<SERVER_PUBLIC_IP>`**
   * Port: **`5060`**
   * User Name / Register Name: **`100`**
   * Password: **`Q112233q`**
2. **Audio Codec:** **`G.711u` (u-law 8kHz)**
