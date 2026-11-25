"""« Tu préfères 🔴 ou 🔵 ? » : écran coupé en deux, voix, compte à rebours, pourcentages.

Format copié sur ce qui marche en France (@tu.prefere.quoii6, ≈ 680 000 vues
médianes en 2026) mais 100 % fabriqué ici : emojis + texte, voix Chatterbox.

Déroulé (≈ 60 s pour 7 dilemmes) :
  0 s     accroche lue (« On va voir si t'as des bons goûts ») PENDANT que le
          1er dilemme est déjà à l'écran (rien d'inutile avant la 1re seconde) ;
  chaque dilemme : la voix lit « Tu préfères A, ou B ? » → 3-2-1 dans la
  pastille VS (tic-tac) → les pourcentages se remplissent (ding) → suivant.
Les pourcentages sont une estimation écrite par Claude (affichée comme telle).

JSON : {"theme": "...", "hook": "On va voir si t'as des bons goûts",
        "items": [{"a": "Pouvoir voler", "a_emoji": "🦅", "b": "Être invisible",
                   "b_emoji": "👻", "pa": 58, "voice": "(facultatif)"}],
        "end": "Commente ton score : combien de 🔴 ?"}

Usage : python3 engine/tupreferes.py episodes/tp-001.json sortie.mp4
"""
import json
import math
import os
import subprocess
import sys
import tempfile
import wave

import numpy as np
from PIL import Image, ImageDraw, ImageFont

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, os.path.join(ROOT, "engine"))
FONT = os.path.join(ROOT, "assets", "fonts", "Anton-Regular.ttf")
EMOJI_FONT = "/usr/share/fonts/truetype/noto/NotoColorEmoji.ttf"
W, H, FPS, SR = 1080, 1920, 30, 44100
MID = H // 2
RED, RED_D = (232, 52, 72), (150, 20, 40)
BLUE, BLUE_D = (40, 110, 255), (16, 50, 150)
COUNT = 3.0            # durée du 3-2-1
REVEAL = 1.6           # durée de l'affichage des pourcentages

_fonts, _emo = {}, {}


def font(size):
    if size not in _fonts:
        _fonts[size] = ImageFont.truetype(FONT, size)
    return _fonts[size]


def emoji(ch, size):
    key = (ch, size)
    if key not in _emo:
        f = ImageFont.truetype(EMOJI_FONT, 109)
        im = Image.new("RGBA", (200, 200), (0, 0, 0, 0))
        ImageDraw.Draw(im).text((100, 100), ch, font=f, embedded_color=True, anchor="mm")
        bb = im.getbbox()
        if not bb:
            raise SystemExit(f"Emoji illisible : {ch!r}")
        im = im.crop(bb)
        s = size / max(im.size)
        _emo[key] = im.resize((max(1, int(im.width * s)), max(1, int(im.height * s))), Image.LANCZOS)
    return _emo[key]


def wrap(d, txt, size, maxw):
    words, lines, cur = txt.split(), [], ""
    for w_ in words:
        t = (cur + " " + w_).strip()
        if d.textlength(t, font=font(size)) <= maxw or not cur:
            cur = t
        else:
            lines.append(cur)
            cur = w_
    lines.append(cur)
    return lines


def label(d, cx, cy, txt, size=78, maxw=900):
    while True:
        lines = wrap(d, txt.upper(), size, maxw)
        if len(lines) <= 2 or size <= 44:
            break
        size -= 6
    if len(lines) == 2:          # équilibrer les 2 lignes (pas de mot seul en bas)
        ws = txt.upper().split()
        best = min(range(1, len(ws)), key=lambda i: max(d.textlength(" ".join(ws[:i]), font=font(size)),
                                                      d.textlength(" ".join(ws[i:]), font=font(size))))
        lines = [" ".join(ws[:best]), " ".join(ws[best:])]
    lh = int(size * 1.12)
    y0 = cy - lh * (len(lines) - 1) / 2
    for i, ln in enumerate(lines):
        d.text((cx, y0 + i * lh), ln, font=font(size), fill=(255, 255, 255), anchor="mm",
               stroke_width=7, stroke_fill=(0, 0, 0))


