"""« Les Fruits » : petits drames entre fruits qui parlent (format du 11/11).

Usage : python3 engine/fruits.py episodes/fruits-NNN.json /tmp/fruits-NNN.mp4
        FRUITS_VOICE=0 → sans voix (essai rapide des images)
        python3 engine/fruits.py --casting /tmp/casting.png   (planche de tous les fruits)

Les personnages sont dessinés ici (aucune image extérieure) : fruit « gonflé »
en relief (ombre + reflet), gros yeux, sourcils et bouche selon l'émotion, la
bouche bouge avec la voix. Chaque perso a sa voix Chatterbox (fichier de
référence LibriVox dans assets/ref/).

Format JSON :
{
  "type": "fruits",
  "title": "...", "caption": "...",
  "lieu": "cuisine",            (cuisine | frigo | plage | marche | table)
  "hook": "IL SENT LA FRAISE…", (gros texte en haut pendant la 1re réplique, ≤ 22 car.)
  "cast": {
     "pomme":  {"fruit": "pomme",  "nom": "Pomme",  "voix": "femme1"},
     "banane": {"fruit": "banane", "nom": "Banane", "voix": "homme1"}
  },
  "lines": [
     {"who": "pomme", "text": "Banane ! Pourquoi tu sens la fraise ?", "emo": "colere"},
     {"who": "banane", "text": "...", "emo": "surpris", "shot": "duo", "sfx": "dun"},
     ...
  ],
  "twist": "couteau",          (facultatif : un couteau descend à la fin)
  "end": "TEAM POMME OU TEAM FRAISE ?"
}
- emo : neutre, content, colere, triste, pleure, surpris, peur, malin.
- shot : "proche" (gros plan sur celui qui parle, défaut) ou "duo"/"groupe"
  (tout le monde). "voice" : phrase lue si différente du texte affiché.
- retry : 1, 2… = autre tirage de la voix si la réplique est mal lue.
- sfx : "dun" (coup dramatique), "choc" (zoom brusque), "tiroir" (bruit de tiroir).
- Fruits : pomme, banane, fraise, orange, citron, poire, raisin, ananas,
  pasteque, kiwi, cerise, peche, avocat, tomate.
- Voix : femme1, femme2, femme3, homme1, homme2, homme3, grave.
"""
import json
import math
import os
import random
import subprocess
import sys
import tempfile
import wave
import zlib

import numpy as np
from PIL import Image, ImageChops, ImageDraw, ImageFilter, ImageFont

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
FONT = os.path.join(ROOT, "assets", "fonts", "Anton-Regular.ttf")
W, H, FPS, SR = 1080, 1920, 30, 44100
SAFE_L, SAFE_R = 60, 950
CX = (SAFE_L + SAFE_R) // 2
YELLOW, WHITE = (255, 214, 10), (255, 255, 255)
FLOOR = 1430          # ligne où les fruits sont posés
SPRITE = 700          # taille de fabrication des personnages

VOICES = {  # référence (assets/ref), exagération, hauteur (1 = naturelle)
    "femme1": ("ref-femme-1.wav", 0.7, 1.0),
    "femme2": ("ref-femme-2.wav", 0.7, 1.0),
    "femme3": ("ref-femme-3.wav", 0.7, 1.0),
    "homme1": ("ref-tom.wav", 0.7, 1.0),
    "homme2": ("ref-pierre.wav", 0.7, 1.0),
    "homme3": ("ref-pierre-moyen.wav", 0.7, 1.0),
    "grave": ("ref-narrateur-grave.wav", 0.6, 1.0),
}

_fonts = {}


def font(size):
    if size not in _fonts:
        _fonts[size] = ImageFont.truetype(FONT, size)
    return _fonts[size]


# --------------------------------------------------------------------------- FRUITS

def _blur(a, r):
    """Flou gaussien en flottant (pas de marches de couleur, contrairement à PIL 8 bits)."""
    a = np.asarray(a, np.float32)
    n0, n1 = a.shape
    p = int(r * 3)
    b = np.pad(a, p)
    for ax in (0, 1):
        n = b.shape[ax]
        f = np.fft.rfftfreq(n)
        g = np.exp(-2 * (np.pi * f * r) ** 2)
        b = np.fft.irfft(np.fft.rfft(b, axis=ax) * (g[:, None] if ax == 0 else g[None, :]), n=n, axis=ax)
    return b[p:p + n0, p:p + n1].astype(np.float32)


def shade(albedo, mask, gloss=1.0, puff=0.11):
    """Relief « gonflé » : hauteur = masque flouté, lumière en haut à gauche, reflet blanc."""
    S = mask.shape[0]
    h = _blur(mask, S * puff) * 0.6 + _blur(mask, S * puff * 0.4) * 0.4
    h = np.sqrt(np.clip(h, 0, 1))
    gy, gx = np.gradient(h * S * 0.35)
    n = np.stack([-gx, -gy, np.ones_like(h)], -1)
    n /= np.linalg.norm(n, axis=-1, keepdims=True)
    L = np.array([-0.45, -0.6, 0.66])
    L /= np.linalg.norm(L)
    dif = np.clip((n * L).sum(-1), 0, 1)
    Hv = L + np.array([0, 0, 1.0])
    Hv /= np.linalg.norm(Hv)
    spec = np.clip((n * Hv).sum(-1), 0, 1) ** 38 * 0.75 * gloss
    # lumière de rebond en bas à droite (couleur chaude), pour le volume
    rim = np.clip((n * np.array([0.5, 0.6, 0.2])).sum(-1), 0, 1) ** 2 * 0.25
    col = albedo * (0.38 + 0.72 * dif[..., None]) + rim[..., None] * albedo * 0.8 + spec[..., None] * 255
    out = np.dstack([np.clip(col, 0, 255), mask * 255]).astype(np.uint8)
    return Image.fromarray(out, "RGBA")


def _mask(draw_fn, S=SPRITE):
    im = Image.new("L", (S, S), 0)
    draw_fn(ImageDraw.Draw(im), S)
    return np.asarray(im.filter(ImageFilter.GaussianBlur(1.2))).astype(np.float32) / 255


