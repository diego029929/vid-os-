"""« Bataille de pays » : simulation physique, dernier pays dans l'anneau gagne.

Des billes-drapeaux rebondissent dans un anneau qui tourne. L'anneau a une
ouverture : une bille qui sort est éliminée. La dernière qui reste gagne.
Chaque rebond sur l'anneau joue la note suivante d'une mélodie du domaine
public, ce qui donne le son « satisfaisant » des vidéos du genre.

Tout est calculé d'avance (on cherche la graine qui donne une durée et un
suspense corrects), puis rendu image par image avec Pillow, sans voix.

Usage : python3 engine/bataille.py episodes/bataille-001.json sortie.mp4
"""
import json
import math
import os
import random
import subprocess
import sys
import wave

import numpy as np
import pymunk
from PIL import Image, ImageDraw, ImageFilter, ImageFont

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
FONT = os.path.join(ROOT, "assets", "fonts", "Anton-Regular.ttf")
EMOJI_FONT = "/usr/share/fonts/truetype/noto/NotoColorEmoji.ttf"
W, H, FPS = 1080, 1920, 30
SR = 44100
CX, CY = 540, 1010          # centre de l'arène (zones sûres TikTok : texte haut 250-420, bas > 1500)
R = 400                     # rayon intérieur de l'anneau
BALL = 46                   # rayon d'une bille
SUB = 4                     # sous-pas physiques par image

# mélodies du domaine public (demi-tons au-dessus de do4)
MELODIES = {
    "ode": [4, 4, 5, 7, 7, 5, 4, 2, 0, 0, 2, 4, 4, 2, 2, 4, 4, 5, 7, 7, 5, 4, 2, 0, 0, 2, 4, 2, 0, 0],
    "elise": [16, 15, 16, 15, 16, 11, 14, 12, 9, 0, 4, 9, 11, 4, 8, 11, 12, 4, 16, 15, 16, 15, 16, 11, 14, 12, 9],
    "jacques": [0, 2, 4, 0, 0, 2, 4, 0, 4, 5, 7, 4, 5, 7, 7, 9, 7, 5, 4, 0, 7, 9, 7, 5, 4, 0, 0, -5, 0, 0, -5, 0],
    "clair": [0, 0, 0, 2, 4, 2, 0, 4, 2, 2, 0, 0, 0, 0, 2, 4, 2, 0, 4, 2, 2, 0],
}

_fonts, _emo = {}, {}


def font(size):
    if size not in _fonts:
        _fonts[size] = ImageFont.truetype(FONT, size)
    return _fonts[size]


def flag_ball(ch, r):
    """Drapeau emoji découpé en disque, bord blanc."""
    key = (ch, r)
    if key in _emo:
        return _emo[key]
    f = ImageFont.truetype(EMOJI_FONT, 109)
    im = Image.new("RGBA", (180, 180), (0, 0, 0, 0))
    ImageDraw.Draw(im).text((90, 90), ch, font=f, embedded_color=True, anchor="mm")
    im = im.crop(im.getbbox())
    # remplir le disque : on agrandit le drapeau pour couvrir le cercle
    d = 2 * r
    s = d / min(im.size) * 1.02
    im = im.resize((int(im.width * s), int(im.height * s)), Image.LANCZOS)
    x0, y0 = (im.width - d) // 2, (im.height - d) // 2
    im = im.crop((x0, y0, x0 + d, y0 + d))
    big = 4
    mask = Image.new("L", (d * big, d * big), 0)
    ImageDraw.Draw(mask).ellipse((0, 0, d * big - 1, d * big - 1), fill=255)
    mask = mask.resize((d, d), Image.LANCZOS)
    out = Image.new("RGBA", (d + 12, d + 12), (0, 0, 0, 0))
    ring = Image.new("L", ((d + 12) * big, (d + 12) * big), 0)
    ImageDraw.Draw(ring).ellipse((0, 0, (d + 12) * big - 1, (d + 12) * big - 1), fill=255)
    ring = ring.resize((d + 12, d + 12), Image.LANCZOS)
    out.paste((255, 255, 255, 255), (0, 0), ring)
    out.paste(im, (6, 6), mask)
    _emo[key] = out
    return out


# ---------------------------------------------------------------- physique

