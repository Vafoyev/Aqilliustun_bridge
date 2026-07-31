"""KV6114 domofoni bilan Gemini Live o'rtasidagi jonli ovozli ko'prik.

Oqim:
    [tugma bosiladi]
      -> KV6114 SIP INVITE yuboradi
      -> biz javob beramiz, RTP kanali ochiladi
      -> Gemini Live sessiyasi ochiladi va AI birinchi bo'lib salomlashadi
      -> tashrifchi gapiradi  -> RTP (u-law 8kHz) -> PCM16 16kHz -> Gemini
      -> Gemini javobi (PCM16 24kHz) -> u-law 8kHz -> RTP -> domofon dinamigi
      -> BYE kelganda sessiya yopiladi va transkript saqlanadi

`sip_server.py` shu ishning faqat SIP qismini qilardi va javob sifatida
oldindan yozilgan fayllarni qo'yardi; bu modul uni jonli AI bilan
almashtiradi. Eski fayl ma'lumotnoma sifatida tegilmasdan qoldirilgan.
"""

import asyncio
import json
import os
import re
import time
from datetime import datetime

import config
from audio_codec import InboundAudio, OutboundAudio
from gemini_live import GeminiLiveSession

BIND_IP = "0.0.0.0"
SERVER_IP = config.SERVER_IP
SIP_PORT = getattr(config, "SIP_PORT", 5060)
RTP_PORT = getattr(config, "RTP_PORT", 10000)

LOGS_DIR = "logs"

# G.711 8kHz: 20 ms = 160 bayt. RTP shu ritmda yuborilishi kerak.
PACKET_MS = 20
PACKET_BYTES = 160
ULAW_SILENCE = 0xFF

# Salomlashish har safar bir xil bo'lishi uchun matn aniq beriladi —
# improvizatsiyaga qoldirilsa, model har qo'ng'iroqda boshqacha gapiradi.
GREETING_PROMPT = (
    "Tashrifchi domofon tugmasini bosdi. Darhol aynan shunday salomlash, "
    "boshqa hech narsa qo'shma: "
    "\"Assalomu alaykum! Men Aqilli Ustun sun'iy intellektiman. "
    "Qanday murojaatingiz bor?\""
)


def log(msg):
    print(f"[{time.strftime('%H:%M:%S')}] {msg}", flush=True)


def header(msg, name):
    m = re.search(rf"^{name}:\s*(.+)$", msg, re.IGNORECASE | re.MULTILINE)
    return m.group(1).strip() if m else ""


def rtp_payload(packet):
    """RTP paketidan foydali yukni ajratadi (CSRC va kengaytmani hisobga olib)."""
    if len(packet) < 12:
        return b""
    byte0 = packet[0]
    if (byte0 >> 6) != 2:  # RTP versiyasi 2 bo'lishi kerak
        return b""
    csrc_count = byte0 & 0x0F
    offset = 12 + 4 * csrc_count
    if byte0 & 0x10:  # kengaytma sarlavhasi bor
        if len(packet) < offset + 4:
            return b""
        ext_words = int.from_bytes(packet[offset + 2 : offset + 4], "big")
        offset += 4 + 4 * ext_words
    return packet[offset:] if len(packet) > offset else b""


