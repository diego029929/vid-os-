"""Vidéos « défi » courtes (nouveau concept du 10/11) : TROUVE L'INTRUS et QUIZ.

Usage : python3 engine/quiz.py episodes/defi-XX.json /tmp/defi-XX.mp4

Rendu rapide (≈ 1-3 min avec la voix Chatterbox, quelques secondes sans).
Variable d'environnement QUIZ_VOICE=0 : pas de voix (pour un essai).

Format JSON — « intrus » (≈ 22 s) :
{
  "type": "intrus",
  "title": "Défi n°1 · Trouve le chat",           (titre Zernio, ≤ 80 caractères)
  "caption": "...",                                (légende + hashtags)
  "hook": "TROUVE LE CHAT CACHÉ",                  (en haut de l'écran, ≤ 24 caractères)
  "voice_hook": "Trouve le chat caché. Trois niveaux. Le dernier est vraiment dur.",
  "levels": [
    {"crowd": "🐶", "target": "🐱", "cols": 6, "rows": 8, "seconds": 5},
    {"crowd": "😄", "target": "😆", "cols": 8, "rows": 11, "seconds": 5},
    {"crowd": "😀", "target": "😃", "cols": 10, "rows": 13, "seconds": 6}
  ],
  "end": "T'AS TROUVÉ LES 3 ?"
}

Format JSON — « quiz » (≈ 35 s) :
{
  "type": "quiz",
  "title": "...", "caption": "...",
  "hook": "QUIZ CULTURE G",                         (en haut)
  "voice_hook": "Cinq questions. Si tu as cinq sur cinq, t'es un génie.",
  "questions": [
    {"q": "Quelle est la capitale de l'Australie ?", "choices": ["Sydney", "Canberra", "Melbourne"],
     "answer": 1, "emoji": "🦘", "voice": "(facultatif : phrase lue si différente)"},
    {"q": "Devine le film :", "big": ["🦁", "👑", "🐗"], "choices": ["Le Roi lion", "Madagascar", "Zootopie"],
     "answer": 0, "voice": "Devine le film avec ces emojis."},
    ...  (5 questions, de la plus facile à la plus dure)
  ],
  "end": "T'AS EU COMBIEN SUR 5 ?"
}

Format JSON — « indices » (≈ 16 s par manche, 1 manche conseillée) : DEVINE EN 4 INDICES.
Une grosse image (emoji) très pixelisée devient nette indice après indice ;
pas de voix (tic-tac + ding), tout se joue à l'écran.
{
  "type": "indices",
  "title": "...", "caption": "...",
  "hook": "DEVINE L'ANIMAL",                       (en haut, ≤ 20 caractères)
  "rounds": [
    {"emoji": "🦒", "answer": "LA GIRAFE",
     "clues": ["Je vis en Afrique", "Je dors debout", "Mon cœur pèse 11 kg", "J'ai le plus long cou"],
     "seconds": 3.4}
  ],
  "end": "TROUVÉ À QUEL INDICE ?"
}
"""
import json
import math
import os
import random
import subprocess
import sys
import tempfile
import wave

import numpy as np
from PIL import Image, ImageDraw, ImageFilter, ImageFont

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
FONT = os.path.join(ROOT, "assets", "fonts", "Anton-Regular.ttf")
EMOJI_FONT = "/usr/share/fonts/truetype/noto/NotoColorEmoji.ttf"
W, H, FPS, SR = 1080, 1920, 30, 44100
# zone sûre TikTok : rien d'important à droite (boutons) ni en bas (légende)
SAFE_L, SAFE_R = 60, 950
YELLOW, WHITE, GREEN, RED, DARK = (255, 214, 10), (255, 255, 255), (46, 204, 113), (235, 59, 59), (25, 22, 40)

_fonts = {}


def font(size):
    if size not in _fonts:
        _fonts[size] = ImageFont.truetype(FONT, size)
    return _fonts[size]


_emo = {}


