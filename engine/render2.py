"""Moteur de rendu, style 2 (« cinéma TikTok »), demandé par Fio le 01/11.

Usage : python3 engine/render2.py episodes/epNN.json sortie.mp4

Inspiré de la vidéo de référence envoyée par Fio :
- cadrage serré : le personnage remplit l'écran (gros plans, vue de dos,
  plan assis), la caméra bouge en continu (zoom/panoramique doux) ;
- sous-titres géants 1 à 2 mots à la fois, calés sur la voix ;
- décors en dégradés violet nuit / orange, lumières douces ;
- grosse horloge qui défile en haut, rien d'autre à l'écran ;
- voix rapide et propre (sans effet radio), plans enchaînés sans blanc.

Format d'un plan (beat) :
  {"scene": "chambre", "text": "IL EST *2 H 47*.", "voice": "...",
   "char": {"pose": "sit|stand|back|face", "expr": "normal|side|wide|scared|closed",
            "x": 0.5, "y": 0.95, "h": 0.6, "hoodie": [230,120,30]},
   "cam": {"z": [1.05, 1.15], "x": [0.5, 0.5], "y": [0.5, 0.5]},
   "sfx": [["hit", 0, 0.8]], "choice": {...}, "record": "r1" / {"type":"rewind","of":"r1"}}
Les anciens décors (bunker, radio, door, notebook...) restent utilisables :
ils sont recolorés dans la palette du style 2.
"""
import json
import math
import os
import random
import subprocess
import sys
import tempfile

import numpy as np
from PIL import Image, ImageDraw, ImageFilter, ImageFont

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import render as R  # noqa: E402

W, H, FPS, SR = R.W, R.H, R.FPS, R.SR
ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
FONT = os.path.join(ROOT, "assets", "fonts", "Anton-Regular.ttf")
K = 1.25            # le décor est plus grand que l'écran pour que la caméra bouge
CW, CH = int(W * K), int(H * K)
SSF = 2             # suréchantillonnage des dessins
RED = (255, 64, 64)
WHITE = (255, 255, 255)
RIM = (225, 225, 255)

_fonts = {}


def font(size):
    if size not in _fonts:
        _fonts[size] = ImageFont.truetype(FONT, size)
    return _fonts[size]


def smooth(t):
    t = min(1.0, max(0.0, t))
    return t * t * (3 - 2 * t)


# ------------------------------------------------------------------ dessin