def _albedo(mask, color, color2=None):
    S = mask.shape[0]
    a = np.ones((S, S, 3), np.float32) * np.array(color, np.float32)
    if color2 is not None:  # dégradé vertical
        t = np.linspace(0, 1, S)[:, None, None]
        a = a * (1 - t) + np.array(color2, np.float32) * t
    return a


def _dots(alb, mask, rnd, n, r, col, S, jitter=0):
    im = Image.fromarray(alb.astype(np.uint8))
    d = ImageDraw.Draw(im)
    tries = 0
    while n > 0 and tries < n * 40:
        tries += 1
        x, y = rnd.uniform(0, S), rnd.uniform(0, S)
        if mask[int(y) % S, int(x) % S] > 0.95 and mask[int(min(S - 1, y + r * 2)), int(x)] > 0.9:
            rr = r + rnd.uniform(-jitter, jitter)
            d.ellipse((x - rr, y - rr * 1.3, x + rr, y + rr * 1.3), fill=col)
            n -= 1
    return np.asarray(im).astype(np.float32)


def _leaf(im, x, y, size, angle, col=(70, 170, 60)):
    lf = Image.new("RGBA", (int(size * 2), int(size)), (0, 0, 0, 0))
    m = np.zeros((lf.height, lf.width), np.float32)
    mi = Image.new("L", lf.size, 0)
    ImageDraw.Draw(mi).ellipse((0, lf.height * 0.18, lf.width, lf.height * 0.82), fill=255)
    m = np.asarray(mi).astype(np.float32) / 255
    alb = np.ones((lf.height, lf.width, 3), np.float32) * np.array(col, np.float32)
    sq = max(lf.size)
    pad_m = np.zeros((sq, sq), np.float32)
    pad_a = np.zeros((sq, sq, 3), np.float32)
    oy = (sq - lf.height) // 2
    pad_m[oy:oy + lf.height] = m
    pad_a[oy:oy + lf.height] = alb
    s = shade(pad_a, pad_m, 0.6, 0.2)
    dd = ImageDraw.Draw(s)
    dd.line((sq * 0.08, sq / 2, sq * 0.9, sq / 2), fill=(40, 110, 40, 200), width=max(2, int(size * 0.05)))
    s = s.rotate(angle, resample=Image.BICUBIC, expand=True)
    im.alpha_composite(s, (int(x - s.width / 2), int(y - s.height / 2)))


def _stem(im, x0, y0, x1, y1, w, col=(110, 70, 35)):
    d = ImageDraw.Draw(im)
    d.line((x0, y0, x1, y1), fill=col + (255,), width=w)
    d.ellipse((x1 - w / 2, y1 - w / 2, x1 + w / 2, y1 + w / 2), fill=col + (255,))


