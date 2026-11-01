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
import zlib

import numpy as np

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
with open(os.path.join(ROOT, "engine", "voice_config.json")) as _fh:
    CONFIG = json.load(_fh)
# VOICE / VOICE_PITCH en variables d'environnement permettent de comparer des voix
VOICE = os.environ.get("VOICE", CONFIG["voice"])
PITCH = float(os.environ.get("VOICE_PITCH", CONFIG.get("pitch", 1.0)))
SPEED = float(CONFIG.get("speed", 1.0))
SPEAKER = os.environ.get("VOICE_SPEAKER", CONFIG.get("speaker"))
SPEAKER = int(SPEAKER) if SPEAKER not in (None, "") else None
# effet : "megaphone" (défaut), "leger" (voix naturelle, juste un peu de présence) ou "aucun"
FX = os.environ.get("VOICE_FX", CONFIG.get("effect", "megaphone"))
# débit de lecture de Piper (> 1 = plus lent, plus posé) et expressivité
LENGTH = float(os.environ.get("VOICE_LENGTH", CONFIG.get("length", 1.0)))
EXPRESS = float(os.environ.get("VOICE_EXPRESS", CONFIG.get("expressivity", 0.667)))
# accélère chaque réplique sans changer la hauteur (1.2 = 20 % plus rapide)
TEMPO = float(os.environ.get("VOICE_TEMPO", CONFIG.get("tempo", 1.0)))
# "serré" : chaque plan dure juste le temps de la réplique, pour que ça s'enchaîne
TIGHT = os.environ.get("VOICE_TIGHT", str(CONFIG.get("tight", False))).lower() in ("1", "true", "oui")
RHYTHM = float(os.environ.get("VOICE_RHYTHM", CONFIG.get("rhythm", 0.8)))
MODEL = os.path.join(ROOT, "assets", "voices", VOICE + ".onnx")
SR = 44100

# voix plus grave : on baisse la hauteur sans changer le débit (pitch < 1)
DEEPEN = f"asetrate={SR}*{PITCH},aresample={SR},atempo={1 / PITCH * SPEED:.4f},"
# effet mégaphone léger : on garde les graves pour une voix profonde,
# saturation douce et petit écho
MEGAPHONE = (DEEPEN + "highpass=f=160,lowpass=f=4200,bass=g=4:f=140,volume=5dB,"
             "asoftclip=type=tanh,aecho=0.8:0.45:22:0.18,volume=-3dB")
LIGHT = DEEPEN + "highpass=f=70,acompressor=threshold=-18dB:ratio=3:attack=5:release=80,volume=2dB"
NONE = DEEPEN + "anull"
# narrateur de film : graves renforcés, voix bien en avant, réverbération de grande salle vide
CINEMA = (DEEPEN + "highpass=f=60,bass=g=5:f=110,equalizer=f=3000:t=q:w=1:g=2,"
          "acompressor=threshold=-20dB:ratio=4:attack=5:release=120,"
          "aecho=0.8:0.6:60|130|240:0.22|0.14|0.08,volume=2dB")
# message radio d'un survivant : bande étroite, légère saturation, souffle
RADIO = (DEEPEN + "highpass=f=300,lowpass=f=3400,acompressor=threshold=-22dB:ratio=6,"
         "asoftclip=type=tanh,volume=3dB")
# radio douce : couleur radio sans écraser la voix, petite pièce autour
RADIO_SOFT = (DEEPEN + "highpass=f=180,lowpass=f=5200,equalizer=f=1800:t=q:w=1.2:g=3,"
              "acompressor=threshold=-20dB:ratio=2.5:attack=8:release=150,"
              "aecho=0.8:0.5:18:0.08,volume=3dB")


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
    from piper import SynthesisConfig
    cfg = SynthesisConfig(speaker_id=SPEAKER, length_scale=LENGTH, noise_scale=EXPRESS, noise_w_scale=RHYTHM)
    chunks = [c.audio_int16_array for c in _piper.synthesize(text, syn_config=cfg)]
    audio = np.concatenate(chunks).astype(np.float32) / 32768
    return audio, _piper.config.sample_rate


_cb = None
# Chatterbox : voix neuronale récente, bien plus naturelle (≈ 8x plus lent que le temps réel sur CPU).
# Elle copie le timbre d'un court enregistrement de référence.
CB_REF = os.path.join(ROOT, "assets", "ref", os.environ.get("VOICE_REF", CONFIG.get("reference", "ref-pierre.wav")))
CB_EXAG = float(os.environ.get("VOICE_EXAG", CONFIG.get("exaggeration", 0.6)))
CB_CFG = float(os.environ.get("VOICE_CFG", CONFIG.get("cfg", 0.4)))


def _synth_chatterbox(text):
    global _cb
    import torch
    from chatterbox.mtl_tts import ChatterboxMultilingualTTS
    if _cb is None:
        _cb = ChatterboxMultilingualTTS.from_pretrained(device="cpu")
    torch.manual_seed(zlib.crc32(text.encode()))
    w = _cb.generate(text, language_id="fr", audio_prompt_path=CB_REF,
                     exaggeration=CB_EXAG, cfg_weight=CB_CFG)
    return w.squeeze(0).numpy().astype(np.float32), _cb.sr


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
    if VOICE == "chatterbox":
        return "chatterbox"
    return "piper" if os.path.exists(MODEL) else "espeak"


def synth(text):
    """Renvoie l'audio (float32, 44,1 kHz) de la phrase."""
    audio, rate = {"chatterbox": _synth_chatterbox, "piper": _synth_piper}.get(engine_name(), _synth_espeak)(clean(text))
    if rate != SR:
        x = np.linspace(0, len(audio) - 1, int(len(audio) * SR / rate))
        audio = np.interp(x, np.arange(len(audio)), audio).astype(np.float32)
    # retire les silences au début et à la fin
    idx = np.where(np.abs(audio) > 0.01)[0]
    if len(idx):
        audio = audio[max(0, idx[0] - 200): idx[-1] + 1200]
    if TEMPO != 1.0:
        audio = _tempo(audio, TEMPO)
    return audio


def _tempo(audio, factor):
    import tempfile
    with tempfile.TemporaryDirectory() as d:
        src, dst = os.path.join(d, "a.wav"), os.path.join(d, "b.wav")
        write_wav(src, audio)
        subprocess.run(["ffmpeg", "-loglevel", "error", "-y", "-i", src, "-af", f"atempo={factor:.3f}", dst], check=True)
        with wave.open(dst) as wf:
            return np.frombuffer(wf.readframes(wf.getnframes()), np.int16).astype(np.float32) / 32768


def megaphone(track, tmpdir):
    """Applique l'effet mégaphone à une piste mono float32."""
    src = os.path.join(tmpdir, "voice_raw.wav")
    dst = os.path.join(tmpdir, "voice_fx.wav")
    write_wav(src, track)
    subprocess.run(["ffmpeg", "-loglevel", "error", "-y", "-i", src, "-af", {"leger": LIGHT, "aucun": NONE, "cinema": CINEMA, "radio": RADIO, "radio_douce": RADIO_SOFT}.get(FX, MEGAPHONE), "-ar", str(SR), "-ac", "1", dst], check=True)
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