class Canvas:
    """Dessin en coordonnées fractionnaires (u, v) sur une toile suréchantillonnée."""

    def __init__(self, top, bottom, w=CW, h=CH):
        self.w, self.h = w * SSF, h * SSF
        self.img = R.gradient(self.w, self.h, top, bottom)
        self.d = ImageDraw.Draw(self.img)

    def P(self, u, v):
        return (u * self.w, v * self.h)

    def box(self, u0, v0, u1, v1):
        return [u0 * self.w, v0 * self.h, u1 * self.w, v1 * self.h]

    def glow(self, u, v, r, color, strength):
        self.img = R.glow(self.img, self.P(u, v), r * self.w, color, strength)
        self.d = ImageDraw.Draw(self.img)

    def soft(self, draw_fn, blur, alpha=255):
        layer = Image.new("RGBA", (self.w, self.h), (0, 0, 0, 0))
        draw_fn(ImageDraw.Draw(layer), self)
        layer = layer.filter(ImageFilter.GaussianBlur(blur * self.w))
        if alpha < 255:
            a = layer.getchannel("A").point(lambda x: x * alpha // 255)
            layer.putalpha(a)
        self.img.paste(layer, (0, 0), layer)
        self.d = ImageDraw.Draw(self.img)

    def done(self):
        return self.img.resize((self.w // SSF, self.h // SSF), Image.LANCZOS)


NIGHT = ((22, 18, 48), (88, 56, 120))     # ciel : haut, horizon
FIRE = (255, 130, 60)


def ruined_skyline(c, base_v, color, seed, scale=1.0, lit=0.10, fire=True):
    rnd = random.Random(seed)
    u = -0.02
    d = c.d
    while u < 1.02:
        bw = rnd.uniform(0.07, 0.16) * scale
        bh = rnd.uniform(0.06, 0.20) * scale
        top = base_v - bh
        pts = [c.P(u, base_v), c.P(u, top)]
        for i in range(1, rnd.randint(2, 4) + 1):
            pts.append(c.P(u + bw * i / 5, top + rnd.uniform(-0.004, 0.03) * scale))
        pts += [c.P(u + bw, top + rnd.uniform(0, 0.02) * scale), c.P(u + bw, base_v)]
        d.polygon(pts, fill=color)
        wv = top + 0.02 * scale
        while wv < base_v - 0.012:
            wu = u + 0.012 * scale
            while wu < u + bw - 0.02 * scale:
                if rnd.random() < lit:
                    col = rnd.choice([(255, 196, 110), (255, 160, 80), (255, 220, 150)])
                    d.rectangle(c.box(wu, wv, wu + 0.008 * scale, wv + 0.006 * scale), fill=col)
                wu += 0.02 * scale
            wv += 0.016 * scale
        u += bw + rnd.uniform(-0.01, 0.02)
    if fire:
        c.glow(0.7, base_v, 0.45, FIRE, 0.28)


def night_sky(c, u0, v0, u1, v1, moon=(0.7, 0.3), seed=1, horizon=0.85):
    """Ciel nocturne + ville en ruine dans le rectangle (fractions du rectangle)."""
    sub = Canvas(NIGHT[0], NIGHT[1], int((u1 - u0) * c.w / SSF), int((v1 - v0) * c.h / SSF))
    sub.glow(0.5, horizon, 0.9, (200, 90, 90), 0.35)
    rnd = random.Random(seed)
    for _ in range(60):
        x, y = rnd.uniform(0, 1), rnd.uniform(0, 0.6)
        r = rnd.uniform(0.0015, 0.004)
        sub.d.ellipse(sub.box(x - r, y - r * sub.w / sub.h, x + r, y + r * sub.w / sub.h), fill=(220, 220, 255))
    if moon:
        mu, mv = moon
        sub.glow(mu, mv, 0.45, (200, 190, 255), 0.35)
        r = 0.07
        sub.d.ellipse(sub.box(mu - r, mv - r * sub.w / sub.h, mu + r, mv + r * sub.w / sub.h), fill=(255, 252, 235))
    ruined_skyline(sub, horizon + 0.02, (40, 28, 66), seed + 3, 1.4, 0.06)
    ruined_skyline(sub, 1.0, (24, 16, 40), seed + 7, 2.0, 0.12)
    img = sub.done().resize((int((u1 - u0) * c.w), int((v1 - v0) * c.h)), Image.LANCZOS)
    c.img.paste(img, (int(u0 * c.w), int(v0 * c.h)))
    c.d = ImageDraw.Draw(c.img)


def scene_chambre(p):
    """L'abri, vue de côté : fenêtre sur la ville en ruine, canapé, horloge."""
    c = Canvas((60, 44, 100), (26, 20, 50))
    night_sky(c, 0.10, 0.16, 0.56, 0.50, moon=(0.72, 0.28), seed=p.get("seed", 2))
    d = c.d
    fr = (22, 16, 40)
    d.rectangle(c.box(0.09, 0.15, 0.57, 0.165), fill=fr)
    d.rectangle(c.box(0.09, 0.495, 0.57, 0.51), fill=fr)
    d.rectangle(c.box(0.09, 0.15, 0.10, 0.51), fill=fr)
    d.rectangle(c.box(0.56, 0.15, 0.57, 0.51), fill=fr)
    d.rectangle(c.box(0.325, 0.16, 0.335, 0.50), fill=fr)
    d.rectangle(c.box(0.10, 0.325, 0.56, 0.333), fill=fr)
    # rayon de lune sur le sol
    c.soft(lambda dd, cc: dd.polygon([cc.P(0.10, 0.51), cc.P(0.56, 0.51), cc.P(0.85, 0.95), cc.P(0.25, 0.95)],
                                     fill=(150, 130, 220, 70)), 0.02)
    # horloge murale
    d = c.d
    d.ellipse(c.box(0.70, 0.22, 0.80, 0.22 + 0.10 * CW / CH), fill=(30, 24, 54), outline=(150, 140, 200), width=8)
    cu, cv = 0.75, 0.22 + 0.05 * CW / CH
    d.line([c.P(cu, cv), c.P(cu + 0.025, cv - 0.006)], fill=(220, 220, 240), width=8)
    d.line([c.P(cu, cv), c.P(cu - 0.004, cv - 0.022)], fill=(220, 220, 240), width=8)
    # sol + canapé
    d.rectangle(c.box(0, 0.74, 1, 1), fill=(22, 16, 40))
    d.rounded_rectangle(c.box(0.04, 0.56, 0.96, 0.66), radius=60, fill=(66, 54, 118))
    d.rounded_rectangle(c.box(0.02, 0.63, 0.98, 0.76), radius=60, fill=(80, 66, 140))
    d.rounded_rectangle(c.box(0.06, 0.75, 0.10, 0.79), radius=10, fill=(30, 22, 50))
    d.rounded_rectangle(c.box(0.90, 0.75, 0.94, 0.79), radius=10, fill=(30, 22, 50))
    if p.get("lamp"):
        c.glow(0.88, 0.5, 0.35, FIRE, 0.25)
    return c.done()


def scene_fenetre(p):
    """Grande baie vitrée sur la ville en ruine (pour la vue de dos)."""
    c = Canvas((34, 26, 64), (18, 14, 36))
    night_sky(c, 0.06, 0.07, 0.94, 0.66, moon=tuple(p.get("moon", (0.66, 0.22))), seed=p.get("seed", 5), horizon=0.8)
    d = c.d
    fr = (16, 12, 30)
    for box in ((0.05, 0.06, 0.95, 0.075), (0.05, 0.655, 0.95, 0.67), (0.05, 0.06, 0.065, 0.67),
                (0.935, 0.06, 0.95, 0.67), (0.495, 0.07, 0.505, 0.66)):
        d.rectangle(c.box(*box), fill=fr)
    d.rectangle(c.box(0, 0.67, 1, 1), fill=(20, 15, 38))
    if p.get("figure"):
        # silhouette immobile dehors
        fu = p["figure"]
        d.ellipse(c.box(fu - 0.012, 0.565, fu + 0.012, 0.565 + 0.024 * CW / CH), fill=(6, 4, 12))
        d.rounded_rectangle(c.box(fu - 0.014, 0.578, fu + 0.014, 0.63), radius=8, fill=(6, 4, 12))
    if p.get("green"):
        c.glow(0.3, 0.5, 0.35, (90, 255, 120), 0.4)
    return c.done()


def scene_rue(p):
    """Rue en ruine au crépuscule, perspective."""
    c = Canvas((40, 24, 74), (250, 130, 80))
    c.glow(0.5, 0.62, 0.7, (255, 170, 100), 0.5)
    d = c.d
    rnd = random.Random(p.get("seed", 9))
    for side in (0, 1):
        for i in range(6):
            t = i / 6
            near = 1 - t
            bw = 0.10 + 0.22 * near
            u = (0.5 - 0.08 - bw * 0.2 - t * 0.0) if side == 0 else 0.58
            ux0 = 0.42 - (0.42 * near) - bw if side == 0 else 0.58 + 0.42 * near
            ux0 = max(-0.2, ux0) if side == 0 else min(1.1, ux0)
            top = 0.62 - (0.12 + 0.5 * near) + rnd.uniform(-0.03, 0.03)
            col = R.mix((70, 40, 90), (14, 10, 26), near)
            x0, x1 = (ux0, ux0 + bw) if side == 0 else (ux0, ux0 + bw)
            pts = [c.P(x0, 0.66), c.P(x0, top), c.P((x0 + x1) / 2, top + rnd.uniform(0, 0.05)), c.P(x1, top + rnd.uniform(0, 0.03)), c.P(x1, 0.66)]
            d.polygon(pts, fill=col)
            for k in range(int(8 * near) + 2):
                if rnd.random() < 0.35:
                    wu, wv = rnd.uniform(x0 + 0.01, x1 - 0.03), rnd.uniform(top + 0.03, 0.62)
                    d.rectangle(c.box(wu, wv, wu + 0.015 * near + 0.005, wv + 0.012 * near + 0.004), fill=(255, 190, 110))
            del u
    d.polygon([c.P(0.46, 0.66), c.P(0.54, 0.66), c.P(1.2, 1.0), c.P(-0.2, 1.0)], fill=(30, 22, 44))
    # marquage au sol effacé
    for k in range(6):
        v0 = 0.68 + k * 0.05 * (1 + k * 0.25)
        d.polygon([c.P(0.497 - 0.002 * k, v0), c.P(0.503 + 0.002 * k, v0), c.P(0.505 + 0.004 * k, v0 + 0.02 + 0.006 * k),
                   c.P(0.495 - 0.004 * k, v0 + 0.02 + 0.006 * k)], fill=(70, 56, 80))
    # lampadaires éteints et câbles
    for side, u in ((-1, 0.16), (1, 0.84)):
        d.line([c.P(u, 0.95), c.P(u, 0.40)], fill=(16, 12, 26), width=22)
        d.line([c.P(u, 0.40), c.P(u - side * 0.08, 0.38)], fill=(16, 12, 26), width=18)
    for k in range(3):
        d.line([c.P(0.16, 0.41 + k * 0.012), c.P(0.5, 0.47 + k * 0.01), c.P(0.84, 0.41 + k * 0.012)], fill=(20, 14, 30), width=5, joint="curve")
    # voiture abandonnée
    d.rounded_rectangle(c.box(0.60, 0.72, 0.86, 0.775), radius=30, fill=(18, 13, 28))
    d.rounded_rectangle(c.box(0.64, 0.695, 0.80, 0.73), radius=24, fill=(18, 13, 28))
    d.polygon([c.P(0.66, 0.70), c.P(0.70, 0.70), c.P(0.70, 0.725), c.P(0.655, 0.725)], fill=(90, 60, 80))
    for u in (0.65, 0.81):
        d.ellipse(c.box(u - 0.025, 0.76, u + 0.025, 0.76 + 0.05 * CW / CH), fill=(8, 6, 14))
    d.rectangle(c.box(0, 0.66, 1, 0.665), fill=(50, 30, 60))
    c.soft(lambda dd, cc: dd.rectangle(cc.box(-0.1, 0.55, 1.1, 0.72), fill=(255, 170, 130, 90)), 0.03)
    if p.get("green"):
        c.glow(0.5, 0.6, 0.25, (90, 255, 120), 0.6)
    return c.done()


def scene_flou(p):
    """Fond flou pour les gros plans. Avec "of": "<décor>", c'est ce décor-là, très flou
    (le moteur le remplit tout seul avec le dernier décor du plan précédent) ; sinon bokeh."""
    if p.get("of") in SCENES and p["of"] != "flou":
        img = SCENES[p["of"]]({k: v for k, v in p.items() if k not in ("of", "colors")})
        img = img.convert("RGB").filter(ImageFilter.GaussianBlur(26))
        if p.get("light"):
            c = Canvas((0, 0, 0), (0, 0, 0))
            c.img = img.resize((c.w, c.h), Image.LANCZOS)
            c.d = ImageDraw.Draw(c.img)
            c.glow(0.5, 0.95, 0.8, tuple(p["light"]), 0.35)
            return c.done()
        return img
    a, b = p.get("colors", [(60, 40, 110), (20, 14, 40)])
    c = Canvas(tuple(a), tuple(b))
    rnd = random.Random(p.get("seed", 3))

    def bokeh(dd, cc):
        for _ in range(28):
            u, v = rnd.uniform(0, 1), rnd.uniform(0.05, 0.7)
            r = rnd.uniform(0.02, 0.07)
            col = rnd.choice([(255, 170, 90), (255, 200, 130), (180, 150, 255), (255, 120, 80)])
            dd.ellipse(cc.box(u - r, v - r * CW / CH, u + r, v + r * CW / CH), fill=col + (rnd.randint(70, 150),))
    c.soft(bokeh, 0.012)
    c.glow(0.5, 0.95, 0.8, tuple(p.get("light", FIRE)), 0.35)
    return c.done()


def scene_porte(p):
    """Porte de l'abri dans un couloir violet, lumière dessous."""
    c = Canvas((44, 32, 80), (16, 12, 30))
    d = c.d
    light = (120, 255, 130) if p.get("green") else (255, 170, 90)
    d.rectangle(c.box(0.20, 0.14, 0.80, 0.80), fill=(26, 20, 46))
    d.rectangle(c.box(0.24, 0.17, 0.76, 0.79), fill=(70, 58, 112))
    for v in (0.32, 0.48, 0.64):
        d.rectangle(c.box(0.24, v, 0.76, v + 0.006), fill=(52, 42, 88))
    d.rounded_rectangle(c.box(0.66, 0.47, 0.72, 0.49), radius=12, fill=(200, 190, 220))
    d.rectangle(c.box(0.28, 0.44, 0.44, 0.455), fill=(140, 130, 170))
    d.rectangle(c.box(0.24, 0.79, 0.76, 0.80), fill=light)
    c.glow(0.5, 0.80, 0.55, light, 0.45)
    c.d.rectangle(c.box(0, 0.80, 1, 1), fill=(18, 14, 32))
    c.glow(0.5, 0.82, 0.4, light, 0.3)
    return c.done()


def scene_radio(p):
    """La radio en gros plan sur la table, cadran lumineux."""
    c = Canvas((52, 36, 90), (18, 12, 32))
    c.glow(0.5, 0.45, 0.7, FIRE, 0.25)
    d = c.d
    d.rectangle(c.box(0, 0.66, 1, 1), fill=(40, 26, 40))
    d.line([c.P(0.74, 0.40), c.P(0.92, 0.12)], fill=(150, 140, 170), width=22)
    d.rounded_rectangle(c.box(0.10, 0.38, 0.90, 0.67), radius=90, fill=(30, 22, 44))
    d.rounded_rectangle(c.box(0.12, 0.40, 0.88, 0.65), radius=80, fill=(96, 62, 70))
    d.rounded_rectangle(c.box(0.17, 0.45, 0.50, 0.61), radius=40, fill=(40, 26, 36))
    for v in np.arange(0.47, 0.60, 0.018):
        d.line([c.P(0.20, v), c.P(0.47, v)], fill=(70, 46, 56), width=16)
    d.rounded_rectangle(c.box(0.55, 0.45, 0.84, 0.52), radius=20, fill=(255, 196, 110))
    d.line([c.P(0.66, 0.455), c.P(0.66, 0.515)], fill=(230, 40, 40), width=12)
    for u in (0.61, 0.77):
        d.ellipse(c.box(u - 0.045, 0.54, u + 0.045, 0.54 + 0.09 * CW / CH), fill=(40, 26, 36))
    c.glow(0.70, 0.485, 0.3, (255, 190, 110), 0.35)
    if p.get("on", True):
        c.glow(0.34, 0.53, 0.3, (255, 120, 90), 0.15)
    return c.done()


def scene_escalier(p):
    """Cage d'escalier d'immeuble, marches qui montent vers une lumière en haut."""
    c = Canvas((48, 34, 86), (14, 10, 28))
    light = (120, 255, 130) if p.get("green") else (255, 170, 90)
    if p.get("dark"):
        light = (70, 50, 110)
    c.glow(0.62, 0.12, 0.6, light, 0.45)
    d = c.d
    # murs
    d.polygon([c.P(0, 0), c.P(0.28, 0.18), c.P(0.28, 0.82), c.P(0, 1)], fill=(30, 22, 52))
    d.polygon([c.P(1, 0), c.P(0.78, 0.14), c.P(0.78, 0.86), c.P(1, 1)], fill=(36, 26, 60))
    # marches en perspective
    n = 14
    for i in range(n):
        t0, t1 = i / n, (i + 1) / n
        v0 = 1.0 - 0.80 * t0
        v1 = 1.0 - 0.80 * t1
        ua0, ub0 = 0.0 + 0.28 * t0, 1.0 - 0.22 * t0
        ua1, ub1 = 0.0 + 0.28 * t1, 1.0 - 0.22 * t1
        col = R.mix((74, 58, 110), (40, 30, 66), t0)
        d.polygon([c.P(ua0, v0), c.P(ub0, v0), c.P(ub1, v1 + 0.02 * (1 - t0)), c.P(ua1, v1 + 0.02 * (1 - t0))], fill=col)
        d.line([c.P(ua0, v0), c.P(ub0, v0)], fill=(20, 14, 34), width=10)
    # rampe
    d.line([c.P(0.86, 0.95), c.P(0.70, 0.22)], fill=(16, 12, 26), width=26)
    for k in range(7):
        t = k / 7
        u, v = 0.86 - 0.16 * t, 0.95 - 0.73 * t
        d.line([c.P(u, v), c.P(u, v + 0.09 * (1 - t * 0.6))], fill=(16, 12, 26), width=10)
    # palier en haut
    d.rectangle(c.box(0.28, 0.14, 0.78, 0.20), fill=(24, 18, 40))
    c.glow(0.53, 0.17, 0.25, light, 0.35)
    return c.done()


def scene_wagon(p):
    """Intérieur d'un train de nuit vide : sièges, vitres noires, néons."""
    c = Canvas((40, 30, 70), (16, 12, 30))
    d = c.d
    neon = (120, 255, 140) if p.get("green") else ((255, 70, 60) if p.get("red") else (200, 190, 255))
    dark = p.get("dark")
    # plafond et néons
    d.polygon([c.P(0, 0), c.P(1, 0), c.P(0.62, 0.30), c.P(0.38, 0.30)], fill=(30, 24, 52))
    if not dark:
        for k in range(5):
            t = k / 5
            v = 0.04 + 0.24 * (1 - (1 - t) ** 1.6)
            hw = 0.22 * (1 - t) + 0.03
            d.rectangle(c.box(0.5 - hw * 0.35, v, 0.5 + hw * 0.35, v + 0.008 * (1 - t) + 0.003), fill=neon)
        c.glow(0.5, 0.12, 0.6, neon, 0.18)
    d = c.d
    # vitres de chaque côté (nuit qui défile)
    for side in (0, 1):
        for k in range(4):
            t0, t1 = k / 4, (k + 0.8) / 4
            def ux(t):
                return (0.38 * (1 - (1 - t) ** 1.4)) if side == 0 else (1 - 0.38 * (1 - (1 - t) ** 1.4))
            def vt(t):
                return 0.16 + 0.15 * (1 - (1 - t) ** 1.4)
            def vb(t):
                return 0.50 - 0.08 * (1 - (1 - t) ** 1.4)
            pts = [c.P(ux(t0), vt(t0)), c.P(ux(t1), vt(t1)), c.P(ux(t1), vb(t1)), c.P(ux(t0), vb(t0))]
            d.polygon(pts, fill=(10, 8, 20))
            d.line(pts + [pts[0]], fill=(60, 50, 90), width=10)
            d.line([pts[0], pts[2]], fill=(28, 24, 48), width=6)
    # couloir central
    d.polygon([c.P(0.40, 0.62), c.P(0.60, 0.62), c.P(0.85, 1.0), c.P(0.15, 1.0)], fill=(26, 20, 40))
    d.polygon([c.P(0.42, 0.40), c.P(0.58, 0.40), c.P(0.60, 0.62), c.P(0.40, 0.62)], fill=(20, 16, 34))
    # porte du fond
    d.rectangle(c.box(0.455, 0.42, 0.545, 0.62), fill=(60, 50, 96))
    d.rectangle(c.box(0.47, 0.44, 0.53, 0.52), fill=(12, 10, 22))
    # sièges en perspective
    seat = (110, 40, 60) if not dark else (50, 24, 40)
    top = (140, 56, 76) if not dark else (60, 30, 50)
    for side in (0, 1):
        for k in reversed(range(5)):
            t = k / 5
            near = 1 - t
            w = 0.08 + 0.20 * near
            h = 0.10 + 0.26 * near
            u0 = (0.40 - 0.40 * near - w * 0.2) if side == 0 else (0.60 + 0.40 * near - w * 0.8)
            v1 = 0.62 + 0.36 * near
            d.rounded_rectangle(c.box(u0, v1 - h, u0 + w, v1), radius=int(30 * near + 8), fill=seat)
            d.rounded_rectangle(c.box(u0, v1 - h, u0 + w, v1 - h * 0.8), radius=int(20 * near + 6), fill=top)
            d.rounded_rectangle(c.box(u0, v1 - h, u0 + w, v1), radius=int(30 * near + 8), outline=(40, 16, 30), width=8)
    if dark:
        c.glow(0.5, 0.5, 0.6, (60, 40, 120), 0.2)
    if p.get("green") or p.get("red"):
        c.glow(0.5, 0.55, 0.5, neon, 0.25)
    return c.done()


def scene_couloir(p):
    """Couloir d'hôtel de montagne : moquette rouge, portes numérotées, appliques."""
    c = Canvas((46, 32, 70), (16, 12, 28))
    d = c.d
    lamp = (255, 70, 60) if p.get("red") else ((120, 255, 140) if p.get("green") else (255, 190, 120))
    dark = p.get("dark")
    deep = 0.2 if p.get("long") else 0.36   # largeur du fond : plus petit = couloir plus long
    vu0, vu1, vv0, vv1 = 0.5 - deep / 4, 0.5 + deep / 4, 0.36, 0.56
    # plafond, murs, sol
    d.polygon([c.P(0, 0), c.P(1, 0), c.P(vu1, vv0), c.P(vu0, vv0)], fill=(34, 26, 52))
    d.polygon([c.P(0, 0), c.P(vu0, vv0), c.P(vu0, vv1), c.P(0, 1)], fill=(58, 40, 70))
    d.polygon([c.P(1, 0), c.P(vu1, vv0), c.P(vu1, vv1), c.P(1, 1)], fill=(64, 44, 78))
    d.polygon([c.P(0, 1), c.P(vu0, vv1), c.P(vu1, vv1), c.P(1, 1)], fill=(110, 30, 44) if not dark else (50, 18, 30))
    # motif de la moquette
    for k in range(1, 8):
        t = 1 - (1 - k / 8) ** 1.6
        v = 1 - (1 - vv1) * t
        ua, ub = vu0 * t, 1 - (1 - vu1) * t
        d.line([c.P(ua, v), c.P(ub, v)], fill=(80, 20, 34) if not dark else (36, 12, 22), width=8)
    # portes de chaque côté
    for side in (0, 1):
        for k in range(4):
            t0 = 1 - (1 - (k + 0.15) / 4.2) ** 1.5
            t1 = 1 - (1 - (k + 0.65) / 4.2) ** 1.5
            def U(t):
                return vu0 * t if side == 0 else 1 - (1 - vu1) * t
            def VT(t):
                return 0.16 + (vv0 + 0.04 - 0.16) * t
            def VB(t):
                return 1.0 - (1.0 - vv1) * t - 0.02 * (1 - t)
            pts = [c.P(U(t0), VT(t0)), c.P(U(t1), VT(t1)), c.P(U(t1), VB(t1)), c.P(U(t0), VB(t0))]
            d.polygon(pts, fill=(36, 24, 44) if not dark else (22, 16, 30))
            d.line(pts + [pts[0]], fill=(90, 66, 100), width=8)
            # plaque du numéro
            um, vm = (U(t0) + U(t1)) / 2, VT(t0) + (VB(t0) - VT(t0)) * 0.22
            r = 0.012 * (1 - t0 * 0.7)
            d.rectangle(c.box(um - r, vm - r * 0.6, um + r, vm + r * 0.6), fill=(210, 180, 110))
            # applique entre les portes
            if not dark:
                ul = U(t1 + (t0 - t1) * -0.4)
                vl = VT(t1) + 0.04
                c.glow(ul, vl, 0.12 * (1 - t1 * 0.6), lamp, 0.35)
                d = c.d
    # porte du fond
    d.rectangle(c.box(0.5 - deep / 10, vv0 + 0.03, 0.5 + deep / 10, vv1), fill=(60, 44, 80))
    d.rectangle(c.box(0.5 - deep / 10, vv1 - 0.004, 0.5 + deep / 10, vv1), fill=lamp)
    c.glow(0.5, vv1, 0.3, lamp, 0.3 if not dark else 0.15)
    if dark:
        c.glow(0.5, 0.5, 0.6, (60, 40, 120), 0.2)
    return c.done()


def _lightcol(p, base):
    if p.get("red"):
        return (255, 70, 60)
    if p.get("green"):
        return (120, 255, 140)
    return tuple(p.get("light", base))


def scene_foret(p):
    """Forêt la nuit : troncs en rangs, brume au sol, lune entre les arbres."""
    c = Canvas((20, 26, 52), (40, 34, 70))
    rnd = random.Random(p.get("seed", 11))
    c.glow(0.62, 0.22, 0.5, (200, 200, 255), 0.4)
    d = c.d
    r = 0.06
    d.ellipse(c.box(0.62 - r, 0.22 - r * CW / CH, 0.62 + r, 0.22 + r * CW / CH), fill=(250, 248, 235))
    rows = (((38, 40, 72), 14, 0.015, 0.03), ((24, 26, 50), 10, 0.03, 0.05), ((12, 12, 26), 6, 0.06, 0.10))
    for layer, (col, n, wmin, wmax) in enumerate(rows):
        for _ in range(n):
            u = rnd.uniform(-0.05, 1.05)
            w = rnd.uniform(wmin, wmax)
            d.polygon([c.P(u - w * 0.5, -0.02), c.P(u + w * 0.5, -0.02), c.P(u + w * 0.7, 1.02), c.P(u - w * 0.7, 1.02)], fill=col)
            for _ in range(2 + layer):
                v = rnd.uniform(0.05, 0.6)
                side = rnd.choice((-1, 1))
                d.line([c.P(u, v), c.P(u + side * rnd.uniform(0.05, 0.12), v - rnd.uniform(0.03, 0.08))], fill=col, width=int(10 + 8 * layer))
        if layer == 1:
            c.soft(lambda dd, cc: dd.rectangle(cc.box(-0.1, 0.62, 1.1, 0.85), fill=(150, 140, 200, 80)), 0.04)
            d = c.d
    d.rectangle(c.box(0, 0.86, 1, 1), fill=(10, 10, 22))
    c.soft(lambda dd, cc: dd.rectangle(cc.box(-0.1, 0.78, 1.1, 0.95), fill=(170, 160, 220, 110)), 0.05)
    if p.get("eyes"):
        d = c.d
        for u in (0.30, 0.33):
            d.ellipse(c.box(u - 0.006, 0.58, u + 0.006, 0.58 + 0.012 * CW / CH), fill=(255, 60, 50))
        c.glow(0.315, 0.585, 0.08, (255, 60, 50), 0.4)
    if p.get("red") or p.get("green"):
        c.glow(0.5, 0.6, 0.6, _lightcol(p, FIRE), 0.25)
    return c.done()


def scene_parking(p):
    """Parking souterrain : piliers en béton, néons, places numérotées, voiture seule."""
    c = Canvas((40, 40, 58), (18, 18, 30))
    lamp = _lightcol(p, (210, 230, 255))
    dark = p.get("dark")
    d = c.d
    d.polygon([c.P(0, 0), c.P(1, 0), c.P(0.62, 0.40), c.P(0.38, 0.40)], fill=(34, 34, 50))
    d.polygon([c.P(0, 1), c.P(0.38, 0.52), c.P(0.62, 0.52), c.P(1, 1)], fill=(46, 44, 58) if not dark else (24, 24, 34))
    d.rectangle(c.box(0.38, 0.40, 0.62, 0.52), fill=(20, 20, 32))
    for k in range(5):
        t = 1 - (1 - k / 5) ** 1.5
        # néons au plafond
        v = 0.40 * t
        hw = 0.12 * (1 - t) + 0.02
        if not dark and not (p.get("flicker") and k == 2):
            d.rectangle(c.box(0.5 - hw, v + 0.02 * (1 - t), 0.5 + hw, v + 0.02 * (1 - t) + 0.008 * (1 - t) + 0.002), fill=lamp)
        # lignes au sol
        vg = 1 - 0.48 * t
        for side in (-1, 1):
            u0 = 0.5 + side * (0.5 - 0.12 * t) * 0.9
            d.line([c.P(u0, vg), c.P(0.5 + side * 0.06 * (1 - t), vg)], fill=(200, 190, 120), width=int(4 + 8 * (1 - t)))
        # piliers
        for side in (-1, 1):
            u = 0.5 + side * (0.5 - 0.38 * t) * 0.95
            pw = 0.07 * (1 - t) + 0.012
            d.rectangle(c.box(u - pw / 2, 0.40 * t, u + pw / 2, 1 - 0.48 * t), fill=(70, 68, 86) if not dark else (36, 36, 48))
            d.rectangle(c.box(u - pw / 2, 0.62 + 0.0 * t, u + pw / 2, 0.68), fill=(200, 160, 60)) if k == 0 else None
            if k < 3:
                d.text(c.P(u - pw * 0.3, 0.30 + 0.2 * t), str(k * 2 + (1 if side < 0 else 2)), fill=(230, 230, 240),
                       font=font(int(110 * (1 - t) + 20) * SSF))
    if not dark:
        c.glow(0.5, 0.1, 0.7, lamp, 0.2)
    # voiture seule au fond
    d = c.d
    d.rounded_rectangle(c.box(0.42, 0.47, 0.58, 0.52), radius=16, fill=(14, 14, 22))
    d.rounded_rectangle(c.box(0.445, 0.45, 0.555, 0.48), radius=12, fill=(14, 14, 22))
    if p.get("headlights"):
        for u in (0.44, 0.56):
            c.glow(u, 0.50, 0.12, (255, 250, 220), 0.7)
    return c.done()


def scene_station(p):
    """Station-service isolée la nuit : auvent lumineux, pompes, route vide."""
    c = Canvas((14, 14, 36), (48, 30, 70))
    sign = _lightcol(p, (255, 90, 70))
    d = c.d
    rnd = random.Random(p.get("seed", 4))
    for _ in range(50):
        x, y = rnd.uniform(0, 1), rnd.uniform(0, 0.35)
        d.ellipse(c.box(x - 0.002, y - 0.001, x + 0.002, y + 0.001), fill=(210, 210, 255))
    d.rectangle(c.box(0, 0.58, 1, 1), fill=(22, 20, 32))
    d.polygon([c.P(0, 0.70), c.P(1, 0.64), c.P(1, 0.70), c.P(0, 0.78)], fill=(34, 30, 44))
    # boutique
    d.rectangle(c.box(0.62, 0.40, 0.98, 0.60), fill=(40, 34, 56))
    d.rectangle(c.box(0.65, 0.45, 0.95, 0.58), fill=(255, 230, 170) if not p.get("dark") else (30, 26, 40))
    if p.get("figure"):
        d.ellipse(c.box(0.79, 0.47, 0.81, 0.47 + 0.02 * CW / CH), fill=(10, 8, 16))
        d.rectangle(c.box(0.785, 0.49, 0.815, 0.58), fill=(10, 8, 16))
    # auvent
    d.rectangle(c.box(0.02, 0.30, 0.60, 0.36), fill=(230, 232, 240))
    d.rectangle(c.box(0.02, 0.345, 0.60, 0.36), fill=sign)
    for u in (0.08, 0.54):
        d.rectangle(c.box(u, 0.36, u + 0.025, 0.62), fill=(200, 200, 210))
    c.glow(0.31, 0.45, 0.5, (240, 240, 255), 0.35)
    d = c.d
    # pompes
    for u in (0.18, 0.40):
        d.rounded_rectangle(c.box(u, 0.47, u + 0.07, 0.61), radius=10, fill=(200, 60, 60))
        d.rectangle(c.box(u + 0.012, 0.49, u + 0.058, 0.52), fill=(30, 30, 40))
    # panneau
    d.rectangle(c.box(0.88, 0.12, 0.89, 0.40), fill=(30, 28, 40))
    d.rectangle(c.box(0.80, 0.10, 0.97, 0.20), fill=sign)
    c.glow(0.885, 0.15, 0.2, sign, 0.4)
    c.soft(lambda dd, cc: dd.polygon([cc.P(0.02, 0.36), cc.P(0.60, 0.36), cc.P(0.75, 0.66), cc.P(-0.1, 0.66)],
                                     fill=(240, 240, 255, 60)), 0.03)
    return c.done()


def scene_ascenseur(p):
    """Intérieur d'ascenseur : parois métal, boutons, écran d'étage, néon au plafond."""
    c = Canvas((60, 58, 76), (24, 22, 34))
    lamp = _lightcol(p, (230, 235, 255))
    d = c.d
    d.polygon([c.P(0, 0), c.P(0.22, 0.12), c.P(0.22, 0.86), c.P(0, 1)], fill=(70, 68, 84))
    d.polygon([c.P(1, 0), c.P(0.78, 0.12), c.P(0.78, 0.86), c.P(1, 1)], fill=(78, 76, 92))
    d.rectangle(c.box(0.22, 0.12, 0.78, 0.86), fill=(90, 88, 104))
    d.polygon([c.P(0, 1), c.P(0.22, 0.86), c.P(0.78, 0.86), c.P(1, 1)], fill=(36, 32, 44))
    for u in np.arange(0.26, 0.78, 0.06):
        d.line([c.P(u, 0.13), c.P(u, 0.85)], fill=(80, 78, 94), width=6)
    d.line([c.P(0.5, 0.12), c.P(0.5, 0.86)], fill=(40, 38, 52), width=12)   # jonction des portes
    d.rectangle(c.box(0.30, 0.0, 0.70, 0.035), fill=lamp)
    c.glow(0.5, 0.02, 0.6, lamp, 0.35)
    d = c.d
    # panneau de boutons
    d.rounded_rectangle(c.box(0.80, 0.38, 0.90, 0.66), radius=12, fill=(50, 48, 62))
    for k in range(6):
        on = k == p.get("floor_btn", 3)
        d.ellipse(c.box(0.83, 0.41 + k * 0.04, 0.87, 0.41 + k * 0.04 + 0.04 * CW / CH * 0.55),
                  fill=(255, 190, 90) if on else (130, 128, 140))
    # écran d'étage
    d.rectangle(c.box(0.40, 0.04, 0.60, 0.10), fill=(12, 10, 16))
    floor = str(p.get("floor", "-2"))
    d.text(c.P(0.46, 0.045), floor, fill=_lightcol(p, (255, 70, 60)), font=font(110 * SSF))
    if p.get("dark"):
        c.glow(0.5, 0.5, 0.8, (20, 20, 40), 0.5)
    return c.done()


def scene_cuisine(p):
    """Cuisine d'appartement la nuit : frigo ouvert qui éclaire, fenêtre, plan de travail."""
    c = Canvas((44, 36, 70), (20, 16, 32))
    d = c.d
    night_sky(c, 0.08, 0.14, 0.40, 0.40, moon=(0.6, 0.3), seed=p.get("seed", 8))
    d = c.d
    d.rectangle(c.box(0.07, 0.13, 0.41, 0.41), outline=(24, 18, 40), width=24)
    # placards hauts
    for u in (0.46, 0.62, 0.78):
        d.rectangle(c.box(u, 0.10, u + 0.14, 0.30), fill=(70, 56, 96), outline=(40, 30, 60), width=8)
    # plan de travail
    d.rectangle(c.box(0, 0.56, 0.70, 0.60), fill=(130, 110, 140))
    d.rectangle(c.box(0, 0.60, 0.70, 0.95), fill=(60, 46, 80))
    for u in (0.0, 0.23, 0.46):
        d.rectangle(c.box(u + 0.01, 0.62, u + 0.22, 0.93), outline=(40, 30, 60), width=8)
    # couteaux / bouilloire
    d.rounded_rectangle(c.box(0.48, 0.48, 0.58, 0.56), radius=20, fill=(40, 34, 56))
    # frigo
    d.rectangle(c.box(0.74, 0.32, 0.98, 0.95), fill=(150, 150, 170))
    if p.get("fridge", True):
        d.rectangle(c.box(0.76, 0.34, 0.96, 0.93), fill=(255, 248, 220))
        for v in (0.48, 0.62, 0.76):
            d.line([c.P(0.76, v), c.P(0.96, v)], fill=(200, 190, 170), width=8)
        c.glow(0.86, 0.6, 0.6, (255, 240, 200), 0.4)
    d = c.d
    d.rectangle(c.box(0, 0.95, 1, 1), fill=(16, 12, 26))
    if p.get("red") or p.get("green"):
        c.glow(0.5, 0.5, 0.6, _lightcol(p, FIRE), 0.25)
    return c.done()


def scene_old(name):
    """Anciens décors, recolorés dans la palette violet / orange."""
    def f(p):
        img = R.SCENES[name](p).resize((CW, CH), Image.LANCZOS)
        a = np.asarray(img).astype(np.float32) / 255
        lum = a.mean(axis=2, keepdims=True)
        tint = np.array([0.55, 0.42, 0.95])[None, None, :] * (1 - lum) + np.array([1.0, 0.72, 0.45])[None, None, :] * lum
        out = (a * 0.45 + lum * tint * 0.75) * 255
        return Image.fromarray(np.clip(out, 0, 255).astype(np.uint8))
    return f


SCENES = {"chambre": scene_chambre, "fenetre": scene_fenetre, "rue": scene_rue, "flou": scene_flou,
          "porte": scene_porte, "radio": scene_radio, "escalier": scene_escalier,
          "wagon": scene_wagon, "couloir": scene_couloir, "foret": scene_foret, "parking": scene_parking,
          "station": scene_station, "ascenseur": scene_ascenseur, "cuisine": scene_cuisine}
NEW_SCENES = set(SCENES)
for _n in R.SCENES:
    SCENES.setdefault(_n, scene_old(_n))


# ------------------------------------------------------------------ personnage

def _eyes(d, cx, ey, r, expr, look=(0.0, 0.0), s=1):
    blk = (8, 8, 12)
    for side in (-1, 1):
        ex = cx + side * r * 1.25
        lx, ly = look[0] * r * 0.45, look[1] * r * 0.45
        if expr == "none":
            return  # visage vide (personnage « sans visage »)
        if expr == "closed":
            d.line([(ex - r * 0.8, ey), (ex + r * 0.8, ey)], fill=WHITE, width=int(r * 0.22))
        elif expr == "wide":
            d.ellipse([ex - r * 1.05, ey - r * 1.05, ex + r * 1.05, ey + r * 1.05], fill=WHITE)
            d.ellipse([ex - r * 0.62 + lx, ey - r * 0.62 + ly, ex + r * 0.62 + lx, ey + r * 0.62 + ly], fill=blk)
            d.ellipse([ex - r * 0.40 + lx, ey - r * 0.40 + ly, ex + r * 0.40 + lx, ey + r * 0.40 + ly], fill=WHITE)
            d.ellipse([ex - r * 0.22 + lx, ey - r * 0.22 + ly, ex + r * 0.22 + lx, ey + r * 0.22 + ly], fill=blk)
        elif expr == "scared":
            d.ellipse([ex - r * 1.1, ey - r * 1.1, ex + r * 1.1, ey + r * 1.1], fill=WHITE)
            d.ellipse([ex - r * 0.18 + lx, ey - r * 0.18 + ly, ex + r * 0.18 + lx, ey + r * 0.18 + ly], fill=blk)
        elif expr == "side":
            # paupière mi-close, regard sur le côté (méfiant)
            d.ellipse([ex - r * 0.9, ey - r * 0.6, ex + r * 0.9, ey + r * 0.6], fill=WHITE)
            d.ellipse([ex + r * 0.15, ey - r * 0.38, ex + r * 0.75, ey + r * 0.38], fill=blk)
            d.rectangle([ex - r * 1.0, ey - r * 0.7, ex + r * 1.0, ey - r * 0.12], fill=blk)
            d.line([(ex - r * 0.95, ey - r * 0.12), (ex + r * 0.95, ey - r * 0.12)], fill=WHITE, width=int(r * 0.12))
        else:
            d.ellipse([ex - r, ey - r, ex + r, ey + r], fill=WHITE)
            d.ellipse([ex - r * 0.45 + lx, ey - r * 0.45 + ly, ex + r * 0.45 + lx, ey + r * 0.45 + ly], fill=blk)


def hero(pose="stand", expr="normal", hoodie=(240, 190, 40), look=(0.0, 0.0), blink=False):
    """Personnage bâton style 2 : grosse tête noire avec liseré lumineux, sweat coloré."""
    s = 2
    w, h = 1000 * s, 1400 * s
    img = Image.new("RGBA", (w, h), (0, 0, 0, 0))
    d = ImageDraw.Draw(img)
    blk = (8, 8, 12, 255)
    hood = tuple(hoodie) + (255,)
    shade = tuple(int(c * 0.72) for c in hoodie) + (255,)
    deep = tuple(int(c * 0.5) for c in hoodie) + (255,)
    rim = RIM + (255,)
    e = "closed" if blink and expr != "none" else expr
    cx = w / 2

    def head(hx, hy, r, face=True):
        d.ellipse([hx - r - 6 * s, hy - r - 6 * s, hx + r + 6 * s, hy + r + 6 * s], fill=rim)
        d.ellipse([hx - r, hy - r, hx + r, hy + r], fill=blk)
        if face:
            _eyes(d, hx, hy - r * 0.08, r * 0.2, e, look, s)
            if e == "none":
                pass
            elif e in ("scared",):
                d.ellipse([hx - r * 0.08, hy + r * 0.38, hx + r * 0.08, hy + r * 0.56], fill=WHITE)
            else:
                d.line([(hx - r * 0.09, hy + r * 0.42), (hx + r * 0.09, hy + r * 0.42)], fill=WHITE, width=int(r * 0.045))

    if pose in ("face", "back"):
        # gros plan / vue de dos : image plus large, les épaules sortent du cadre
        img = Image.new("RGBA", (1400 * s, 2600 * s), (0, 0, 0, 0))
        d = ImageDraw.Draw(img)
        cx = 700 * s
    if pose == "face":
        d.rounded_rectangle([cx - 690 * s, 1040 * s, cx + 690 * s, 2600 * s], radius=380 * s, fill=hood)
        d.ellipse([cx - 360 * s, 880 * s, cx + 360 * s, 1220 * s], fill=deep)
        d.line([(cx - 130 * s, 1140 * s), (cx - 160 * s, 1460 * s)], fill=deep, width=20 * s)
        d.line([(cx + 130 * s, 1140 * s), (cx + 160 * s, 1460 * s)], fill=deep, width=20 * s)
        for fx in (-1, 1):
            d.arc([cx + fx * 380 * s - 260 * s, 1300 * s, cx + fx * 380 * s + 260 * s, 1900 * s], 200 if fx < 0 else 280, 260 if fx < 0 else 340, fill=shade, width=16 * s)
        head(cx, 560 * s, 420 * s)
    elif pose == "back":
        d.rounded_rectangle([cx - 690 * s, 1000 * s, cx + 690 * s, 2600 * s], radius=400 * s, fill=hood)
        d.ellipse([cx - 320 * s, 820 * s, cx + 320 * s, 1280 * s], fill=deep)
        d.ellipse([cx - 240 * s, 900 * s, cx + 240 * s, 1220 * s], fill=shade)
        d.ellipse([cx - 360 * s, 270 * s, cx + 360 * s, 990 * s], fill=rim)
        d.ellipse([cx - 352 * s, 278 * s, cx + 352 * s, 982 * s], fill=blk)
    elif pose == "sit":
        # assis, de face légèrement de côté
        d.line([(cx - 90 * s, 1010 * s), (cx + 170 * s, 1030 * s), (cx + 190 * s, 1380 * s)], fill=blk, width=44 * s, joint="curve")
        d.line([(cx + 10 * s, 1010 * s), (cx + 260 * s, 1040 * s), (cx + 280 * s, 1380 * s)], fill=blk, width=44 * s, joint="curve")
        d.rounded_rectangle([cx - 200 * s, 640 * s, cx + 150 * s, 1060 * s], radius=120 * s, fill=hood)
        d.ellipse([cx - 230 * s, 560 * s, cx + 170 * s, 820 * s], fill=deep)
        d.line([(cx + 60 * s, 720 * s), (cx + 120 * s, 980 * s), (cx + 200 * s, 1000 * s)], fill=blk, width=28 * s, joint="curve")
        head(cx - 30 * s, 400 * s, 240 * s)
    else:  # stand
        d.line([(cx - 70 * s, 1060 * s), (cx - 80 * s, 1390 * s)], fill=blk, width=36 * s)
        d.line([(cx + 70 * s, 1060 * s), (cx + 80 * s, 1390 * s)], fill=blk, width=36 * s)
        d.line([(cx - 170 * s, 700 * s), (cx - 230 * s, 1000 * s)], fill=blk, width=30 * s)
        d.line([(cx + 170 * s, 700 * s), (cx + 230 * s, 1000 * s)], fill=blk, width=30 * s)
        d.rounded_rectangle([cx - 190 * s, 620 * s, cx + 190 * s, 1090 * s], radius=130 * s, fill=hood)
        d.rounded_rectangle([cx - 100 * s, 870 * s, cx + 100 * s, 960 * s], radius=30 * s, fill=deep)
        d.ellipse([cx - 230 * s, 540 * s, cx + 230 * s, 800 * s], fill=deep)
        head(cx, 380 * s, 250 * s)
    return img.resize((img.width // s, img.height // s), Image.LANCZOS)


# centre et rayon de la tête dans l'image du personnage (unités de 1000 px de large)
HEAD = {"face": (700, 560, 420), "back": (700, 630, 352), "sit": (470, 400, 240), "stand": (500, 380, 250)}


# ------------------------------------------------------------------ sous-titres

def chunks(text):
    """Découpe le texte affiché en morceaux de 1 à 2 mots (les petits mots s'accrochent)."""
    words = [w for w in text.replace("«", "").replace("»", "").split() if w]
    out, cur = [], []
    for wd in words:
        cur.append(wd)
        plain = " ".join(x.replace("*", "") for x in cur)
        small = len(wd.replace("*", "")) <= 3 and not wd.endswith((".", ",", "?", "!", ":"))
        if len(cur) >= 2 or (not small and len(plain) >= 4) or len(plain) >= 9:
            out.append(cur)
            cur = []
    if cur:
        if out and len(" ".join(out[-1] + cur)) <= 14:
            out[-1] += cur
        else:
            out.append(cur)
    # mots en rouge entre astérisques (peuvent couvrir plusieurs mots)
    res, on = [], False
    for ch in out:
        items = []
        for wd in ch:
            st = wd.startswith("*")
            if st:
                on = True
            items.append((wd.replace("*", ""), on))
            if wd.count("*") == 2 or (wd.count("*") == 1 and not st):
                on = False
        res.append(items)
    return res


_cap_cache = {}


def caption_img(items, size=150):
    key = (tuple(items), size)
    if key in _cap_cache:
        return _cap_cache[key]
    f = font(size)
    txt = " ".join(w for w, _ in items)
    while f.getlength(txt) > W - 300 and size > 70:  # zone sûre TikTok (boutons à droite)
        size -= 8
        f = font(size)
    tw = int(f.getlength(txt)) + 60
    img = Image.new("RGBA", (tw, int(size * 1.5)), (0, 0, 0, 0))
    d = ImageDraw.Draw(img)
    x = 30
    for wd, red in items:
        d.text((x + 5, 12), wd, font=f, fill=(0, 0, 0, 150))
        d.text((x, 6), wd, font=f, fill=RED if red else WHITE, stroke_width=9, stroke_fill=(0, 0, 0))
        x += f.getlength(wd + " ")
    _cap_cache[key] = img
    return img


def draw_caption(frame, items, lt, y):
    img = caption_img(items)
    pop = 1.18 - 0.18 * smooth(lt / 0.09)
    if pop != 1:
        img = img.resize((int(img.width * pop), int(img.height * pop)), Image.BILINEAR)
    frame.paste(img, (int((W - img.width) / 2), int(H * y - img.height / 2)), img)


def draw_clock(frame, clock_s):
    hh, rem = divmod(int(clock_s) % 86400, 3600)
    mm, ss = divmod(rem, 60)
    txt = f"{hh:02d}:{mm:02d}:{ss:02d}"
    f = font(104)
    d = ImageDraw.Draw(frame)
    d.text(((W - f.getlength(txt)) / 2, 160), txt, font=f, fill=WHITE, stroke_width=6, stroke_fill=(0, 0, 0))


def heart(d, cx, cy, r, fill):
    d.ellipse([cx - r, cy - r * 0.9, cx, cy + r * 0.1], fill=fill)
    d.ellipse([cx, cy - r * 0.9, cx + r, cy + r * 0.1], fill=fill)
    d.polygon([(cx - r * 0.97, cy - r * 0.25), (cx + r * 0.97, cy - r * 0.25), (cx, cy + r * 1.05)], fill=fill)


def draw_lives(frame, lives, total, lost_t=None):
    """Vies du héros sous l'horloge (compteur sur toute la série, idée validée pour faire follow)."""
    d = ImageDraw.Draw(frame)
    r, gap = 30, 84
    x0 = W / 2 - gap * (total - 1) / 2
    for i in range(total):
        alive = i < lives
        cx, cy = x0 + i * gap, 330
        if lost_t is not None and i == lives and lost_t < 1.2 and int(lost_t * 6) % 2 == 0:
            alive = True   # le cœur perdu clignote avant de s'éteindre
        heart(d, cx, cy + 3, r + 6, (0, 0, 0))
        heart(d, cx, cy, r, (235, 40, 50) if alive else (60, 50, 70))


def draw_choice(frame, a, b, t, picked=None, count=None, enter=True):
    """Cartes A / B en grosses lettres ; elles glissent seulement à leur apparition."""
    d = ImageDraw.Draw(frame)
    fl, ft = font(150), font(96)
    for i, (lab, txt, col) in enumerate((("A", a, (214, 48, 58)), ("B", b, (52, 98, 214)))):
        k = R.ease_out(min(1, max(0, (t - i * 0.12) / 0.28))) if enter else 1
        y0 = 560 + i * 450
        x_off = (1 - k) * (-W if i == 0 else W)
        box = [60 + x_off, y0, W - 170 + x_off, y0 + 390]  # libère la colonne des boutons TikTok
        dim = picked is not None and picked != lab
        fill = R.mix(col, (25, 20, 40), 0.7) if dim else col
        d.rounded_rectangle(box, radius=56, fill=fill, outline=WHITE if picked == lab else (10, 8, 20),
                            width=16 if picked == lab else 8)
        d.text((box[0] + 50, y0 + 110), lab, font=fl, fill=WHITE, stroke_width=7, stroke_fill=(0, 0, 0))
        f = ft
        while f.getlength(txt) > W - 520 and f.size > 50:
            f = font(f.size - 6)
        d.text((box[0] + 230, y0 + 200 - f.size * 0.7), txt, font=f, fill=WHITE, stroke_width=6, stroke_fill=(0, 0, 0))
    if count is not None:
        fc = font(190)
        d.text(((W - 110 - fc.getlength(count)) / 2, 1440), count, font=fc, fill=WHITE, stroke_width=9, stroke_fill=(0, 0, 0))


# ------------------------------------------------------------------ voix

def squeeze(a, max_gap=0.10, min_gap=0.16):
    """Raccourcit les silences dans une réplique (pauses de virgule / point trop longues)."""
    if len(a) < SR // 5:
        return a
    hop = SR // 100
    n = len(a) // hop
    rms = np.sqrt(np.mean(a[: n * hop].reshape(n, hop) ** 2, axis=1))
    thr = max(0.006, 0.05 * rms.max())
    silent = rms < thr
    keep = np.ones(len(a), bool)
    i = 0
    while i < n:
        if silent[i]:
            j = i
            while j < n and silent[j]:
                j += 1
            if (j - i) * hop > min_gap * SR:
                cut0 = i * hop + int(max_gap * SR / 2)
                cut1 = j * hop - int(max_gap * SR / 2)
                keep[cut0:cut1] = False
            i = j
        else:
            i += 1
    out = a[keep]
    # fondu de 5 ms aux jonctions pour éviter les clics
    return out.astype(np.float32)


_asr = None


def _norm(t):
    import re
    import voice
    t = t.lower().replace("’", "'")
    t = re.sub(r"\d{1,3}", lambda m: voice.nombre(int(m.group())), t)
    import unicodedata
    t = unicodedata.normalize("NFD", t)
    t = "".join(c for c in t if unicodedata.category(c) != "Mn")
    t = re.sub(r"[^a-z ]", " ", t)
    return " ".join(t.split())


def heard_ok(audio, line):
    """Fait écouter la réplique par Whisper et la compare au texte. Renvoie (ok, score, entendu)."""
    global _asr
    import difflib
    import voice
    if os.environ.get("VOICE_ASR", "1") == "0":
        return True, 1.0, ""
    if _asr is None:
        try:
            from transformers import pipeline
            _asr = pipeline("automatic-speech-recognition", model="openai/whisper-small", device=-1)
            print("contrôle de la voix : whisper-small")
        except Exception as e:  # pas de Whisper : on garde seulement le contrôle de débit
            print("contrôle de la voix indisponible :", e)
            _asr = False
    if _asr is False:
        return True, 1.0, ""
    x = np.interp(np.arange(0, len(audio), SR / 16000), np.arange(len(audio)), audio).astype(np.float32)
    try:
        heard = _asr({"raw": x, "sampling_rate": 16000},
                     generate_kwargs={"language": "french", "task": "transcribe"})["text"]
    except Exception as e:
        print("contrôle de la voix en erreur :", e)
        return True, 1.0, ""
    want, got = _norm(voice.clean(line)), _norm(heard)
    # comparaison lettre à lettre : tolère les homophones (ses / ces), pas les mots en trop
    score = difflib.SequenceMatcher(None, want, got).ratio()
    ok = score >= 0.85 and len(got) <= len(want) * 1.2 + 4

    def doubles(t):
        w = t.split()
        return sum(1 for i in range(1, len(w)) if w[i] == w[i - 1])
    if doubles(got) > doubles(want):  # mot répété (« plus, plus ») = bégaiement
        ok = False
    return ok, score, heard


def prepare_voice(beats):
    import voice
    clips = {}
    for i, b in enumerate(beats):
        if b.get("type") == "rewind":
            continue
        line = b.get("voice", b.get("text", ""))
        if not line:
            b.setdefault("dur", 1.2)
            continue
        a = squeeze(voice.synth(line))
        clips[i] = a
        need = len(a) / SR + 0.03
        if "choice" in b:
            need = max(need, b.get("dur", 0))
        last_sfx = max([s[1] for s in b.get("sfx", [])], default=0)
        b["dur"] = round(max(need, 0.6, last_sfx + 0.3), 2)
    # Chatterbox bégaie parfois (répète un bout de phrase) ou baragouine : la réplique a
    # alors une durée anormale pour son nombre de lettres. On compare chaque réplique au
    # débit médian de l'épisode et on retire celles qui s'en écartent (4 essais max).
    if voice.engine_name() == "chatterbox" and len(clips) >= 5:
        def rate(k, a):
            return len(a) / SR / max(4, len(voice.clean(beats[k].get("voice", beats[k].get("text", "")))))
        med = float(np.median([rate(k, a) for k, a in clips.items()]))
        for k, a in list(clips.items()):
            r = rate(k, a) / med
            if 0.65 <= r <= 1.25:
                continue
            line = beats[k].get("voice", beats[k].get("text", ""))
            best = a
            for t in range(1, 5):
                voice.RETRY = t
                c = squeeze(voice.synth(line))
                voice.RETRY = 0
                if abs(rate(k, c) / med - 1) < abs(rate(k, best) / med - 1):
                    best = c
                if 0.75 <= rate(k, best) / med <= 1.2:
                    break
            print(f"  réplique retirée (débit x{r:.2f} → x{rate(k, best) / med:.2f}) : {line[:45]}")
            clips[k] = best
            need = len(best) / SR + 0.03
            if "choice" in beats[k] and "countdown" in beats[k]["choice"]:
                need = max(need, 3.2)
            last_sfx = max([s[1] for s in beats[k].get("sfx", [])], default=0)
            beats[k]["dur"] = round(max(need, 0.6, last_sfx + 0.3), 2)
    # Contrôle à l'oreille (Whisper) : chaque réplique doit être comprise mot pour mot,
    # sans mot répété ni parasite. Sinon on la refait (6 tirages max, on garde la meilleure).
    if voice.engine_name() == "chatterbox":
        bad = []
        for k, a in list(clips.items()):
            line = beats[k].get("voice", beats[k].get("text", ""))
            ok, score, heard = heard_ok(a, line)
            t = 0
            best = (score, a, heard)
            while not ok and t < 6:
                t += 1
                voice.RETRY = 10 + t
                c = squeeze(voice.synth(line))
                voice.RETRY = 0
                ok, score, heard = heard_ok(c, line)
                if score > best[0] or ok:
                    best = (score, c, heard)
            if t:
                print(f"  réplique refaite {t} fois (score {best[0]:.2f}) : {line[:45]} → entendu « {best[2].strip()[:50]} »")
            if not ok and best[0] < 0.85:
                bad.append((line, best[2]))
            if t:
                clips[k] = best[1]
                need = len(best[1]) / SR + 0.03
                if "choice" in beats[k] and "countdown" in beats[k]["choice"]:
                    need = max(need, 3.2)
                last_sfx = max([s[1] for s in beats[k].get("sfx", [])], default=0)
                beats[k]["dur"] = round(max(need, 0.6, last_sfx + 0.3), 2)
        if bad:
            print("RÉPLIQUES ENCORE MAL LUES (à réécrire plus simplement) :")
            for line, heard in bad:
                print(f"  - {line}  →  entendu « {heard.strip()} »")
    print(f"voix off : {voice.engine_name()}, {len(clips)} répliques")
    return clips


def voice_track(beats, clips, total, tmp):
    import voice
    track = np.zeros(int(total * SR) + SR, np.float32)
    t0 = 0.0
    for i, b in enumerate(beats):
        if i in clips:
            a = clips[i]
            j = int((t0 + 0.01) * SR)
            track[j:j + len(a)] += a[: len(track) - j]
        t0 += b["dur"]
    return voice.megaphone(track, tmp)


# ------------------------------------------------------------------ rendu

# lumière principale de chaque décor (pour éclairer le personnage)
LIGHT = {"chambre": (170, 160, 255), "fenetre": (180, 170, 255), "rue": (255, 150, 90), "flou": FIRE,
         "porte": (255, 170, 90), "radio": FIRE, "foret": (190, 190, 255), "parking": (210, 230, 255),
         "station": (240, 240, 255), "ascenseur": (230, 235, 255), "cuisine": (255, 240, 200)}
# poussière / braises qui flottent dans l'air
DUST = {"rue": ((255, 150, 70), 46, -1), "chambre": ((210, 200, 255), 30, 1), "fenetre": ((210, 200, 255), 30, 1),
        "flou": ((255, 200, 140), 26, -1), "porte": ((255, 190, 120), 26, 1), "radio": ((255, 190, 120), 22, 1)}


def bloom(img, amount=0.55):
    """Halo autour des zones lumineuses (lune, fenêtres, feu) : rendu plus « caméra »."""
    a = np.asarray(img).astype(np.float32)
    lum = a.max(axis=2, keepdims=True)
    bright = np.clip((lum - 150) / 105, 0, 1) * a
    small = Image.fromarray(bright.astype(np.uint8)).resize((img.width // 4, img.height // 4), Image.BILINEAR)
    small = small.filter(ImageFilter.GaussianBlur(14)).resize(img.size, Image.BILINEAR)
    out = a + np.asarray(small).astype(np.float32) * amount
    return Image.fromarray(np.clip(out, 0, 255).astype(np.uint8))


def light_char(hc, color, side=-1):
    """Éclaire le personnage : dégradé de lumière sur le sweat + liseré coloré côté lumière."""
    a = np.asarray(hc).astype(np.float32)
    h, w = a.shape[:2]
    alpha = a[..., 3:4] / 255
    xx = np.linspace(0, 1, w)[None, :, None]
    yy = np.linspace(0, 1, h)[:, None, None]
    lit = (1 - xx) if side < 0 else xx
    g = 0.78 + 0.42 * lit - 0.22 * yy
    cloth = (a[..., :3].max(axis=2, keepdims=True) > 45)
    rgb = np.where(cloth, a[..., :3] * g, a[..., :3])
    # liseré : bord de la silhouette, plus fort du côté de la lumière
    al = Image.fromarray(a[..., 3].astype(np.uint8))
    k = max(5, (w // 60) | 1)
    edge = np.asarray(al).astype(np.float32) - np.asarray(al.filter(ImageFilter.MinFilter(k))).astype(np.float32)
    edge = np.asarray(Image.fromarray(np.clip(edge, 0, 255).astype(np.uint8)).filter(ImageFilter.GaussianBlur(k / 3))).astype(np.float32) / 255
    rim = (edge * (0.25 + 0.75 * lit[..., 0]))[..., None]
    rgb = rgb + np.array(color, np.float32)[None, None, :] * rim * 0.9
    out = np.concatenate([np.clip(rgb, 0, 255), alpha * 255], axis=2).astype(np.uint8)
    return Image.fromarray(out, "RGBA")


def compose(b, cache):
    """Renvoie (décor, [personnages, personnages yeux fermés]) en deux calques pour la profondeur."""
    key = json.dumps([b.get("scene", "flou"), b.get("params", {}), b.get("char"), b.get("char2")], sort_keys=True)
    if key in cache:
        return cache[key]
    scene = b.get("scene", "flou")
    bg = bloom(SCENES[scene](b.get("params", {})).convert("RGB"), 0.55 if scene in NEW_SCENES else 0.12)
    chars = [c for c in (b.get("char"), b.get("char2")) if c]
    # profondeur de champ : le décor est flou derrière un personnage en gros plan
    close = [c for c in chars if c.get("pose") in ("face", "back") or c.get("head", [0, 0, 0])[2] >= 0.2]
    blur = b.get("dof", 7 if close else (2.5 if chars else 0))
    if blur:
        bg = bg.filter(ImageFilter.GaussianBlur(blur))
    light = tuple(b.get("params", {}).get("light", LIGHT.get(scene, FIRE)))
    layers = []
    for blink in (False, True):
        fg = Image.new("RGBA", (CW, CH), (0, 0, 0, 0))
        for ch in chars:
            hc = hero(ch.get("pose", "stand"), ch.get("expr", "normal"), tuple(ch.get("hoodie", (240, 190, 40))),
                      tuple(ch.get("look", (0, 0))), blink=blink and ch.get("expr", "normal") in ("normal", "side"))
            if "head" in ch:
                # placement par la tête : [u, v, r] en fractions de l'ÉCRAN (caméra au centre, zoom 1.1),
                # r = rayon de la tête en fraction de la largeur de l'écran
                hu, hv, hr = ch["head"]
                hx, hy, hrad = HEAD[ch.get("pose", "stand")]
                sc = (hr * W / 1.1) / hrad
                hc = hc.resize((int(hc.width * sc), int(hc.height * sc)), Image.LANCZOS)
                cu = CW / 2 + (hu - 0.5) * W / 1.1
                cv = CH / 2 + (hv - 0.5) * H / 1.1
                if ch.get("flip"):
                    hc = hc.transpose(Image.FLIP_LEFT_RIGHT)
                    hx = hc.width / sc - hx
                x, y = int(cu - hx * sc), int(cv - hy * sc)
            else:
                th = int(CH * ch.get("h", 0.6))
                hc = hc.resize((int(hc.width * th / hc.height), th), Image.LANCZOS)
                if ch.get("flip"):
                    hc = hc.transpose(Image.FLIP_LEFT_RIGHT)
                x = int(CW * ch.get("x", 0.5) - hc.width / 2)
                y = int(CH * ch.get("y", 1.0) - hc.height)
            hc = light_char(hc, light, ch.get("light_side", -1))
            if ch.get("pose", "stand") in ("stand", "sit"):
                # ombre de contact au sol
                sh = Image.new("RGBA", (CW, CH), (0, 0, 0, 0))
                ImageDraw.Draw(sh).ellipse([x + hc.width * 0.18, y + hc.height * 0.95, x + hc.width * 0.82,
                                            y + hc.height * 1.03], fill=(0, 0, 0, 150))
                fg.alpha_composite(sh.filter(ImageFilter.GaussianBlur(hc.width * 0.04)))
            # ombre portée douce derrière le personnage (le détache du décor)
            shadow = Image.new("RGBA", hc.size, (0, 0, 0, 0))
            shadow.putalpha(hc.getchannel("A").point(lambda v: v * 0.45))
            shadow = shadow.filter(ImageFilter.GaussianBlur(max(4, hc.width // 40)))
            fg.alpha_composite(shadow, (max(0, x + hc.width // 50), max(0, y + hc.width // 60)))
            fg.alpha_composite(hc, (x, y)) if x >= 0 and y >= 0 else fg.paste(hc, (x, y), hc)
        layers.append(fg if chars else None)
    cache[key] = (bg, layers)
    return cache[key]


def particles(fr, b, bi, lt):
    color, n, direction = DUST.get(b.get("scene", "flou"), ((230, 220, 255), 24, 1))
    if b.get("particles") is False:
        return
    rnd = np.random.default_rng(bi * 7 + 3)
    x0 = rnd.uniform(0, W, n)
    y0 = rnd.uniform(0, H, n)
    sp = rnd.uniform(25, 90, n)
    r = rnd.uniform(2, 7, n)
    ph = rnd.uniform(0, 6.28, n)
    layer = Image.new("RGBA", (W, H), (0, 0, 0, 0))
    d = ImageDraw.Draw(layer)
    for i in range(n):
        x = x0[i] + 18 * math.sin(lt * 1.3 + ph[i])
        y = (y0[i] + direction * sp[i] * lt) % H
        al = int(70 + 120 * (0.5 + 0.5 * math.sin(lt * 2 + ph[i])))
        d.ellipse([x - r[i], y - r[i], x + r[i], y + r[i]], fill=color + (al,))
    layer = layer.filter(ImageFilter.GaussianBlur(1.6))
    fr.paste(layer, (0, 0), layer)


def camera(b, k):
    cam = b.get("cam", {})
    z0, z1 = cam.get("z", [1.04, 1.12])
    x0, x1 = cam.get("x", [0.5, 0.5])
    y0, y1 = cam.get("y", [0.5, 0.5])
    t = smooth(k) * 0.6 + k * 0.4
    return R.lerp(z0, z1, t), R.lerp(x0, x1, t), R.lerp(y0, y1, t)


def render(ep, out):
    os.environ.setdefault("VOICE_TEMPO", str(ep.get("voice_tempo", 1.3)))
    os.environ.setdefault("VOICE_FX", ep.get("voice_fx", "leger"))
    beats = ep["beats"]
    # mauvais choix : on annonce « TU ES MORT. » avant de rembobiner (demande de Fio, 02/11)
    for i in range(len(beats) - 1, 0, -1):
        b = beats[i]
        if b.get("type") == "rewind" and "MORT" not in beats[i - 1].get("text", "").upper():
            beats.insert(i, {"scene": "flou", "params": {"light": [255, 40, 40], "colors": [[70, 10, 20], [15, 4, 8]]},
                             "text": "TU ES *MORT*.", "record": b["of"], "shake": 8, "glitch": 0.25,
                             "sfx": [["hit", 0, 0.9]], "cam": {"z": [1.0, 1.12]}})
    # gros plans : le fond flou reprend le décor du lieu où l'on est (demande de Fio, 04/11)
    last = None
    for b in beats:
        sc = b.get("scene", "flou")
        if sc != "flou":
            last = sc
        elif last and "of" not in b.get("params", {}) and "MORT" not in b.get("text", "").upper():
            b["params"] = dict(b.get("params", {}), of=last)
    clips = prepare_voice(beats) if ep.get("voiceover", True) else {}
    for b in beats:
        b.setdefault("dur", 1.5)
    total = sum(b["dur"] for b in beats)
    print(f"durée totale : {total:.1f} s, {len(beats)} plans")
    tmp = tempfile.mkdtemp()
    wav = os.path.join(tmp, "a.wav")
    proc = subprocess.Popen(
        ["ffmpeg", "-loglevel", "error", "-y", "-f", "rawvideo", "-pix_fmt", "rgb24", "-s", f"{W}x{H}",
         "-r", str(FPS), "-i", "-", "-c:v", "libx264", "-preset", "slow", "-crf", "28",
         "-pix_fmt", "yuv420p", os.path.join(tmp, "v.mp4")], stdin=subprocess.PIPE)
    cache, recorded, rec_clock, events = {}, {}, {}, []
    clock = ep.get("clock_start", 2 * 3600 + 47 * 60 + 5)
    lives_total = ep.get("lives_total", 3)
    lives = ep.get("lives")          # vies au début de l'épisode (None = pas de compteur)
    n, t0 = 0, 0.0
    for bi, b in enumerate(beats):
        for s in b.get("sfx", []):
            name, off, vol = (s + [0, 1.0])[:3] if isinstance(s, list) else (s, 0, 1.0)
            events.append((t0 + off, name, vol))
        nf = max(1, int(round(b["dur"] * FPS)))
        if b.get("type") == "rewind":
            src = recorded.get(b["of"], [])
            step = max(1, len(src) // nf) if src else 1
            seq = src[::-1][::step] if src else []
            for i in range(nf):
                a = seq[min(i, len(seq) - 1)] if seq else np.zeros((H, W, 3), np.uint8)
                fr = Image.fromarray(a)
                if (i // 8) % 2 == 0:
                    draw_caption(fr, [("<< ON REMBOBINE", False)], 1, 0.5)
                draw_clock(fr, R.lerp(clock, rec_clock.get(b["of"], clock), i / nf))
                proc.stdin.write(R.finish(fr, n, glitch=0.3, vhs=True).tobytes())
                n += 1
            clock = rec_clock.get(b["of"], clock)
            t0 += b["dur"]
            continue
        lost = None
        if lives is not None and "lives" not in b and "MORT" in b.get("text", "").upper() and b.get("record"):
            b["lives"] = max(0, lives - 1)   # chaque « TU ES MORT » coûte une vie
        if lives is not None and "lives" in b:
            lost = b["lives"] < lives
            lives = b["lives"]
        imgs = compose(b, cache)
        # sous-titres calés sur la voix : chaque morceau dure au prorata de ses lettres
        caps = chunks(b["text"]) if b.get("text") else []
        speak = (len(clips[bi]) / SR) if bi in clips else b["dur"]
        weights = [sum(len(w) for w, _ in c) + 2 for c in caps]
        starts, acc = [], 0.02
        for wgt in weights:
            starts.append(acc)
            acc += speak * wgt / max(1, sum(weights))
        rec = recorded.setdefault(b["record"], []) if b.get("record") else None
        if b.get("record"):
            rec_clock.setdefault(b["record"], clock)
        for i in range(nf):
            lt = i / FPS
            k = i / max(1, nf - 1)
            z, cx, cy = camera(b, k)
            # petit « coup de zoom » à chaque coupe, pour que ça s'enchaîne
            z *= 1 + 0.035 * (1 - smooth(lt / 0.22))
            cw, chh = CW / (K * z), CH / (K * z)
            ox = min(max(0, cx * CW - cw / 2), CW - cw)
            oy = min(max(0, cy * CH - chh / 2), CH - chh)
            if b.get("shake"):
                ox += random.uniform(-1, 1) * b["shake"]
                oy += random.uniform(-1, 1) * b["shake"]
                ox, oy = min(max(0, ox), CW - cw), min(max(0, oy), CH - chh)
            blink = (n % 84) in (0, 1, 2, 3)
            bg, fgs = imgs
            fr = bg.resize((W, H), Image.BILINEAR, box=(ox, oy, ox + cw, oy + chh))
            fg = fgs[1 if blink else 0]
            if fg is not None:
                # parallaxe : le personnage (premier plan) bouge un peu plus que le décor
                pz = 1 + (z - 1) * 1.35
                pw, ph = CW / (K * pz), CH / (K * pz)
                px = min(max(0, cx * CW - pw / 2 + (ox - (cx * CW - cw / 2))), CW - pw)
                py = min(max(0, cy * CH - ph / 2 + (oy - (cy * CH - chh / 2))), CH - ph)
                layer = fg.resize((W, H), Image.BILINEAR, box=(px, py, px + pw, py + ph))
                fr.paste(layer, (0, 0), layer)
            particles(fr, b, bi, lt)
            if lt < 0.1 and bi > 0:
                fr = fr.filter(ImageFilter.GaussianBlur(14 * (1 - lt / 0.1)))
            if b.get("choice"):
                c = b["choice"]
                cnt = str(max(1, c["countdown"] - int(lt))) if c.get("countdown") else None
                prev = beats[bi - 1].get("choice") if bi > 0 else None
                same = bool(prev) and (prev["a"], prev["b"]) == (c["a"], c["b"])
                draw_choice(fr, c["a"], c["b"], lt, c.get("picked"), cnt, enter=not same)
            if caps:
                j = max([x for x in range(len(caps)) if starts[x] <= lt] or [0])
                draw_caption(fr, caps[j], lt - starts[j], max(b.get("text_y", 0.68), 0.235) if lives is not None else b.get("text_y", 0.68))
            draw_clock(fr, clock + lt)
            if lives is not None:
                draw_lives(fr, lives, lives_total, lt if lost else None)
            g = b.get("glitch", 0.0)
            fl = max(0.0, 1 - lt / 0.25) if b.get("flash_in") else 0.0
            arr = R.finish(fr, n, glitch=g, flash=fl, flash_level=0 if t0 == 0 else 255)
            if rec is not None:
                rec.append(arr)
            proc.stdin.write(arr.tobytes())
            n += 1
        clock += b["dur"]
        t0 += b["dur"]
    proc.stdin.close()
    proc.wait()
    R.build_audio(total, events, wav, voice_track(beats, clips, total, tmp) if clips else None)
    subprocess.run(["ffmpeg", "-loglevel", "error", "-y", "-i", os.path.join(tmp, "v.mp4"), "-i", wav,
                    "-c:v", "copy", "-c:a", "aac", "-b:a", "160k", "-shortest", "-movflags", "+faststart", out], check=True)


if __name__ == "__main__":
    with open(sys.argv[1]) as fh:
        render(json.load(fh), sys.argv[2])