def make_fruit(kind):
    """Renvoie (image RGBA SPRITE×SPRITE, centre du visage (x, y), échelle du visage, couleur des joues)."""
    S = SPRITE
    rnd = random.Random(kind)
    face, fs, blush = (0.5, 0.56), 1.0, (255, 120, 140)
    if kind == "pomme":
        m = _mask(lambda d, S: (d.ellipse((S * .1, S * .2, S * .58, S * .9), fill=255),
                                d.ellipse((S * .42, S * .2, S * .9, S * .9), fill=255),
                                d.ellipse((S * .2, S * .45, S * .8, S * .95), fill=255)))
        alb = _albedo(m, (230, 40, 45), (175, 20, 35))
        im = shade(alb, m)
        _stem(im, S * .5, S * .26, S * .54, S * .1, int(S * .035))
        _leaf(im, S * .64, S * .14, S * .13, 20)
        face = (0.5, 0.58)
    elif kind == "tomate":
        m = _mask(lambda d, S: d.ellipse((S * .1, S * .24, S * .9, S * .9), fill=255))
        im = shade(_albedo(m, (235, 55, 40), (200, 30, 30)), m)
        for a in range(0, 360, 60):
            _leaf(im, S * .5 + math.cos(math.radians(a)) * S * .07, S * .27 + math.sin(math.radians(a)) * S * .02, S * .09, -a, (60, 150, 50))
        face = (0.5, 0.6)
    elif kind == "cerise":
        m = _mask(lambda d, S: d.ellipse((S * .15, S * .3, S * .85, S * .95), fill=255))
        im = shade(_albedo(m, (200, 10, 40), (140, 0, 30)), m, 1.3)
        d = ImageDraw.Draw(im)
        d.arc((S * .5, S * -.05, S * 1.1, S * .7), 180, 250, fill=(90, 120, 40, 255), width=int(S * .03))
        _leaf(im, S * .72, S * .06, S * .12, -30)
        face = (0.5, 0.64)
    elif kind == "orange":
        m = _mask(lambda d, S: d.ellipse((S * .1, S * .15, S * .9, S * .95), fill=255))
        alb = _albedo(m, (255, 150, 20), (240, 120, 10))
        alb = _dots(alb, m, rnd, 260, S * .006, (235, 125, 5), S)
        im = shade(alb, m, 0.7)
        _leaf(im, S * .58, S * .14, S * .11, 25)
        face = (0.5, 0.56)
    elif kind == "citron":
        m = _mask(lambda d, S: (d.ellipse((S * .1, S * .22, S * .9, S * .9), fill=255),
                                d.polygon([(S * .02, S * .56), (S * .2, S * .46), (S * .2, S * .66)], fill=255),
                                d.polygon([(S * .98, S * .56), (S * .8, S * .46), (S * .8, S * .66)], fill=255)))
        alb = _dots(_albedo(m, (255, 228, 40)), m, rnd, 200, S * .005, (240, 205, 20), S)
        im = shade(alb, m, 0.8)
        face = (0.5, 0.58)
    elif kind == "peche":
        m = _mask(lambda d, S: (d.ellipse((S * .1, S * .18, S * .9, S * .95), fill=255)))
        alb = _albedo(m, (255, 175, 120), (245, 110, 90))
        im = shade(alb, m, 0.4)
        d = ImageDraw.Draw(im)
        d.arc((S * .2, S * .2, S * .62, S * .9), 300, 30, fill=(225, 100, 80, 160), width=int(S * .015))
        _leaf(im, S * .58, S * .17, S * .12, 30)
        face = (0.48, 0.6)
    elif kind == "poire":
        m = _mask(lambda d, S: (d.ellipse((S * .32, S * .12, S * .68, S * .52), fill=255),
                                d.ellipse((S * .14, S * .38, S * .86, S * .96), fill=255),
                                d.polygon([(S * .33, S * .38), (S * .67, S * .38), (S * .8, S * .6), (S * .2, S * .6)], fill=255)))
        im = shade(_albedo(m, (190, 215, 60), (160, 190, 40)), m)
        _stem(im, S * .5, S * .16, S * .47, S * .04, int(S * .03))
        face = (0.5, 0.66)
    elif kind == "raisin":
        m = _mask(lambda d, S: d.ellipse((S * .15, S * .2, S * .85, S * .95), fill=255))
        im = shade(_albedo(m, (130, 60, 170), (90, 30, 130)), m, 1.2)
        _stem(im, S * .5, S * .23, S * .5, S * .08, int(S * .03), (90, 110, 50))
        face = (0.5, 0.58)
    elif kind == "kiwi":
        m = _mask(lambda d, S: d.ellipse((S * .06, S * .25, S * .94, S * .92), fill=255))
        alb = _dots(_albedo(m, (140, 100, 55), (110, 75, 40)), m, rnd, 500, S * .004, (120, 85, 45), S)
        im = shade(alb, m, 0.15)
        face = (0.5, 0.58)
        blush = (230, 120, 110)
    elif kind == "fraise":
        m = _mask(lambda d, S: (d.ellipse((S * .1, S * .2, S * .9, S * .62), fill=255),
                                d.polygon([(S * .12, S * .45), (S * .88, S * .45), (S * .62, S * .9), (S * .5, S * .96), (S * .38, S * .9)], fill=255),
                                d.ellipse((S * .3, S * .7, S * .7, S * .97), fill=255)))
        alb = _dots(_albedo(m, (240, 40, 60), (200, 20, 45)), m, rnd, 60, S * .009, (255, 225, 110), S)
        im = shade(alb, m, 1.1)
        for a in (-50, -20, 10, 40, 70):
            _leaf(im, S * .5 + a * S * .0025, S * .22, S * .14, a + 10 if a < 10 else a - 10, (60, 170, 60))
        face = (0.5, 0.56)
    elif kind == "banane":
        def bd(d, S):
            left, right = [], []
            for k in range(61):  # banane debout, courbée, épaisse au milieu
                t = k / 60
                cx = S * (.42 + .32 * (2 * t - 1) ** 2)
                cy = S * (.06 + .9 * t)
                w = S * (.035 + .22 * math.sin(math.pi * t) ** .55)
                left.append((cx - w, cy))
                right.append((cx + w, cy))
            d.polygon(left + right[::-1], fill=255)
        m = _mask(bd)
        im = shade(_albedo(m, (255, 225, 55), (240, 195, 35)), m, 0.8, 0.09)
        d = ImageDraw.Draw(im)
        d.rounded_rectangle((S * .71, S * .0, S * .79, S * .09), 8, fill=(95, 70, 35, 255))
        d.ellipse((S * .68, S * .93, S * .76, S * .99), fill=(70, 50, 30, 255))
        face = (0.46, 0.5)
        fs = 0.85
    elif kind == "ananas":
        m = _mask(lambda d, S: d.ellipse((S * .2, S * .3, S * .8, S * .97), fill=255))
        alb = _albedo(m, (240, 175, 40), (210, 130, 30))
        im0 = Image.fromarray(alb.astype(np.uint8))
        d0 = ImageDraw.Draw(im0)
        for k in range(-12, 13):
            d0.line((S * .5 + k * S * .06 - S * .5, 0, S * .5 + k * S * .06 + S * .5, S), fill=(190, 120, 20), width=4)
            d0.line((S * .5 + k * S * .06 + S * .5, 0, S * .5 + k * S * .06 - S * .5, S), fill=(190, 120, 20), width=4)
        im = shade(np.asarray(im0).astype(np.float32), m, 0.5)
        for a in (-40, -20, 0, 20, 40):
            _leaf(im, S * .5 + a * S * .002, S * .2, S * .17, 90 + a * 1.4, (50, 150, 70))
        face = (0.5, 0.64)
    elif kind == "pasteque":
        m = _mask(lambda d, S: d.ellipse((S * .04, S * .2, S * .96, S * .96), fill=255))
        alb = _albedo(m, (60, 160, 60))
        im0 = Image.fromarray(alb.astype(np.uint8))
        d0 = ImageDraw.Draw(im0)
        for k in range(-3, 4):
            d0.ellipse((S * .5 + k * S * .14 - S * .05, S * .15, S * .5 + k * S * .14 + S * .05, S), fill=(30, 110, 40))
        im = shade(np.asarray(im0).astype(np.float32), m, 0.9)
        face = (0.5, 0.58)
        fs = 1.1
    elif kind == "avocat":
        m = _mask(lambda d, S: (d.ellipse((S * .3, S * .1, S * .7, S * .55), fill=255),
                                d.ellipse((S * .17, S * .35, S * .83, S * .96), fill=255),
                                d.polygon([(S * .3, S * .35), (S * .7, S * .35), (S * .8, S * .6), (S * .2, S * .6)], fill=255)))
        im = shade(_albedo(m, (70, 110, 40), (45, 80, 30)), m, 0.5)
        face = (0.5, 0.62)
    else:
        raise SystemExit(f"Fruit inconnu : {kind}")
    return im, (face[0] * S, face[1] * S), fs * S / 700, blush


# --------------------------------------------------------------------------- VISAGE

