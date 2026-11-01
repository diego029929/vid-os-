"""Voix des personnages : edge-tts (voix neuronales Microsoft, gratuites, sans clé).

Chaque réplique donne un fichier WAV et la liste des mots avec leur instant
de début et de fin (en secondes), pour caler les sous-titres mot à mot.

FAKE_TTS=1 génère du silence avec des timings simulés (tests hors ligne).
"""
import asyncio
import json
import os
import re
import subprocess

SR = 44100


def _probe_duration(path):
    out = subprocess.check_output(
        ["ffprobe", "-v", "error", "-show_entries", "format=duration",
         "-of", "default=nw=1:nk=1", path])
    return float(out.strip())


def _to_wav(src, dst, tempo=1.0):
    af = f"atempo={tempo}," if abs(tempo - 1.0) > 1e-3 else ""
    # léger « punch » : compression + normalisation pour une voix TikTok bien présente
    af += "acompressor=threshold=-18dB:ratio=3:attack=5:release=80,loudnorm=I=-14:TP=-1.5:LRA=7"
    subprocess.run(["ffmpeg", "-v", "error", "-y", "-i", src, "-af", af,
                    "-ar", str(SR), "-ac", "1", dst], check=True)


async def _edge(text, voice, rate, pitch, mp3):
    import edge_tts
    com = edge_tts.Communicate(text, voice, rate=rate, pitch=pitch, boundary="WordBoundary")
    words = []
    with open(mp3, "wb") as fh:
        async for chunk in com.stream():
            if chunk["type"] == "audio":
                fh.write(chunk["data"])
            elif chunk["type"] == "WordBoundary":
                start = chunk["offset"] / 1e7
                words.append({"w": chunk["text"], "start": start,
                              "end": start + chunk["duration"] / 1e7})
    return words


def _fake(text, wav):
    words, t = [], 0.0
    for w in text.split():
        d = 0.12 + 0.055 * len(w)
        words.append({"w": w, "start": t, "end": t + d})
        t += d + 0.04
    subprocess.run(["ffmpeg", "-v", "error", "-y", "-f", "lavfi", "-i",
                    f"anullsrc=r={SR}:cl=mono", "-t", f"{t + 0.1:.3f}", wav], check=True)
    return words


def speak(text, voice, wav, rate="+0%", pitch="+0Hz", tempo=1.0, retries=4):
    """Écrit `wav` et renvoie (durée, mots)."""
    if os.environ.get("FAKE_TTS") == "1":
        words = _fake(text, wav)
        return _probe_duration(wav), words
    mp3 = wav[:-4] + ".mp3"
    last = None
    for attempt in range(retries):
        try:
            words = asyncio.run(_edge(text, voice, rate, pitch, mp3))
            if not words or os.path.getsize(mp3) < 1000:
                raise RuntimeError("réponse TTS vide")
            break
        except Exception as exc:  # réseau capricieux : on réessaie
            last = exc
            import time
            time.sleep(2 + 3 * attempt)
    else:
        raise RuntimeError(f"edge-tts a échoué pour « {text} » : {last}")
    _to_wav(mp3, wav, tempo)
    os.remove(mp3)
    if abs(tempo - 1.0) > 1e-3:
        for w in words:
            w["start"] /= tempo
            w["end"] /= tempo
    # edge-tts renvoie les mots sans ponctuation : on la récupère dans le texte
    tokens = text.split()
    if len(tokens) == len(words):
        for w, tok in zip(words, tokens):
            w["w"] = tok
    else:
        _realign(words, text)
    return _probe_duration(wav), words


def _realign(words, text):
    """Recolle la ponctuation du texte original sur les mots renvoyés."""
    pos = 0
    for w in words:
        i = text.find(w["w"], pos)
        if i < 0:
            continue
        j = i + len(w["w"])
        m = re.match(r"[^\s\w]*", text[j:])
        if m and m.group(0):
            w["w"] += m.group(0)
            j += len(m.group(0))
        pos = j


if __name__ == "__main__":
    import sys
    d, ws = speak(sys.argv[1], sys.argv[2] if len(sys.argv) > 2 else "fr-FR-HenriNeural", "/tmp/tts_test.wav")
    print(d, json.dumps(ws, ensure_ascii=False))
