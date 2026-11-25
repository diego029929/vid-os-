"""« Histoire vraie en 40 s » : voix off grave, une image par phrase, sous-titres mot à mot.

Chaque phrase (« beat ») a son visuel :
  {"img": "chemin.jpg"}   photo d'archive (domaine public) en carte, zoom lent ;
  {"emoji": "💰"}          gros emoji qui respire ;
  {"big": "1925"}          date ou chiffre géant.
+ "key" : mot-clé géant affiché en haut (jaune), facultatif.
L'accroche (1re phrase) est aussi écrite en gros dès la 1re image.

JSON : {"hook_text": "IL A VENDU LA TOUR EIFFEL", "source": "Wikipédia : Victor Lustig",
        "beats": [{"text": "...", "img": "...", "key": "..."}], "end": "TU TE SERAIS FAIT AVOIR ?"}
Usage : python3 engine/histoire.py episodes/histoire-001.json sortie.mp4
"""
import json
import math
import os
import subprocess
import sys
import tempfile

import numpy as np
from PIL import Image, ImageDraw, ImageEnhance, ImageFilter, ImageFont, ImageOps

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, os.path.join(ROOT, "engine"))
FONT = os.path.join(ROOT, "assets", "fonts", "Anton-Regular.ttf")
EMOJI_FONT = "/usr/share/fonts/truetype/noto/NotoColorEmoji.ttf"
W, H, FPS, SR = 1080, 1920, 30, 44100
YELLOW = (255, 214, 64)
_fonts, _emo = {}, {}


def font(size):
    if size not in _fonts:
        _fonts[size] = ImageFont.truetype(FONT, size)
    return _fonts[size]


def emoji(ch, size):
    key = (ch, size)
    if key not in _emo:
        f = ImageFont.truetype(EMOJI_FONT, 109)
        im = Image.new("RGBA", (220, 220), (0, 0, 0, 0))
        ImageDraw.Draw(im).text((110, 110), ch, font=f, embedded_color=True, anchor="mm")
        im = im.crop(im.getbbox())
        s = size / max(im.size)
        _emo[key] = im.resize((max(1, int(im.width * s)), max(1, int(im.height * s))), Image.LANCZOS)
    return _emo[key]


def text_c(d, xy, txt, size, fill=(255, 255, 255), stroke=8, maxw=960):
    while size > 24 and d.textlength(txt, font=font(size)) > maxw:
        size -= 4
    d.text(xy, txt, font=font(size), fill=fill, anchor="mm", stroke_width=stroke, stroke_fill=(0, 0, 0))


def lines_c(d, cx, cy, txt, size, fill, maxw=940, stroke=8):
    words, lines, cur = txt.split(), [], ""
    for w_ in words:
        t = (cur + " " + w_).strip()
        if d.textlength(t, font=font(size)) <= maxw or not cur:
            cur = t
        else:
            lines.append(cur)
            cur = w_
    lines.append(cur)
    lh = int(size * 1.1)
    for i, ln in enumerate(lines):
        d.text((cx, cy + (i - (len(lines) - 1) / 2) * lh), ln, font=font(size), fill=fill, anchor="mm",
               stroke_width=stroke, stroke_fill=(0, 0, 0))


def archive(path):
    """Photo ancienne : sépia léger, contraste, cadre blanc."""
    im = Image.open(path).convert("RGB")
    g = ImageOps.grayscale(im)
    g = ImageOps.autocontrast(g, cutoff=1)
    sep = ImageOps.colorize(g, (30, 22, 14), (250, 236, 210))
    return sep


def background_from(img):
    bg = ImageOps.fit(img, (W, H), Image.LANCZOS).filter(ImageFilter.GaussianBlur(40))
    return ImageEnhance.Brightness(bg).enhance(0.35)