def build_space(n, seed, gap_deg, spin):
    rnd = random.Random(seed)
    space = pymunk.Space()
    space.gravity = (0, 900)
    ring = pymunk.Body(body_type=pymunk.Body.KINEMATIC)
    ring.position = (CX, CY)
    ring.angular_velocity = spin
    segs = []
    steps = 120
    gap = math.radians(gap_deg)
    for i in range(steps):
        a0 = 2 * math.pi * i / steps
        a1 = 2 * math.pi * (i + 1) / steps
        if a1 <= gap:           # l'ouverture, autour de l'angle 0 du repère de l'anneau
            continue
        p0 = ((R + 8) * math.cos(a0), (R + 8) * math.sin(a0))
        p1 = ((R + 8) * math.cos(a1), (R + 8) * math.sin(a1))
        s = pymunk.Segment(ring, p0, p1, 8)
        s.elasticity = 1.0
        s.friction = 0.0
        s.collision_type = 2
        s.a1 = a1
        segs.append(s)
    space.add(ring, *segs)
    space.segs = segs
    balls = []
    for i in range(n):
        while True:
            ang = rnd.uniform(0, 2 * math.pi)
            dist = rnd.uniform(0, R - BALL - 20)
            x, y = CX + dist * math.cos(ang), CY + dist * math.sin(ang)
            if all((x - b.position.x) ** 2 + (y - b.position.y) ** 2 > (2 * BALL + 6) ** 2 for b in balls):
                break
        b = pymunk.Body(1, pymunk.moment_for_circle(1, 0, BALL))
        b.position = (x, y)
        sp = rnd.uniform(500, 800)
        a = rnd.uniform(0, 2 * math.pi)
        b.velocity = (sp * math.cos(a), sp * math.sin(a))
        c = pymunk.Circle(b, BALL)
        c.elasticity = 1.0
        c.friction = 0.0
        c.collision_type = 1
        b.idx = i
        space.add(b, c)
        balls.append(b)
    return space, ring, balls


GROW = 0.7   # l'ouverture s'agrandit de 0,7° par seconde : la partie finit toujours

def simulate(n, seed, gap_deg, spin, max_s=75, keep=False):
    """Retourne (images, rebonds, éliminations). images = positions par image si keep."""
    space, ring, balls = build_space(n, seed, gap_deg, spin)
    hits = []
    frame = [0]

    def on_hit(arb, sp, data):
        if arb.is_first_contact:
            b = arb.shapes[0].body
            hits.append((frame[0], b.idx))
            # garde l'énergie : vitesse minimale après rebond
            v = b.velocity
            if v.length < 650:
                b.velocity = v.normalized() * 650 if v.length > 1 else (0, -650)

    space.on_collision(1, 2, post_solve=on_hit)
    alive = {b.idx for b in balls}
    elim = []                # (image, idx, rang)
    frames = []
    nf = int(max_s * FPS)
    for f in range(nf):
        frame[0] = f
        g = math.radians(gap_deg + GROW * f / FPS)
        for sg in [x for x in space.segs if x.a1 <= g]:
            space.remove(sg)
            space.segs.remove(sg)
        for _ in range(SUB):
            space.step(1 / (FPS * SUB))
        for b in balls:
            if b.idx in alive:
                dx, dy = b.position.x - CX, b.position.y - CY
                if dx * dx + dy * dy > (R + BALL + 30) ** 2:
                    alive.discard(b.idx)
                    elim.append((f, b.idx, len(alive) + 1))
        if keep:
            frames.append(([(b.position.x, b.position.y) for b in balls], ring.angle, gap_deg + GROW * f / FPS))
        if len(alive) == 1:
            win = next(iter(alive))
            return frames, hits, elim, win, f
    return frames, hits, elim, None, nf


def pick_seed(n, gap_deg, spin, lo=28, hi=45, base=0):
    """Graine qui finit entre lo et hi secondes, éliminations bien étalées, fin serrée."""
    best = None
    for seed in range(base, base + 400):
        _, _, elim, win, end = simulate(n, seed, gap_deg, spin)
        if win is None:
            continue
        dur = end / FPS
        if not lo <= dur <= hi:
            continue
        times = [e[0] / FPS for e in elim]
        first = times[0]
        # la finale (dernier duel) doit durer un peu : suspense
        final = (end - elim[-2][0]) / FPS if len(elim) >= 2 else 0
        score = -abs(first - 3) - max(0, 5 - final) - max(0, final - 9)
        if best is None or score > best[0]:
            best = (score, seed, dur)
        if score > -1:
            break
    return best


# ---------------------------------------------------------------- son

def tone(freq, dur, vol=0.35, kind="pluck"):
    t = np.arange(int(SR * dur)) / SR
    if kind == "pluck":
        w = (np.sin(2 * np.pi * freq * t) + 0.35 * np.sin(4 * np.pi * freq * t) + 0.12 * np.sin(6 * np.pi * freq * t))
        env = np.exp(-t * 7) * np.minimum(1, t * 400)
    else:
        w = np.sign(np.sin(2 * np.pi * freq * t)) * 0.5
        env = np.exp(-t * 4) * np.minimum(1, t * 300)
    return w * env * vol


