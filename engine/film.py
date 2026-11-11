"""« Films de fruits » (modèle envoyé par Fio le 11/11) : humains réalistes à tête de fruit,
vrais décors, une histoire à idée forte, un plan par réplique, « À SUIVRE… » à la fin.

1) Images : /tmp/sdenv/bin/python engine/film_images.py episodes/film-NNN.json /tmp/film-NNN-img
2) Vidéo  : python3 engine/film.py episodes/film-NNN.json /tmp/film-NNN-img /tmp/film-NNN.mp4
   (FILM_VOICE=0 : sans voix, pour un essai rapide ; FILM_STILL=t : une seule image PNG)

Le décor et le corps viennent de SDXL-Turbo (gratuit, sur CPU). La tête de fruit est
dessinée par engine/fruits.py et posée sur le visage détecté ; sa bouche bouge avec la voix.

JSON :
{
  "type": "film", "title": "...", "caption": "...",
  "hook": "IL REÇOIT DES SMS DE DEMAIN",            (en haut sur le 1er plan, ≤ 26 car.)
  "cast": {
    "nico": {"fruit": "poire", "nom": "Nico", "voix": "homme1",
             "look": "a young man with short brown hair, black sweater and jeans"}
  },
  "shots": [
    {"who": "nico", "text": "Ce message vient de moi.", "emo": "surpris",
     "lieu": "in a small bedroom in the morning", "action": "holding a smartphone",
     "sfx": "dun", "banner": "FLASH SPÉCIAL", "retry": 0, "seed": 0},
    {"who": "nico", "off": true, "text": "...", "lieu": "a dark apartment front door at night"}
  ],
  "end": "À SUIVRE…"
}
- look : TOUJOURS la même description pour un perso (vêtements compris), en anglais.
- lieu / action : en anglais (c'est le texte donné au générateur d'images).
- off : la voix parle hors champ (image sans personnage).
"""
import json
import math
import os
import subprocess
import sys
import tempfile
import zlib

import numpy as np
from PIL import Image, ImageDraw, ImageFilter

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import fruits  # noqa: E402

W, H, FPS, SR = 1080, 1920, 30, 44100
CX = 505
YELLOW, WHITE = (255, 214, 10), (255, 255, 255)


def head_sprite(kind, emo, mouth, blink, t):
    if kind not in fruits._cache:
        fruits._cache[kind] = fruits.make_fruit(kind)
    base, fc, fs, blush = fruits._cache[kind]
    im = base.copy()
    fruits.draw_face(im, fc, fs, emo, mouth, blink, (0, 0.1), blush, t)
    a = np.asarray(im.split()[3])
    xs = np.nonzero(a.max(0) > 100)[0]
    ys = np.nonzero(a.max(1) > 100)[0]
    return im, fc, (xs.min(), xs.max(), ys.min(), ys.max())


def suspense(dur, seed):
    """Nappe grave + battement lent, générée (libre de droits)."""
    n = int(dur * SR)
    t = np.arange(n) / SR
    out = 0.035 * (np.sin(2 * np.pi * 55 * t) + 0.6 * np.sin(2 * np.pi * 82.4 * t) + 0.4 * np.sin(2 * np.pi * 110.3 * t))
    out *= 0.6 + 0.4 * np.sin(2 * np.pi * 0.15 * t)
    beat = 60 / 70
    for k in range(int(dur / beat)):
        a = int(k * beat * SR)
        m = min(n - a, int(0.25 * SR))
        tt = np.arange(m) / SR
        out[a:a + m] += 0.18 * np.sin(2 * np.pi * (48 + 30 * np.exp(-tt * 25)) * tt) * np.exp(-tt * 14)
    return out.astype(np.float32)


def knock():
    t = np.arange(int(1.2 * SR)) / SR
    out = np.zeros_like(t)
    for st in (0, 0.28, 0.56):
        a = int(st * SR)
        tt = t[: len(t) - a]
        out[a:] += (np.sin(2 * np.pi * 120 * tt) + np.random.default_rng(int(st * 100)).standard_normal(len(tt)) * 0.3) * np.exp(-tt * 35)
    return (out * 0.5).astype(np.float32)