def grain(seed):
    rnd = np.random.default_rng(seed)
    n = rnd.normal(0, 14, (H // 2, W // 2)).astype(np.int16)
    return Image.fromarray(np.clip(n + 128, 0, 255).astype(np.uint8), "L").resize((W, H))


def vignette():
    v = Image.new("L", (W, H), 0)
    ImageDraw.Draw(v).ellipse((-300, -200, W + 300, H + 200), fill=255)
    return v.filter(ImageFilter.GaussianBlur(220))


def render(ep, out):
    import voice
    if ep.get("ref"):
        voice.CB_REF = os.path.join(ROOT, "assets", "ref", ep["ref"])
    tmp = tempfile.mkdtemp()
    beats = ep["beats"]
    clips = [voice.synth(b.get("voice", b["text"])) for b in beats]
    gap = 0.18
    starts, t = [], 0.0
    for c in clips:
        starts.append(t)
        t += len(c) / SR + gap
    end0 = t
    total = end0 + 2.8
    n = int(total * SR) + SR
    track = np.zeros(n, np.float32)
    for c, s in zip(clips, starts):
        a = int(s * SR)
        track[a:a + len(c)] += c[: n - a]
    track = voice.megaphone(track, tmp) if voice.FX != "aucun" else track
    # nappe grave + « boum » à chaque coupe
    tt = np.arange(n) / SR
    drone = (0.05 * np.sin(2 * np.pi * 55 * tt) + 0.03 * np.sin(2 * np.pi * 82.4 * tt)) * (0.6 + 0.4 * np.sin(2 * np.pi * 0.1 * tt))
    fx = np.zeros(n, np.float32)
    for s in starts[1:] + [end0]:
        a = int(s * SR)
        k = np.arange(int(0.5 * SR)) / SR
        hit = 0.35 * np.sin(2 * np.pi * (60 - 30 * k) * k) * np.exp(-k * 7)
        fx[a:a + len(hit)] += hit[: n - a]
    mix = track + drone.astype(np.float32) + fx
    wav = os.path.join(tmp, "mix.wav")
    voice.write_wav(wav, mix / max(1e-6, np.abs(mix).max()) * 0.9)

    # visuels préparés
    cache = {}
    first_img = next((b["img"] for b in beats if b.get("img")), None)
    base_bg = background_from(archive(first_img)) if first_img else Image.new("RGB", (W, H), (20, 16, 12))
    vig = vignette()
    dark = Image.new("RGB", (W, H), (0, 0, 0))
    grains = [grain(i) for i in range(6)]

    def card(path):
        if path not in cache:
            a = archive(path)
            bg = background_from(a)
            maxw, maxh = 940, 1000
            s = min(maxw / a.width, maxh / a.height)
            a = a.resize((int(a.width * s), int(a.height * s)), Image.LANCZOS)
            framed = ImageOps.expand(a, 18, fill=(245, 240, 228)).convert("RGBA")
            cache[path] = (bg, framed)
        return cache[path]

    proc = subprocess.Popen(
        ["ffmpeg", "-y", "-loglevel", "error", "-f", "rawvideo", "-pix_fmt", "rgb24", "-s", f"{W}x{H}",
         "-r", str(FPS), "-i", "-", "-i", wav,
         "-af", "loudnorm=I=-14:TP=-2:LRA=11,aresample=44100,alimiter=limit=0.7:level=false",
         "-c:v", "libx264", "-preset", "medium", "-crf", "20", "-pix_fmt", "yuv420p",
         "-c:a", "aac", "-b:a", "160k", "-shortest", "-movflags", "+faststart", out],
        stdin=subprocess.PIPE)
    nf = int(total * FPS)
    for f in range(nf):
        t = f / FPS
        k = max(i for i, s in enumerate(starts) if s <= t + 1e-6)
        b = beats[k]
        lt = t - starts[k]
        dur = len(clips[k]) / SR + gap
        if b.get("img"):
            bg, fr = card(b["img"])
            im = bg.copy()
            z = 1.0 + 0.10 * min(1, lt / max(dur, 1)) + (0.02 if k % 2 else 0)
            c = fr.resize((int(fr.width * z), int(fr.height * z)), Image.BILINEAR)
            c = c.rotate((-2.5 if k % 2 else 2.0), expand=True, resample=Image.BILINEAR)
            cx = W // 2 + int(math.sin(t * 0.7) * 12)
            cy = 900
            im.paste(c, (cx - c.width // 2, cy - c.height // 2), c)
        else:
            im = base_bg.copy()
            d = ImageDraw.Draw(im)
            if b.get("big"):
                s = 1 + 0.08 * min(1, lt / 0.4)
                text_c(d, (W // 2, 860), b["big"], int(330 * s), fill=YELLOW, stroke=12)
            if b.get("emoji"):
                pop = min(1, lt / 0.25)
                size = int((300 if b.get("big") else 420) * (0.6 + 0.4 * pop) * (1 + 0.03 * math.sin(t * 3)))
                e = emoji(b["emoji"], size)
                y = 560 if b.get("big") else 860
                im.paste(e, (W // 2 - e.width // 2, y - e.height // 2), e)
        im = Image.composite(im, dark, vig)
        d = ImageDraw.Draw(im)
        # mot-clé géant en haut / accroche
        top = ep.get("hook_text") if k == 0 else b.get("key")
        if top:
            lines_c(d, W // 2, 330, top.upper(), 96 if k == 0 else 88, YELLOW, stroke=10)
        # sous-titres mot à mot (3 mots max visibles, le mot courant en jaune)
        if t < end0:
            words = b["text"].split()
            clip_d = len(clips[k]) / SR
            lens = np.cumsum([len(w_) + 1 for w_ in words])
            pos = min(len(words) - 1, int(np.searchsorted(lens, (lt / max(clip_d, 0.1)) * lens[-1])))
            g0 = (pos // 3) * 3
            grp = [w_.upper() for w_ in words[g0:g0 + 3]]
            x_tot = sum(d.textlength(w_ + " ", font=font(86)) for w_ in grp)
            x = W // 2 - x_tot / 2
            for j, w_ in enumerate(grp):
                col = YELLOW if g0 + j == pos else (255, 255, 255)
                d.text((x, 1440), w_, font=font(86), fill=col, anchor="lm", stroke_width=8, stroke_fill=(0, 0, 0))
                x += d.textlength(w_ + " ", font=font(86))
        if t >= end0:
            a = min(1, (t - end0) / 0.3)
            ov = Image.new("RGBA", (W, H), (0, 0, 0, int(210 * a)))
            im.paste(ov, (0, 0), ov)
            d = ImageDraw.Draw(im)
            lines_c(d, W // 2, 900, ep.get("end", "ET TOI ?").upper(), 104, (255, 255, 255))
            e = emoji("👇", 170)
            im.paste(e, (W // 2 - e.width // 2, 1120), e)
        if ep.get("source"):
            d.text((W // 2, 1560), ep["source"], font=font(34), fill=(220, 220, 220), anchor="mm", stroke_width=3, stroke_fill=(0, 0, 0))
        # grain de film
        im = Image.composite(Image.new("RGB", (W, H), (255, 255, 255)), im, grains[f % 6].point(lambda v: max(0, v - 150)))
        proc.stdin.write(im.tobytes())
    proc.stdin.close()
    proc.wait()
    print(f"OK {out} : {total:.1f} s")


if __name__ == "__main__":
    render(json.load(open(sys.argv[1])), sys.argv[2])