class CallSession:
    """Bitta qo'ng'iroq: Gemini sessiyasi, audio buferlari va transkript."""

    def __init__(self, rtp_transport, remote_rtp_addr):
        self._rtp = rtp_transport
        self._remote = remote_rtp_addr

        self._inbound = InboundAudio()
        self._outbound = OutboundAudio()

        self._out_buffer = bytearray()
        self._in_queue = asyncio.Queue(maxsize=200)
        self._sender_task = None
        self._feeder_task = None
        self._active = False
        self._gemini_ready = False
        self._last_error = None

        self._seq = 0
        self._timestamp = 0
        self._ssrc = 0x41C1D057  # "AqilUstun" sessiyasi uchun barqaror SSRC

        self.transcript = []
        self._visitor_text = ""
        self._ai_text = ""
        self.started_at = datetime.now()

        self._gemini = GeminiLiveSession(
            on_audio_chunk=self._on_gemini_audio,
            on_input_transcript=self._on_visitor_text,
            on_output_transcript=self._on_ai_text,
            on_turn_complete=self._on_turn_complete,
            on_interrupted=self._on_interrupted,
        )

    # --- boshlash / tugatish -------------------------------------------------

    async def start(self):
        self._active = True
        # RTP oqimi Gemini'ni kutmasdan darhol boshlanadi: domofon ACK'dan
        # keyin paket kelmasa qo'ng'iroqni uzib yuboradi, Gemini ulanishi esa
        # bir soniyacha vaqt oladi. Bu oraliqda sukunat yuboriladi.
        self._sender_task = asyncio.create_task(self._rtp_sender_loop())
        self._feeder_task = asyncio.create_task(self._gemini_feed_loop())

        await self._gemini.connect()
        self._gemini_ready = True

        # AI birinchi bo'lib gapiradi — tashrifchi jim turmasin.
        await self._gemini.send_text_turn(GREETING_PROMPT)
        log("Suhbat boshlandi, AI salomlashmoqda")

    async def stop(self):
        if not self._active:
            return
        self._active = False
        self._gemini_ready = False
        for task in (self._sender_task, self._feeder_task):
            if task:
                task.cancel()
                try:
                    await task
                except asyncio.CancelledError:
                    pass
        await self._gemini.close()
        self._flush_turn()
        self._save_transcript()

    # --- domofondan Gemini'ga ------------------------------------------------

    def feed_rtp(self, packet):
        """RTP paketi kelganda chaqiriladi (tashrifchi ovozi).

        Gemini hali ulanmagan bo'lsa paket tashlanadi — navbatda saqlab
        qo'yishdan foyda yo'q, chunki eski audio kechikib borsa suhbat
        ritmi buziladi.
        """
        if not (self._active and self._gemini_ready):
            return
        payload = rtp_payload(packet)
        if not payload:
            return
        try:
            self._in_queue.put_nowait(self._inbound.convert(payload))
        except asyncio.QueueFull:
            self._log_once("kirish navbati to'ldi, paket tashlandi")

    async def _gemini_feed_loop(self):
        """Navbatdagi audioni Gemini'ga tartib bilan uzatadi.

        Har paket uchun alohida task ochilsa tartib kafolatlanmaydi va
        sekundiga 50 ta task paydo bo'ladi — shuning uchun bitta iste'molchi.
        """
        while self._active:
            pcm16k = await self._in_queue.get()
            try:
                await self._gemini.send_audio_chunk(pcm16k)
            except Exception as e:
                self._log_once(f"audio yuborishda xato: {type(e).__name__}: {e}")

    def _log_once(self, message):
        """Bir xil xatoni takrorlab bosmaydi (log sekundiga 50 marta to'lmasin)."""
        if message != self._last_error:
            self._last_error = message
            log(f"[Gemini] {message}")

    # --- Gemini'dan domofonga ------------------------------------------------

    async def _on_gemini_audio(self, pcm24k):
        self._out_buffer.extend(self._outbound.convert(pcm24k))

    async def _rtp_sender_loop(self):
        """Har 20 ms da bitta RTP paketi yuboradi.

        Gemini audioni to'lqin-to'lqin yuboradi, domofon esa tekis oqim
        kutadi — shuning uchun bufer bo'sh bo'lsa sukunat yuboriladi.
        Bu RTP ketma-ketligini uzmaydi va ovoz bo'linib qolmaydi.
        """
        loop = asyncio.get_running_loop()
        next_tick = loop.time()
        while self._active:
            if len(self._out_buffer) >= PACKET_BYTES:
                chunk = bytes(self._out_buffer[:PACKET_BYTES])
                del self._out_buffer[:PACKET_BYTES]
            else:
                chunk = bytes([ULAW_SILENCE]) * PACKET_BYTES

            self._rtp.sendto(self._build_rtp(chunk), self._remote)

            next_tick += PACKET_MS / 1000.0
            await asyncio.sleep(max(0.0, next_tick - loop.time()))

    def _build_rtp(self, payload):
        h = bytearray(12)
        h[0] = 0x80  # versiya 2
        h[1] = 0x00  # payload type 0 = PCMU (G.711 u-law)
        h[2] = (self._seq >> 8) & 0xFF
        h[3] = self._seq & 0xFF
        h[4] = (self._timestamp >> 24) & 0xFF
        h[5] = (self._timestamp >> 16) & 0xFF
        h[6] = (self._timestamp >> 8) & 0xFF
        h[7] = self._timestamp & 0xFF
        h[8] = (self._ssrc >> 24) & 0xFF
        h[9] = (self._ssrc >> 16) & 0xFF
        h[10] = (self._ssrc >> 8) & 0xFF
        h[11] = self._ssrc & 0xFF

        self._seq = (self._seq + 1) & 0xFFFF
        self._timestamp = (self._timestamp + len(payload)) & 0xFFFFFFFF
        return bytes(h) + payload

    # --- transkript ----------------------------------------------------------

    async def _on_visitor_text(self, text):
        self._visitor_text += text

    async def _on_ai_text(self, text):
        self._ai_text += text

    async def _on_turn_complete(self):
        self._flush_turn()

    async def _on_interrupted(self):
        # Tashrifchi gapni bo'ldi — aytilmagan javobni tashlab yuboramiz,
        # aks holda AI eski gapini davom ettirib, ustma-ust tushadi.
        self._out_buffer.clear()
        self._outbound.reset()
        log("Tashrifchi AI gapini bo'ldi")

    def _flush_turn(self):
        for role, text in (("visitor", self._visitor_text), ("assistant", self._ai_text)):
            if text.strip():
                self.transcript.append({
                    "role": role,
                    "text": text.strip(),
                    "timestamp": datetime.now().isoformat(),
                })
                log(f"  {role}: {text.strip()}")
        self._visitor_text = ""
        self._ai_text = ""

    def _save_transcript(self):
        if not self.transcript:
            log("Transkript bo'sh, saqlanmadi")
            return
        os.makedirs(LOGS_DIR, exist_ok=True)
        path = os.path.join(LOGS_DIR, self.started_at.strftime("call_%Y%m%d_%H%M%S.json"))
        with open(path, "w", encoding="utf-8") as f:
            json.dump({
                "call_start": self.started_at.isoformat(),
                "call_end": datetime.now().isoformat(),
                "transcript": self.transcript,
            }, f, ensure_ascii=False, indent=2)
        log(f"Transkript saqlandi: {path}")


