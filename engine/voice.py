"""Voix off : synthèse vocale française + effet mégaphone.

Moteur principal : Piper (voix neuronale gratuite, modèle téléchargé par
engine/get_voice.sh dans assets/voices/). Secours : eSpeak NG (plus
robotique), utilisé seulement si le modèle Piper est absent.
"""
import ctypes
import json
import os
import re
import subprocess
import wave

import numpy as np

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
with open(os.path.join(ROOT, "engine", "voice_config.json")) as _fh:
    CONFIG = json.load(_fh)
# VOICE / VOICE_PITCH en variables d'environnement permettent de comparer des voix
VOICE = os.environ.get("VOICE", CONFIG["voice"])
PITCH = float(os.environ.get("VOICE_PITCH", CONFIG.get("pitch", 1.0)))
SPEED = float(CONFIG.get("speed", 1.0))
MODEL = os.path.join(ROOT, "assets", "voices", VOICE + ".onnx")
SR = 44100

# voix plus grave : on baisse la hauteur sans changer le débit (pitch < 1)
DEEPEN = f"asetrate={SR}*{PITCH},aresample={SR},atempo={1 / PITCH * SPEED:.4f},"
# effet mégaphone léger : on garde les graves pour une voix profonde,
# saturation douce et petit écho
MEGAPHONE = (DEEPEN + "highpass=f=160,lowpass=f=4200,bass=g=4:f=140,volume=5dB,"
             "asoftclip=type=tanh,aecho=0.8:0.45:22:0.18,volume=-3dB")


def clean(text):
    """Texte affiché → texte à lire."""
    t = text.replace("*", "").replace("«", "").replace("»", "")
    t = re.sub(r"N°\s*(\d+)", r"numéro \1", t)
    t = t.replace("...", ",").replace("…", ",")
    t = re.sub(r"\s+", " ", t).strip(" :")
    return t.lower().capitalize()


_piper = None


def _synth_piper(text):
    global _piper
    from piper import PiperVoice
    if _piper is None:
        _piper = PiperVoice.load(MODEL)
    chunks = [c.audio_int16_array for c in _piper.synthesize(text)]
    audio = np.concatenate(chunks).astype(np.float32) / 32768
    return audio, _piper.config.sample_rate


_espeak = None


def _synth_espeak(text):
    global _espeak
    import espeakng_loader as el
    if _espeak is None:
        lib = ctypes.CDLL(el.get_library_path())
        rate = lib.espeak_Initialize(1, 0, el.get_data_path().encode(), 0)
        lib.espeak_SetVoiceByName(b"fr")
        lib.espeak_SetParameter(1, 150, 0)  # vitesse
        lib.espeak_SetParameter(3, 45, 0)   # hauteur
        buf = []
        CB = ctypes.CFUNCTYPE(ctypes.c_int, ctypes.POINTER(ctypes.c_short), ctypes.c_int, ctypes.c_void_p)

        def cb(wav, n, ev):
            if n > 0:
                buf.append(np.ctypeslib.as_array(wav, (n,)).copy())
            return 0
        cbf = CB(cb)
        lib.espeak_SetSynthCallback(cbf)
        _espeak = (lib, rate, buf, cbf)
    lib, rate, buf, _ = _espeak
    buf.clear()
    data = text.encode("utf-8") + b"\0"
    lib.espeak_Synth(data, len(data), 0, 0, 0, 1, None, None)
    lib.espeak_Synchronize()
    audio = np.concatenate(buf).astype(np.float32) / 32768 if buf else np.zeros(1, np.float32)
    return audio, rate


def engine_name():
    return "piper" if os.path.exists(MODEL) else "espeak"


def synth(text):
    """Renvoie l'audio (float32, 44,1 kHz) de la phrase."""
    audio, rate = (_synth_piper if engine_name() == "piper" else _synth_espeak)(clean(text))
    if rate != SR:
        x = np.linspace(0, len(audio) - 1, int(len(audio) * SR / rate))
        audio = np.interp(x, np.arange(len(audio)), audio).astype(np.float32)
    # retire les silences au début et à la fin
    idx = np.where(np.abs(audio) > 0.01)[0]
    if len(idx):
        audio = audio[max(0, idx[0] - 200): idx[-1] + 2000]
    return audio


def megaphone(track, tmpdir):
    """Applique l'effet mégaphone à une piste mono float32."""
    src = os.path.join(tmpdir, "voice_raw.wav")
    dst = os.path.join(tmpdir, "voice_fx.wav")
    write_wav(src, track)
    subprocess.run(["ffmpeg", "-loglevel", "error", "-y", "-i", src, "-af", MEGAPHONE, "-ar", str(SR), "-ac", "1", dst], check=True)
    with wave.open(dst) as wf:
        out = np.frombuffer(wf.readframes(wf.getnframes()), np.int16).astype(np.float32) / 32768
    res = np.zeros_like(track)
    res[: min(len(res), len(out))] = out[: len(res)]
    return res


def write_wav(path, track):
    pcm = (np.clip(track, -1, 1) * 32767).astype(np.int16)
    with wave.open(path, "wb") as wf:
        wf.setnchannels(1)
        wf.setsampwidth(2)
        wf.setframerate(SR)
        wf.writeframes(pcm.tobytes())