def emoji(ch, size):
    """Emoji en couleur (police Noto, taille native 109 px), redimensionné."""
    key = (ch, size)
    if key not in _emo:
        if not os.path.exists(EMOJI_FONT):
            raise SystemExit("Police emoji absente : apt-get install fonts-noto-color-emoji")
        f = ImageFont.truetype(EMOJI_FONT, 109)
        im = Image.new("RGBA", (160, 160), (0, 0, 0, 0))
        ImageDraw.Draw(im).text((80, 80), ch, font=f, embedded_color=True, anchor="mm")
        bb = im.getbbox()
        if not bb:
            raise SystemExit(f"Emoji illisible par la police : {ch!r}")
        im = im.crop(bb)
        s = size / max(im.size)
        _emo[key] = im.resize((max(1, int(im.width * s)), max(1, int(im.height * s))), Image.LANCZOS)
    return _emo[key]


def background(seed):
    """Dégradé vif (change à chaque vidéo) + légères bulles floues."""
    rnd = random.Random(seed)
    palettes = [((88, 24, 196), (255, 70, 140)), ((18, 92, 220), (0, 200, 200)), ((255, 94, 58), (255, 170, 0)),
                ((20, 160, 110), (30, 90, 200)), ((140, 30, 200), (40, 120, 255)), ((230, 40, 90), (120, 30, 200))]
    a, b = palettes[rnd.randrange(len(palettes))]
    t = np.linspace(0, 1, H)[:, None, None]
    grad = (np.array(a)[None, None] * (1 - t) + np.array(b)[None, None] * t) * np.ones((1, W, 1))
    im = Image.fromarray(grad.astype(np.uint8), "RGB")
    over = Image.new("RGBA", (W, H), (0, 0, 0, 0))
    d = ImageDraw.Draw(over)
    for _ in range(9):
        r = rnd.randint(80, 260)
        x, y = rnd.randint(0, W), rnd.randint(0, H)
        d.ellipse((x - r, y - r, x + r, y + r), fill=(255, 255, 255, 28))
    over = over.filter(ImageFilter.GaussianBlur(30))
    im.paste(over, (0, 0), over)
    return im


def text_c(d, xy, txt, size, fill=WHITE, stroke=8, maxw=None):
    """Texte centré avec contour noir ; réduit la taille si trop large."""
    maxw = maxw or (SAFE_R - SAFE_L)
    while size > 20 and d.textlength(txt, font=font(size)) > maxw:
        size -= 4
    d.text(xy, txt, font=font(size), fill=fill, anchor="mm", stroke_width=stroke, stroke_fill=(0, 0, 0))


def wrap(d, txt, size, maxw):
    words, lines, cur = txt.split(), [], ""
    for w in words:
        t = (cur + " " + w).strip()
        if d.textlength(t, font=font(size)) <= maxw:
            cur = t
        else:
            lines.append(cur)
            cur = w
    lines.append(cur)
    return lines


def rounded(d, box, r, fill, outline=None, width=0):
    d.rounded_rectangle(box, r, fill=fill, outline=outline, width=width)