def make_audio(hits, elim, end_f, total_f, melody, path):
    n = int(total_f / FPS * SR) + SR
    out = np.zeros(n)
    mel = MELODIES[melody]
    k = 0
    last = -99
    for f, _ in hits:
        if f - last < 2:            # pas deux notes dans la même image
            continue
        last = f
        semi = mel[k % len(mel)]
        k += 1
        fr = 523.25 * 2 ** (semi / 12)
        s = tone(fr, 0.45)
        i = int(f / FPS * SR)
        out[i:i + len(s)] += s[: n - i]
    for f, _, _ in elim:
        i = int(f / FPS * SR)
        for j, fr in enumerate((330, 247)):
            s = tone(fr, 0.25, 0.22, "square")
            a = i + int(j * 0.09 * SR)
            out[a:a + len(s)] += s[: n - a]
    i = int(end_f / FPS * SR)
    for j, semi in enumerate((0, 4, 7, 12, 16)):
        s = tone(523.25 * 2 ** (semi / 12), 1.2, 0.3)
        a = i + int(j * 0.11 * SR)
        out[a:a + len(s)] += s[: n - a]
    out = out / max(1e-6, np.abs(out).max()) * 0.8
    pcm = (out * 32767).astype(np.int16)
    with wave.open(path, "wb") as w:
        w.setnchannels(1)
        w.setsampwidth(2)
        w.setframerate(SR)
        w.writeframes(pcm.tobytes())


# ---------------------------------------------------------------- image