def draw_face(im, fc, fs, emo, mouth, blink, look, blush, t):
    """Yeux, sourcils, bouche, joues sur le personnage (image SPRITE)."""
    d = ImageDraw.Draw(im)
    fx, fy = fc
    k = fs
    ex, ey, er = 78 * k, -40 * k, 50 * k   # écart des yeux, hauteur, rayon
    BL = (25, 15, 20, 255)
    # joues
    if emo not in ("peur",):
        for sx in (-1, 1):
            cx = fx + sx * 128 * k
            d.ellipse((cx - 34 * k, fy + 20 * k, cx + 34 * k, fy + 44 * k), fill=blush + (110,))
    for sx in (-1, 1):
        cx, cy = fx + sx * ex, fy + ey
        rx, ry = er * 0.86, er
        if emo == "surpris" or emo == "peur":
            rx, ry = er * 0.95, er * 1.12
        if blink or emo == "pleure_ferme":
            d.arc((cx - rx, cy - ry * .5, cx + rx, cy + ry * .6), 15, 165, fill=BL, width=int(9 * k))
        elif emo == "content":  # yeux « ^ ^ »
            d.arc((cx - rx, cy - ry * .2, cx + rx, cy + ry * 1.2), 200, 340, fill=BL, width=int(11 * k))
        else:
            d.ellipse((cx - rx, cy - ry, cx + rx, cy + ry), fill=(255, 255, 255, 255), outline=BL, width=int(6 * k))
            pr = er * (0.42 if emo == "peur" else 0.55)
            px, py = cx + look[0] * er * .3, cy + look[1] * er * .25 + er * .12
            d.ellipse((px - pr, py - pr, px + pr, py + pr), fill=(30, 20, 25, 255))
            d.ellipse((px - pr * .55, py - pr * .7, px - pr * .05, py - pr * .2), fill=(255, 255, 255, 255))
            d.ellipse((px + pr * .25, py + pr * .2, px + pr * .5, py + pr * .45), fill=(255, 255, 255, 220))
            if emo == "malin":  # paupière à moitié fermée
                lid = im.getpixel((int(cx), int(cy - ry - 8 * k)))
                d.chord((cx - rx - 3, cy - ry - 3, cx + rx + 3, cy + ry + 3), 180, 360, fill=lid[:3] + (255,))
                d.line((cx - rx, cy, cx + rx, cy), fill=BL, width=int(7 * k))
        # sourcils
        by = cy - ry - 22 * k
        x_in, x_out = cx - sx * rx * .2, cx + sx * rx * 1.05
        if emo == "colere":
            pts = (x_out, by - 18 * k, x_in, by + 22 * k)
        elif emo in ("triste", "pleure", "peur"):
            pts = (x_out, by + 12 * k, x_in, by - 16 * k)
        elif emo == "surpris":
            pts = (x_out, by - 22 * k, x_in, by - 24 * k)
        elif emo == "malin":
            pts = (x_out, by - (20 if sx > 0 else 0) * k, x_in, by - 6 * k)
        else:
            pts = (x_out, by - 6 * k, x_in, by - 10 * k)
        d.line(pts, fill=BL, width=int(14 * k))
        for p in ((pts[0], pts[1]), (pts[2], pts[3])):
            d.ellipse((p[0] - 7 * k, p[1] - 7 * k, p[0] + 7 * k, p[1] + 7 * k), fill=BL)
        # larmes
        if emo == "pleure":
            ty = cy + ry + ((t * 160) % (120 * k))
            d.ellipse((cx - 11 * k, ty, cx + 11 * k, ty + 26 * k), fill=(120, 190, 255, 230))
            d.polygon([(cx - 11 * k, ty + 10 * k), (cx + 11 * k, ty + 10 * k), (cx, ty - 10 * k)], fill=(120, 190, 255, 230))
    # bouche
    my = fy + 48 * k
    mw = 46 * k
    if mouth > 0.08:
        oh = (10 + 62 * mouth) * k
        ow = mw * (0.8 + 0.4 * mouth) * (0.75 if emo in ("surpris", "peur") else 1)
        top = my - oh * .25
        d.ellipse((fx - ow, top, fx + ow, top + oh), fill=(90, 15, 30, 255), outline=BL, width=int(6 * k))
        if oh > 30 * k:
            d.chord((fx - ow * .6, top + oh * .45, fx + ow * .6, top + oh * 1.05), 180, 360, fill=(240, 100, 120, 255))
        d.chord((fx - ow * .7, top + 2 * k, fx + ow * .7, top + oh * .3), 0, 180, fill=(255, 255, 255, 255))
    else:
        if emo in ("content", "malin", "neutre"):
            span = (20, 160) if emo != "malin" else (10, 120)
            d.arc((fx - mw, my - 30 * k, fx + mw, my + 22 * k), span[0], span[1], fill=BL, width=int(9 * k))
        elif emo in ("triste", "pleure", "colere"):
            d.arc((fx - mw * .8, my + 2 * k, fx + mw * .8, my + 42 * k), 200, 340, fill=BL, width=int(9 * k))
        else:  # surpris / peur : petit « o »
            d.ellipse((fx - 15 * k, my - 6 * k, fx + 15 * k, my + 24 * k), fill=(90, 15, 30, 255), outline=BL, width=int(6 * k))
    if emo == "peur":  # goutte de sueur
        sx_, sy_ = fx + 170 * k, fy - 120 * k + (t * 40 % 30) * k
        d.ellipse((sx_ - 13 * k, sy_, sx_ + 13 * k, sy_ + 32 * k), fill=(150, 210, 255, 230))
        d.polygon([(sx_ - 12 * k, sy_ + 12 * k), (sx_ + 12 * k, sy_ + 12 * k), (sx_, sy_ - 14 * k)], fill=(150, 210, 255, 230))


def add_limbs(im, fc, fs, emo, t, talking):
    """Petits bras (traits noirs + mains rondes) : bougent quand le perso parle."""
    d = ImageDraw.Draw(im)
    S = im.width
    alpha = np.asarray(im.split()[3])
    rows = np.nonzero(alpha[int(fc[1] + 40 * fs)] > 128)[0]
    if not len(rows):
        return
    BL = (25, 15, 20, 255)
    y0 = fc[1] + 60 * fs
    for sx, x0 in ((-1, rows.min() + 10), (1, rows.max() - 10)):
        wav = math.sin(t * 7 + sx) * (0.6 if talking else 0.12)
        if emo in ("colere",):
            ang = -20 + wav * 30
        elif emo in ("surpris", "peur"):
            ang = -60 + wav * 15
        elif emo in ("pleure", "triste"):
            ang = 50
        else:
            ang = 20 + wav * 40
        L = 120 * fs
        x1 = x0 + sx * L * math.cos(math.radians(ang))
        y1 = y0 + L * math.sin(math.radians(ang))
        d.line((x0, y0, x1, y1), fill=BL, width=int(12 * fs))
        d.ellipse((x1 - 20 * fs, y1 - 20 * fs, x1 + 20 * fs, y1 + 20 * fs), fill=(255, 255, 255, 255), outline=BL, width=int(6 * fs))