def header(im, hook, sub):
    d = ImageDraw.Draw(im)
    text_c(d, ((SAFE_L + SAFE_R) // 2, 215), hook, 104, YELLOW, 10)
    if sub:
        text_c(d, ((SAFE_L + SAFE_R) // 2 - (60 if sub.startswith("NIVEAU") else 0), 320), sub, 60, WHITE, 7, 640)


CX = (SAFE_L + SAFE_R) // 2


def timer(im, frac, secs_left):
    """Barre de temps + gros chiffre, sous la grille (zone sûre)."""
    d = ImageDraw.Draw(im)
    x0, x1, y = SAFE_L + 40, SAFE_R - 40, 1440
    rounded(d, (x0, y, x1, y + 34), 17, (0, 0, 0, 110))
    w = int((x1 - x0) * max(0.0, frac))
    col = GREEN if frac > 0.5 else (YELLOW if frac > 0.25 else RED)
    if w > 34:
        rounded(d, (x0, y, x0 + w, y + 34), 17, col)
    text_c(d, (CX, 1375), str(secs_left), 80, WHITE, 8)


# --------------------------------------------------------------------------- TROUVE L'INTRUS

def intrus_grid(level, seed):
    cols, rows = level["cols"], level["rows"]
    rnd = random.Random(seed)
    # jamais sur les bords (trop facile à repérer) sauf si la grille est petite
    tc = rnd.randrange(1, cols - 1) if cols > 3 else rnd.randrange(cols)
    tr = rnd.randrange(1, rows - 1) if rows > 3 else rnd.randrange(rows)
    gx0, gx1, gy0, gy1 = SAFE_L + 10, SAFE_R - 10, 410, 1290
    cell = min((gx1 - gx0) / cols, (gy1 - gy0) / rows)
    size = int(cell * 0.84)
    ox = gx0 + ((gx1 - gx0) - cell * cols) / 2
    oy = gy0 + ((gy1 - gy0) - cell * rows) / 2
    card = Image.new("RGBA", (W, H), (0, 0, 0, 0))
    d = ImageDraw.Draw(card)
    rounded(d, (int(ox) - 24, int(oy) - 24, int(ox + cell * cols) + 24, int(oy + cell * rows) + 24), 40,
            (255, 255, 255, 235))
    for r in range(rows):
        for c in range(cols):
            e = emoji(level["target"] if (r, c) == (tr, tc) else level["crowd"], size)
            x = int(ox + c * cell + (cell - e.width) / 2)
            y = int(oy + r * cell + (cell - e.height) / 2)
            card.paste(e, (x, y), e)
    center = (ox + (tc + 0.5) * cell, oy + (tr + 0.5) * cell)
    return card, center, cell


def build_intrus(spec, seed):
    """Renvoie la liste des segments : (durée, fonction t -> image, texte à lire ou None, son)."""
    bg = background(seed)
    segs = []
    n = len(spec["levels"])
    for i, lv in enumerate(spec["levels"]):
        card, (cx, cy), cell = intrus_grid(lv, seed * 31 + i)
        sub = f"NIVEAU {i + 1}/{n}" + (" · LE PLUS DUR" if i == n - 1 and n > 1 else "")
        base = bg.copy()
        header(base, spec.get("hook", "TROUVE L'INTRUS"), sub)
        # rappel de la cible à trouver, à droite du niveau
        tgt = emoji(lv["target"], 84)
        d = ImageDraw.Draw(base)
        rounded(d, (SAFE_R - 150, 262, SAFE_R - 30, 378), 26, (255, 255, 255, 235))
        base.paste(tgt, (SAFE_R - 90 - tgt.width // 2, 320 - tgt.height // 2), tgt)
        base.paste(card, (0, 0), card)
        secs = float(lv.get("seconds", 5))
        if i == 0:
            voice = spec.get("voice_hook")
        elif i == n - 1:
            voice = lv.get("voice", "Dernier niveau, le plus difficile.")
        else:
            voice = lv.get("voice", "Niveau deux, un peu plus dur.")

        def play(t, base=base, secs=secs):
            im = base.copy()
            timer(im, 1 - t / secs, max(1, math.ceil(secs - t)))
            return im

        def reveal(t, base=base, cx=cx, cy=cy, cell=cell):
            im = base.copy()
            d = ImageDraw.Draw(im)
            r = cell * (0.75 + 0.15 * math.sin(min(t, 0.4) / 0.4 * math.pi / 2))
            for k in range(3):
                d.ellipse((cx - r - k * 3, cy - r - k * 3, cx + r + k * 3, cy + r + k * 3), outline=RED, width=10)
            text_c(d, (CX, 1400), "ICI !", 110, RED, 10)
            return im
        segs.append((secs, play, voice, None))
        segs.append((1.6, reveal, None, "ding"))
    segs.append(end_card(spec, bg))
    return segs


# --------------------------------------------------------------------------- QUIZ

def build_quiz(spec, seed):
    bg = background(seed)
    segs = []
    qs = spec["questions"]
    letters = "ABCD"
    for i, q in enumerate(qs):
        base = bg.copy()
        header(base, spec.get("hook", "QUIZ CULTURE G"), f"QUESTION {i + 1}/{len(qs)}")
        d = ImageDraw.Draw(base)
        # question dans une carte blanche
        lines = wrap(d, q["q"], 76, SAFE_R - SAFE_L - 90)
        top = 470
        hq = 100 * len(lines) + 70
        rounded(d, (SAFE_L, top, SAFE_R, top + hq), 40, (255, 255, 255, 240))
        for k, line in enumerate(lines):
            d.text((CX, top + 85 + k * 100), line, font=font(76), fill=DARK, anchor="mm")
        if q.get("emoji"):
            e = emoji(q["emoji"], 120)
            base.paste(e, (SAFE_R - e.width + 10, top - 70), e)
        if q.get("big"):  # rébus en emojis (« devine le film »), liste d'emojis
            n = len(q["big"])
            sz = min(150, int((SAFE_R - SAFE_L - 80) / n * 0.9))
            row_h = sz + 40
            rounded(d, (SAFE_L, top + hq + 25, SAFE_R, top + hq + 25 + row_h), 40, (255, 255, 255, 240))
            for k, ch in enumerate(q["big"]):
                e = emoji(ch, sz)
                x = int(CX - n * sz * 1.05 / 2 + k * sz * 1.05 + (sz - e.width) / 2)
                base.paste(e, (x, top + hq + 25 + (row_h - e.height) // 2), e)
            hq += row_h + 25
        boxes = []
        y = top + hq + 60
        for k, ch in enumerate(q["choices"]):
            boxes.append((SAFE_L + 30, y, SAFE_R - 30, y + 150))
            y += 180

        def draw_choices(im, state, q=q, boxes=boxes):
            d = ImageDraw.Draw(im)
            for k, (ch, bx) in enumerate(zip(q["choices"], boxes)):
                fill, col = (0, 0, 0, 130), WHITE
                if state == "reveal":
                    if k == q["answer"]:
                        fill, col = GREEN, WHITE
                    else:
                        fill, col = (0, 0, 0, 70), (200, 200, 200)
                rounded(d, bx, 36, fill, WHITE, 5)
                d.text((bx[0] + 70, (bx[1] + bx[3]) // 2), letters[k], font=font(80), fill=YELLOW, anchor="mm",
                       stroke_width=5, stroke_fill=(0, 0, 0))
                size = 70
                while size > 34 and d.textlength(ch, font=font(size)) > bx[2] - bx[0] - 170:
                    size -= 4
                d.text((bx[0] + 140, (bx[1] + bx[3]) // 2), ch, font=font(size), fill=col, anchor="lm",
                       stroke_width=4, stroke_fill=(0, 0, 0))
        voice = q.get("voice") or q["q"]
        if i == 0 and spec.get("voice_hook"):
            voice = spec["voice_hook"] + " " + voice
        secs = float(q.get("seconds", 3.5))

        def play(t, base=base, secs=secs, draw_choices=draw_choices, boxes=boxes):
            im = base.copy()
            draw_choices(im, "play")
            # le minuteur démarre après la lecture (voir render : t négatif pendant la voix)
            if t >= 0:
                frac = 1 - t / secs
                d = ImageDraw.Draw(im)
                yb = boxes[-1][3] + 40
                rounded(d, (SAFE_L + 40, yb, SAFE_R - 40, yb + 30), 15, (0, 0, 0, 110))
                w = int((SAFE_R - SAFE_L - 80) * max(0, frac))
                if w > 30:
                    rounded(d, (SAFE_L + 40, yb, SAFE_L + 40 + w, yb + 30), 15,
                            GREEN if frac > 0.5 else (YELLOW if frac > 0.25 else RED))
                text_c(d, (CX, yb + 95), str(max(1, math.ceil(secs - t))), 80, WHITE, 7)
            return im

        def reveal(t, base=base, draw_choices=draw_choices):
            im = base.copy()
            draw_choices(im, "reveal")
            return im
        segs.append(("voice+timer", secs, play, voice))
        segs.append((1.8, reveal, None, "ding"))
    segs.append(end_card(spec, bg))
    return segs


def end_card(spec, bg):
    im = bg.copy()
    d = ImageDraw.Draw(im)
    text_c(d, (CX, 620), spec.get("end", "T'AS RÉUSSI ?"), 120, YELLOW, 11)
    text_c(d, (CX, 800), "ÉCRIS TON SCORE", 96, WHITE, 9)
    text_c(d, (CX, 910), "EN COMMENTAIRE", 96, WHITE, 9)
    e = emoji("👇", 170)
    im.paste(e, (CX - e.width // 2, 1000), e)
    text_c(d, (CX, 1330), "UN NOUVEAU DÉFI CHAQUE JOUR", 64, WHITE, 6)
    text_c(d, (CX, 1420), "ABONNE-TOI", 96, YELLOW, 9)
    voice = spec.get("voice_end", "Écris ton score en commentaire, et abonne-toi pour le défi de demain.")
    return (2.4, lambda t: im, voice, None)


# --------------------------------------------------------------------------- DEVINE EN 4 INDICES

PIX = [4, 6, 10, 18]  # nombre de « gros pixels » sur la largeur, indice après indice


def pixelate(img, n):
    small = img.resize((n, max(1, round(n * img.height / img.width))), Image.BILINEAR)
    return small.resize(img.size, Image.NEAREST)


def build_indices(spec, seed):
    bg = background(seed)
    segs = []
    rounds = spec["rounds"]
    for ri, rd in enumerate(rounds):
        big = emoji(rd["emoji"], 640)
        sq = Image.new("RGBA", (700, 700), (255, 255, 255, 0))
        sq.paste(big, ((700 - big.width) // 2, (700 - big.height) // 2), big)
        clues = rd["clues"]
        n = len(clues)
        secs = float(rd.get("seconds", 3.4))
        sub = "" if len(rounds) == 1 else f"MANCHE {ri + 1}/{len(rounds)}"

        def frame(im, img, scale, shown, active, glow=0.0):
            d = ImageDraw.Draw(im)
            # carte blanche + image au centre (léger zoom continu = ça bouge)
            cy = 770
            rounded(d, (CX - 385, cy - 385, CX + 385, cy + 385), 55, (255, 255, 255, 240))
            s = int(700 * scale)
            im2 = img.resize((s, s), Image.NEAREST)
            box = (CX - 350, cy - 350, CX + 350, cy + 350)
            off = (s - 700) // 2
            crop = im2.crop((off, off, off + 700, off + 700))
            im.paste(crop, box[:2], crop)
            # indices déjà donnés
            y = 1265
            for k in range(shown):
                last = k == active
                col = YELLOW if last else WHITE
                size = 70 if last else 56
                text_c(d, (CX, y), f"{k + 1}. {clues[k]}", size, col, 7)
                y += 88
            return im

        def play(t, k=None, img=None):
            im = bg.copy()
            header(im, spec.get("hook", "DEVINE"), f"INDICE {k + 1}/{n}" + (" · " + sub if sub else ""))
            g = (k * secs + t) / (n * secs)  # avance globale de la manche
            frame(im, img, 1.0 + 0.10 * (1 - g) + 0.03 * math.sin(t * 2.2), k + 1, k)
            # barre de temps de l'indice
            d = ImageDraw.Draw(im)
            frac = 1 - t / secs
            rounded(d, (SAFE_L + 40, 1180, SAFE_R - 40, 1202), 10, (0, 0, 0, 110))
            w = int((SAFE_R - SAFE_L - 80) * max(0, frac))
            if w > 20:
                rounded(d, (SAFE_L + 40, 1180, SAFE_L + 40 + w, 1202), 10,
                        GREEN if frac > 0.5 else (YELLOW if frac > 0.25 else RED))
            return im

        for k in range(n):
            img = pixelate(sq, PIX[round(k * (len(PIX) - 1) / max(1, n - 1))])
            segs.append((secs, (lambda t, k=k, img=img: play(t, k, img)), None, "tick" if k else "whoosh"))

        def reveal(t, sq=sq, rd=rd):
            im = bg.copy()
            header(im, spec.get("hook", "DEVINE"), "RÉPONSE")
            pop = 1.0 + 0.12 * math.sin(min(t, 0.35) / 0.35 * math.pi)
            frame(im, sq, pop, 0, -1)
            d = ImageDraw.Draw(im)
            rounded(d, (SAFE_L, 1200, SAFE_R, 1370), 45, GREEN, WHITE, 6)
            text_c(d, (CX, 1285), rd["answer"], 104, WHITE, 8, SAFE_R - SAFE_L - 60)
            return im
        segs.append((2.2, reveal, None, "ding"))
    # fin : question à commenter, puis on reboucle visuellement sur le début (même fond)
    im = bg.copy()
    d = ImageDraw.Draw(im)
    text_c(d, (CX, 650), spec.get("end", "TROUVÉ À QUEL INDICE ?"), 104, YELLOW, 10)
    for k, lab in enumerate(["1", "2", "3", "4"]):
        x = CX - 330 + k * 220
        rounded(d, (x - 85, 800, x + 85, 970), 35, (255, 255, 255, 235))
        d.text((x, 885), lab, font=font(110), fill=DARK, anchor="mm")
    text_c(d, (CX, 1070), "RÉPONDS EN COMMENTAIRE", 76, WHITE, 8)
    e = emoji("👇", 150)
    im.paste(e, (CX - e.width // 2, 1140), e)
    segs.append((1.8, lambda t: im, None, None))
    return segs


# --------------------------------------------------------------------------- SON

def say(text):
    if os.environ.get("QUIZ_VOICE", "1") == "0" or not text:
        return np.zeros(0, np.float32)
    global _VOICE_OK
    if not _VOICE_OK:
        return np.zeros(0, np.float32)
    sys.path.insert(0, os.path.join(ROOT, "engine"))
    try:
        import voice
        return voice.synth(text)
    except ImportError as e:  # Chatterbox pas installé : vidéo sans voix plutôt que rien
        print(f"ATTENTION : voix indisponible ({e}), vidéo SANS voix", file=sys.stderr)
        _VOICE_OK = False
        return np.zeros(0, np.float32)


_VOICE_OK = True


def ding():
    t = np.arange(int(0.6 * SR)) / SR
    s = sum(np.sin(2 * np.pi * f * t) * a for f, a in ((1318.5, 0.5), (1975.5, 0.3), (2637, 0.15)))
    return (s * np.exp(-t * 7) * 0.35).astype(np.float32)


def tick():
    t = np.arange(int(0.05 * SR)) / SR
    return (np.sin(2 * np.pi * 2200 * t) * np.exp(-t * 120) * 0.25).astype(np.float32)


def whoosh():
    n = int(0.45 * SR)
    t = np.arange(n) / SR
    x = np.random.default_rng(1).standard_normal(n) * np.sin(np.pi * t / t[-1]) ** 2
    return (np.convolve(x, np.ones(30) / 30, "same") * 0.35).astype(np.float32)


def music(dur, seed):
    """Fond musical léger et entraînant (accords + petit rythme), généré : 100 % libre de droits."""
    rnd = random.Random(seed)
    n = int(dur * SR)
    t = np.arange(n) / SR
    bpm = 112
    beat = 60 / bpm
    roots = rnd.choice([[220, 174.6, 261.6, 196], [196, 246.9, 220, 174.6], [261.6, 220, 174.6, 196]])
    out = np.zeros(n, np.float32)
    bar = beat * 4
    for k in range(int(dur / bar) + 1):
        f = roots[k % 4]
        a, b = int(k * bar * SR), min(n, int((k + 1) * bar * SR))
        if a >= n:
            break
        tt = t[a:b] - k * bar
        chord = sum(np.sin(2 * np.pi * f * m * tt) for m in (1, 1.26, 1.5)) / 3
        out[a:b] += 0.06 * chord * np.minimum(1, tt * 4) * np.exp(-tt * 0.4)
    for k in range(int(dur / (beat / 2)) + 1):
        a = int(k * beat / 2 * SR)
        if a >= n:
            break
        m = min(n - a, int(0.05 * SR))
        noise = np.random.default_rng(k).standard_normal(m) * np.exp(-np.arange(m) / SR * 80)
        out[a:a + m] += 0.03 * noise * (1.6 if k % 4 == 2 else 1)
        if k % 2 == 0:
            m2 = min(n - a, int(0.15 * SR))
            tk = np.arange(m2) / SR
            out[a:a + m2] += 0.12 * np.sin(2 * np.pi * (55 + 60 * np.exp(-tk * 30)) * tk) * np.exp(-tk * 18) * (k % 4 == 0)
    return out


def write_wav(path, x):
    with wave.open(path, "wb") as wf:
        wf.setnchannels(1)
        wf.setsampwidth(2)
        wf.setframerate(SR)
        wf.writeframes((np.clip(x, -1, 1) * 32767).astype(np.int16).tobytes())


# --------------------------------------------------------------------------- RENDU

def render(spec_path, out):
    spec = json.load(open(spec_path))
    seed = sum(map(ord, os.path.basename(spec_path)))
    segs = {"intrus": build_intrus, "indices": build_indices}.get(spec["type"], build_quiz)(spec, seed)
    # 1) voix et durées
    timeline = []  # (durée, f(t), décalage_voix, audio_voix, son)
    for s in segs:
        if s[0] == "voice+timer":  # quiz : la question est lue, puis le minuteur tourne
            _, secs, fn, txt = s
            v = say(txt)
            lead = len(v) / SR + 0.3 if len(v) else 1.8
            timeline.append((lead + secs, (lambda t, fn=fn, lead=lead: fn(t - lead)), v, None))
        else:
            dur, fn, txt, snd = s
            v = say(txt)
            dur = max(dur, len(v) / SR + 0.4)
            timeline.append((dur, fn, v, snd))
    total = sum(x[0] for x in timeline)
    voice_tr = np.zeros(int((total + 1) * SR), np.float32)
    fx_tr = np.zeros_like(voice_tr)
    pos = 0.0
    for dur, fn, v, snd in timeline:
        a = int(pos * SR)
        if len(v):
            voice_tr[a:a + len(v)] += v[: len(voice_tr) - a]
        if snd == "ding":
            dg = ding()
            fx_tr[a:a + len(dg)] += dg
        if snd in ("tick", "whoosh"):
            w = whoosh() if snd == "whoosh" else tick() * 2.2
            fx_tr[a:a + len(w)] += w[: len(fx_tr) - a]
        if snd in ("tick", "whoosh"):  # tic-tac pendant tout l'indice
            for j in range(1, int(dur / 0.5)):
                b = a + int(j * 0.5 * SR)
                tk = tick() * (1.0 if j % 2 else 0.6)
                fx_tr[b:b + len(tk)] += tk[: max(0, len(fx_tr) - b)]
        pos += dur
    mix = voice_tr * 1.0 + fx_tr + music(len(voice_tr) / SR, seed) * (0.55 if voice_tr.any() else 1.0)
    with tempfile.TemporaryDirectory() as tmp:
        wav = os.path.join(tmp, "a.wav")
        write_wav(wav, mix[: int(total * SR)] * 0.8)
        # 2) images, envoyées directement à ffmpeg
        cmd = ["ffmpeg", "-loglevel", "error", "-y", "-f", "rawvideo", "-pix_fmt", "rgb24", "-s", f"{W}x{H}",
               "-r", str(FPS), "-i", "-", "-i", wav, "-c:v", "libx264", "-preset", "medium", "-crf", "20",
               "-pix_fmt", "yuv420p", "-c:a", "aac", "-b:a", "160k",
               "-af", "acompressor=threshold=-20dB:ratio=4:attack=2:release=100,alimiter=limit=0.5:level=disabled,loudnorm=I=-14:TP=-2:LRA=7,alimiter=limit=0.8:level=disabled,aresample=44100", "-shortest", "-movflags", "+faststart", out]
        p = subprocess.Popen(cmd, stdin=subprocess.PIPE)
        for dur, fn, _, _ in timeline:
            nf = int(round(dur * FPS))
            last_key, last = None, None
            for k in range(nf):
                t = k / FPS
                # n'avance l'image que quand elle change (minuteur : 10 images/s suffisent)
                key = round(t * 10)
                if key != last_key:
                    last = np.asarray(fn(t).convert("RGB")).tobytes()
                    last_key = key
                p.stdin.write(last)
        p.stdin.close()
        if p.wait():
            raise SystemExit("ffmpeg a échoué")
    print(f"OK {out} ({total:.1f} s)")


if __name__ == "__main__":
    render(sys.argv[1], sys.argv[2])
