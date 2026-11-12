"""Monte un « film de fruits » ANIMÉ à partir des clips Kaggle (engine/kaggle_film.py).

python3 engine/film_anim.py episodes/film-NNN.json /tmp/film-NNN-clips /tmp/film-NNN.mp4
  (FILM_VOICE=0 : sans voix, essai rapide ; FILM_STILL=t : une seule image PNG au temps t)

Chaque plan = le clip shot-XX.mp4 (4 s, 480×864) agrandi en 1080×1920, coupé à la longueur
de la réplique (va-et-vient si la réplique est plus longue que le clip ; les 10 dernières
images, parfois abîmées, ne sont jamais montrées). Voix Chatterbox (fruits.say), sous-titres
1-3 mots, accroche sur le 1er plan, bandeau facultatif, musique de suspense, « À SUIVRE… ».
"""
import json
import os
import subprocess
import sys
import tempfile
import zlib

import numpy as np
from PIL import Image, ImageDraw, ImageFilter

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import fruits  # noqa: E402
from film import knock, suspense  # noqa: E402

W, H, FPS, SR = 1080, 1920, 30, 44100
CLIP_FPS, DROP = 24, 10
CX = 540
YELLOW, WHITE = (255, 214, 10), (255, 255, 255)


def load_clip(path):
    """Images du clip (480×864, RGB) sans les dernières, souvent ratées."""
    w, h = 480, 864
    raw = subprocess.run(["ffmpeg", "-loglevel", "error", "-i", path, "-vf", f"scale={w}:{h}", "-f", "rawvideo",
                          "-pix_fmt", "rgb24", "-"], capture_output=True, check=True).stdout
    fr = np.frombuffer(raw, np.uint8).reshape(-1, h, w, 3)
    return fr[: max(8, len(fr) - DROP)]


def pick(n, lt):
    """Index d'image du clip au temps lt : lecture normale puis va-et-vient (jamais de saut)."""
    k = int(lt * CLIP_FPS)
    period = 2 * (n - 1)
    k %= period
    return k if k < n else period - k


def render(spec_path, clip_dir, out):
    spec = json.load(open(spec_path))
    seed = zlib.crc32(os.path.basename(spec_path).encode())
    shots = spec["shots"]
    voice_on = os.environ.get("FILM_VOICE", "1") != "0"
    if not voice_on:
        os.environ["FRUITS_VOICE"] = "0"
    for i, sh in enumerate(shots):
        c = spec["cast"][sh["who"]]
        sh["audio"], _ = fruits.say(sh.get("voice", sh["text"]), c["voix"], sh.get("retry", 0))
        sh["dur"] = len(sh["audio"]) / SR + 0.18
        sh["clip"] = os.path.join(clip_dir, f"shot-{i:02d}.mp4")
        sh["chunks"] = fruits.chunks(sh["text"])
        print(f"  voix {i + 1}/{len(shots)}", file=sys.stderr, flush=True)
    end_dur = 2.2
    total = sum(s["dur"] for s in shots) + end_dur
    voice_tr = np.zeros(int((total + 1) * SR), np.float32)
    fx_tr = np.zeros_like(voice_tr)
    pos = 0.0
    for sh in shots:
        sh["t0"] = pos
        a = int(pos * SR)
        voice_tr[a:a + len(sh["audio"])] += sh["audio"]
        if sh.get("sfx"):
            s = knock() if sh["sfx"] == "knock" else fruits.sfx(sh["sfx"])
            fx_tr[a:a + len(s)] += s[: len(fx_tr) - a]
        pos += sh["dur"]
    t_end = pos
    mix = voice_tr + fx_tr * 0.9 + suspense(len(voice_tr) / SR, seed) * (0.55 if voice_on else 1)

    cache = {}

    def clip(i):
        if i not in cache:
            cache.clear()  # un seul clip en mémoire
            cache[i] = load_clip(shots[i]["clip"])
        return cache[i]

    last_img = [None]

    def frame(t):
        if t >= t_end:
            fade = min(1, (t - t_end) / 0.4)
            if np.asarray(last_img[0]).mean() < 70:  # dernier plan trop sombre → on reprend le 1er plan
                last_img[0] = Image.fromarray(load_clip(shots[0]["clip"])[0]).resize((W, H), Image.LANCZOS)
            im = Image.blend(last_img[0].filter(ImageFilter.GaussianBlur(14)), Image.new("RGB", (W, H)), 0.55 + 0.15 * fade).convert("RGBA")
            d = ImageDraw.Draw(im)
            fruits.text_c(d, (CX, 900), spec.get("end", "À SUIVRE…"), 110, tuple(int(c * fade) for c in YELLOW), 0)
            if spec.get("end_sub"):
                fruits.text_c(d, (CX, 1040), spec["end_sub"], 60, tuple(int(c * fade) for c in WHITE), 0)
            return im
        i = max(k for k, s in enumerate(shots) if s["t0"] <= t)
        sh = shots[i]
        lt = t - sh["t0"]
        fr = clip(i)
        bg = Image.fromarray(fr[pick(len(fr), lt)]).resize((W, H), Image.LANCZOS)
        bg = bg.filter(ImageFilter.UnsharpMask(radius=2, percent=60, threshold=2))
        last_img[0] = bg
        bg = bg.convert("RGBA")
        d = ImageDraw.Draw(bg)
        if i == 0 and spec.get("hook"):
            fruits.text_c(d, (CX, 230), spec["hook"], 80, YELLOW, 9)
        if sh.get("banner"):
            d.rectangle((0, 1380, W, 1500), fill=(200, 20, 30))
            fruits.text_c(d, (CX, 1440), sh["banner"], 90, WHITE, 0)
        speak = sh["dur"] - 0.18
        lens = np.cumsum([len(c) + 2 for c in sh["chunks"]])
        kk = int(np.searchsorted(lens / lens[-1], min(0.999, lt / max(0.1, speak)), side="right"))
        fruits.text_c(d, (CX, 1220), sh["chunks"][min(kk, len(sh["chunks"]) - 1)].upper(), 76, WHITE, 8)
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
