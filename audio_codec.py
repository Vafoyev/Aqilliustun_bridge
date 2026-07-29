"""Jonli suhbat uchun tez audio konvertatsiya (protsess ochmasdan, audioop orqali).

Chastota zanjiri:
    Domofondan:  G.711 u-law 8kHz  ->  PCM16 16kHz  (Gemini kirishi)
    Domofonga:   PCM16 24kHz       ->  G.711 u-law 8kHz  (Gemini chiqishi)

`audio_convert.py` shu ishni ffmpeg bilan qiladi, lekin u har chaqiruvda
alohida protsess ochadi — RTP'da sekundiga 50 ta bo'lak kelgani uchun
jonli oqimga yaramaydi. Bu modul o'sha o'rinni egallaydi.

`ratecv` uzluksiz oqimda oldingi holatni saqlashi shart, aks holda har
bo'lak chegarasida chirsillash paydo bo'ladi — shuning uchun holat klass
ichida saqlanadi, funksiya sifatida emas.
"""

import audioop

HIKVISION_RATE = 8000
GEMINI_INPUT_RATE = 16000
GEMINI_OUTPUT_RATE = 24000

SAMPLE_WIDTH = 2  # PCM16
CHANNELS = 1


class _Resampler:
    """audioop.ratecv ustidan holatni saqlab turuvchi yupqa qobiq."""

    def __init__(self, in_rate, out_rate):
        self._in_rate = in_rate
        self._out_rate = out_rate
        self._state = None

    def __call__(self, pcm_bytes):
        converted, self._state = audioop.ratecv(
            pcm_bytes,
            SAMPLE_WIDTH,
            CHANNELS,
            self._in_rate,
            self._out_rate,
            self._state,
        )
        return converted

    def reset(self):
        self._state = None


class InboundAudio:
    """Domofondan kelgan u-law 8kHz -> Gemini kutadigan PCM16 16kHz."""

    def __init__(self):
        self._resample = _Resampler(HIKVISION_RATE, GEMINI_INPUT_RATE)

    def convert(self, ulaw_bytes):
        pcm8k = audioop.ulaw2lin(ulaw_bytes, SAMPLE_WIDTH)
        return self._resample(pcm8k)

    def reset(self):
        self._resample.reset()


class OutboundAudio:
    """Gemini'dan kelgan PCM16 24kHz -> domofon kutadigan u-law 8kHz."""

    def __init__(self):
        self._resample = _Resampler(GEMINI_OUTPUT_RATE, HIKVISION_RATE)

    def convert(self, pcm24k_bytes):
        pcm8k = self._resample(pcm24k_bytes)
        return audioop.lin2ulaw(pcm8k, SAMPLE_WIDTH)

    def reset(self):
        self._resample.reset()
