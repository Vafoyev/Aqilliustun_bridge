import asyncio
import base64
import json

import websockets

import config

import os

MODEL = "models/gemini-3.1-flash-live-preview"

DEFAULT_SYSTEM_INSTRUCTION = (
    "Sen \"Aqilli Ustun\" — domofonga o'rnatilgan sun'iy intellekt "
    "yordamchisisan. Isming ikki so'z: \"Aqilli\" va \"Ustun\". Uni doim "
    "to'liq, \"Aqilli Ustun\" deb ayt; \"Aqil Ustun\" deb qisqartirma. "
    "Tashrifchi bilan o'zbek tilida, samimiy va xushmuomala gaplashasan.\n"
    "\n"
    "Qat'iy qoidalar:\n"
    "1. Suhbatni HAR DOIM sen boshlaysan va o'zingni tanishtirasan: "
    "\"Assalomu alaykum! Men Aqilli Ustun sun'iy intellektiman. "
    "Qanday murojaatingiz bor?\"\n"
    "2. Tashrifchining maqsadini so'raganda faqat \"Qanday murojaatingiz bor?\" "
    "deb so'raysan. \"Kim kerak\", \"kimni yoqlab keldingiz\", \"kimni "
    "so'rab keldingiz\" kabi iboralarni HECH QACHON ishlatma.\n"
    "3. Foydalanuvchi so'ragan HAR QANDAY savolga bemalol javob ber — "
    "aqlli shahar, O'zbekiston, tarix, fan, texnika, umumiy bilim, "
    "istalgan mavzu. Mavzuni cheklama, \"men faqat domofonman\" dema. "
    "Bilmasang, halol ayt.\n"
    "\n"
    "Uslub: bu ovozli suhbat, shuning uchun javoblar qisqa bo'lsin — "
    "1-3 gap. Ro'yxat, belgi yoki formatlash ishlatma, jonli gapirgandek "
    "gapir. Tashrifchi boshqa tilda gapirsa, o'sha tilda javob ber."
)


def get_system_instruction():
    """prompt.txt dan tizim yo'riqnomasini dinamik o'qiydi."""
    prompt_path = os.path.join(os.path.dirname(__file__), "prompt.txt")
    if os.path.exists(prompt_path):
        try:
            with open(prompt_path, "r", encoding="utf-8") as f:
                text = f.read().strip()
                if text:
                    return text
        except Exception as e:
            print(f"[Gemini] prompt.txt o'qishda xato: {e}")
    return DEFAULT_SYSTEM_INSTRUCTION


def get_ws_uri():
    """config.py dan Gemini API Key ni dinamik oladi."""
    return (
        "wss://generativelanguage.googleapis.com/ws/"
        "google.ai.generativelanguage.v1beta.GenerativeService.BidiGenerateContent"
        f"?key={config.GEMINI_API_KEY}"
    )


class GeminiLiveSession:
    """Bitta qo'ng'iroq davomida ochiq turadigan Gemini Live WebSocket sessiyasi."""

    def __init__(
        self,
        on_audio_chunk,
        on_input_transcript,
        on_output_transcript,
        on_turn_complete,
        on_interrupted=None,
    ):
        self._ws = None
        self._recv_task = None
        self.on_audio_chunk = on_audio_chunk
        self.on_input_transcript = on_input_transcript
        self.on_output_transcript = on_output_transcript
        self.on_turn_complete = on_turn_complete
        self.on_interrupted = on_interrupted

    async def connect(self):
        print("[Gemini] WebSocket'ga ulanilmoqda...")
        ws_uri = get_ws_uri()
        system_instruction = get_system_instruction()

        self._ws = await websockets.connect(ws_uri, max_size=None)

        setup_msg = {
            "setup": {
                "model": MODEL,
                "generationConfig": {"responseModalities": ["AUDIO"]},
                "systemInstruction": {"parts": [{"text": system_instruction}]},
                "inputAudioTranscription": {},
                "outputAudioTranscription": {},
            }
        }
        await self._ws.send(json.dumps(setup_msg))
        response = json.loads(await self._ws.recv())
        if "setupComplete" not in response:
            raise RuntimeError(f"Gemini Live sozlash muvaffaqiyatsiz: {response}")

        print("[Gemini] Ulanildi, sessiya sozlandi")
        self._recv_task = asyncio.create_task(self._receive_loop())

    async def send_text_turn(self, text):
        """Matnli navbat yuboradi — AI shu asosda ovozli javob beradi.

        Qo'ng'iroq boshida ishlatiladi: tashrifchi jim turgan holda ham
        AI birinchi bo'lib salomlashishi kerak.
        """
        msg = {
            "clientContent": {
                "turns": [{"role": "user", "parts": [{"text": text}]}],
                "turnComplete": True,
            }
        }
        await self._ws.send(json.dumps(msg))

    async def send_audio_chunk(self, pcm16k_bytes):
        msg = {
            "realtimeInput": {
                "audio": {
                    "data": base64.b64encode(pcm16k_bytes).decode("ascii"),
                    "mimeType": "audio/pcm;rate=16000",
                }
            }
        }
        await self._ws.send(json.dumps(msg))

    async def _receive_loop(self):
        try:
            async for message in self._ws:
                data = json.loads(message)
                server_content = data.get("serverContent")
                if not server_content:
                    continue

                if server_content.get("interrupted") and self.on_interrupted:
                    await self.on_interrupted()

                model_turn = server_content.get("modelTurn")
                if model_turn:
                    for part in model_turn.get("parts", []):
                        inline = part.get("inlineData")
                        if inline:
                            await self.on_audio_chunk(base64.b64decode(inline["data"]))

                if "inputTranscription" in server_content:
                    text = server_content["inputTranscription"].get("text", "")
                    if text:
                        await self.on_input_transcript(text)

                if "outputTranscription" in server_content:
                    text = server_content["outputTranscription"].get("text", "")
                    if text:
                        await self.on_output_transcript(text)

                if server_content.get("turnComplete"):
                    await self.on_turn_complete()
        except websockets.exceptions.ConnectionClosed as e:
            print(f"[Gemini] Ulanish yopildi: {e}")

    async def close(self):
        if self._recv_task:
            self._recv_task.cancel()
        if self._ws:
            await self._ws.close()
        print("[Gemini] Sessiya yopildi")