_cache = {}


def character(kind, emo, mouth, blink, look, t, talking):
    if kind not in _cache:
        _cache[kind] = make_fruit(kind)
    base, fc, fs, blush = _cache[kind]
    pad = 120
    im = Image.new("RGBA", (SPRITE + 2 * pad, SPRITE + 2 * pad), (0, 0, 0, 0))
    im.alpha_composite(base, (pad, pad))
    fc2 = (fc[0] + pad, fc[1] + pad)
    add_limbs(im, fc2, fs, emo, t, talking)
    im.alpha_composite(base, (pad, pad))  # le corps passe devant l'épaule
    # petites jambes
    d = ImageDraw.Draw(im)
    alpha = np.asarray(base.split()[3])
    ys = np.nonzero(alpha.max(1) > 128)[0]
    yb = ys.max() + pad - 6
    for sx in (-1, 1):
        x = pad + SPRITE / 2 + sx * 70 * fs
        col = np.nonzero(alpha[:, int(x - pad)] > 128)[0]
        ytop = (col.max() + pad - 12) if len(col) else yb - 20
        d.line((x, ytop, x, yb + 55 * fs), fill=(25, 15, 20, 255), width=int(12 * fs))
        d.ellipse((x - 32 * fs + sx * 10, yb + 40 * fs, x + 32 * fs + sx * 10, yb + 72 * fs), fill=(255, 255, 255, 255), outline=(25, 15, 20, 255), width=int(6 * fs))
    draw_face(im, fc2, fs, emo, mouth, blink, look, blush, t)
    return im, yb + 72 * fs  # image, bas des pieds


# --------------------------------------------------------------------------- DÉCORS