def background(colors):
    a, b = colors
    t = np.linspace(0, 1, H)[:, None, None]
    grad = (np.array(a)[None, None] * (1 - t) + np.array(b)[None, None] * t) * np.ones((1, W, 1))
    im = Image.fromarray(grad.astype(np.uint8), "RGB")
    # halo derrière l'arène
    glow = Image.new("L", (W, H), 0)
    ImageDraw.Draw(glow).ellipse((CX - R - 120, CY - R - 120, CX + R + 120, CY + R + 120), fill=70)
    glow = glow.filter(ImageFilter.GaussianBlur(90))
    im = Image.composite(Image.new("RGB", (W, H), (255, 255, 255)), im, glow.point(lambda v: v // 3))
    return im


def text_c(d, xy, txt, size, fill=(255, 255, 255), stroke=8, maxw=960):
    while size > 20 and d.textlength(txt, font=font(size)) > maxw:
        size -= 4
    d.text(xy, txt, font=font(size), fill=fill, anchor="mm", stroke_width=stroke, stroke_fill=(0, 0, 0))


def emoji_inline(ch, size):
    f = ImageFont.truetype(EMOJI_FONT, 109)
    im = Image.new("RGBA", (180, 180), (0, 0, 0, 0))
    ImageDraw.Draw(im).text((90, 90), ch, font=f, embedded_color=True, anchor="mm")
    im = im.crop(im.getbbox())
    s = size / im.height
    return im.resize((int(im.width * s), size), Image.LANCZOS)


def render(ep, out):
    teams = ep["teams"]
    n = len(teams)
    gap, spin = ep.get("gap_deg", 18), ep.get("spin", 0.9)
    seed = ep.get("seed")
    if seed is None:
        best = pick_seed(n, gap, spin, base=ep.get("seed_base", 0))
        if not best:
            raise SystemExit("Aucune graine correcte : changer gap_deg/spin")
        seed = best[1]
        print(f"graine {seed} ({best[2]:.1f} s)")
    frames, hits, elim, win, end = simulate(n, seed, gap, spin, keep=True)
    outro = int(4.5 * FPS)
    total = end + outro
    tmp = out + ".tmp"
    os.makedirs(tmp, exist_ok=True)
    wav = os.path.join(tmp, "son.wav")
    make_audio(hits, elim, end, total, ep.get("melody", "ode"), wav)

    bg = background(ep.get("colors", ((20, 16, 60), (90, 20, 110))))
    balls = [flag_ball(t["flag"], BALL) for t in teams]
    gray = [b.convert("LA").convert("RGBA") for b in balls]
    ring_col = tuple(ep.get("ring", (255, 214, 64)))
    elim_at = {idx: (f, rank) for f, idx, rank in elim}
    proc = subprocess.Popen(
        ["ffmpeg", "-y", "-loglevel", "error", "-f", "rawvideo", "-pix_fmt", "rgb24", "-s", f"{W}x{H}",
         "-r", str(FPS), "-i", "-", "-i", wav,
         "-af", "loudnorm=I=-14:TP=-2:LRA=11,aresample=44100,alimiter=limit=0.7:level=false",
         "-c:v", "libx264", "-preset", "medium", "-crf", "20", "-pix_fmt", "yuv420p",
         "-c:a", "aac", "-b:a", "160k", "-shortest", "-movflags", "+faststart", out],
        stdin=subprocess.PIPE)
    shorts = [t.get("short") or (t["name"].upper() if len(t["name"]) <= 10 else t["name"][:3].upper()) for t in teams]
    winflag = emoji_inline(teams[win]["flag"], 150)
    for f in range(total):
        sf = min(f, end)
        pos, ang, gcur = frames[sf]
        im = bg.copy()
        d = ImageDraw.Draw(im)
        # anneau (épais, avec trou qui tourne)
        gap_r = math.radians(gcur)
        a0 = math.degrees(ang + gap_r)
        a1 = math.degrees(ang + 2 * math.pi)
        box = (CX - R - 16, CY - R - 16, CX + R + 16, CY + R + 16)
        d.arc(box, a0, a1, fill=ring_col, width=18)
        alive = n - sum(1 for e in elim if e[0] <= sf)
        # traînées lumineuses derrière les billes en jeu
        if f <= end:
            tr = Image.new("RGBA", (W, H), (0, 0, 0, 0))
            dt = ImageDraw.Draw(tr)
            for back in (6, 4, 2):
                pp = frames[max(0, sf - back)][0]
                for i, (x, y) in enumerate(pp):
                    if i in elim_at and elim_at[i][0] <= sf:
                        continue
                    rr = int(BALL * (1 - back / 10))
                    dt.ellipse((x - rr, y - rr, x + rr, y + rr), fill=ring_col + (int(90 - back * 12),))
            im.paste(tr, (0, 0), tr)
            d = ImageDraw.Draw(im)
        names = []
        # billes : éliminées en gris qui tombent, vivantes en couleur
        for i, (x, y) in enumerate(pos):
            if i in elim_at and elim_at[i][0] <= sf:
                if y > H + 80 or f > end:
                    continue
                im.paste(gray[i], (int(x) - BALL - 6, int(y) - BALL - 6), gray[i])
            else:
                if f > end and i == win:
                    continue
                im.paste(balls[i], (int(x) - BALL - 6, int(y) - BALL - 6), balls[i])
                names.append((x, y, shorts[i]))
        d = ImageDraw.Draw(im)
        for x, y, nm in names:     # petit nom sous chaque bille (drapeaux qui se ressemblent)
            d.text((x, y + BALL + 14), nm, font=font(26), fill=(255, 255, 255), anchor="mm",
                   stroke_width=4, stroke_fill=(0, 0, 0))
        # titre (visible dès la 1re image)
        text_c(d, (W // 2, 300), ep["title"], 92)
        text_c(d, (W // 2, 400), ep.get("subtitle", "CHOISIS TON PAYS"), 54, fill=(255, 225, 90), stroke=6)
        # compteur
        if f <= end:
            text_c(d, (W // 2, CY + R + 110), f"ENCORE {alive} PAYS", 66, fill=(255, 255, 255))
        # bandeau de la dernière élimination (1,2 s)
        recent = [e for e in elim if 0 <= sf - e[0] < int(1.3 * FPS)]
        if recent and f <= end:
            fe, idx, rank = recent[-1]
            t = teams[idx]
            label = f"{t['name'].upper()} ÉLIMINÉ{'E' if t.get('f') else ''} ({rank}e)"
            fl = emoji_inline(t["flag"], 64)
            tw = d.textlength(label, font=font(58)) + fl.width + 20
            x0 = int(W // 2 - tw // 2)
            d.rounded_rectangle((x0 - 24, 1585, x0 + tw + 24, 1675), 22, fill=(200, 30, 50))
            im.paste(fl, (x0, 1598), fl)
            d.text((x0 + fl.width + 20, 1630), label, font=font(58), fill=(255, 255, 255), anchor="lm")
        # finale
        if f > end:
            k = min(1, (f - end) / 12)
            ov = Image.new("RGBA", (W, H), (0, 0, 0, int(150 * k)))
            im.paste(ov, (0, 0), ov)
            d = ImageDraw.Draw(im)
            s = int(150 + 210 * k)
            big = flag_ball(teams[win]["flag"], s // 2)
            im.paste(big, (W // 2 - big.width // 2, CY - 120 - big.height // 2), big)
            text_c(d, (W // 2, CY + 170), f"{teams[win]['name'].upper()} GAGNE !", 110, fill=(255, 214, 64), stroke=10)
            text_c(d, (W // 2, CY + 330), ep.get("end", "TON PAYS A FINI À QUELLE PLACE ?"), 58, stroke=7)
        proc.stdin.write(im.tobytes())
    proc.stdin.close()
    proc.wait()
    print(f"OK {out} : {total / FPS:.1f} s, gagnant {teams[win]['name']}, graine {seed}")
    return teams[win]["name"], seed


if __name__ == "__main__":
    ep = json.load(open(sys.argv[1]))
    render(ep, sys.argv[2])