# ---------------------------------------------------------------- son

def env_tone(freq, dur, vol, decay=8, harm=0.3):
    t = np.arange(int(SR * dur)) / SR
    w = np.sin(2 * np.pi * freq * t) + harm * np.sin(4 * np.pi * freq * t)
    return (w * np.exp(-t * decay) * np.minimum(1, t * 500) * vol).astype(np.float32)


def tick():
    n = int(SR * 0.05)
    rnd = np.random.default_rng(3)
    return (rnd.standard_normal(n) * np.exp(-np.arange(n) / SR * 90) * 0.25).astype(np.float32) + env_tone(1800, 0.05, 0.15, 60)


def ding():
    return env_tone(1318.5, 0.9, 0.25, 5) + env_tone(1975.5, 0.9, 0.12, 6)


def whoosh():
    n = int(SR * 0.35)
    rnd = np.random.default_rng(5)
    x = rnd.standard_normal(n).astype(np.float32)
    k = np.ones(40) / 40
    x = np.convolve(x, k, mode="same")
    e = np.sin(np.linspace(0, np.pi, n)) ** 2
    return (x * e * 0.5).astype(np.float32)


def music(total_s):
    """Petite boucle légère (basse + charleston) pour ne pas avoir de silence."""
    n = int(SR * total_s)
    out = np.zeros(n, np.float32)
    bpm = 112
    beat = 60 / bpm
    bass = [55.0, 55.0, 65.41, 73.42, 49.0, 49.0, 65.41, 61.74]
    i = 0
    t = 0.0
    while t < total_s:
        a = int(t * SR)
        s = env_tone(bass[i % len(bass)], beat * 0.9, 0.18, 3, 0.6)
        out[a:a + len(s)] += s[: n - a]
        h = int((t + beat / 2) * SR)
        hh = (np.random.default_rng(i).standard_normal(int(SR * 0.04)) * np.exp(-np.arange(int(SR * 0.04)) / SR * 120) * 0.05).astype(np.float32)
        out[h:h + len(hh)] += hh[: max(0, n - h)]
        t += beat
        i += 1
    return out


def add(track, clip, at):
    a = int(at * SR)
    if a >= len(track):
        return
    track[a:a + len(clip)] += clip[: len(track) - a]


# ---------------------------------------------------------------- voix

def say(text, cache):
    import voice
    key = text
    if key not in cache:
        cache[key] = voice.synth(text)
    return cache[key]


def build(ep, tmp):
    import voice
    if ep.get("ref"):
        voice.CB_REF = os.path.join(ROOT, "assets", "ref", ep["ref"])
    cache = {}
    hook = say(ep.get("hook", "On va voir si t'as des bons goûts."), cache)
    clips = []
    for it in ep["items"]:
        txt = it.get("voice") or f"Tu préfères {it['a'].lower()}, ou {it['b'].lower()} ?"
        clips.append(say(txt, cache))
    end = say(ep.get("end_voice", "Alors, t'as eu combien de rouges ? Dis-le en commentaire."), cache)
    # plan temporel
    t = len(hook) / SR + 0.15
    seg = []
    for c in clips:
        v0 = t
        v1 = v0 + len(c) / SR
        c0 = v1 + 0.1
        r0 = c0 + COUNT
        r1 = r0 + REVEAL
        seg.append((v0, v1, c0, r0, r1))
        t = r1
    end0 = t
    total = end0 + len(end) / SR + 1.6
    return hook, clips, end, seg, end0, total


# ---------------------------------------------------------------- image