def render(spec_path, img_dir, out):
    spec = json.load(open(spec_path))
    faces = json.load(open(os.path.join(img_dir, "faces.json")))
    seed = zlib.crc32(os.path.basename(spec_path).encode())
    shots = spec["shots"]
    voice_on = os.environ.get("FILM_VOICE", "1") != "0"
    if not voice_on:
        os.environ["FRUITS_VOICE"] = "0"
    for i, sh in enumerate(shots):
        c = spec["cast"][sh["who"]]
        sh["audio"], _ = fruits.say(sh.get("voice", sh["text"]), c["voix"], sh.get("retry", 0))
        sh["dur"] = len(sh["audio"]) / SR + 0.22
        sh["img"] = Image.open(os.path.join(img_dir, f"shot-{i:02d}.png")).convert("RGB")
        sh["face"] = faces.get(f"shot-{i:02d}.png")
        print(f"  voix {i + 1}/{len(shots)}", file=sys.stderr, flush=True)
    end_dur = 2.0
    total = sum(s["dur"] for s in shots) + end_dur
    voice_tr = np.zeros(int((total + 1) * SR), np.float32)
    fx_tr = np.zeros_like(voice_tr)
    pos = 0.0
    for sh in shots:
        sh["t0"] = pos
        a = int(pos * SR)
        voice_tr[a:a + len(sh["audio"])] += sh["audio"]
        s = {"knock": knock}.get(sh.get("sfx"), lambda: fruits.sfx(sh["sfx"]) if sh.get("sfx") else np.zeros(1, np.float32))()
        fx_tr[a:a + len(s)] += s[: len(fx_tr) - a]
        pos += sh["dur"]
    t_end = pos
    mix = voice_tr + fx_tr * 0.9 + suspense(len(voice_tr) / SR, seed) * (0.6 if voice_on else 1)
    for sh in shots:
        sh["env"] = fruits.envelope(sh["audio"])
        sh["chunks"] = fruits.chunks(sh["text"])
    rnd = np.random.default_rng(seed)
    blinks = sorted(rnd.uniform(0, total, int(total / 2.6)))

    def frame(t):
        if t >= t_end:
            fade = min(1, (t - t_end) / 0.4)
            last = shots[-1]["img"].resize((W, H), Image.BICUBIC).filter(ImageFilter.GaussianBlur(12))
            im = Image.blend(last, Image.new("RGB", (W, H), (0, 0, 0)), 0.55 + 0.15 * fade).convert("RGBA")
            d = ImageDraw.Draw(im)
            fruits.text_c(d, (CX, 900), spec.get("end", "À SUIVRE…"), 110, tuple(int(c * fade) for c in YELLOW), 0)
            if spec.get("end_sub"):
                fruits.text_c(d, (CX, 1040), spec["end_sub"], 60, tuple(int(c * fade) for c in WHITE), 0)
            return im
        i = max(k for k, s in enumerate(shots) if s["t0"] <= t)
        sh = shots[i]
        lt = t - sh["t0"]
        # caméra : lent zoom avant (ou arrière un plan sur deux)
        z0, z1 = (1.0, 1.07) if i % 2 == 0 else (1.07, 1.0)
        z = z0 + (z1 - z0) * min(1, lt / max(0.5, sh["dur"]))
        sw, shh = sh["img"].size
        cw, ch = sw / z, shh / z
        fx = (sh["face"][0] + sh["face"][2] / 2) if sh["face"] else sw / 2
        cx0 = min(max(0, fx - cw / 2), sw - cw)
        cy0 = (shh - ch) * 0.1
        bg = sh["img"].resize((W, H), Image.BICUBIC, box=(cx0, cy0, cx0 + cw, cy0 + ch)).convert("RGBA")
        k = W / cw
        if sh["face"] and not sh.get("off"):
            x, y, w, h = sh["face"]
            c = spec["cast"][sh["who"]]
            mouth = float(sh["env"][int(lt * FPS)]) if int(lt * FPS) < len(sh["env"]) else 0
            bl = any(0 <= t - b < 0.12 for b in blinks)
            hd, fc, (bx0, bx1, by0, by1) = head_sprite(c["fruit"], sh.get("emo", "neutre"), mouth, bl, t)
            target_w = w * 1.75 * k
            s = target_w / (bx1 - bx0)
            hs = hd.resize((int(hd.width * s), int(hd.height * s)), Image.BICUBIC)
            # lumière du décor autour du visage
            reg = np.asarray(sh["img"].crop((x - w, y - h, x + 2 * w, y + 2 * h)).convert("L"), np.float32)
            lum = float(np.clip(reg.mean() / 150, 0.65, 1.08))
            if lum < 0.99:
                r, g, b, a = hs.split()
                rgb = Image.merge("RGB", (r, g, b)).point(lambda v: int(v * lum))
                hs = Image.merge("RGBA", (*rgb.split(), a))
            # centre du visage du fruit sur le centre du visage détecté (un peu plus haut : le fruit couvre les cheveux)
            fcx, fcy = (x + w / 2 - cx0) * k, (y + h * 0.5 - cy0) * k
            bob = math.sin(t * 8) * 4 * mouth
            px, py = fcx - fc[0] * s, fcy - fc[1] * s - bob
            # ombre douce sur le cou
            shadow = Image.new("RGBA", (int(target_w * 0.8), int(target_w * 0.25)), (0, 0, 0, 0))
            ImageDraw.Draw(shadow).ellipse((0, 0, shadow.width, shadow.height), fill=(0, 0, 0, 110))
            shadow = shadow.filter(ImageFilter.GaussianBlur(14))
            bg.alpha_composite(shadow, (int(fcx - shadow.width / 2), int(py + by1 * s - shadow.height * 0.45)))
            bg.alpha_composite(hs, (int(px), int(py)))
        d = ImageDraw.Draw(bg)
        if i == 0 and spec.get("hook"):
            fruits.text_c(d, (CX, 210), spec["hook"], 80, YELLOW, 9)
        if sh.get("banner"):
            d.rectangle((0, 1380, W, 1500), fill=(200, 20, 30))
            fruits.text_c(d, (CX, 1440), sh["banner"], 90, WHITE, 0)
        # sous-titres
        speak = sh["dur"] - 0.22
        lens = np.cumsum([len(c) + 2 for c in sh["chunks"]])
        kk = int(np.searchsorted(lens / lens[-1], min(0.999, lt / max(0.1, speak)), side="right"))
        kk = min(kk, len(sh["chunks"]) - 1)
        fruits.text_c(d, (CX, 1180), sh["chunks"][kk].upper(), 80, WHITE, 8)
        if lt < 0.12 and i > 0:  # coupe franche : petit flash
            bg.alpha_composite(Image.new("RGBA", (W, H), (255, 255, 255, int(60 * (1 - lt / 0.12)))))
        return bg

    if os.environ.get("FILM_STILL"):
        frame(float(os.environ["FILM_STILL"])).convert("RGB").save(out)
        return
    with tempfile.TemporaryDirectory() as tmp:
        wav = os.path.join(tmp, "a.wav")
        fruits.write_wav(wav, mix[: int(total * SR)] * 0.8)
        cmd = ["ffmpeg", "-loglevel", "error", "-y", "-f", "rawvideo", "-pix_fmt", "rgb24", "-s", f"{W}x{H}",
               "-r", str(FPS), "-i", "-", "-i", wav, "-c:v", "libx264", "-preset", "medium", "-crf", "20",
               "-pix_fmt", "yuv420p", "-c:a", "aac", "-b:a", "160k",
               "-af", "acompressor=threshold=-20dB:ratio=3:attack=3:release=120,loudnorm=I=-14:TP=-1.5:LRA=9,aresample=44100",
               "-shortest", "-movflags", "+faststart", out]
        p = subprocess.Popen(cmd, stdin=subprocess.PIPE)
        nf = int(total * FPS)
        for f in range(nf):
            p.stdin.write(np.asarray(frame(f / FPS).convert("RGB")).tobytes())
            if f % 300 == 0:
                print(f"  image {f}/{nf}", file=sys.stderr, flush=True)
        p.stdin.close()
        if p.wait():
            raise SystemExit("ffmpeg a échoué")
    print(f"OK {out} ({total:.1f} s)")


if __name__ == "__main__":
    render(sys.argv[1], sys.argv[2], sys.argv[3])