def decor(lieu, seed):
    rnd = random.Random(seed)
    im = Image.new("RGB", (W, H), (0, 0, 0))
    d = ImageDraw.Draw(im)

    def vgrad(y0, y1, a, b):
        for y in range(int(y0), int(y1)):
            t = (y - y0) / max(1, y1 - y0)
            d.line((0, y, W, y), fill=tuple(int(a[i] * (1 - t) + b[i] * t) for i in range(3)))
    top = FLOOR - 80
    if lieu == "cuisine":
        vgrad(0, top, (255, 236, 205), (250, 215, 175))
        for y in range(0, top, 110):  # carrelage
            for x in range(-55 * ((y // 110) % 2), W, 110):
                d.rounded_rectangle((x + 4, y + 4, x + 106, y + 106), 10, fill=(255, 247, 230), outline=(235, 210, 175), width=3)
        d.rounded_rectangle((120, 260, 620, 820), 24, fill=(150, 210, 255), outline=(255, 255, 255), width=26)
        d.line((370, 270, 370, 810), fill=(255, 255, 255), width=18)
        d.line((130, 540, 610, 540), fill=(255, 255, 255), width=18)
        d.ellipse((440, 330, 560, 450), fill=(255, 240, 150))
        d.rectangle((700, 300, 1000, 900), fill=(90, 160, 150))
        d.rectangle((715, 315, 985, 590), outline=(70, 130, 120), width=8)
        d.rectangle((715, 610, 985, 885), outline=(70, 130, 120), width=8)
        vgrad(top, H, (200, 140, 90), (150, 95, 60))
        d.rectangle((0, top, W, top + 26), fill=(230, 180, 130))
    elif lieu == "frigo":
        vgrad(0, H, (225, 245, 255), (175, 215, 245))
        for y in (380, 800):
            d.rectangle((0, y, W, y + 22), fill=(245, 252, 255))
            d.rectangle((0, y + 22, W, y + 36), fill=(190, 220, 240))
        d.rectangle((120, 200, 260, 380), fill=(255, 255, 255))
        d.rectangle((300, 240, 420, 380), fill=(250, 220, 120))
        d.ellipse((620, 650, 780, 800), fill=(250, 245, 230))
        d.ellipse((800, 660, 940, 800), fill=(250, 245, 230))
        vgrad(top, H, (230, 245, 255), (190, 220, 240))
        d.rectangle((0, top, W, top + 22), fill=(255, 255, 255))
    elif lieu == "plage":
        vgrad(0, 900, (90, 190, 255), (190, 235, 255))
        d.ellipse((700, 160, 900, 360), fill=(255, 230, 90))
        vgrad(900, top, (40, 170, 210), (30, 140, 190))
        for k in range(8):
            y = 920 + k * 45
            d.arc((rnd.randint(-100, 900), y, rnd.randint(200, 1200), y + 30), 200, 340, fill=(220, 245, 255), width=5)
        vgrad(top, H, (250, 225, 160), (235, 200, 130))
        d.rectangle((60, 500, 90, top), fill=(140, 95, 50))
        for a in (-40, -10, 20, 50, 160, 190, 220):
            x1, y1 = 75 + 230 * math.cos(math.radians(a)), 500 + 120 * math.sin(math.radians(a))
            d.line((75, 500, x1, y1), fill=(50, 160, 70), width=36)
    elif lieu == "marche":
        vgrad(0, top, (130, 200, 255), (210, 240, 255))
        for k in range(0, W, 120):
            d.rectangle((k, 120, k + 60, 330), fill=(230, 50, 60))
            d.rectangle((k + 60, 120, k + 120, 330), fill=(255, 255, 255))
        for k in range(0, W, 120):
            d.pieslice((k, 270, k + 120, 390), 0, 180, fill=(230, 50, 60) if (k // 120) % 2 == 0 else (255, 255, 255))
        for x in range(0, W, 270):
            d.rectangle((x + 10, 700, x + 260, top), fill=(190, 130, 70), outline=(140, 90, 45), width=8)
            for i in range(9):
                d.ellipse((x + 20 + (i % 3) * 78, 640 + (i // 3) * 0, x + 98 + (i % 3) * 78, 718), fill=[(240, 120, 30), (220, 40, 50), (250, 220, 50)][(x // 270 + i) % 3])
        vgrad(top, H, (180, 170, 160), (140, 130, 120))
    else:  # table
        vgrad(0, top, (255, 220, 225), (245, 190, 200))
        d.rectangle((0, 980, W, 1010), fill=(255, 255, 255))
        for k in range(5):
            d.rectangle((150 + k * 170, 300, 270 + k * 170, 520), outline=(230, 160, 170), width=10)
        vgrad(top, H, (255, 255, 255), (235, 235, 235))
        for x in range(0, W, 90):
            for y in range(top, H, 90):
                if ((x + y) // 90) % 2 == 0:
                    d.rectangle((x, y, x + 90, y + 90), fill=(230, 60, 70))
    im = im.filter(ImageFilter.GaussianBlur(7))  # profondeur de champ : les persos ressortent
    # vignette douce
    v = Image.new("L", (W, H), 0)
    ImageDraw.Draw(v).ellipse((-300, -200, W + 300, H + 200), fill=255)
    v = v.filter(ImageFilter.GaussianBlur(160))
    return Image.composite(im, Image.blend(im, Image.new("RGB", (W, H), (20, 10, 20)), 0.45), v)


# --------------------------------------------------------------------------- TEXTE

def text_c(d, xy, txt, size, fill=WHITE, stroke=10, maxw=None):
    maxw = maxw or (SAFE_R - SAFE_L)
    while size > 30 and d.textlength(txt, font=font(size)) > maxw:
        size -= 4
    d.text(xy, txt, font=font(size), fill=fill, anchor="mm", stroke_width=stroke, stroke_fill=(0, 0, 0))


def chunks(text, n=3):
    """Découpe la réplique en morceaux de 1-3 mots pour les sous-titres."""
    words = text.replace("…", "… ").split()
    out, cur = [], []
    for w in words:
        cur.append(w)
        if len(cur) >= n or w[-1] in ".?!,…" and len(cur) >= 1:
            out.append(" ".join(cur))
            cur = []
    if cur:
        out.append(" ".join(cur))
    return out


# --------------------------------------------------------------------------- SON

def say(text, voix, retry=0):
    if os.environ.get("FRUITS_VOICE", "1") == "0":
        return np.zeros(int(SR * (0.4 + len(text) / 16)), np.float32), True
    sys.path.insert(0, os.path.join(ROOT, "engine"))
    import voice
    ref, exag, pitch = VOICES[voix]
    voice.CB_REF = os.path.join(ROOT, "assets", "ref", ref)
    voice.CB_EXAG = exag
    voice.TEMPO = 1.12
    voice.RETRY = retry  # autre tirage si la réplique est mal lue
    a = voice.synth(text)
    if pitch != 1.0:
        a = _pitch(a, pitch)
    return a, False


def _pitch(a, p):
    with tempfile.TemporaryDirectory() as d:
        src, dst = os.path.join(d, "a.wav"), os.path.join(d, "b.wav")
        write_wav(src, a)
        subprocess.run(["ffmpeg", "-loglevel", "error", "-y", "-i", src, "-af",
                        f"asetrate={SR}*{p},aresample={SR},atempo={1 / p:.4f}", dst], check=True)
        with wave.open(dst) as wf:
            return np.frombuffer(wf.readframes(wf.getnframes()), np.int16).astype(np.float32) / 32768


def write_wav(path, x):
    with wave.open(path, "wb") as wf:
        wf.setnchannels(1)
        wf.setsampwidth(2)
        wf.setframerate(SR)
        wf.writeframes((np.clip(x, -1, 1) * 32767).astype(np.int16).tobytes())


def sfx(kind):
    t = np.arange(int(1.6 * SR)) / SR
    if kind == "dun":  # « dun dun DUN » grave
        out = np.zeros_like(t)
        for k, (st, f) in enumerate(((0, 98), (0.32, 92.5), (0.64, 73.4))):
            a = int(st * SR)
            tt = t[: len(t) - a]
            env = np.exp(-tt * (2.2 if k == 2 else 6))
            out[a:] += (np.sin(2 * np.pi * f * tt) + 0.5 * np.sin(2 * np.pi * f * 2 * tt) + 0.3 * np.sign(np.sin(2 * np.pi * f * tt)) * 0.3) * env * (0.5 if k < 2 else 0.7)
        return (out * 0.55).astype(np.float32)
    if kind == "choc":  # coup + souffle
        n = np.random.default_rng(3).standard_normal(len(t))
        return ((np.sin(2 * np.pi * (60 + 80 * np.exp(-t * 20)) * t) * 0.8 + n * 0.15) * np.exp(-t * 5) * 0.5).astype(np.float32)
    if kind == "tiroir":  # glissement + cliquetis métallique
        n = np.random.default_rng(5).standard_normal(len(t))
        slide = n * 0.12 * np.clip(np.sin(np.pi * t / 0.9), 0, 1) * (t < 0.9)
        clink = sum(np.sin(2 * np.pi * f * t) for f in (2400, 3150, 4100)) * np.exp(-np.clip(t - 0.95, 0, None) * 12) * (t > 0.95) * 0.12
        return (slide + clink).astype(np.float32)
    if kind == "zing":  # lame qui brille
        return (sum(np.sin(2 * np.pi * f * t) for f in (3000, 4500, 6100)) * np.exp(-t * 3) * 0.08).astype(np.float32)
    return np.zeros(1, np.float32)


def music(dur, seed):
    """Musique de « télénovela » douce : accords mineurs en pizzicato, 100 % générée."""
    n = int(dur * SR)
    t = np.arange(n) / SR
    out = np.zeros(n, np.float32)
    beat = 60 / 96
    prog = [(220, 261.6, 329.6), (174.6, 220, 261.6), (196, 246.9, 293.7), (164.8, 207.7, 246.9)]
    for k in range(int(dur / beat) + 1):
        a = int(k * beat * SR)
        if a >= n:
            break
        ch = prog[(k // 4) % 4]
        f = ch[k % 3] if k % 4 != 0 else ch[0] / 2
        m = min(n - a, int(0.7 * SR))
        tt = np.arange(m) / SR
        out[a:a + m] += (np.sin(2 * np.pi * f * tt) + 0.3 * np.sin(4 * np.pi * f * tt)) * np.exp(-tt * 6) * 0.07
    return out


# --------------------------------------------------------------------------- MISE EN SCÈNE

def envelope(a, fps=FPS):
    hop = SR // fps
    m = len(a) // hop + 1
    e = np.array([np.sqrt(np.mean(a[i * hop:(i + 1) * hop] ** 2)) if i * hop < len(a) else 0 for i in range(m)])
    if e.max() > 0:
        e = e / (np.percentile(e, 95) + 1e-6)
    return np.clip(e, 0, 1)


def knife(im, prog):
    """Gros couteau de cuisine qui descend d'en haut (twist final)."""
    k = Image.new("RGBA", (520, 1500), (0, 0, 0, 0))
    d = ImageDraw.Draw(k)
    OL = (20, 20, 30, 255)
    d.rounded_rectangle((150, 0, 370, 520), 50, fill=(45, 30, 25, 255), outline=OL, width=10)
    for y in (90, 250, 410):
        d.ellipse((240, y, 280, y + 40), fill=(210, 210, 215, 255), outline=OL, width=4)
    d.rectangle((140, 500, 380, 560), fill=(150, 150, 160, 255), outline=OL, width=8)
    d.polygon([(150, 560), (380, 560), (380, 1300), (150, 1480), (150, 560)], fill=(170, 180, 195, 255), outline=OL)
    d.polygon([(150, 560), (230, 560), (230, 1420), (150, 1480)], fill=(225, 232, 242, 255))
    d.line((150, 560, 150, 1480), fill=OL, width=10)
    d.line((380, 560, 380, 1300, 150, 1480), fill=OL, width=10, joint="curve")
    d.line((300, 640, 300, 1250), fill=(255, 255, 255, 200), width=10)
    y = int(-1500 + prog * 1150)
    im.alpha_composite(k, (CX - 260 + 40, y))


def render(spec_path, out):
    spec = json.load(open(spec_path))
    seed = zlib.crc32(os.path.basename(spec_path).encode())
    cast = spec["cast"]
    names = list(cast)
    nc = len(names)
    # positions des persos (centre x) dans le plan large
    x0, x1 = (SAFE_L, SAFE_R) if nc <= 2 else (30, W - 60)
    xs = {nm: x0 + (x1 - x0) * (k + .5) / nc for k, nm in enumerate(names)}
    bg = decor(spec.get("lieu", "cuisine"), seed)
    # ---- voix
    lines = []
    silent = False
    for i, ln in enumerate(spec["lines"]):
        a, silent = say(ln.get("voice", ln["text"]), cast[ln["who"]]["voix"], ln.get("retry", 0))
        gap = 0.18
        lines.append(dict(ln, audio=a, dur=len(a) / SR + gap))
        print(f"  voix {i + 1}/{len(spec['lines'])}", file=sys.stderr)
    twist = spec.get("twist")
    end_dur = 3.0
    twist_dur = 2.2 if twist else 0
    total = sum(l["dur"] for l in lines) + twist_dur + end_dur
    voice_tr = np.zeros(int((total + 1) * SR), np.float32)
    fx_tr = np.zeros_like(voice_tr)
    pos = 0.0
    for l in lines:
        l["t0"] = pos
        a = int(pos * SR)
        voice_tr[a:a + len(l["audio"])] += l["audio"]
        if l.get("sfx"):
            s = sfx(l["sfx"])
            fx_tr[a:a + len(s)] += s[: len(fx_tr) - a]
        pos += l["dur"]
    t_twist = pos
    if twist:
        s = sfx("zing")
        a = int((t_twist + 0.6) * SR)
        fx_tr[a:a + len(s)] += s
        s = sfx("dun")
        a = int((t_twist + 0.9) * SR)
        fx_tr[a:a + len(s)] += s
    t_end = t_twist + twist_dur
    mix = voice_tr + fx_tr + music(len(voice_tr) / SR, seed) * (0.5 if not silent else 1)
    envs = [envelope(l["audio"]) for l in lines]
    rnd = random.Random(seed)
    blinks = {nm: sorted(rnd.uniform(0, total) for _ in range(int(total / 2.8))) for nm in names}
    emo_now = {nm: "neutre" for nm in names}
    for l in lines:  # émotion de départ = 1re émotion du perso
        if emo_now[l["who"]] == "neutre":
            emo_now[l["who"]] = l.get("emo", "neutre")

    def frame(t):
        # réplique en cours
        li = None
        for i, l in enumerate(lines):
            if l["t0"] <= t < l["t0"] + l["dur"]:
                li = i
        speaker = lines[li]["who"] if li is not None else None
        emos = dict(emo_now)
        for l in lines:  # chaque perso garde l'émotion de sa dernière réplique
            if l["t0"] <= t:
                emos[l["who"]] = l.get("emo", "neutre")
        if t >= t_twist and twist:
            emos = {nm: "peur" for nm in names}
        # caméra
        shot = "duo"
        if li is not None:
            shot = lines[li].get("shot", "proche" if nc > 1 else "duo")
        if t >= t_twist:
            shot = "duo"
        if shot == "proche":
            z, cx = {1: 1.0, 2: 1.35}.get(nc, 1.7), xs[speaker]
        else:
            z, cx = 1.0, (SAFE_L + SAFE_R) / 2
        # petit zoom lent pendant la réplique + choc
        lt = t - lines[li]["t0"] if li is not None else 0
        z *= 1 + 0.025 * lt
        if li is not None and lines[li].get("sfx") in ("choc", "dun") and lt < 0.25:
            z *= 1 + 0.12 * (1 - lt / 0.25)
        shake = 0
        if t >= t_twist + 0.9 and t < t_end:
            shake = 10 * math.sin(t * 60)
        # fond (zoom autour de la ligne du sol)
        bz = 1 + (z - 1) * 0.5
        bw, bh = int(W / bz), int(H / bz)
        bx = int(min(max(0, (cx - W / 2) * 0.5 + (W - bw) / 2), W - bw))
        by = int((FLOOR - FLOOR / bz) * 0.9)
        by = min(max(0, by), H - bh)
        im = bg.crop((bx, by, bx + bw, by + bh)).resize((W, H), Image.BILINEAR).convert("RGBA")
        # personnages
        size = {1: 0.95, 2: 0.72, 3: 0.6}.get(nc, 0.46)
        order = sorted(names, key=lambda nm: nm == speaker)
        for nm in order:
            c = cast[nm]
            talking = nm == speaker
            mouth = 0.0
            if talking:
                e = envs[li]
                fi = int(lt * FPS)
                mouth = float(e[fi]) if fi < len(e) else 0
            bl = any(0 <= t - b < 0.13 for b in blinks[nm])
            look = ((xs[speaker] - xs[nm]) / 300 if speaker and not talking else 0, 0.2 if talking else 0)
            look = (max(-1, min(1, look[0])), look[1])
            sp, foot = character(c["fruit"], emos[nm], mouth, bl, look, t + xs[nm], talking)
            s = size * z
            hop = (abs(math.sin(t * 9)) * 18 * mouth if talking else 0)
            squash = 1 + (0.035 * mouth if talking else 0.012 * math.sin(t * 2.4 + xs[nm]))
            sw, sh = int(sp.width * s * (2 - squash) ** .5), int(sp.height * s * squash)
            spr = sp.resize((sw, sh), Image.BILINEAR)
            spread = 1.5 if (z > 1.2 and not talking) else 1.0  # en gros plan, les autres sont poussés sur les bords
            sx = (xs[nm] - cx) * z * spread + W / 2 - sw / 2 + shake
            sy = FLOOR + 110 * (z - 1) - foot * s * squash - hop
            # ombre
            sh_im = Image.new("RGBA", (int(sw * .6), int(40 * s * 2)), (0, 0, 0, 0))
            ImageDraw.Draw(sh_im).ellipse((0, 0, sh_im.width, sh_im.height), fill=(0, 0, 0, 90))
            sh_im = sh_im.filter(ImageFilter.GaussianBlur(10))
            im.alpha_composite(sh_im, (int(sx + sw * .2), int(sy + foot * s * squash - sh_im.height / 2 + hop)))
            im.alpha_composite(spr, (int(sx), int(sy)))
        d = ImageDraw.Draw(im)
        if twist and t >= t_twist:
            im.alpha_composite(Image.new("RGBA", (W, H), (60, 0, 10, int(min(1, (t - t_twist) / 0.5) * 120))))
            knife(im, min(1, (t - t_twist) / 1.0) ** 0.7)
            if t_twist + 0.9 <= t < t_twist + 1.0:
                im.alpha_composite(Image.new("RGBA", (W, H), (255, 255, 255, 110)))
        # accroche (1re réplique) + sous-titres
        if li == 0 and spec.get("hook"):
            text_c(d, (CX, 300), spec["hook"], 100, YELLOW, 11)
        if li is not None and t < t_twist:
            l = lines[li]
            ch = l.setdefault("_chunks", chunks(l["text"]))
            speak = l["dur"] - 0.18
            lens = np.cumsum([len(c) + 2 for c in ch])
            frac = min(0.999, lt / max(0.1, speak))
            k = int(np.searchsorted(lens / lens[-1], frac, side="right"))
            k = min(k, len(ch) - 1)
            nm = cast[l["who"]].get("nom", l["who"]).upper()
            text_c(d, (CX, 470), nm, 58, cast[l["who"]].get("couleur") and tuple(cast[l["who"]]["couleur"]) or YELLOW, 8)
            text_c(d, (CX, 570), ch[k].upper(), 104, WHITE, 12)
        if t >= t_end:
            ov = Image.new("RGBA", (W, H), (0, 0, 0, 150))
            im.alpha_composite(ov)
            d = ImageDraw.Draw(im)
            for j, ln in enumerate(wrap_lines(d, spec.get("end", "LA SUITE ?"), 110, SAFE_R - SAFE_L)):
                text_c(d, (CX, 720 + j * 130), ln, 110, YELLOW, 11)
            text_c(d, (CX, 1060), "RÉPONDS EN COMMENTAIRE", 70, WHITE, 8)
            text_c(d, (CX, 1180), "ABONNE-TOI POUR LA SUITE", 64, WHITE, 8)
        return im

    with tempfile.TemporaryDirectory() as tmp:
        wav = os.path.join(tmp, "a.wav")
        write_wav(wav, mix[: int(total * SR)] * 0.8)
        if os.environ.get("FRUITS_STILL"):
            frame(float(os.environ["FRUITS_STILL"])).convert("RGB").save(out)
            return
        cmd = ["ffmpeg", "-loglevel", "error", "-y", "-f", "rawvideo", "-pix_fmt", "rgb24", "-s", f"{W}x{H}",
               "-r", str(FPS), "-i", "-", "-i", wav, "-c:v", "libx264", "-preset", "medium", "-crf", "20",
               "-pix_fmt", "yuv420p", "-c:a", "aac", "-b:a", "160k",
               "-af", "acompressor=threshold=-20dB:ratio=3:attack=3:release=120,loudnorm=I=-14:TP=-1.5:LRA=9,aresample=44100",
               "-shortest", "-movflags", "+faststart", out]
        p = subprocess.Popen(cmd, stdin=subprocess.PIPE)
        nf = int(total * FPS)
        for k in range(nf):
            p.stdin.write(np.asarray(frame(k / FPS).convert("RGB")).tobytes())
            if k % 150 == 0:
                print(f"  image {k}/{nf}", file=sys.stderr)
        p.stdin.close()
        if p.wait():
            raise SystemExit("ffmpeg a échoué")
    print(f"OK {out} ({total:.1f} s)")


def wrap_lines(d, txt, size, maxw):
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


def casting(out):
    kinds = ["pomme", "banane", "fraise", "orange", "citron", "poire", "raisin", "ananas", "pasteque", "kiwi", "cerise", "peche", "avocat", "tomate"]
    emos = ["neutre", "colere", "malin", "pleure", "surpris", "peur", "content", "triste", "colere", "neutre", "content", "malin", "surpris", "triste"]
    cell = 360
    sheet = Image.new("RGB", (cell * 5, cell * 3), (250, 220, 190))
    for i, (k, e) in enumerate(zip(kinds, emos)):
        sp, _ = character(k, e, 0.6 if i % 3 == 0 else 0, False, (0, 0), 0.3, i % 3 == 0)
        sp.thumbnail((cell, cell))
        sheet.paste(sp, ((i % 5) * cell + (cell - sp.width) // 2, (i // 5) * cell), sp)
        ImageDraw.Draw(sheet).text(((i % 5) * cell + 10, (i // 5) * cell + 5), f"{k} · {e}", fill=(0, 0, 0))
    sheet.save(out)


if __name__ == "__main__":
    if sys.argv[1] == "--casting":
        casting(sys.argv[2])
    else:
        render(sys.argv[1], sys.argv[2])