class RtpProtocol(asyncio.DatagramProtocol):
    def __init__(self, server):
        self._server = server

    def connection_made(self, transport):
        self._server.rtp_transport = transport

    def datagram_received(self, data, addr):
        session = self._server.session
        if session:
            session.feed_rtp(data)


class SipProtocol(asyncio.DatagramProtocol):
    def __init__(self, server):
        self._server = server

    def connection_made(self, transport):
        self._server.sip_transport = transport

    def datagram_received(self, data, addr):
        msg = data.decode("utf-8", errors="ignore")
        if len(msg) < 10:
            return
        first_line = msg.split("\r\n")[0].strip()
        method = first_line.split(" ", 1)[0].upper()

        if method in ("REGISTER", "INVITE", "ACK", "BYE", "CANCEL", "OPTIONS", "MESSAGE"):
            log(f"SIP {method} <- {addr[0]}:{addr[1]}")

        handler = {
            "REGISTER": self._server.on_register,
            "INVITE": self._server.on_invite,
            "ACK": self._server.on_ack,
            "BYE": self._server.on_bye,
            "CANCEL": self._server.on_bye,
            "OPTIONS": self._server.on_simple_ok,
            "MESSAGE": self._server.on_simple_ok,
        }.get(method)

        if handler:
            result = handler(msg, addr)
            if asyncio.iscoroutine(result):
                asyncio.create_task(result)