def stripes(col, dark, phase, y0, y1):
    im = Image.new("RGB", (W, y1 - y0), col)
    d = ImageDraw.Draw(im)
    step = 90
    off = int(phase) % (step * 2)
    lite = tuple(min(255, c + 14) for c in col)
    for x in range(-H, W + H, step * 2):
        xx = x + off
        d.polygon([(xx, 0), (xx + step, 0), (xx + step - (y1 - y0), y1 - y0), (xx - (y1 - y0), y1 - y0)], fill=lite)
    # assombrir les bords
    return im


def ease_back(x):
    x = max(0, min(1, x))
    c = 1.70158
    return 1 + (c + 1) * (x - 1) ** 3 + c * (x - 1) ** 2


def frame(ep, f, seg, end0, total):
    t = f / FPS
    items = ep["items"]
    # dilemme courant
    k = 0
    for i, s in enumerate(seg):
        if t >= s[0] - 0.0001 or i == 0:
            k = i
    if t >= end0:
        k = len(items) - 1
    it = items[k]
    v0, v1, c0, r0, r1 = seg[k]
    im = Image.new("RGB", (W, H))
    im.paste(stripes(RED, RED_D, t * 40, 0, MID), (0, 0))
    im.paste(stripes(BLUE, BLUE_D, -t * 40, MID, H), (0, MID))
    d = ImageDraw.Draw(im)
    # révélation : barre qui se remplit + pourcentages
    rv = 0 if t < r0 else min(1, (t - r0) / 0.6)
    pa = it.get("pa", 50)
    pb = 100 - pa
    if rv > 0:
        for (y0, y1, p, dark) in ((0, MID, pa, RED_D), (MID, H, pb, BLUE_D)):
            wfill = int(W * p / 100 * rv)
            ov = Image.new("RGBA", (W, y1 - y0), (0, 0, 0, 0))
            ImageDraw.Draw(ov).rectangle((0, 0, wfill, y1 - y0), fill=dark + (150,))
            im.paste(ov, (0, y0), ov)
        d = ImageDraw.Draw(im)
    # contenu des deux moitiés (pop à l'arrivée)
    pop = ease_back((t - v0 + 0.25) / 0.35) if k > 0 or t > 0.05 else 1
    if k == 0:
        pop = 1
    bob = math.sin(t * 3.2) * 10
    for (cy, em, txt, p, sgn) in ((MID // 2 + 10, it["a_emoji"], it["a"], pa, 1),
                                   (MID + MID // 2 - 30, it["b_emoji"], it["b"], pb, -1)):
        size = max(10, int(330 * pop))
        e = emoji(em, size)
        ey = int(cy - 120 + sgn * bob)
        im.paste(e, (W // 2 - e.width // 2, ey - e.height // 2), e)
        label(d, W // 2, cy + 140, txt)
        if rv > 0:
            pct = int(round(p * rv))
            col = (255, 230, 90) if p >= 50 else (255, 255, 255)
            d.text((W - 70, cy - 120), f"{pct} %", font=font(120), fill=col, anchor="rm",
                   stroke_width=8, stroke_fill=(0, 0, 0))
    # compteur 1/7 et thème (haut, sous la barre de recherche TikTok)
    d.text((70, 230), f"{k + 1}/{len(items)}", font=font(70), fill=(255, 255, 255), anchor="lm",
           stroke_width=6, stroke_fill=(0, 0, 0))
    if ep.get("theme"):
        d.text((W - 70, 230), ep["theme"].upper(), font=font(52), fill=(255, 255, 255), anchor="rm",
               stroke_width=6, stroke_fill=(0, 0, 0))
    # pastille centrale : VS / 3-2-1
    r = 120
    if c0 <= t < r0:
        n = 3 - int((t - c0) / (COUNT / 3))
        frac = ((t - c0) % (COUNT / 3)) / (COUNT / 3)
        rr = int(r * (1.18 - 0.18 * frac))
        d.ellipse((W // 2 - rr, MID - rr, W // 2 + rr, MID + rr), fill=(255, 255, 255), outline=(0, 0, 0), width=8)
        # anneau de progression
        d.arc((W // 2 - rr - 16, MID - rr - 16, W // 2 + rr + 16, MID + rr + 16), -90, -90 + 360 * frac,
              fill=(255, 214, 64), width=14)
        d.text((W // 2, MID), str(max(1, n)), font=font(150), fill=(20, 20, 20), anchor="mm")
    else:
        d.ellipse((W // 2 - r, MID - r, W // 2 + r, MID + r), fill=(20, 20, 20), outline=(255, 255, 255), width=8)
        d.text((W // 2, MID + 4), "VS", font=font(110), fill=(255, 255, 255), anchor="mm")
    # accroche (au-dessus de tout, les 2 premières secondes)
    if t < seg[0][0]:
        bw = 940
        d.rounded_rectangle((W // 2 - bw // 2, MID - 75, W // 2 + bw // 2, MID + 75), 30, fill=(0, 0, 0))
        d.text((W // 2, MID), ep.get("hook_text", "T'AS BON GOÛT ?").upper(), font=font(84),
               fill=(255, 214, 64), anchor="mm")
    if rv > 0 and t < r1 + 0.01 and k < len(items) and ep.get("estime", True):
        d.text((W // 2, 232), "(estimation)", font=font(40), fill=(255, 255, 255), anchor="mm")
    # fin
    if t >= end0:
        a = min(1, (t - end0) / 0.3)
        ov = Image.new("RGBA", (W, H), (0, 0, 0, int(235 * a)))
        im.paste(ov, (0, 0), ov)
        d = ImageDraw.Draw(im)
        label(d, W // 2, MID - 140, ep.get("end", "T'AS EU COMBIEN DE 🔴 ?").replace("🔴", "ROUGES"), 110)
        e = emoji("👇", 200)
        im.paste(e, (W // 2 - e.width // 2, MID + 80), e)
    return im


def render(ep, out):
    tmp = tempfile.mkdtemp()
    hook, clips, end, seg, end0, total = build(ep, tmp)
    import voice
    n = int(total * SR) + SR
    vtrack = np.zeros(n, np.float32)
    add(vtrack, hook, 0.0)
    for c, s in zip(clips, seg):
        add(vtrack, c, s[0])
    add(vtrack, end, end0 + 0.2)
    vtrack = voice.megaphone(vtrack, tmp) if voice.FX != "aucun" else vtrack
    fx = np.zeros(n, np.float32)
    for i, s in enumerate(seg):
        if i:
            add(fx, whoosh(), s[0] - 0.1)
        for j in range(3):
            add(fx, tick(), s[2] + j * COUNT / 3)
        add(fx, ding(), s[3])
    mus = music(total + 1)[:n]
    mix = vtrack * 1.0 + fx * 0.9 + np.pad(mus, (0, max(0, n - len(mus))))[:n] * 0.6
    wav = os.path.join(tmp, "mix.wav")
    voice.write_wav(wav, mix / max(1e-6, np.abs(mix).max()) * 0.9)
    nf = int(total * FPS)
    proc = subprocess.Popen(
        ["ffmpeg", "-y", "-loglevel", "error", "-f", "rawvideo", "-pix_fmt", "rgb24", "-s", f"{W}x{H}",
         "-r", str(FPS), "-i", "-", "-i", wav,
         "-af", "loudnorm=I=-14:TP=-2:LRA=11,aresample=44100,alimiter=limit=0.7:level=false",
         "-c:v", "libx264", "-preset", "medium", "-crf", "20", "-pix_fmt", "yuv420p",
         "-c:a", "aac", "-b:a", "160k", "-shortest", "-movflags", "+faststart", out],
        stdin=subprocess.PIPE)
    for f in range(nf):
        proc.stdin.write(frame(ep, f, seg, end0, total).tobytes())
    proc.stdin.close()
    proc.wait()
    print(f"OK {out} : {total:.1f} s")


if __name__ == "__main__":
    render(json.load(open(sys.argv[1])), sys.argv[2])