class AiCallServer:
    def __init__(self, server_ip=SERVER_IP, sip_port=SIP_PORT, rtp_port=RTP_PORT):
        self.server_ip = server_ip
        self.sip_port = sip_port
        self.rtp_port = rtp_port
        self.sip_transport = None
        self.rtp_transport = None
        self.session = None
        self._pending_remote = None

    # --- SIP javoblari -------------------------------------------------------

    def _reply(self, msg, addr, status_line, extra="", body="", to_tag=None):
        via = header(msg, "Via")
        if "rport" in via and f"rport={addr[1]}" not in via:
            via = re.sub(r";rport(?![=\d])", f";received={addr[0]};rport={addr[1]}", via)
        elif "received=" not in via:
            via += f";received={addr[0]}"

        to_hdr = header(msg, "To")
        if to_tag and ";tag=" not in to_hdr:
            to_hdr += f";tag={to_tag}"

        date_str = time.strftime("%a, %d %b %Y %H:%M:%S GMT", time.gmtime())

        response = (
            f"{status_line}\r\n"
            f"Via: {via}\r\n"
            f"From: {header(msg, 'From')}\r\n"
            f"To: {to_hdr}\r\n"
            f"Call-ID: {header(msg, 'Call-ID')}\r\n"
            f"CSeq: {header(msg, 'CSeq')}\r\n"
            f"User-Agent: AqilUstun-Bridge/1.0\r\n"
            f"Date: {date_str}\r\n"
            f"{extra}"
            f"Content-Length: {len(body)}\r\n\r\n"
            f"{body}"
        )
        self.sip_transport.sendto(response.encode(), addr)

    def on_simple_ok(self, msg, addr):
        self._reply(msg, addr, "SIP/2.0 200 OK")

    def on_register(self, msg, addr):
        contact = header(msg, "Contact") or f"<sip:100@{addr[0]}:{addr[1]}>"
        self._reply(
            msg, addr, "SIP/2.0 200 OK",
            extra=f"Contact: {contact}\r\nExpires: 3600\r\n",
            to_tag="reg123",
        )
        log(f"Domofon ro'yxatdan o'tdi ({addr[0]}:{addr[1]})")

    async def _start_session_async(self):
        if self.session or not self._pending_remote:
            return
        session = CallSession(self.rtp_transport, self._pending_remote)
        self.session = session
        try:
            await session.start()
        except Exception as e:
            log(f"Suhbatni boshlashda xato: {type(e).__name__}: {e}")
            self.session = None
            await session.stop()

    def on_invite(self, msg, addr):
        m = re.search(r"m=audio\s+(\d+)\s+RTP/AVP", msg)
        remote_rtp_port = int(m.group(1)) if m else RTP_PORT
        self._pending_remote = (addr[0], remote_rtp_port)
        log(f"Qo'ng'iroq keldi! Domofon RTP manzili: {self._pending_remote}")

        self._reply(msg, addr, "SIP/2.0 100 Trying")
        self._reply(msg, addr, "SIP/2.0 180 Ringing", to_tag="aqilustun123")

        sdp = (
            "v=0\r\n"
            f"o=AqilUstun 1000 1000 IN IP4 {self.server_ip}\r\n"
            "s=AqilUstun AI Intercom\r\n"
            f"c=IN IP4 {self.server_ip}\r\n"
            "t=0 0\r\n"
            f"m=audio {self.rtp_port} RTP/AVP 0 101\r\n"
            "a=rtpmap:0 PCMU/8000\r\n"
            "a=rtpmap:101 telephone-event/8000\r\n"
            "a=sendrecv\r\n"
        )
        self._reply(
            msg, addr, "SIP/2.0 200 OK",
            extra=f"Contact: <sip:1@{self.server_ip}:{self.sip_port}>\r\n"
                  "Content-Type: application/sdp\r\n",
            body=sdp,
            to_tag="aqilustun123",
        )
        asyncio.create_task(self._start_session_async())

    async def on_ack(self, msg, addr):
        if not self.session:
            await self._start_session_async()

    async def on_bye(self, msg, addr):
        self._reply(msg, addr, "SIP/2.0 200 OK")
        log("Qo'ng'iroq yakunlandi")
        session, self.session = self.session, None
        self._pending_remote = None
        if session:
            await session.stop()

    # --- ishga tushirish -----------------------------------------------------

    async def run(self):
        loop = asyncio.get_running_loop()
        await loop.create_datagram_endpoint(
            lambda: SipProtocol(self), local_addr=(BIND_IP, self.sip_port)
        )
        await loop.create_datagram_endpoint(
            lambda: RtpProtocol(self), local_addr=(BIND_IP, self.rtp_port)
        )
        log("=" * 50)
        log(f"AqilUstun AI qo'ng'iroq serveri: SIP {self.sip_port}, RTP {self.rtp_port}")
        log(f"KV6114 ({config.KV6114_IP}) tugmasi kutilmoqda...")
        log("=" * 50)
        await asyncio.Event().wait()


if __name__ == "__main__":
    try:
        asyncio.run(AiCallServer().run())
    except KeyboardInterrupt:
        log("To'xtatildi")
