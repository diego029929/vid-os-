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


def scene_salledebain(p):
    """Salle de bain : carrelage, miroir (silhouette possible), lavabo, néon qui grésille."""
    c = Canvas((56, 60, 84), (24, 26, 40))
    d = c.d
    for i in range(0, 26):
        v = i * 0.04
        d.line([c.P(0, v), c.P(1, v)], fill=(40, 44, 64), width=6)
    for i in range(0, 14):
        u = i * 0.08
        d.line([c.P(u, 0), c.P(u, 1)], fill=(40, 44, 64), width=6)
    d.rectangle(c.box(0.28, 0.16, 0.72, 0.50), fill=(20, 22, 36), outline=(150, 150, 170), width=14)
    d.rectangle(c.box(0.30, 0.18, 0.70, 0.48), fill=(70, 74, 104))
    if p.get("figure"):
        d.ellipse(c.box(0.55, 0.24, 0.63, 0.24 + 0.08 * CW / CH), fill=(16, 14, 26))
        d.polygon([c.P(0.52, 0.48), c.P(0.54, 0.31), c.P(0.64, 0.31), c.P(0.66, 0.48)], fill=(16, 14, 26))
        for u in (0.575, 0.605):
            d.ellipse(c.box(u - 0.005, 0.265, u + 0.005, 0.265 + 0.01 * CW / CH), fill=(255, 60, 50))
    d.rectangle(c.box(0.26, 0.10, 0.74, 0.12), fill=(230, 240, 255))
    c.glow(0.5, 0.11, 0.5, (200, 220, 255), 0.35 if not p.get("dark") else 0.1)
    d = c.d
    d.rounded_rectangle(c.box(0.30, 0.56, 0.70, 0.64), radius=30, fill=(200, 200, 215))
    d.rectangle(c.box(0.46, 0.64, 0.54, 0.95), fill=(170, 170, 190))
    d.rectangle(c.box(0.48, 0.52, 0.52, 0.57), fill=(150, 150, 170))
    d.rectangle(c.box(0, 0.95, 1, 1), fill=(18, 18, 30))
    if p.get("red") or p.get("green"):
        c.glow(0.5, 0.33, 0.5, _lightcol(p, FIRE), 0.3)
    return c.done()


def scene_grenier(p):
    """Grenier : charpente en pente, lucarne avec la lune, cartons, ampoule nue."""
    c = Canvas((30, 24, 44), (52, 38, 50))
    d = c.d
    d.polygon([c.P(0, 0), c.P(0.5, -0.05), c.P(1, 0), c.P(1, 0.45), c.P(0.5, 0.05), c.P(0, 0.45)], fill=(22, 16, 30))
    for k in range(1, 6):
        t = k / 6
        d.line([c.P(0.5, 0.05), c.P(-0.1 + 0.0 * t, 0.45 + t * 0.6)], fill=(70, 48, 50), width=26)
        d.line([c.P(0.5, 0.05), c.P(1.1, 0.45 + t * 0.6)], fill=(70, 48, 50), width=26)
    d.rectangle(c.box(0.40, 0.18, 0.60, 0.32), fill=(40, 40, 90))
    c.glow(0.5, 0.25, 0.3, (200, 200, 255), 0.35)
    d = c.d
    d.ellipse(c.box(0.52, 0.20, 0.57, 0.20 + 0.05 * CW / CH), fill=(250, 248, 235))
    d.line([c.P(0.5, 0.18), c.P(0.5, 0.32)], fill=(20, 16, 30), width=10)
    d.line([c.P(0.40, 0.25), c.P(0.60, 0.25)], fill=(20, 16, 30), width=10)
    d.line([c.P(0.30, 0.05), c.P(0.30, 0.40)], fill=(20, 16, 20), width=4)
    d.ellipse(c.box(0.29, 0.40, 0.31, 0.43), fill=(255, 220, 150))
    if not p.get("dark"):
        c.glow(0.30, 0.42, 0.5, (255, 190, 110), 0.35)
    d = c.d
    rnd = random.Random(p.get("seed", 5))
    for _ in range(6):
        u = rnd.uniform(0.0, 0.85)
        w = rnd.uniform(0.10, 0.18)
        h = rnd.uniform(0.08, 0.16)
        d.rectangle(c.box(u, 0.92 - h, u + w, 0.92), fill=(120, 86, 60), outline=(70, 50, 36), width=8)
    d.rectangle(c.box(0, 0.92, 1, 1), fill=(40, 28, 26))
    if p.get("red") or p.get("green"):
        c.glow(0.5, 0.6, 0.6, _lightcol(p, FIRE), 0.25)
    return c.done()


def scene_cave(p):
    """Cave voûtée : pierres, escalier qui descend, bouteilles, lampe torche."""
    c = Canvas((26, 22, 30), (14, 12, 18))
    d = c.d
    rnd = random.Random(p.get("seed", 3))
    for row in range(22):
        v = row * 0.045
        off = 0.04 if row % 2 else 0
        u = -off
        while u < 1:
            g = rnd.randint(46, 70)
            d.rectangle(c.box(u + 0.004, v + 0.004, u + 0.08, v + 0.041), fill=(g, g - 8, g - 4))
            u += 0.084
    d.ellipse(c.box(0.15, 0.05, 0.85, 0.75), fill=(18, 14, 22))
    d.rectangle(c.box(0.15, 0.40, 0.85, 0.95), fill=(18, 14, 22))
    for i in range(6):
        d.rectangle(c.box(0.30 + i * 0.03, 0.42 + i * 0.07, 0.70 - i * 0.03, 0.47 + i * 0.07), fill=(60, 50, 56))
    for k in range(5):
        for j in range(3):
            d.ellipse(c.box(0.02 + j * 0.035, 0.55 + k * 0.07, 0.05 + j * 0.035, 0.58 + k * 0.07), fill=(30, 60, 40))
    beam = p.get("torch", True)
    if beam:
        c.soft(lambda dd, cc: dd.polygon([cc.P(0.9, 1.0), cc.P(0.35, 0.35), cc.P(0.65, 0.30)], fill=(255, 240, 200, 90)), 0.02)
        c.glow(0.5, 0.33, 0.25, (255, 240, 200), 0.3)
    if p.get("eyes"):
        d = c.d
        for u in (0.48, 0.52):
            d.ellipse(c.box(u - 0.006, 0.30, u + 0.006, 0.30 + 0.012 * CW / CH), fill=(255, 60, 50))
        c.glow(0.5, 0.305, 0.08, (255, 60, 50), 0.4)
    if p.get("red") or p.get("green"):
        c.glow(0.5, 0.5, 0.6, _lightcol(p, FIRE), 0.25)
    return c.done()


def scene_cimetiere(p):
    """Cimetière la nuit : tombes, croix, grille, brume, lune."""
    c = Canvas((18, 20, 44), (56, 46, 86))
    d = c.d
    c.glow(0.3, 0.2, 0.45, (200, 200, 255), 0.4)
    d = c.d
    r = 0.07
    d.ellipse(c.box(0.3 - r, 0.2 - r * CW / CH, 0.3 + r, 0.2 + r * CW / CH), fill=(250, 248, 235))
    d.polygon([c.P(0.62, 0.62), c.P(0.62, 0.36), c.P(0.70, 0.28), c.P(0.78, 0.36), c.P(0.78, 0.62)], fill=(20, 18, 36))
    d.polygon([c.P(0.68, 0.28), c.P(0.70, 0.18), c.P(0.72, 0.28)], fill=(20, 18, 36))
    for i in range(40):
        u = i * 0.026
        d.line([c.P(u, 0.50), c.P(u, 0.64)], fill=(16, 14, 28), width=8)
    d.line([c.P(0, 0.52), c.P(1, 0.52)], fill=(16, 14, 28), width=8)
    d.rectangle(c.box(0, 0.64, 1, 1), fill=(22, 24, 34))
    rnd = random.Random(p.get("seed", 9))
    for row, (v, s) in enumerate(((0.70, 0.6), (0.80, 0.8), (0.93, 1.1))):
        u = rnd.uniform(-0.05, 0.05)
        while u < 1:
            w = 0.07 * s
            h = rnd.uniform(0.06, 0.10) * s
            col = (70 + row * 10, 70 + row * 10, 90 + row * 10)
            if rnd.random() < 0.35:
                d.rectangle(c.box(u + w * 0.4, v - h * 1.3, u + w * 0.6, v), fill=col)
                d.rectangle(c.box(u + w * 0.15, v - h * 1.0, u + w * 0.85, v - h * 0.82), fill=col)
            else:
                d.rounded_rectangle(c.box(u, v - h, u + w, v), radius=int(30 * s), fill=col)
            u += w + rnd.uniform(0.05, 0.12)
    c.soft(lambda dd, cc: dd.rectangle(cc.box(-0.1, 0.72, 1.1, 0.90), fill=(170, 160, 220, 110)), 0.05)
    if p.get("figure"):
        d = c.d
        d.ellipse(c.box(0.47, 0.60, 0.53, 0.60 + 0.06 * CW / CH), fill=(10, 8, 18))
        d.polygon([c.P(0.45, 0.80), c.P(0.47, 0.64), c.P(0.53, 0.64), c.P(0.55, 0.80)], fill=(10, 8, 18))
    if p.get("red") or p.get("green"):
        c.glow(0.5, 0.6, 0.6, _lightcol(p, FIRE), 0.25)
    return c.done()


def scene_eglise(p):
    """Intérieur d'église : vitrail, bancs, cierges, allée centrale."""
    c = Canvas((24, 18, 40), (40, 28, 46))
    d = c.d
    for u in (0.12, 0.88):
        d.rectangle(c.box(u - 0.05, 0, u + 0.05, 1), fill=(34, 26, 46))
    d.ellipse(c.box(0.35, 0.06, 0.65, 0.06 + 0.30 * CW / CH), fill=(20, 16, 30))
    d.rectangle(c.box(0.35, 0.14, 0.65, 0.42), fill=(20, 16, 30))
    cols = [(200, 60, 70), (70, 110, 220), (230, 180, 60), (80, 170, 110)]
    rnd = random.Random(p.get("seed", 2))
    for i in range(6):
        for j in range(5):
            d.rectangle(c.box(0.37 + i * 0.044, 0.16 + j * 0.052, 0.405 + i * 0.044, 0.205 + j * 0.052), fill=rnd.choice(cols))
    c.glow(0.5, 0.28, 0.5, (180, 120, 255), 0.3)
    d = c.d
    for k in range(5):
        v = 0.58 + k * 0.08
        sp = 0.06 + k * 0.012
        d.rectangle(c.box(0.0, v, 0.5 - sp, v + 0.03), fill=(70, 44, 36))
        d.rectangle(c.box(0.5 + sp, v, 1.0, v + 0.03), fill=(70, 44, 36))
    for u in (0.30, 0.34, 0.66, 0.70):
        d.rectangle(c.box(u - 0.006, 0.46, u + 0.006, 0.52), fill=(240, 230, 210))
        d.ellipse(c.box(u - 0.005, 0.445, u + 0.005, 0.46), fill=(255, 200, 100))
        if not p.get("dark"):
            c.glow(u, 0.45, 0.08, (255, 190, 100), 0.4)
            d = c.d
    if p.get("figure"):
        d.ellipse(c.box(0.47, 0.44, 0.53, 0.44 + 0.06 * CW / CH), fill=(10, 8, 18))
        d.polygon([c.P(0.45, 0.62), c.P(0.47, 0.48), c.P(0.53, 0.48), c.P(0.55, 0.62)], fill=(10, 8, 18))
    if p.get("red") or p.get("green"):
        c.glow(0.5, 0.5, 0.6, _lightcol(p, FIRE), 0.25)
    return c.done()


def scene_voiture(p):
    """Intérieur de voiture la nuit : pare-brise, route éclairée par les phares, volant."""
    c = Canvas((10, 10, 22), (10, 10, 18))
    d = c.d
    d.polygon([c.P(0.05, 0.12), c.P(0.95, 0.12), c.P(1.0, 0.55), c.P(0.0, 0.55)], fill=(20, 20, 44))
    d.polygon([c.P(0.0, 0.55), c.P(1.0, 0.55), c.P(1.0, 0.45), c.P(0.58, 0.33), c.P(0.42, 0.33), c.P(0.0, 0.45)], fill=(26, 24, 36))
    d.polygon([c.P(0.46, 0.33), c.P(0.54, 0.33), c.P(0.85, 0.55), c.P(0.15, 0.55)], fill=(70, 66, 80))
    if p.get("headlights", True):
        c.soft(lambda dd, cc: dd.polygon([cc.P(0.47, 0.34), cc.P(0.53, 0.34), cc.P(0.80, 0.55), cc.P(0.20, 0.55)], fill=(255, 240, 190, 110)), 0.02)
        d = c.d
    for k in range(4):
        v = 0.36 + k * 0.05
        d.rectangle(c.box(0.497 - k * 0.003, v, 0.503 + k * 0.003, v + 0.015 + k * 0.006), fill=(230, 220, 180))
    rnd = random.Random(p.get("seed", 6))
    for side in (0, 1):
        for _ in range(6):
            u = rnd.uniform(0.0, 0.38) if side == 0 else rnd.uniform(0.62, 1.0)
            h = rnd.uniform(0.08, 0.2)
            d.polygon([c.P(u, 0.40 - h), c.P(u - 0.05, 0.42), c.P(u + 0.05, 0.42)], fill=(12, 14, 24))
    if p.get("figure"):
        d.ellipse(c.box(0.47, 0.37, 0.53, 0.37 + 0.06 * CW / CH), fill=(8, 6, 14))
        d.polygon([c.P(0.46, 0.50), c.P(0.475, 0.41), c.P(0.525, 0.41), c.P(0.54, 0.50)], fill=(8, 6, 14))
    d.rectangle(c.box(0, 0, 1, 0.12), fill=(16, 14, 24))
    d.rectangle(c.box(0, 0.55, 1, 1), fill=(22, 20, 32))
    d.rectangle(c.box(0.40, 0.02, 0.60, 0.07), fill=(40, 38, 54))
    d.ellipse(c.box(0.10, 0.62, 0.60, 0.62 + 0.5 * CW / CH), outline=(8, 8, 14), width=40)
    d.rectangle(c.box(0.62, 0.62, 0.86, 0.70), fill=(14, 12, 22))
    if p.get("red") or p.get("green"):
        c.glow(0.5, 0.4, 0.6, _lightcol(p, FIRE), 0.25)
    return c.done()


def scene_salon(p):
    """Salon la nuit : télé qui grésille (neige), canapé, lampe, fenêtre aux rideaux."""
    c = Canvas((40, 30, 60), (20, 16, 30))
    d = c.d
    night_sky(c, 0.70, 0.12, 0.96, 0.42, moon=(0.4, 0.3), seed=p.get("seed", 4))
    d = c.d
    d.rectangle(c.box(0.69, 0.11, 0.97, 0.43), outline=(24, 18, 40), width=22)
    d.polygon([c.P(0.66, 0.08), c.P(0.74, 0.08), c.P(0.72, 0.48), c.P(0.66, 0.50)], fill=(90, 40, 60))
    d.polygon([c.P(0.92, 0.08), c.P(1.0, 0.08), c.P(1.0, 0.50), c.P(0.94, 0.48)], fill=(90, 40, 60))
    d.rectangle(c.box(0.10, 0.30, 0.52, 0.56), fill=(16, 16, 20))
    rnd = random.Random(p.get("seed", 4) + 1)
    if p.get("tv", True):
        for _ in range(900):
            u = rnd.uniform(0.12, 0.50)
            v = rnd.uniform(0.32, 0.54)
            g = rnd.randint(90, 255)
            d.rectangle(c.box(u, v, u + 0.006, v + 0.004), fill=(g, g, g))
        c.glow(0.31, 0.43, 0.6, (190, 210, 255), 0.35)
        d = c.d
    if p.get("text"):
        d.text(c.P(0.16, 0.40), str(p["text"]), fill=(255, 60, 50), font=font(int(c.w * 0.05)))
    d.rectangle(c.box(0.08, 0.56, 0.54, 0.62), fill=(50, 38, 60))
    d.rounded_rectangle(c.box(0.0, 0.70, 0.75, 0.92), radius=40, fill=(90, 50, 70))
    d.rounded_rectangle(c.box(0.0, 0.64, 0.75, 0.76), radius=40, fill=(110, 62, 84))
    d.line([c.P(0.86, 0.50), c.P(0.86, 0.92)], fill=(30, 24, 40), width=10)
    d.polygon([c.P(0.80, 0.50), c.P(0.92, 0.50), c.P(0.89, 0.42), c.P(0.83, 0.42)], fill=(220, 180, 120))
    d.rectangle(c.box(0, 0.92, 1, 1), fill=(16, 12, 24))
    if p.get("red") or p.get("green"):
        c.glow(0.5, 0.5, 0.6, _lightcol(p, FIRE), 0.25)
    return c.done()


IA_STYLE = ("cinematic horror movie still, night, dark moody lighting, purple and orange tones, "
            "empty, no people, no text, highly detailed, vertical")
IA_DIR = os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "assets", "ia")


def ia_image(prompt, seed=1):
    """Décor généré par IA (Pollinations, gratuit, sans clé), mis en cache dans assets/ia/."""
    import hashlib
    import time
    import urllib.parse
    import urllib.request
    os.makedirs(IA_DIR, exist_ok=True)
    full = f"{prompt}, {IA_STYLE}"
    path = os.path.join(IA_DIR, hashlib.sha1(f"{full}|{seed}".encode()).hexdigest()[:16] + ".jpg")
    if not os.path.exists(path):
        url = ("https://image.pollinations.ai/prompt/" + urllib.parse.quote(full)
               + f"?width=720&height=1280&nologo=true&seed={seed}")
        last = None
        for attempt in range(4):
            try:
                with urllib.request.urlopen(url, timeout=180) as r:
                    data = r.read()
                if len(data) < 5000:
                    raise RuntimeError("image trop petite")
                open(path, "wb").write(data)
                break
            except Exception as e:  # noqa: BLE001
                last = e
                time.sleep(5 * (attempt + 1))
        else:
            raise RuntimeError(f"décor IA impossible à générer ({prompt!r}) : {last}")
    img = Image.open(path).convert("RGB")
    img = img.crop((0, 0, img.width, int(img.height * 0.93)))  # retire le filigrane du bas
    s = max(CW / img.width, CH / img.height)
    img = img.resize((int(img.width * s) + 1, int(img.height * s) + 1), Image.LANCZOS)
    x, y = (img.width - CW) // 2, (img.height - CH) // 2
    return img.crop((x, y, x + CW, y + CH))


def scene_ia(p):
    """Décor IA : "params": {"prompt": "abandoned hospital corridor", "seed": 3}.
    Accepte aussi "red" / "green" / "dark" (assombrit) et "figure" (silhouette aux yeux rouges)."""
    img = ia_image(p.get("prompt", "dark empty room"), p.get("seed", 1))
    if p.get("dark"):
        img = Image.eval(img, lambda x: int(x * 0.55))
    if not (p.get("red") or p.get("green") or p.get("figure")):
        return img
    c = Canvas((0, 0, 0), (0, 0, 0))
    c.img = img.resize((c.w, c.h), Image.LANCZOS)
    c.d = ImageDraw.Draw(c.img)
    if p.get("figure"):
        u, v = p.get("fig_at", (0.5, 0.75))
        s = p.get("fig_size", 1.0)
        d = c.d
        r = 0.03 * s
        d.ellipse(c.box(u - r, v - 0.20 * s, u + r, v - 0.20 * s + 2 * r * CW / CH), fill=(8, 6, 14))
        d.polygon([c.P(u - 0.05 * s, v), c.P(u - 0.03 * s, v - 0.15 * s), c.P(u + 0.03 * s, v - 0.15 * s),
                   c.P(u + 0.05 * s, v)], fill=(8, 6, 14))
        for du in (-0.012, 0.012):
            e = 0.005 * s
            d.ellipse(c.box(u + du * s - e, v - 0.18 * s, u + du * s + e, v - 0.18 * s + 2 * e * CW / CH),
                      fill=(255, 60, 50))
        c.glow(u, v - 0.175 * s, 0.06 * s, (255, 60, 50), 0.4)
    if p.get("red") or p.get("green"):
        c.glow(0.5, 0.5, 0.7, _lightcol(p, FIRE), 0.3)
    return c.done()


def _fig(c, u, v, s=1.0, col=(10, 8, 18), eyes=False):
    """Silhouette debout, pieds en (u, v), hauteur ~0.2*s."""
    d = c.d
    r = 0.03 * s
    d.ellipse(c.box(u - r, v - 0.20 * s, u + r, v - 0.20 * s + 2 * r * CW / CH), fill=col)
    d.polygon([c.P(u - 0.05 * s, v), c.P(u - 0.03 * s, v - 0.15 * s), c.P(u + 0.03 * s, v - 0.15 * s), c.P(u + 0.05 * s, v)], fill=col)
    if eyes:
        for du in (-0.012, 0.012):
            e = 0.005 * s
            d.ellipse(c.box(u + du * s - e, v - 0.18 * s, u + du * s + e, v - 0.18 * s + 2 * e * CW / CH), fill=(255, 60, 50))
        c.glow(u, v - 0.175 * s, 0.06 * s, (255, 60, 50), 0.4)


def _end(c, p, u=0.5, v=0.5):
    if p.get("figure"):
        _fig(c, *p.get("fig_at", (u, v + 0.15)), s=p.get("fig_size", 1.0), eyes=True)
    if p.get("red") or p.get("green"):
        c.glow(0.5, 0.5, 0.6, _lightcol(p, FIRE), 0.25)
    return c.done()


def _moon(c, u, v, r=0.06):
    c.glow(u, v, r * 7, (200, 200, 255), 0.35)
    c.d.ellipse(c.box(u - r, v - r * CW / CH, u + r, v + r * CW / CH), fill=(250, 248, 235))


def _stars(c, seed, vmax=0.4, n=50):
    rnd = random.Random(seed)
    for _ in range(n):
        x, y, r = rnd.uniform(0, 1), rnd.uniform(0, vmax), rnd.uniform(0.0015, 0.0035)
        c.d.ellipse(c.box(x - r, y - r * CW / CH, x + r, y + r * CW / CH), fill=(220, 220, 255))


def scene_hopital(p):
    """Couloir d'hôpital : néons, portes de chambres, brancard abandonné."""
    c = Canvas((60, 74, 80), (28, 36, 40))
    d = c.d
    d.polygon([c.P(0, 0), c.P(0.4, 0.35), c.P(0.6, 0.35), c.P(1, 0)], fill=(80, 96, 100))
    d.polygon([c.P(0, 1), c.P(0.4, 0.55), c.P(0.6, 0.55), c.P(1, 1)], fill=(70, 90, 86))
    d.rectangle(c.box(0.4, 0.35, 0.6, 0.55), fill=(16, 22, 26))
    for k in range(4):
        t = k / 4
        uL, uR = 0.4 * t, 1 - 0.4 * t
        v0, v1 = 0.35 * t, 1 - 0.45 * t
        d.line([c.P(uL + 0.02, v0 + 0.02), c.P(uR - 0.02, v0 + 0.02)], fill=(230, 255, 250), width=int(14 - 3 * k))
        if k < 3:
            dh = (v1 - v0) * 0.55
            d.rectangle(c.box(uL + 0.01, v1 - dh, uL + 0.06 - 0.01 * k, v1 - 0.02), fill=(40, 70, 80))
            d.rectangle(c.box(uR - 0.06 + 0.01 * k, v1 - dh, uR - 0.01, v1 - 0.02), fill=(40, 70, 80))
    if not p.get("dark"):
        c.glow(0.5, 0.05, 0.6, (210, 255, 245), 0.3)
    d = c.d
    d.rectangle(c.box(0.55, 0.72, 0.85, 0.76), fill=(200, 210, 210))
    for u in (0.57, 0.83):
        d.line([c.P(u, 0.76), c.P(u, 0.86)], fill=(120, 130, 130), width=8)
    return _end(c, p, 0.5, 0.40)


def scene_classe(p):
    """Salle de classe vide : tableau noir avec un message, pupitres, horloge."""
    c = Canvas((52, 44, 60), (30, 24, 34))
    d = c.d
    d.rectangle(c.box(0.10, 0.14, 0.90, 0.42), fill=(28, 52, 40), outline=(110, 80, 50), width=16)
    d.text(c.P(0.16, 0.22), str(p.get("text", "NE TE RETOURNE PAS")), fill=(235, 235, 225), font=font(int(c.w * 0.055)))
    d.ellipse(c.box(0.45, 0.04, 0.55, 0.04 + 0.10 * CW / CH), fill=(230, 225, 210), outline=(40, 30, 30), width=8)
    d.line([c.P(0.5, 0.07), c.P(0.5, 0.045 + 0.05 * CW / CH)], fill=(20, 20, 20), width=6)
    for row, (v, s) in enumerate(((0.60, 0.7), (0.72, 0.85), (0.88, 1.05))):
        for u in (0.12, 0.42, 0.72):
            uu = 0.5 + (u - 0.5) * s
            d.rectangle(c.box(uu - 0.10 * s, v, uu + 0.10 * s, v + 0.03 * s), fill=(150, 110, 70))
            d.line([c.P(uu - 0.08 * s, v), c.P(uu - 0.08 * s, v + 0.09 * s)], fill=(60, 60, 70), width=8)
            d.line([c.P(uu + 0.08 * s, v), c.P(uu + 0.08 * s, v + 0.09 * s)], fill=(60, 60, 70), width=8)
    c.glow(0.95, 0.3, 0.5, (160, 170, 255), 0.25)
    return _end(c, p, 0.5, 0.45)


def scene_metro(p):
    """Quai de métro désert : carrelage blanc, panneau, rails, tunnel noir."""
    c = Canvas((70, 70, 84), (30, 30, 40))
    d = c.d
    for i in range(30):
        d.line([c.P(0, i * 0.02), c.P(1, i * 0.02)], fill=(56, 56, 70), width=4)
    d.rectangle(c.box(0.25, 0.08, 0.75, 0.15), fill=(30, 60, 140))
    d.text(c.P(0.30, 0.085), str(p.get("text", "STATION FANTÔME")), fill=(255, 255, 255), font=font(int(c.w * 0.05)))
    if p.get("tunnel", True):
        d.ellipse(c.box(0.30, 0.22, 0.70, 0.22 + 0.40 * CW / CH), fill=(8, 8, 12))
    else:   # mur carrelé avec plan du métro et banc (pour les gros plans : pas de rond noir derrière la tête)
        d.rectangle(c.box(0.08, 0.30, 0.40, 0.50), fill=(40, 50, 90), outline=(200, 200, 210), width=6)
        for k in range(4):
            d.line([c.P(0.10, 0.34 + k * 0.04), c.P(0.38, 0.36 + k * 0.035)], fill=(230, 120, 60), width=5)
        d.rectangle(c.box(0.58, 0.50, 0.92, 0.53), fill=(60, 110, 170))
        c.glow(0.5, 0.3, 0.6, (230, 230, 255), 0.18)
        d = c.d
    d.rectangle(c.box(0, 0.62, 1, 0.70), fill=(150, 140, 120))
    d.rectangle(c.box(0, 0.70, 1, 0.71), fill=(230, 200, 60))
    d.rectangle(c.box(0, 0.71, 1, 1), fill=(20, 18, 24))
    for v in (0.80, 0.92):
        d.line([c.P(0, v), c.P(1, v)], fill=(120, 120, 130), width=10)
    if p.get("headlights"):
        for u in (0.44, 0.56):
            c.glow(u, 0.45, 0.15, (255, 250, 220), 0.6)
    return _end(c, p, 0.5, 0.47)


def scene_plage(p):
    """Plage la nuit (Bretagne) : mer, vagues, rochers, lune sur l'eau."""
    c = Canvas((14, 16, 40), (60, 50, 96))
    _stars(c, p.get("seed", 1), 0.35)
    _moon(c, 0.7, 0.2)
    d = c.d
    d.rectangle(c.box(0, 0.45, 1, 0.70), fill=(20, 28, 60))
    c.soft(lambda dd, cc: dd.rectangle(cc.box(0.66, 0.46, 0.74, 0.70), fill=(220, 220, 255, 120)), 0.01)
    d = c.d
    for k in range(6):
        v = 0.50 + k * 0.035
        d.line([c.P(0, v), c.P(1, v + 0.005)], fill=(60, 70, 120), width=4)
    d.polygon([c.P(0, 0.70), c.P(1, 0.66), c.P(1, 1), c.P(0, 1)], fill=(70, 60, 74))
    d.polygon([c.P(0, 0.70), c.P(1, 0.66), c.P(1, 0.68), c.P(0, 0.73)], fill=(150, 156, 190))
    for u, w, h in ((0.05, 0.18, 0.12), (0.80, 0.22, 0.16)):
        d.polygon([c.P(u, 0.72), c.P(u + w * 0.3, 0.72 - h), c.P(u + w * 0.7, 0.72 - h * 0.8), c.P(u + w, 0.72)], fill=(30, 26, 40))
    return _end(c, p, 0.45, 0.66)


def scene_phare(p):
    """Phare sur une falaise, faisceau dans la nuit, mer agitée."""
    c = Canvas((16, 18, 44), (50, 44, 84))
    _stars(c, p.get("seed", 2), 0.4)
    d = c.d
    c.soft(lambda dd, cc: dd.polygon([cc.P(0.62, 0.20), cc.P(-0.2, 0.05), cc.P(-0.2, 0.30)], fill=(255, 245, 200, 90)), 0.02)
    d = c.d
    d.polygon([c.P(0.40, 1), c.P(0.45, 0.62), c.P(0.80, 0.58), c.P(1, 0.66), c.P(1, 1)], fill=(24, 22, 34))
    d.polygon([c.P(0.57, 0.62), c.P(0.59, 0.24), c.P(0.65, 0.24), c.P(0.67, 0.62)], fill=(220, 220, 230))
    for v in (0.32, 0.42, 0.52):
        d.rectangle(c.box(0.58, v, 0.66, v + 0.04), fill=(200, 50, 60))
    d.rectangle(c.box(0.585, 0.18, 0.655, 0.24), fill=(255, 240, 180))
    d.polygon([c.P(0.575, 0.18), c.P(0.62, 0.13), c.P(0.665, 0.18)], fill=(30, 26, 40))
    c.glow(0.62, 0.21, 0.25, (255, 240, 180), 0.6)
    d = c.d
    d.polygon([c.P(0, 0.80), c.P(0.45, 0.78), c.P(0.40, 1), c.P(0, 1)], fill=(18, 26, 56))
    for k in range(5):
        v = 0.82 + k * 0.035
        d.line([c.P(0, v), c.P(0.42, v - 0.01)], fill=(80, 90, 150), width=5)
    return _end(c, p, 0.75, 0.45)


def scene_grange(p):
    """Grange : poutres, foin, lanterne, porte entrouverte sur la nuit."""
    c = Canvas((44, 28, 24), (28, 18, 16))
    d = c.d
    for i in range(14):
        u = i * 0.075
        d.rectangle(c.box(u, 0, u + 0.07, 1), fill=(64 + (i % 3) * 6, 40, 30))
    d.polygon([c.P(0.30, 0.95), c.P(0.30, 0.35), c.P(0.70, 0.35), c.P(0.70, 0.95)], fill=(18, 16, 34))
    _moon(c, 0.58, 0.45, 0.03)
    d = c.d
    d.polygon([c.P(0.50, 0.95), c.P(0.50, 0.35), c.P(0.70, 0.35), c.P(0.70, 0.95)], fill=(90, 56, 40))
    d.line([c.P(0.50, 0.35), c.P(0.70, 0.95)], fill=(60, 36, 26), width=14)
    d.line([c.P(0, 0.18), c.P(1, 0.18)], fill=(40, 24, 18), width=40)
    for u, w in ((0.0, 0.26), (0.74, 0.26)):
        d.rounded_rectangle(c.box(u, 0.70, u + w, 0.95), radius=20, fill=(140, 108, 50))
        d.rounded_rectangle(c.box(u + 0.03, 0.55, u + w - 0.03, 0.72), radius=20, fill=(150, 118, 56))
    d.line([c.P(0.85, 0.18), c.P(0.85, 0.40)], fill=(20, 16, 14), width=4)
    d.rectangle(c.box(0.83, 0.40, 0.87, 0.46), fill=(255, 200, 100))
    if not p.get("dark"):
        c.glow(0.85, 0.43, 0.4, (255, 180, 90), 0.4)
    d = c.d
    d.rectangle(c.box(0, 0.95, 1, 1), fill=(30, 22, 16))
    return _end(c, p, 0.6, 0.80)


def scene_tente(p):
    """Camping : intérieur de tente éclairé par une lampe, ombre sur la toile."""
    c = Canvas((120, 70, 40), (60, 34, 24))
    d = c.d
    d.polygon([c.P(0.5, 0.02), c.P(-0.1, 1), c.P(1.1, 1)], fill=(170, 100, 50))
    d.polygon([c.P(0.5, 0.02), c.P(0.35, 1), c.P(0.65, 1)], fill=(150, 86, 44))
    d.line([c.P(0.5, 0.02), c.P(0.5, 1)], fill=(110, 60, 30), width=10)
    if p.get("shadow", True):
        c.soft(lambda dd, cc: (dd.ellipse(cc.box(0.66, 0.30, 0.78, 0.30 + 0.12 * CW / CH), fill=(30, 14, 10, 200)),
                               dd.polygon([cc.P(0.62, 0.75), cc.P(0.65, 0.42), cc.P(0.79, 0.42), cc.P(0.84, 0.75)], fill=(30, 14, 10, 200)),
                               dd.line([cc.P(0.79, 0.45), cc.P(0.95, 0.30)], fill=(30, 14, 10, 200), width=30)), 0.01)
    d = c.d
    d.rectangle(c.box(0, 0.86, 1, 1), fill=(50, 40, 60))
    d.rounded_rectangle(c.box(0.05, 0.84, 0.55, 0.96), radius=30, fill=(40, 70, 120))
    d.rectangle(c.box(0.44, 0.78, 0.50, 0.86), fill=(240, 230, 200))
    c.glow(0.47, 0.80, 0.5, (255, 220, 160), 0.45)
    return c.done() if not (p.get("red") or p.get("green")) else _end(c, p)


def scene_bureau(p):
    """Open space la nuit : écrans allumés, chaises vides, baie vitrée sur la ville."""
    c = Canvas((24, 22, 44), (14, 12, 24))
    night_sky(c, 0.0, 0.08, 1.0, 0.45, moon=(0.8, 0.3), seed=p.get("seed", 12))
    d = c.d
    for u in (0.0, 0.25, 0.5, 0.75, 1.0):
        d.line([c.P(u, 0.08), c.P(u, 0.45)], fill=(30, 30, 44), width=14)
    d.rectangle(c.box(0, 0, 1, 0.08), fill=(34, 32, 46))
    d.rectangle(c.box(0, 0.45, 1, 1), fill=(26, 24, 36))
    for v, s in ((0.62, 0.7), (0.80, 1.0)):
        d.rectangle(c.box(0.0, v, 1.0, v + 0.025 * s), fill=(90, 86, 100))
        for u in (0.15, 0.5, 0.85):
            d.rectangle(c.box(u - 0.07 * s, v - 0.10 * s, u + 0.07 * s, v - 0.01), fill=(10, 10, 16))
            d.rectangle(c.box(u - 0.06 * s, v - 0.09 * s, u + 0.06 * s, v - 0.02 * s), fill=(80, 140, 255))
            c.glow(u, v - 0.05 * s, 0.15 * s, (80, 140, 255), 0.3)
            d = c.d
    return _end(c, p, 0.5, 0.55)


def scene_piscine(p):
    """Piscine couverte la nuit : eau turquoise, carrelage, plongeoir, reflets."""
    c = Canvas((30, 40, 60), (14, 20, 30))
    d = c.d
    for i in range(10):
        d.rectangle(c.box(0.02 + i * 0.1, 0.06, 0.09 + i * 0.1, 0.30), fill=(40, 50, 90))
    d.rectangle(c.box(0, 0.40, 1, 0.48), fill=(170, 180, 190))
    d.polygon([c.P(0, 0.48), c.P(1, 0.48), c.P(1, 0.95), c.P(0, 0.95)], fill=(20, 150, 170))
    rnd = random.Random(p.get("seed", 7))
    for _ in range(40):
        u, v = rnd.uniform(0, 1), rnd.uniform(0.5, 0.93)
        d.line([c.P(u, v), c.P(u + rnd.uniform(0.03, 0.08), v)], fill=(120, 230, 240), width=5)
    for k in range(1, 6):
        d.line([c.P(k / 6, 0.48), c.P(k / 6, 0.95)], fill=(10, 100, 130), width=6)
    c.glow(0.5, 0.75, 0.7, (40, 220, 230), 0.3)
    d = c.d
    d.rectangle(c.box(0.70, 0.36, 0.95, 0.39), fill=(230, 230, 240))
    d.line([c.P(0.92, 0.39), c.P(0.92, 0.48)], fill=(180, 180, 190), width=10)
    if p.get("floating"):
        c.soft(lambda dd, cc: dd.ellipse(cc.box(0.38, 0.62, 0.56, 0.70), fill=(10, 30, 40, 220)), 0.008)
        d = c.d
    d.rectangle(c.box(0, 0.95, 1, 1), fill=(150, 160, 170))
    return _end(c, p, 0.3, 0.30)


def scene_supermarche(p):
    """Rayon de supermarché la nuit : étagères, néons qui clignotent, caddie seul."""
    c = Canvas((60, 60, 70), (30, 30, 36))
    d = c.d
    d.polygon([c.P(0.42, 0.40), c.P(0.58, 0.40), c.P(1, 1), c.P(0, 1)], fill=(150, 150, 150))
    for side in (0, 1):
        for k in range(5):
            v = 0.15 + k * 0.12
            if side == 0:
                d.polygon([c.P(0, v - 0.05), c.P(0.42, 0.33 + k * 0.025), c.P(0.42, 0.355 + k * 0.025), c.P(0, v + 0.02)], fill=(110, 110, 120))
            else:
                d.polygon([c.P(1, v - 0.05), c.P(0.58, 0.33 + k * 0.025), c.P(0.58, 0.355 + k * 0.025), c.P(1, v + 0.02)], fill=(110, 110, 120))
    rnd = random.Random(p.get("seed", 4))
    cols = [(220, 60, 60), (60, 160, 220), (240, 200, 60), (80, 200, 100), (240, 240, 240)]
    for _ in range(140):
        side = rnd.random() < 0.5
        k = rnd.randint(0, 4)
        t = rnd.uniform(0.0, 0.85)
        u = t * 0.42 if side else 1 - t * 0.42
        v0 = 0.15 + k * 0.12 - 0.05
        v = v0 + (0.33 + k * 0.025 - v0) * t - 0.03 * (1 - t)
        s = 0.03 * (1 - t) + 0.006
        d.rectangle(c.box(u - s / 2, v - s * 1.4, u + s / 2, v), fill=rnd.choice(cols))
    d.rectangle(c.box(0.42, 0.0, 0.58, 0.40), fill=(20, 20, 26))
    d.line([c.P(0.45, 0.04), c.P(0.55, 0.04)], fill=(240, 255, 255), width=10)
    if not p.get("dark"):
        c.glow(0.5, 0.04, 0.5, (220, 240, 255), 0.25)
    d = c.d
    d.rectangle(c.box(0.40, 0.70, 0.62, 0.82), outline=(200, 200, 210), width=8)
    for u in (0.42, 0.60):
        d.ellipse(c.box(u - 0.012, 0.85, u + 0.012, 0.85 + 0.024 * CW / CH), fill=(30, 30, 30))
    return _end(c, p, 0.5, 0.42)


def scene_laverie(p):
    """Laverie automatique la nuit : machines à hublot, une seule tourne."""
    c = Canvas((50, 46, 70), (24, 22, 34))
    d = c.d
    d.rectangle(c.box(0, 0.05, 1, 0.30), fill=(16, 16, 30))
    d.text(c.P(0.10, 0.10), "LAVERIE 24/24", fill=(255, 90, 160), font=font(int(c.w * 0.09)))
    c.glow(0.2, 0.13, 0.3, (255, 90, 160), 0.3)
    d = c.d
    for k in range(4):
        u = 0.02 + k * 0.245
        d.rectangle(c.box(u, 0.42, u + 0.23, 0.88), fill=(120, 118, 134), outline=(80, 78, 92), width=8)
        d.ellipse(c.box(u + 0.03, 0.55, u + 0.20, 0.55 + 0.17 * CW / CH), fill=(40, 40, 60), outline=(150, 150, 160), width=12)
        if k == p.get("spin", 2):
            d.ellipse(c.box(u + 0.05, 0.57, u + 0.18, 0.57 + 0.13 * CW / CH), fill=(60, 120, 200))
            c.glow(u + 0.115, 0.63, 0.15, (120, 180, 255), 0.35)
            d = c.d
        d.rectangle(c.box(u + 0.02, 0.45, u + 0.10, 0.48), fill=(30, 30, 40))
    d.rectangle(c.box(0, 0.88, 1, 1), fill=(60, 56, 70))
    for i in range(10):
        d.line([c.P(i * 0.1, 0.88), c.P(i * 0.1 - 0.05, 1)], fill=(40, 36, 50), width=4)
    return _end(c, p, 0.5, 0.40)


def scene_bibliotheque(p):
    """Bibliothèque ancienne : rayonnages de livres, lampe verte, échelle."""
    c = Canvas((36, 26, 30), (20, 14, 18))
    d = c.d
    rnd = random.Random(p.get("seed", 3))
    cols = [(120, 40, 40), (40, 70, 110), (60, 90, 50), (140, 110, 60), (80, 50, 90)]
    for k in range(7):
        v = 0.04 + k * 0.11
        d.rectangle(c.box(0, v + 0.09, 1, v + 0.105), fill=(80, 52, 36))
        u = 0.0
        while u < 1:
            w = rnd.uniform(0.015, 0.03)
            h = rnd.uniform(0.06, 0.088)
            if rnd.random() < 0.06:
                u += w
                continue
            d.rectangle(c.box(u, v + 0.09 - h, u + w, v + 0.09), fill=rnd.choice(cols))
            u += w + 0.002
    d.line([c.P(0.70, 0.0), c.P(0.80, 0.92)], fill=(110, 76, 50), width=14)
    d.line([c.P(0.80, 0.0), c.P(0.90, 0.92)], fill=(110, 76, 50), width=14)
    for k in range(10):
        t = k / 10
        d.line([c.P(0.70 + 0.1 * t, 0.92 * t), c.P(0.80 + 0.1 * t, 0.92 * t)], fill=(110, 76, 50), width=10)
    d.rectangle(c.box(0, 0.80, 0.6, 0.84), fill=(90, 60, 40))
    d.polygon([c.P(0.22, 0.76), c.P(0.34, 0.76), c.P(0.31, 0.72), c.P(0.25, 0.72)], fill=(40, 140, 80))
    c.glow(0.28, 0.77, 0.3, (255, 230, 150), 0.45)
    d = c.d
    d.rectangle(c.box(0, 0.92, 1, 1), fill=(26, 18, 20))
    return _end(c, p, 0.5, 0.60)


def scene_usine(p):
    """Usine désaffectée : grandes vitres cassées, poutrelles, chaînes, flaques."""
    c = Canvas((40, 40, 50), (22, 22, 28))
    d = c.d
    for k in range(4):
        u = 0.05 + k * 0.24
        d.rectangle(c.box(u, 0.08, u + 0.18, 0.45), fill=(60, 70, 110))
        for i in range(1, 4):
            d.line([c.P(u, 0.08 + i * 0.09), c.P(u + 0.18, 0.08 + i * 0.09)], fill=(20, 20, 26), width=8)
        d.line([c.P(u + 0.09, 0.08), c.P(u + 0.09, 0.45)], fill=(20, 20, 26), width=8)
        if k % 2:
            d.polygon([c.P(u + 0.02, 0.10), c.P(u + 0.08, 0.14), c.P(u + 0.03, 0.20)], fill=(16, 16, 22))
    c.glow(0.5, 0.25, 0.6, (160, 170, 255), 0.25)
    d = c.d
    d.line([c.P(0, 0.05), c.P(1, 0.05)], fill=(70, 50, 40), width=40)
    for u in (0.25, 0.65):
        d.line([c.P(u, 0.05), c.P(u, 0.55)], fill=(90, 90, 100), width=6)
        d.rectangle(c.box(u - 0.015, 0.55, u + 0.015, 0.58), fill=(90, 90, 100))
    d.rectangle(c.box(0, 0.62, 1, 1), fill=(36, 36, 40))
    for u, w in ((0.1, 0.25), (0.55, 0.3)):
        d.ellipse(c.box(u, 0.80, u + w, 0.86), fill=(70, 80, 120))
    return _end(c, p, 0.45, 0.62)


def scene_pont(p):
    """Pont de pierre la nuit au-dessus d'une rivière, lampadaires, brouillard."""
    c = Canvas((18, 20, 44), (60, 50, 90))
    _moon(c, 0.25, 0.15, 0.05)
    d = c.d
    d.rectangle(c.box(0, 0.55, 1, 1), fill=(18, 22, 46))
    d.rectangle(c.box(0, 0.40, 1, 0.47), fill=(70, 64, 80))
    for k in range(3):
        u = 0.0 + k * 0.36
        d.ellipse(c.box(u + 0.04, 0.47, u + 0.32, 0.75), fill=(18, 22, 46))
        d.rectangle(c.box(u + 0.32, 0.47, u + 0.40, 0.72), fill=(70, 64, 80))
    for u in (0.15, 0.5, 0.85):
        d.line([c.P(u, 0.40), c.P(u, 0.22)], fill=(20, 18, 30), width=10)
        d.ellipse(c.box(u - 0.015, 0.20, u + 0.015, 0.23), fill=(255, 210, 130))
        c.glow(u, 0.22, 0.15, (255, 200, 120), 0.45)
        d = c.d
    for k in range(6):
        d.line([c.P(0, 0.80 + k * 0.03), c.P(1, 0.80 + k * 0.03)], fill=(50, 60, 110), width=4)
    c.soft(lambda dd, cc: dd.rectangle(cc.box(-0.1, 0.62, 1.1, 0.80), fill=(170, 160, 220, 110)), 0.05)
    return _end(c, p, 0.5, 0.25)


def scene_champ(p):
    """Champ de maïs la nuit : tiges hautes, épouvantail, ciel orageux."""
    c = Canvas((22, 20, 40), (70, 56, 80))
    _moon(c, 0.8, 0.15, 0.05)
    d = c.d
    if p.get("scarecrow", True):
        d.line([c.P(0.5, 0.25), c.P(0.5, 0.70)], fill=(60, 40, 30), width=14)
        d.line([c.P(0.38, 0.33), c.P(0.62, 0.33)], fill=(60, 40, 30), width=14)
        d.polygon([c.P(0.42, 0.33), c.P(0.58, 0.33), c.P(0.56, 0.52), c.P(0.44, 0.52)], fill=(90, 60, 50))
        d.ellipse(c.box(0.46, 0.20, 0.54, 0.20 + 0.08 * CW / CH), fill=(200, 170, 110))
        d.polygon([c.P(0.43, 0.22), c.P(0.57, 0.22), c.P(0.5, 0.15)], fill=(40, 30, 30))
    rnd = random.Random(p.get("seed", 8))
    for layer, (v0, col, n, h) in enumerate(((0.55, (60, 70, 40), 60, 0.15), (0.70, (44, 52, 30), 40, 0.25), (0.88, (26, 30, 20), 22, 0.4))):
        for _ in range(n):
            u = rnd.uniform(-0.05, 1.05)
            top = v0 - h * rnd.uniform(0.7, 1.0)
            d.line([c.P(u, 1.02), c.P(u + rnd.uniform(-0.02, 0.02), top)], fill=col, width=6 + 6 * layer)
            for _ in range(2):
                vv = rnd.uniform(top, v0)
                sd = rnd.choice((-1, 1))
                d.polygon([c.P(u, vv), c.P(u + sd * 0.06 * (1 + layer), vv + 0.04), c.P(u, vv + 0.01)], fill=col)
    return _end(c, p, 0.3, 0.55)


def scene_tunnel(p):
    """Tunnel routier : lampes orange en enfilade, voie qui s'enfonce."""
    c = Canvas((30, 24, 20), (16, 12, 10))
    d = c.d
    d.ellipse(c.box(-0.2, -0.05, 1.2, 0.95), fill=(50, 40, 30))
    for k in range(7):
        t = 1 - k / 7
        w = 0.7 * t + 0.05
        cy = 0.48
        for sd in (-1, 1):
            u = 0.5 + sd * w * 0.75
            vv = cy - w * 0.45
            d.rectangle(c.box(u - 0.01 * t, vv, u + 0.01 * t, vv + 0.006 * t + 0.003), fill=(255, 170, 70))
            c.glow(u, vv, 0.06 * t + 0.01, (255, 160, 60), 0.4)
            d = c.d
    d.ellipse(c.box(0.47, 0.45, 0.53, 0.51), fill=(4, 4, 6))
    d.polygon([c.P(0.48, 0.50), c.P(0.52, 0.50), c.P(0.95, 1), c.P(0.05, 1)], fill=(40, 38, 40))
    for k in range(5):
        v = 0.55 + k * 0.09
        d.rectangle(c.box(0.497 - k * 0.003, v, 0.503 + k * 0.003, v + 0.02 + k * 0.01), fill=(230, 220, 180))
    return _end(c, p, 0.5, 0.40)


def scene_cabane(p):
    """Cabane dans les bois : intérieur en rondins, poêle rougeoyant, fenêtre noire."""
    c = Canvas((60, 38, 28), (32, 20, 16))
    d = c.d
    for k in range(18):
        v = k * 0.055
        d.rounded_rectangle(c.box(-0.02, v, 1.02, v + 0.05), radius=20, fill=(90 + (k % 2) * 10, 58, 38))
    d.rectangle(c.box(0.10, 0.20, 0.40, 0.45), fill=(10, 12, 26), outline=(50, 30, 20), width=20)
    d.line([c.P(0.25, 0.20), c.P(0.25, 0.45)], fill=(50, 30, 20), width=12)
    d.line([c.P(0.10, 0.325), c.P(0.40, 0.325)], fill=(50, 30, 20), width=12)
    if p.get("face"):
        d.ellipse(c.box(0.29, 0.25, 0.37, 0.25 + 0.08 * CW / CH), fill=(200, 200, 210))
        for u in (0.315, 0.345):
            d.ellipse(c.box(u - 0.006, 0.28, u + 0.006, 0.29), fill=(10, 10, 10))
    d.rectangle(c.box(0.62, 0.55, 0.86, 0.88), fill=(30, 26, 26))
    d.rectangle(c.box(0.66, 0.65, 0.82, 0.80), fill=(255, 120, 40))
    d.rectangle(c.box(0.72, 0.0, 0.76, 0.55), fill=(30, 26, 26))
    c.glow(0.74, 0.72, 0.5, (255, 120, 40), 0.45)
    d = c.d
    d.rectangle(c.box(0, 0.88, 1, 1), fill=(50, 32, 22))
    return _end(c, p, 0.45, 0.70)


def scene_foraine(p):
    """Fête foraine abandonnée : grande roue, ampoules, chapiteau rayé."""
    c = Canvas((16, 14, 40), (70, 40, 90))
    _stars(c, p.get("seed", 5), 0.3)
    d = c.d
    cx, cy, r = 0.30, 0.35, 0.25
    for k in range(12):
        a = k * math.pi / 6
        d.line([c.P(cx, cy), c.P(cx + r * math.cos(a), cy + r * math.sin(a) * CW / CH)], fill=(150, 140, 170), width=6)
        bu, bv = cx + r * math.cos(a), cy + r * math.sin(a) * CW / CH
        d.rectangle(c.box(bu - 0.02, bv, bu + 0.02, bv + 0.03), fill=(200, 60, 70))
    d.ellipse(c.box(cx - r, cy - r * CW / CH, cx + r, cy + r * CW / CH), outline=(180, 170, 200), width=10)
    d.line([c.P(cx, cy), c.P(cx - 0.12, 0.85)], fill=(120, 110, 140), width=12)
    d.line([c.P(cx, cy), c.P(cx + 0.12, 0.85)], fill=(120, 110, 140), width=12)
    for i in range(8):
        u0 = 0.55 + i * 0.05
        col = (200, 40, 50) if i % 2 else (240, 230, 220)
        d.polygon([c.P(0.75, 0.45), c.P(u0, 0.70), c.P(u0 + 0.05, 0.70)], fill=col)
        d.rectangle(c.box(u0, 0.70, u0 + 0.05, 0.88), fill=col)
    rnd = random.Random(3)
    for k in range(14):
        u = 0.02 + k * 0.07
        on = rnd.random() < 0.6 and not p.get("dark")
        d.ellipse(c.box(u - 0.008, 0.90, u + 0.008, 0.91), fill=(255, 220, 120) if on else (60, 50, 40))
        if on:
            c.glow(u, 0.905, 0.04, (255, 210, 110), 0.4)
            d = c.d
    d.rectangle(c.box(0, 0.92, 1, 1), fill=(20, 16, 24))
    return _end(c, p, 0.5, 0.72)


def scene_toit(p):
    """Toit d'immeuble la nuit : antennes, cheminées, ville en contrebas."""
    c = Canvas((14, 14, 38), (70, 50, 100))
    _stars(c, p.get("seed", 6), 0.3)
    _moon(c, 0.2, 0.18, 0.05)
    ruined_skyline(c, 0.60, (40, 30, 66), 4, 1.3, 0.25, fire=False)
    d = c.d
    d.rectangle(c.box(0, 0.62, 1, 1), fill=(46, 42, 54))
    d.rectangle(c.box(0, 0.60, 1, 0.63), fill=(80, 76, 90))
    for u in (0.12, 0.70):
        d.rectangle(c.box(u, 0.48, u + 0.08, 0.66), fill=(70, 50, 50))
    d.line([c.P(0.85, 0.66), c.P(0.85, 0.30)], fill=(30, 28, 40), width=10)
    for v in (0.34, 0.40, 0.46):
        d.line([c.P(0.80, v), c.P(0.90, v)], fill=(30, 28, 40), width=6)
    d.ellipse(c.box(0.845, 0.29, 0.855, 0.30), fill=(255, 60, 50))
    c.glow(0.85, 0.295, 0.04, (255, 60, 50), 0.5)
    d = c.d
    d.rectangle(c.box(0.30, 0.55, 0.50, 0.66), fill=(36, 32, 44))
    d.rectangle(c.box(0.36, 0.58, 0.44, 0.66), fill=(255, 200, 120))
    return _end(c, p, 0.6, 0.55)


def scene_aire(p):
    """Aire de jeux la nuit : balançoire, toboggan, lampadaire, brouillard."""
    c = Canvas((18, 18, 42), (60, 50, 86))
    _moon(c, 0.75, 0.15, 0.05)
    d = c.d
    d.rectangle(c.box(0, 0.70, 1, 1), fill=(30, 36, 34))
    d.line([c.P(0.10, 0.72), c.P(0.20, 0.35)], fill=(180, 60, 60), width=12)
    d.line([c.P(0.50, 0.72), c.P(0.40, 0.35)], fill=(180, 60, 60), width=12)
    d.line([c.P(0.18, 0.35), c.P(0.42, 0.35)], fill=(180, 60, 60), width=12)
    for u, sway in ((0.24, 0.0), (0.36, 0.04)):
        d.line([c.P(u, 0.35), c.P(u + sway, 0.60)], fill=(150, 150, 160), width=4)
        d.line([c.P(u + 0.04, 0.35), c.P(u + 0.04 + sway, 0.60)], fill=(150, 150, 160), width=4)
        d.rectangle(c.box(u - 0.005 + sway, 0.60, u + 0.045 + sway, 0.615), fill=(60, 50, 40))
    d.polygon([c.P(0.62, 0.72), c.P(0.68, 0.45), c.P(0.72, 0.45), c.P(0.72, 0.72)], fill=(60, 110, 180))
    d.polygon([c.P(0.72, 0.45), c.P(0.76, 0.45), c.P(0.95, 0.72), c.P(0.88, 0.72)], fill=(240, 200, 60))
    d.line([c.P(0.06, 0.72), c.P(0.06, 0.25)], fill=(30, 30, 40), width=10)
    d.ellipse(c.box(0.045, 0.23, 0.075, 0.26), fill=(255, 210, 130))
    if not p.get("dark"):
        c.glow(0.06, 0.25, 0.4, (255, 200, 120), 0.35)
    c.soft(lambda dd, cc: dd.rectangle(cc.box(-0.1, 0.68, 1.1, 0.85), fill=(170, 160, 220, 100)), 0.05)
    return _end(c, p, 0.55, 0.65)


# ---- Décors de la série « Jacques a dit » (village breton près de Saint-Malo) ----
def _jad_sky(c, p, seed):
    """Ciel de nuit, ou d'aube si "aube": true (épisode 6)."""
    if p.get("aube"):
        c.img = R.gradient(c.w, c.h, (60, 50, 110), (255, 150, 110))
        c.d = ImageDraw.Draw(c.img)
        c.glow(0.5, 0.55, 0.8, (255, 180, 120), 0.4)
    else:
        _stars(c, seed, 0.35)
        _moon(c, 0.78, 0.12, 0.045)


def _granite_house(c, u0, u1, base, top, seed, lit=0.4):
    """Maison bretonne : granit gris, toit d'ardoise, volets bleus, cheminée."""
    d = c.d
    rnd = random.Random(seed)
    d.rectangle(c.box(u0, top, u1, base), fill=(78, 76, 92))
    for _ in range(int((u1 - u0) * 120)):
        x, y = rnd.uniform(u0, u1), rnd.uniform(top, base)
        w = rnd.uniform(0.012, 0.03)
        g = rnd.randint(64, 96)
        d.rectangle(c.box(x, y, min(u1, x + w), min(base, y + 0.008)), fill=(g, g - 2, g + 12))
    rh = (u1 - u0) * 0.45
    d.polygon([c.P(u0 - 0.01, top), c.P(u1 + 0.01, top), c.P(u1 - (u1 - u0) * 0.2, top - rh), c.P(u0 + (u1 - u0) * 0.2, top - rh)], fill=(34, 36, 54))
    d.rectangle(c.box(u1 - (u1 - u0) * 0.3, top - rh - 0.04, u1 - (u1 - u0) * 0.18, top - rh * 0.5), fill=(70, 66, 80))
    n = max(1, int((u1 - u0) / 0.12))
    for i in range(n):
        wu = u0 + (i + 0.5) * (u1 - u0) / n
        wv = top + (base - top) * 0.25
        on = rnd.random() < lit
        d.rectangle(c.box(wu - 0.025, wv, wu + 0.025, wv + 0.05), fill=(255, 200, 120) if on else (20, 18, 34))
        d.rectangle(c.box(wu - 0.045, wv, wu - 0.027, wv + 0.05), fill=(50, 80, 150))
        d.rectangle(c.box(wu + 0.027, wv, wu + 0.045, wv + 0.05), fill=(50, 80, 150))
        if on:
            c.glow(wu, wv + 0.025, 0.06, (255, 190, 110), 0.35)
            d = c.d


def _horn(c, u, v, s=1.0, side=1):
    """Haut-parleur en pavillon (celui qui crie les ordres)."""
    d = c.d
    d.polygon([c.P(u, v - 0.012 * s), c.P(u + side * 0.07 * s, v - 0.035 * s), c.P(u + side * 0.07 * s, v + 0.035 * s), c.P(u, v + 0.012 * s)], fill=(150, 150, 160))
    d.ellipse(c.box(u + side * 0.07 * s - 0.008 * s, v - 0.035 * s, u + side * 0.07 * s + 0.008 * s, v + 0.035 * s), fill=(40, 40, 50))


def _jacques(c, u, v, s=1.0):
    """« Jacques » : silhouette sans visage, costume noir, très grande."""
    d = c.d
    r = 0.028 * s
    d.ellipse(c.box(u - r, v - 0.30 * s, u + r, v - 0.30 * s + 2.4 * r * CW / CH), fill=(220, 215, 225))
    d.polygon([c.P(u - 0.06 * s, v), c.P(u - 0.055 * s, v - 0.22 * s), c.P(u - 0.035 * s, v - 0.245 * s), c.P(u + 0.035 * s, v - 0.245 * s), c.P(u + 0.055 * s, v - 0.22 * s), c.P(u + 0.06 * s, v)], fill=(6, 6, 10))
    d.polygon([c.P(u - 0.012 * s, v - 0.245 * s), c.P(u + 0.012 * s, v - 0.245 * s), c.P(u, v - 0.20 * s)], fill=(230, 230, 235))
    d.line([c.P(u - 0.055 * s, v - 0.21 * s), c.P(u - 0.075 * s, v - 0.06 * s)], fill=(6, 6, 10), width=int(26 * s))
    d.line([c.P(u + 0.055 * s, v - 0.21 * s), c.P(u + 0.075 * s, v - 0.06 * s)], fill=(6, 6, 10), width=int(26 * s))


def scene_jad_place(p):
    """Place du village la nuit : maisons de granit, église et haut-parleurs, lampadaire, pavés."""
    c = Canvas((14, 14, 40), (64, 50, 96))
    _jad_sky(c, p, 21)
    d = c.d
    d.rectangle(c.box(0.40, 0.10, 0.60, 0.52), fill=(60, 58, 76))
    d.polygon([c.P(0.40, 0.10), c.P(0.50, -0.06), c.P(0.60, 0.10)], fill=(30, 32, 50))
    d.ellipse(c.box(0.46, 0.15, 0.54, 0.15 + 0.08 * CW / CH), fill=(230, 220, 190))
    d.line([c.P(0.50, 0.19), c.P(0.50, 0.16)], fill=(20, 20, 20), width=6)
    d.line([c.P(0.50, 0.19), c.P(0.505, 0.162)], fill=(20, 20, 20), width=6)
    _horn(c, 0.40, 0.30, 1.0, -1)
    _horn(c, 0.60, 0.30, 1.0, 1)
    d = c.d
    d.rectangle(c.box(0.47, 0.40, 0.53, 0.52), fill=(30, 20, 20))
    _granite_house(c, -0.02, 0.36, 0.62, 0.36, 1)
    _granite_house(c, 0.64, 1.02, 0.62, 0.34, 2)
    d = c.d
    d.rectangle(c.box(0, 0.62, 1, 1), fill=(46, 44, 58))
    rnd = random.Random(5)
    for k in range(9):
        v = 0.64 + k * 0.04
        for _ in range(14 + k * 2):
            u = rnd.uniform(0, 1)
            w = 0.02 + k * 0.005
            g = rnd.randint(52, 70)
            d.rounded_rectangle(c.box(u, v, u + w, v + 0.015 + k * 0.003), radius=6, fill=(g, g, g + 12))
    d.line([c.P(0.80, 0.90), c.P(0.80, 0.50)], fill=(20, 20, 28), width=12)
    d.polygon([c.P(0.78, 0.50), c.P(0.82, 0.50), c.P(0.83, 0.47), c.P(0.77, 0.47)], fill=(255, 210, 130))
    if not p.get("dark"):
        c.glow(0.80, 0.49, 0.45, (255, 200, 120), 0.4)
    if p.get("jacques"):
        _jacques(c, *p.get("jacques_at", (0.30, 0.86)), s=p.get("jacques_size", 1.0))
    return _end(c, p, 0.5, 0.72)


def scene_jad_clocher(p):
    """Gros plan du clocher à minuit : horloge, pavillons des haut-parleurs, fils, lune."""
    c = Canvas((12, 12, 36), (50, 40, 84))
    _jad_sky(c, p, 22)
    d = c.d
    d.rectangle(c.box(0.22, 0.20, 0.78, 1.02), fill=(64, 62, 80))
    rnd = random.Random(9)
    for _ in range(160):
        x, y = rnd.uniform(0.22, 0.76), rnd.uniform(0.2, 1)
        g = rnd.randint(54, 84)
        d.rectangle(c.box(x, y, x + 0.04, y + 0.012), fill=(g, g - 2, g + 12))
    d.polygon([c.P(0.18, 0.20), c.P(0.50, -0.25), c.P(0.82, 0.20)], fill=(28, 30, 48))
    cx, cy, r = 0.50, 0.42, 0.17
    d.ellipse(c.box(cx - r, cy - r * CW / CH, cx + r, cy + r * CW / CH), fill=(230, 222, 196), outline=(40, 34, 30), width=16)
    for k in range(12):
        a = k * math.pi / 6
        d.line([c.P(cx + 0.85 * r * math.cos(a), cy + 0.85 * r * math.sin(a) * CW / CH), c.P(cx + 0.95 * r * math.cos(a), cy + 0.95 * r * math.sin(a) * CW / CH)], fill=(40, 34, 30), width=8)
    h = p.get("hour", 0)
    for ang, ln, wd in ((h % 12 * math.pi / 6, 0.55, 14), (0, 0.8, 9)):
        d.line([c.P(cx, cy), c.P(cx + ln * r * math.sin(ang), cy - ln * r * math.cos(ang) * CW / CH)], fill=(20, 16, 14), width=wd)
    if not p.get("aube"):
        c.glow(cx, cy, 0.35, (255, 220, 160), 0.3)
    for u, v, sd in ((0.22, 0.70, -1), (0.78, 0.70, 1), (0.22, 0.85, -1), (0.78, 0.85, 1)):
        _horn(c, u, v, 1.8, sd)
    d = c.d
    d.line([c.P(0.0, 0.62), c.P(0.22, 0.70)], fill=(10, 10, 16), width=6)
    d.line([c.P(1.0, 0.60), c.P(0.78, 0.70)], fill=(10, 10, 16), width=6)
    if p.get("red"):
        c.glow(0.5, 0.78, 0.5, (255, 60, 50), 0.35)
    return c.done()


def scene_jad_mamie(p):
    """Salle de la grand-mère : armoire bretonne, assiettes de faïence, horloge comtoise, téléphone à fil."""
    c = Canvas((56, 40, 44), (30, 22, 26))
    d = c.d
    for k in range(10):
        d.line([c.P(0, 0.08 + k * 0.09), c.P(1, 0.08 + k * 0.09)], fill=(64, 46, 50), width=4)
    d.rectangle(c.box(0, 0, 1, 0.05), fill=(40, 26, 22))
    for u in (0.2, 0.5, 0.8):
        d.rectangle(c.box(u - 0.02, 0, u + 0.02, 0.06), fill=(70, 46, 34))
    d.rectangle(c.box(0.04, 0.22, 0.42, 0.90), fill=(110, 64, 40), outline=(60, 34, 22), width=12)
    for u in (0.06, 0.24):
        d.rectangle(c.box(u, 0.26, u + 0.16, 0.86), outline=(70, 40, 26), width=8)
        d.ellipse(c.box(u + 0.03, 0.40, u + 0.13, 0.40 + 0.10 * CW / CH), outline=(150, 100, 60), width=6)
    rnd = random.Random(3)
    for k in range(5):
        u = 0.50 + k * 0.09
        d.ellipse(c.box(u, 0.22, u + 0.07, 0.22 + 0.07 * CW / CH), fill=(235, 232, 220), outline=(60, 90, 170), width=6)
        d.ellipse(c.box(u + 0.025, 0.235, u + 0.045, 0.235 + 0.025 * CW / CH), fill=rnd.choice([(60, 90, 170), (200, 60, 50), (240, 190, 60)]))
    d.rectangle(c.box(0.48, 0.30, 0.96, 0.31), fill=(80, 50, 34))
    d.rectangle(c.box(0.80, 0.40, 0.92, 0.95), fill=(90, 54, 36))
    d.ellipse(c.box(0.81, 0.43, 0.91, 0.43 + 0.10 * CW / CH), fill=(230, 220, 190))
    d.ellipse(c.box(0.845, 0.60, 0.875, 0.60 + 0.03 * CW / CH), fill=(200, 160, 60))
    d.line([c.P(0.86, 0.50), c.P(0.86, 0.60)], fill=(200, 160, 60), width=4)
    d.rectangle(c.box(0.48, 0.62, 0.76, 0.66), fill=(100, 70, 50))
    d.rectangle(c.box(0.50, 0.66, 0.52, 0.92), fill=(70, 46, 32))
    d.rectangle(c.box(0.72, 0.66, 0.74, 0.92), fill=(70, 46, 32))
    d.rounded_rectangle(c.box(0.56, 0.57, 0.68, 0.62), radius=10, fill=(150, 30, 30))
    d.ellipse(c.box(0.59, 0.575, 0.65, 0.61), fill=(40, 10, 10))
    if p.get("ring"):
        c.glow(0.62, 0.58, 0.15, (255, 80, 60), 0.5)
        d = c.d
    d.polygon([c.P(0.56, 0.52), c.P(0.64, 0.52), c.P(0.62, 0.47), c.P(0.58, 0.47)], fill=(240, 210, 150))
    if not p.get("dark"):
        c.glow(0.60, 0.52, 0.5, (255, 190, 110), 0.4)
    d = c.d
    d.rectangle(c.box(0, 0.92, 1, 1), fill=(44, 30, 26))
    if p.get("mamie"):
        _fig(c, 0.30, 0.95, 0.9, col=(20, 14, 20), eyes=p.get("eyes", False))
    return _end(c, p, 0.3, 0.75)


def scene_jad_ruelle(p):
    """Ruelle étroite en granit : toits d'ardoise, une fenêtre allumée, téléphone qui brille par terre."""
    c = Canvas((14, 14, 40), (54, 44, 84))
    _jad_sky(c, p, 23)
    _granite_house(c, -0.05, 0.38, 1.05, 0.30, 7, 0.3)
    _granite_house(c, 0.62, 1.05, 1.05, 0.26, 8, 0.3)
    d = c.d
    d.polygon([c.P(0.38, 1.0), c.P(0.46, 0.55), c.P(0.54, 0.55), c.P(0.62, 1.0)], fill=(50, 48, 62))
    rnd = random.Random(4)
    for k in range(10):
        v = 0.58 + k * 0.045
        for _ in range(3 + k):
            u = rnd.uniform(0.46 - k * 0.008, 0.54 + k * 0.008)
            d.ellipse(c.box(u, v, u + 0.01 + k * 0.003, v + 0.008 + k * 0.002), fill=(62, 60, 76))
    d.rectangle(c.box(0.46, 0.40, 0.54, 0.55), fill=(20, 18, 32))
    if p.get("phone", True):
        d.rounded_rectangle(c.box(0.52, 0.86, 0.58, 0.89), radius=6, fill=(170, 220, 255))
        c.glow(0.55, 0.875, 0.12, (150, 210, 255), 0.5)
    if p.get("jacques"):
        _jacques(c, 0.50, 0.58, 0.5)
    return _end(c, p, 0.5, 0.75)


def scene_jad_remparts(p):
    """Remparts de Saint-Malo au-dessus de la plage : murs de granit, mer, fort au loin."""
    c = Canvas((12, 14, 40), (60, 48, 96))
    _jad_sky(c, p, 24)
    d = c.d
    d.rectangle(c.box(0, 0.42, 1, 0.62), fill=(22, 30, 64) if not p.get("aube") else (120, 100, 140))
    for k in range(5):
        d.line([c.P(0, 0.45 + k * 0.035), c.P(1, 0.45 + k * 0.035)], fill=(60, 70, 120), width=4)
    d.polygon([c.P(0.68, 0.43), c.P(0.70, 0.38), c.P(0.80, 0.37), c.P(0.86, 0.43)], fill=(20, 20, 36))
    d.rectangle(c.box(0.74, 0.33, 0.77, 0.38), fill=(20, 20, 36))
    d.polygon([c.P(0, 0.62), c.P(1, 0.62), c.P(1, 0.70), c.P(0, 0.72)], fill=(150, 132, 120))
    d.polygon([c.P(0, 0.72), c.P(1, 0.70), c.P(1, 1), c.P(0, 1)], fill=(70, 68, 84))
    rnd = random.Random(11)
    for row in range(8):
        v = 0.74 + row * 0.035
        u = -0.02 + (row % 2) * 0.03
        while u < 1:
            g = rnd.randint(60, 90)
            d.rectangle(c.box(u, v, u + 0.06, v + 0.03), fill=(g, g - 4, g + 10))
            u += 0.064
    for k in range(6):
        u = 0.02 + k * 0.17
        d.rectangle(c.box(u, 0.68, u + 0.09, 0.74), fill=(84, 82, 98))
    if p.get("jacques"):
        _jacques(c, 0.25, 0.70, 0.6)
    return _end(c, p, 0.5, 0.55)


def scene_jad_jacques(p):
    """« Jacques » sous un lampadaire, dans la brume : la silhouette sans visage."""
    c = Canvas((10, 10, 26), (40, 34, 64))
    d = c.d
    _granite_house(c, -0.05, 0.30, 0.80, 0.30, 12, 0.2)
    _granite_house(c, 0.70, 1.05, 0.80, 0.32, 13, 0.2)
    d = c.d
    d.rectangle(c.box(0, 0.80, 1, 1), fill=(30, 28, 40))
    d.line([c.P(0.62, 0.92), c.P(0.62, 0.20)], fill=(18, 18, 26), width=14)
    d.line([c.P(0.62, 0.20), c.P(0.52, 0.20)], fill=(18, 18, 26), width=10)
    d.polygon([c.P(0.49, 0.20), c.P(0.55, 0.20), c.P(0.56, 0.24), c.P(0.48, 0.24)], fill=(255, 220, 150))
    c.soft(lambda dd, cc: dd.polygon([cc.P(0.49, 0.24), cc.P(0.55, 0.24), cc.P(0.70, 0.92), cc.P(0.34, 0.92)], fill=(255, 220, 160, 70)), 0.02)
    c.glow(0.52, 0.23, 0.2, (255, 220, 150), 0.6)
    _jacques(c, 0.52, 0.90, p.get("size", 1.5))
    c.soft(lambda dd, cc: dd.rectangle(cc.box(-0.1, 0.80, 1.1, 0.98), fill=(170, 160, 210, 110)), 0.05)
    if p.get("red"):
        c.glow(0.5, 0.5, 0.6, (255, 60, 50), 0.25)
    return c.done()


# ---- Plans « objet » en gros plan (07/11, idée de Fio : téléphone, télé…) ----
def _room_blur(seed=1, col=((44, 40, 60), (22, 20, 32))):
    """Pièce sombre très floue derrière un objet en gros plan."""
    c = Canvas(*col)
    d = c.d
    d.rectangle(c.box(0.0, 0.25, 0.25, 0.55), fill=(60, 58, 80))
    for k in range(8):
        d.line([c.P(0.0, 0.27 + k * 0.035), c.P(0.25, 0.27 + k * 0.035)], fill=(40, 38, 56), width=8)
    d.rectangle(c.box(0.55, 0.30, 0.95, 0.52), fill=(14, 14, 22))
    d.rectangle(c.box(0, 0.70, 1, 1), fill=(26, 24, 36))
    img = c.done().filter(ImageFilter.GaussianBlur(30))
    return img


def _hand(c, u, v, side=-1, s=1.0, col=(14, 12, 20), line=(200, 200, 215)):
    """Main stylisée qui tient l'objet : 4 doigts arrondis sur le bord + pouce."""
    d = c.d
    for k in range(4):
        vv = v + k * 0.05 * s
        d.rounded_rectangle(c.box(u - 0.07 * s if side < 0 else u - 0.01 * s, vv, u + 0.01 * s if side < 0 else u + 0.07 * s, vv + 0.03 * s), radius=int(30 * s), fill=col, outline=line, width=5)


def scene_telephone(p):
    """Téléphone tenu en main, en gros plan.
    "mode": "lock" (écran verrouillé : "time", "date", "notif" [titre, texte])
           "chat" ("contact", "messages" : [["moi" | "lui", "texte"], ...])
           "call" ("contact" : appel entrant).  "crack": écran fêlé."""
    c = Canvas((0, 0, 0), (0, 0, 0))
    c.img = _room_blur(p.get("seed", 1)).resize((c.w, c.h), Image.LANCZOS)
    c.d = ImageDraw.Draw(c.img)
    d = c.d
    x0, y0, x1, y1 = 0.17, 0.14, 0.83, 0.86
    c.glow(0.5, 0.45, 0.7, (120, 100, 220), 0.35)
    d = c.d
    d.rounded_rectangle(c.box(x0, y0, x1, y1), radius=int(c.w * 0.07), fill=(30, 30, 40), outline=(150, 150, 170), width=10)
    sx0, sy0, sx1, sy1 = x0 + 0.02, y0 + 0.012, x1 - 0.02, y1 - 0.012
    mode = p.get("mode", "lock")
    scr = R.gradient(int((sx1 - sx0) * c.w), int((sy1 - sy0) * c.h), (70, 56, 150) if mode != "chat" else (24, 24, 32), (26, 20, 60) if mode != "chat" else (18, 18, 24))
    mask = Image.new("L", scr.size, 0)
    ImageDraw.Draw(mask).rounded_rectangle([0, 0, scr.size[0], scr.size[1]], radius=int(c.w * 0.055), fill=255)
    c.img.paste(scr, (int(sx0 * c.w), int(sy0 * c.h)), mask)
    d = c.d = ImageDraw.Draw(c.img)
    d.rounded_rectangle(c.box(0.42, sy0 + 0.012, 0.58, sy0 + 0.032), radius=40, fill=(6, 6, 10))
    W_ = c.w

    def ctext(txt, v, size, col=(255, 255, 255)):
        f = font(int(W_ * size))
        tw = d.textlength(txt, font=f)
        d.text(((0.5 * W_) - tw / 2, v * c.h), txt, fill=col, font=f)

    if mode == "lock":
        ctext(p.get("date", "samedi 7 novembre"), 0.20, 0.035, (230, 230, 245))
        ctext(p.get("time", "0:00"), 0.225, 0.16)
        if p.get("notif"):
            t, body = p["notif"]
            d.rounded_rectangle(c.box(0.22, 0.42, 0.78, 0.50), radius=40, fill=(120, 110, 160))
            d.ellipse(c.box(0.24, 0.435, 0.29, 0.435 + 0.05 * CW / CH), fill=(200, 200, 215))
            d.text(c.P(0.31, 0.432), str(t), fill=(235, 235, 245), font=font(int(W_ * 0.028)))
            d.text(c.P(0.31, 0.457), str(body), fill=(255, 255, 255), font=font(int(W_ * 0.036)))
    elif mode == "call":
        ctext("appel entrant…", 0.24, 0.035, (220, 220, 235))
        ctext(str(p.get("contact", "Inconnu")), 0.28, 0.08)
        for u, col in ((0.32, (220, 60, 60)), (0.68, (60, 200, 100))):
            d.ellipse(c.box(u - 0.06, 0.70, u + 0.06, 0.70 + 0.12 * CW / CH), fill=col)
        c.glow(0.5, 0.35, 0.5, (150, 140, 255), 0.25)
        d = c.d
    else:
        d.rectangle(c.box(sx0, sy0 + 0.05, sx1, sy0 + 0.10), fill=(34, 34, 44))
        d.ellipse(c.box(0.25, sy0 + 0.058, 0.30, sy0 + 0.058 + 0.05 * CW / CH), fill=(170, 170, 190))
        d.text(c.P(0.32, sy0 + 0.06), str(p.get("contact", "Mamie")), fill=(255, 255, 255), font=font(int(W_ * 0.04)))
        v = sy0 + 0.13
        for who, txt in p.get("messages", [["lui", "tu dors ?"]]):
            f = font(int(W_ * 0.038))
            tw = min(d.textlength(txt, font=f), W_ * 0.48)
            mine = who == "moi"
            ux = (sx1 - 0.03) * W_ - tw - W_ * 0.04 if mine else (sx0 + 0.03) * W_
            d.rounded_rectangle([ux, v * c.h, ux + tw + W_ * 0.04, (v + 0.055) * c.h], radius=int(W_ * 0.03),
                                fill=(70, 110, 230) if mine else (58, 58, 72))
            d.text((ux + W_ * 0.02, (v + 0.01) * c.h), txt, fill=(255, 255, 255), font=f)
            v += 0.075
        d.rounded_rectangle(c.box(sx0 + 0.03, sy1 - 0.07, sx1 - 0.03, sy1 - 0.03), radius=40, outline=(80, 80, 96), width=5)
    if p.get("crack"):
        rnd = random.Random(5)
        for _ in range(9):
            a = rnd.uniform(0, 2 * math.pi)
            ln = rnd.uniform(0.1, 0.35)
            d.line([c.P(0.62, 0.62), c.P(0.62 + ln * math.cos(a), 0.62 + ln * math.sin(a) * CW / CH)], fill=(230, 230, 240), width=4)
    d.rounded_rectangle(c.box(0.40, y1 - 0.03, 0.60, y1 - 0.024), radius=10, fill=(200, 200, 210))
    _hand(c, x0 + 0.01, 0.58, -1)
    d = c.d
    d.ellipse(c.box(0.72, 0.80, 0.86, 0.80 + 0.14 * CW / CH), fill=(14, 12, 20), outline=(200, 200, 215), width=5)
    d.polygon([c.P(0.72, 0.90), c.P(0.86, 0.90), c.P(0.95, 1.02), c.P(0.70, 1.02)], fill=tuple(p.get("sleeve", (220, 160, 40))))
    if p.get("red") or p.get("green"):
        c.glow(0.5, 0.5, 0.6, _lightcol(p, FIRE), 0.25)
    return c.done()


def scene_tele(p):
    """Télé en gros plan : neige qui grésille ; "face": un visage qui sourit dans la neige ;
    "text": un mot sur l'écran ; "off": écran noir avec un reflet."""
    c = Canvas((0, 0, 0), (0, 0, 0))
    c.img = _room_blur(p.get("seed", 2)).resize((c.w, c.h), Image.LANCZOS)
    c.d = ImageDraw.Draw(c.img)
    d = c.d
    x0, y0, x1, y1 = 0.04, 0.24, 0.96, 0.66
    d.rounded_rectangle(c.box(x0 - 0.02, y0 - 0.02, x1 + 0.02, y1 + 0.02), radius=20, fill=(12, 12, 16))
    sw, sh = int((x1 - x0) * c.w), int((y1 - y0) * c.h)
    if p.get("off"):
        scr = R.gradient(sw, sh, (18, 18, 26), (8, 8, 12))
    else:
        rnd = np.random.default_rng(p.get("seed", 2))
        small = rnd.integers(60, 175, (sh // 6, sw // 6), dtype=np.uint8)
        scr = Image.fromarray(small).resize((sw, sh), Image.NEAREST).convert("RGB")
        lines = ImageDraw.Draw(scr)
        for y in range(0, sh, 18):
            lines.line([(0, y), (sw, y)], fill=(90, 90, 100), width=4)
        if p.get("face"):
            fl = Image.new("L", (sw, sh), 0)
            fd = ImageDraw.Draw(fl)
            for ex in (0.38, 0.62):
                fd.ellipse([sw * ex - sw * 0.07, sh * 0.25, sw * ex + sw * 0.07, sh * 0.25 + sw * 0.14], outline=255, width=int(sw * 0.03))
                fd.ellipse([sw * ex - sw * 0.02, sh * 0.32, sw * ex + sw * 0.02, sh * 0.32 + sw * 0.04], fill=255)
            fd.arc([sw * 0.28, sh * 0.30, sw * 0.72, sh * 0.85], 20, 160, fill=255, width=int(sw * 0.03))
            fl = fl.filter(ImageFilter.GaussianBlur(sw * 0.012))
            scr = Image.composite(Image.new("RGB", (sw, sh), (25, 25, 32)), scr, fl.point(lambda x: int(x * 0.7)))
        scr = scr.filter(ImageFilter.GaussianBlur(1.5))
    if p.get("text"):
        dd = ImageDraw.Draw(scr)
        f = font(int(sw * 0.12))
        tw = dd.textlength(str(p["text"]), font=f)
        dd.text(((sw - tw) / 2, sh * 0.38), str(p["text"]), fill=(255, 40, 40), font=f)
    c.img.paste(scr, (int(x0 * c.w), int(y0 * c.h)))
    c.d = ImageDraw.Draw(c.img)
    if not p.get("off"):
        c.glow(0.5, 0.45, 0.8, (200, 210, 255), 0.18)
    d = c.d
    d.rectangle(c.box(0.10, 0.70, 0.90, 0.78), fill=(30, 26, 36))
    if p.get("red") or p.get("green"):
        c.glow(0.5, 0.5, 0.6, _lightcol(p, FIRE), 0.25)
    return c.done()


def scene_papier(p):
    """Gros plan objet : affiche ou mot scotché au mur, écrit à la main. "lines": lignes de texte,
    "title": en-tête (ex. "AVIS"), "paper": couleur du papier, "wall": "metal" | "carrelage" | "bois"."""
    c = Canvas((0, 0, 0), (0, 0, 0))
    wall = p.get("wall", "bois")
    cols = {"metal": ((70, 68, 84), (34, 32, 44)), "carrelage": ((66, 66, 80), (30, 30, 40)), "bois": ((70, 46, 40), (34, 22, 20))}
    c.img = R.gradient(c.w, c.h, *cols.get(wall, cols["bois"]))
    c.d = d = ImageDraw.Draw(c.img)
    if wall == "carrelage":
        for k in range(26):
            d.line([c.P(0, k * 0.04), c.P(1, k * 0.04)], fill=(50, 50, 62), width=5)
            d.line([c.P(k * 0.06, 0), c.P(k * 0.06, 1)], fill=(50, 50, 62), width=5)
    elif wall == "metal":
        for u in np.arange(0.0, 1.0, 0.07):
            d.line([c.P(u, 0), c.P(u, 1)], fill=(58, 56, 72), width=8)
    else:
        for k in range(14):
            d.line([c.P(0, k * 0.075), c.P(1, k * 0.075 + 0.01)], fill=(52, 34, 30), width=6)
    c.img = c.img.filter(ImageFilter.GaussianBlur(6))
    c.d = d = ImageDraw.Draw(c.img)
    c.glow(0.5, 0.3, 0.8, (255, 200, 140), 0.12)
    d = c.d
    # ombre puis feuille légèrement penchée
    paper = tuple(p.get("paper", (172, 162, 140)))
    sheet = Image.new("RGBA", (int(c.w * 0.74), int(c.h * 0.50)), paper + (255,))
    sd = ImageDraw.Draw(sheet)
    sw, sh = sheet.size
    rnd = random.Random(p.get("seed", 3))
    for _ in range(400):
        x, y = rnd.randint(0, sw - 1), rnd.randint(0, sh - 1)
        g = rnd.randint(-18, 8)
        sd.point((x, y), fill=tuple(max(0, min(255, v + g)) for v in paper) + (255,))
    sd.rectangle([0, 0, sw - 1, sh - 1], outline=(150, 140, 120, 255), width=4)
    y = sh * 0.07
    if p.get("title"):
        f = font(int(sw * 0.11))
        tw = sd.textlength(p["title"], font=f)
        sd.text(((sw - tw) / 2, y), p["title"], fill=(170, 30, 30, 255), font=f)
        y += sw * 0.16
    for line in p.get("lines", ["NE SORS PAS."]):
        f = font(int(sw * 0.075))
        tw = sd.textlength(line, font=f)
        sd.text(((sw - tw) / 2, y), line, fill=(30, 26, 34, 255), font=f)
        y += sw * 0.105
    # scotch
    for (ux, uy) in ((0.08, 0.0), (0.92, 0.0)):
        sd.rectangle([sw * ux - sw * 0.07, sh * uy - 10, sw * ux + sw * 0.07, sh * uy + sh * 0.05], fill=(240, 235, 200, 170))
    sheet = sheet.rotate(p.get("tilt", -2.5), expand=True, resample=Image.BICUBIC)
    shadow = Image.new("RGBA", sheet.size, (0, 0, 0, 0))
    shadow.putalpha(sheet.getchannel("A").point(lambda v: v * 0.6))
    shadow = shadow.filter(ImageFilter.GaussianBlur(30))
    x, y = int(c.w * 0.5 - sheet.width / 2), int(c.h * 0.40 - sheet.height / 2)
    c.img.paste(shadow, (x + 30, y + 40), shadow)
    c.img.paste(sheet, (x, y), sheet)
    c.d = ImageDraw.Draw(c.img)
    if p.get("hand"):
        _hand(c, 0.86, 0.50, 1, 1.2)
    if p.get("dark"):
        c.glow(0.5, 0.5, 0.9, (10, 10, 30), 0.45)
    return _end(c, p, 0.5, 0.75)


def scene_hall(p):
    """Hall d'immeuble parisien la nuit : boîtes aux lettres, portes d'ascenseur, loge du gardien,
    carrelage en damier, minuterie. "floor": numéro affiché au-dessus de l'ascenseur, "open": portes ouvertes."""
    c = Canvas((52, 44, 62), (28, 22, 34))
    d = c.d
    d.rectangle(c.box(0, 0, 1, 0.08), fill=(36, 30, 44))
    for u in np.arange(0, 1.0, 0.10):
        d.line([c.P(u, 0.08), c.P(u, 0.70)], fill=(60, 52, 72), width=4)
    d.rectangle(c.box(0, 0.40, 1, 0.42), fill=(90, 62, 44))
    # boîtes aux lettres
    for i in range(4):
        for j in range(3):
            u, v = 0.04 + i * 0.07, 0.22 + j * 0.06
            d.rectangle(c.box(u, v, u + 0.06, v + 0.05), fill=(120, 96, 60), outline=(70, 52, 34), width=4)
            d.rectangle(c.box(u + 0.01, v + 0.012, u + 0.05, v + 0.018), fill=(30, 24, 20))
    # ascenseur
    d.rectangle(c.box(0.40, 0.18, 0.66, 0.70), fill=(40, 38, 50))
    if p.get("open"):
        d.rectangle(c.box(0.43, 0.22, 0.63, 0.70), fill=(200, 205, 225))
        c.glow(0.53, 0.45, 0.25, (220, 225, 255), 0.4)
        d = c.d
    else:
        d.rectangle(c.box(0.43, 0.22, 0.53, 0.70), fill=(110, 110, 126))
        d.rectangle(c.box(0.53, 0.22, 0.63, 0.70), fill=(100, 100, 116))
    d.rectangle(c.box(0.48, 0.12, 0.58, 0.17), fill=(10, 8, 14))
    d.text(c.P(0.505, 0.122), str(p.get("floor", "0")), fill=(255, 80, 60), font=font(int(c.w * 0.04)))
    d.ellipse(c.box(0.68, 0.42, 0.70, 0.42 + 0.02 * CW / CH), fill=(255, 190, 90))
    # loge du gardien
    d.rectangle(c.box(0.74, 0.20, 1.0, 0.62), fill=(64, 48, 40))
    d.rectangle(c.box(0.77, 0.25, 0.97, 0.45), fill=(255, 200, 130) if not p.get("dark") else (30, 24, 30))
    if not p.get("dark"):
        c.glow(0.87, 0.35, 0.22, (255, 190, 110), 0.4)
        d = c.d
    d.rectangle(c.box(0.80, 0.40, 0.94, 0.42), fill=(120, 80, 50))
    d.text(c.P(0.79, 0.47), "LOGE", fill=(220, 200, 160), font=font(int(c.w * 0.03)))
    # sol en damier
    for i in range(14):
        for j in range(6):
            if (i + j) % 2 == 0:
                v0 = 0.70 + j * 0.05
                d.rectangle(c.box(i * 0.075, v0, i * 0.075 + 0.075, v0 + 0.05), fill=(150, 144, 150))
            else:
                v0 = 0.70 + j * 0.05
                d.rectangle(c.box(i * 0.075, v0, i * 0.075 + 0.075, v0 + 0.05), fill=(30, 26, 34))
    # minuterie au plafond
    d.ellipse(c.box(0.20, 0.05, 0.30, 0.09), fill=(255, 240, 200))
    c.glow(0.25, 0.07, 0.4, (255, 220, 160), 0.35 if not p.get("dark") else 0.1)
    return _end(c, p, 0.3, 0.6)


def scene_palier(p):
    """Couloir d'immeuble, porte d'appartement entrouverte au fond (lumière chaude), numéro d'étage
    peint au mur ("etage"), moquette, minuterie qui grésille. "long": couloir plus profond."""
    c = Canvas((40, 30, 50), (20, 14, 26))
    d = c.d
    far = 0.30 if p.get("long") else 0.38
    fx0, fx1, fy0, fy1 = 0.5 - far / 2.6, 0.5 + far / 2.6, 0.30, 0.62
    d.polygon([c.P(0, 0), c.P(fx0, fy0), c.P(fx0, fy1), c.P(0, 1)], fill=(70, 50, 62))
    d.polygon([c.P(1, 0), c.P(fx1, fy0), c.P(fx1, fy1), c.P(1, 1)], fill=(60, 42, 54))
    d.polygon([c.P(0, 0), c.P(1, 0), c.P(fx1, fy0), c.P(fx0, fy0)], fill=(34, 26, 40))
    d.polygon([c.P(0, 1), c.P(1, 1), c.P(fx1, fy1), c.P(fx0, fy1)], fill=(90, 24, 34))
    for k in range(6):
        t = k / 6
        v = fy1 + (1 - fy1) * t * t
        d.line([c.P(fx0 - (fx0) * t * t, v), c.P(fx1 + (1 - fx1) * t * t, v)], fill=(74, 20, 30), width=5)
    # portes latérales
    for side in (-1, 1):
        for t in (0.25, 0.6):
            ux = 0.5 + side * (0.5 - (0.5 - (fx1 - 0.5)) * t) * (1 - t * 0.2)
            ux = (1 - t) * (0 if side < 0 else 1) + t * (fx0 if side < 0 else fx1)
            hh = (1 - t) * 0.6 + t * (fy1 - fy0)
            vb = (1 - t) * 0.92 + t * fy1
            ww = 0.06 * (1 - t) + 0.02
            d.rectangle(c.box(min(ux, ux - side * ww), vb - hh * 0.8, max(ux, ux - side * ww), vb), fill=(50, 32, 30), outline=(30, 18, 18), width=4)
    # porte du fond entrouverte
    d.rectangle(c.box(fx0 + 0.02, fy0 + 0.04, fx1 - 0.02, fy1), fill=(40, 26, 24))
    if p.get("open", True):
        d.rectangle(c.box(0.5, fy0 + 0.04, fx1 - 0.02, fy1), fill=(255, 190, 110))
        c.glow(0.53, fy0 + 0.18, 0.35, (255, 170, 90), 0.45)
        d = c.d
    if p.get("figure"):
        pass  # _end s'en charge (silhouette dans l'embrasure)
    # numéro d'étage peint
    d.text(c.P(0.06, 0.20), str(p.get("etage", "13")), fill=(200, 40, 40), font=font(int(c.w * 0.12)))
    # minuterie
    d.rectangle(c.box(0.46, 0.06, 0.54, 0.08), fill=(255, 240, 210) if not p.get("dark") else (60, 56, 60))
    c.glow(0.5, 0.08, 0.5, (255, 220, 170), 0.3 if not p.get("dark") else 0.05)
    return _end(c, p, 0.55, 0.47)


def scene_jad_station(p):
    """Intérieur de la station-service du village (Jacques a dit) : rayons, comptoir et caisse,
    vitre sur la nuit, néon qui grésille. "hand": grande main noire sur la vitre, "sweat": sweat bleu par terre."""
    c = Canvas((40, 44, 58), (20, 22, 30))
    d = c.d
    # vitrine sur la nuit
    d.rectangle(c.box(0.0, 0.12, 1.0, 0.52), fill=(14, 16, 34))
    _stars(c, 41, 0.3, 30)
    d = c.d
    for u in (0.0, 0.33, 0.66, 1.0):
        d.rectangle(c.box(u - 0.01, 0.12, u + 0.01, 0.52), fill=(60, 64, 76))
    d.polygon([c.P(0.1, 0.52), c.P(0.18, 0.40), c.P(0.26, 0.52)], fill=(10, 12, 20))   # sapins dehors
    d.polygon([c.P(0.7, 0.52), c.P(0.8, 0.36), c.P(0.9, 0.52)], fill=(10, 12, 20))
    if p.get("hand"):
        hc = (8, 6, 12)
        d.ellipse(c.box(0.52, 0.24, 0.64, 0.38), fill=hc)
        for k, a in enumerate((-0.05, -0.02, 0.01, 0.04)):
            d.line([c.P(0.58 + a * 0.5, 0.26), c.P(0.56 + a * 1.6, 0.14 + abs(a) * 0.6)], fill=hc, width=30)
        d.line([c.P(0.53, 0.32), c.P(0.47, 0.28)], fill=hc, width=30)
    # rayons
    for k, u in enumerate((0.04, 0.70)):
        d.rectangle(c.box(u, 0.55, u + 0.26, 0.88), fill=(70, 60, 70))
        for j in range(3):
            v = 0.58 + j * 0.10
            d.rectangle(c.box(u, v + 0.07, u + 0.26, v + 0.08), fill=(110, 100, 110))
            rnd = random.Random(k * 10 + j)
            x = u + 0.01
            while x < u + 0.24:
                w = rnd.uniform(0.015, 0.03)
                d.rectangle(c.box(x, v + rnd.uniform(0.01, 0.03), x + w, v + 0.07), fill=rnd.choice([(200, 60, 50), (60, 120, 200), (230, 190, 60), (90, 170, 90)]))
                x += w + 0.006
    # comptoir et caisse
    d.rectangle(c.box(0.34, 0.62, 0.66, 0.90), fill=(90, 70, 60))
    d.rectangle(c.box(0.34, 0.60, 0.66, 0.63), fill=(130, 110, 96))
    d.rectangle(c.box(0.40, 0.53, 0.50, 0.60), fill=(30, 30, 40))
    d.rectangle(c.box(0.41, 0.54, 0.49, 0.575), fill=(60, 200, 120) if not p.get("dark") else (20, 40, 30))
    # sol
    d.rectangle(c.box(0, 0.88, 1, 1), fill=(60, 60, 70))
    for k in range(10):
        d.line([c.P(k * 0.11, 0.88), c.P(k * 0.11 - 0.05, 1)], fill=(46, 46, 56), width=4)
    if p.get("sweat"):
        d.polygon([c.P(0.40, 0.97), c.P(0.46, 0.92), c.P(0.58, 0.93), c.P(0.64, 0.98), c.P(0.52, 0.995)], fill=(50, 100, 200))
        d.line([c.P(0.46, 0.93), c.P(0.36, 0.96)], fill=(50, 100, 200), width=26)
    # néon
    neon = (230, 240, 255) if not p.get("dark") else (70, 74, 90)
    d.rectangle(c.box(0.30, 0.03, 0.70, 0.05), fill=neon)
    c.glow(0.5, 0.04, 0.6, (210, 225, 255), 0.35 if not p.get("dark") else 0.08)
    return _end(c, p, 0.5, 0.75)


def scene_jad_maison(p):
    """La maison de granit de la grand-mère, vue de la ruelle : porte bleue ("open" : grande ouverte, noir
    dedans), lucarne du grenier ("attic" : une lueur rouge), muret, hortensias."""
    c = Canvas((12, 12, 36), (46, 40, 76))
    _jad_sky(c, p, 52)
    d = c.d
    _granite_house(c, 0.12, 0.88, 0.86, 0.40, 7, lit=0.0 if p.get("dark") else 0.5)
    d = c.d
    # lucarne du grenier
    d.polygon([c.P(0.42, 0.33), c.P(0.58, 0.33), c.P(0.5, 0.24)], fill=(40, 40, 58))
    d.rectangle(c.box(0.46, 0.27, 0.54, 0.33), fill=(255, 60, 50) if p.get("attic") else (16, 14, 26))
    if p.get("attic"):
        c.glow(0.5, 0.30, 0.12, (255, 60, 50), 0.5)
        d = c.d
    # porte
    d.rectangle(c.box(0.44, 0.62, 0.56, 0.86), fill=(40, 70, 140))
    if p.get("open"):
        d.rectangle(c.box(0.45, 0.63, 0.55, 0.86), fill=(4, 4, 8))
        d.polygon([c.P(0.45, 0.63), c.P(0.40, 0.60), c.P(0.40, 0.89), c.P(0.45, 0.86)], fill=(50, 84, 160))
    else:
        d.ellipse(c.box(0.535, 0.74, 0.545, 0.745), fill=(220, 190, 90))
    # muret et hortensias
    d.rectangle(c.box(0, 0.86, 1, 1), fill=(46, 44, 58))
    for k in range(9):
        u = 0.04 + k * 0.11
        if 0.38 < u < 0.60:
            continue
        rnd = random.Random(k)
        for _ in range(7):
            x, y = u + rnd.uniform(-0.03, 0.03), 0.85 + rnd.uniform(-0.03, 0.02)
            r = rnd.uniform(0.012, 0.02)
            d.ellipse(c.box(x - r, y - r, x + r, y + r), fill=rnd.choice([(110, 90, 190), (80, 110, 200), (150, 90, 170)]))
    # lampadaire
    d.rectangle(c.box(0.94, 0.30, 0.95, 0.90), fill=(30, 30, 40))
    c.glow(0.94, 0.30, 0.25, (255, 190, 110), 0.4)
    return _end(c, p, 0.5, 0.72)


def scene_rame(p):
    """Intérieur d'une rame de métro vide : sièges, barres, néons, vitres noires.
    "hands": mains noires sur les vitres, "dark": néons éteints, "figure" possible au fond."""
    c = Canvas((60, 62, 74), (26, 26, 34))
    d = c.d
    vx0, vx1, vy0, vy1 = 0.40, 0.60, 0.34, 0.60
    d.polygon([c.P(0, 0), c.P(vx0, vy0), c.P(vx0, vy1), c.P(0, 1)], fill=(84, 86, 100))
    d.polygon([c.P(1, 0), c.P(vx1, vy0), c.P(vx1, vy1), c.P(1, 1)], fill=(78, 80, 94))
    d.polygon([c.P(0, 0), c.P(1, 0), c.P(vx1, vy0), c.P(vx0, vy0)], fill=(110, 112, 124))
    d.polygon([c.P(0, 1), c.P(1, 1), c.P(vx1, vy1), c.P(vx0, vy1)], fill=(44, 44, 54))
    d.rectangle(c.box(vx0, vy0, vx1, vy1), fill=(20, 20, 28))
    d.rectangle(c.box(vx0 + 0.04, vy0 + 0.03, vx1 - 0.04, vy0 + 0.13), fill=(8, 8, 14))
    # fenêtres (noires) et sièges
    for side in (-1, 1):
        for t in (0.15, 0.45, 0.72):
            u = 0.5 + side * (0.5 - t * 0.4)
            u2 = 0.5 + side * (0.5 - (t + 0.18) * 0.4)
            top = 0.12 + t * 0.25
            bot = 0.44 + t * 0.07
            d.polygon([c.P(u, top), c.P(u2, top + 0.06), c.P(u2, bot + 0.02), c.P(u, bot)], fill=(110, 116, 160) if p.get("hands") else (10, 10, 18))
            if p.get("hands"):
                hu, hv = (u + u2) / 2, (top + bot) / 2
                d.ellipse(c.box(hu - 0.03, hv - 0.02, hu + 0.03, hv + 0.04), fill=(4, 2, 6))
                for a in (-0.02, -0.007, 0.007, 0.02):
                    d.line([c.P(hu + a, hv), c.P(hu + a * 1.4, hv - 0.06)], fill=(4, 2, 6), width=16)
            sv = 0.62 + (1 - t) * 0.12
            d.polygon([c.P(u, sv), c.P(u2, sv - 0.04), c.P(u2, sv + 0.04), c.P(u, sv + 0.10)], fill=(40, 90, 150))
    # barres
    for u in (0.33, 0.67):
        d.rectangle(c.box(u - 0.006, 0.05, u + 0.006, 0.95), fill=(200, 200, 210))
    # néons
    on = not p.get("dark")
    for t in (0.0, 0.4, 0.7):
        w = 0.25 * (1 - t) + 0.05
        v = 0.03 + t * 0.28
        d.rectangle(c.box(0.5 - w, v, 0.5 + w, v + 0.015 * (1 - t) + 0.004), fill=(240, 245, 255) if on else (70, 72, 84))
    if on:
        c.glow(0.5, 0.1, 0.7, (220, 230, 255), 0.35)
    else:
        c.glow(0.5, 0.5, 0.9, (10, 10, 30), 0.5)
    return _end(c, p, 0.5, 0.42)


def scene_metro_arrive(p):
    """Le métro entre en station : avant de la rame, phares, fenêtres vides éclairées, bord du quai
    jaune, carrelage. "doors": portes ouvertes (vide dedans), "station": nom sur le panneau."""
    c = Canvas((66, 66, 80), (28, 28, 38))
    d = c.d
    for i in range(30):
        d.line([c.P(0, i * 0.02), c.P(1, i * 0.02)], fill=(54, 54, 68), width=4)
    d.rectangle(c.box(0.06, 0.06, 0.46, 0.12), fill=(30, 60, 140))
    d.text(c.P(0.09, 0.065), str(p.get("station", "CAPITOLE")), fill=(255, 255, 255), font=font(int(c.w * 0.045)))
    # rame vue de trois quarts
    d.polygon([c.P(0.10, 0.22), c.P(1.05, 0.18), c.P(1.05, 0.70), c.P(0.10, 0.66)], fill=(150, 30, 40))
    d.polygon([c.P(0.10, 0.22), c.P(0.0, 0.26), c.P(0.0, 0.64), c.P(0.10, 0.66)], fill=(120, 24, 32))
    d.rectangle(c.box(0.10, 0.50, 1.05, 0.54), fill=(230, 230, 235))
    for k in range(4):
        u = 0.16 + k * 0.22
        if p.get("doors") and k == 1:
            d.rectangle(c.box(u, 0.26, u + 0.16, 0.66), fill=(220, 225, 240))
            c.glow(u + 0.08, 0.45, 0.25, (230, 235, 255), 0.45)
            d = c.d
            d.rectangle(c.box(u + 0.075, 0.27, u + 0.085, 0.66), fill=(200, 200, 210))
        else:
            d.rectangle(c.box(u, 0.28, u + 0.16, 0.45), fill=(225, 232, 245))
            d.line([c.P(u + 0.08, 0.28), c.P(u + 0.08, 0.45)], fill=(150, 30, 40), width=6)
    c.glow(0.6, 0.36, 0.6, (220, 230, 255), 0.25)
    d = c.d
    for v in (0.30, 0.58):
        c.glow(0.03, v, 0.12, (255, 250, 220), 0.6)
    d = c.d
    # quai
    d.rectangle(c.box(0, 0.70, 1, 0.72), fill=(230, 200, 60))
    d.rectangle(c.box(0, 0.72, 1, 1), fill=(120, 112, 100))
    for k in range(12):
        d.line([c.P(k * 0.09, 0.72), c.P(k * 0.09 - 0.06, 1)], fill=(100, 94, 84), width=4)
    if p.get("dark"):
        c.glow(0.5, 0.5, 0.9, (10, 10, 30), 0.45)
    return _end(c, p, 0.4, 0.6)


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
          "station": scene_station, "ascenseur": scene_ascenseur, "cuisine": scene_cuisine,
          "salledebain": scene_salledebain, "grenier": scene_grenier, "cave": scene_cave,
          "cimetiere": scene_cimetiere, "eglise": scene_eglise, "voiture": scene_voiture, "salon": scene_salon,
          "ia": scene_ia,
          "hopital": scene_hopital,
          "classe": scene_classe,
          "metro": scene_metro,
          "plage": scene_plage,
          "phare": scene_phare,
          "grange": scene_grange,
          "tente": scene_tente,
          "bureau": scene_bureau,
          "piscine": scene_piscine,
          "supermarche": scene_supermarche,
          "laverie": scene_laverie,
          "bibliotheque": scene_bibliotheque,
          "usine": scene_usine,
          "pont": scene_pont,
          "champ": scene_champ,
          "tunnel": scene_tunnel,
          "cabane": scene_cabane,
          "foraine": scene_foraine,
          "toit": scene_toit,
          "aire": scene_aire,
          "jad_place": scene_jad_place,
          "jad_clocher": scene_jad_clocher,
          "jad_mamie": scene_jad_mamie,
          "jad_ruelle": scene_jad_ruelle,
          "jad_remparts": scene_jad_remparts,
          "jad_jacques": scene_jad_jacques,
          "telephone": scene_telephone, "tele": scene_tele,
          "papier": scene_papier, "hall": scene_hall, "palier": scene_palier,
          "jad_station": scene_jad_station, "jad_maison": scene_jad_maison,
          "rame": scene_rame, "metro_arrive": scene_metro_arrive}
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


# --- idées de l'épisode exemple « Line 9 » (choix de Fio, 08/11) -------------

def draw_rule_card(frame, rule, t):
    """Carte « RÈGLE N°X » affichée quand la règle est dite, puis quand elle est
    mise à l'épreuve (le spectateur fait le lien tout seul)."""
    n, txt = rule.get("n"), rule["text"]
    k = R.ease_out(min(1, max(0, t / 0.3)))
    layer = Image.new("RGBA", (W, H), (0, 0, 0, 0))
    d = ImageDraw.Draw(layer)
    fh, ft = font(50), font(72)
    lines, cur = [], ""
    for w in txt.split():
        if cur and ft.getlength(cur + " " + w) > W - 380:
            lines.append(cur)
            cur = w
        else:
            cur = (cur + " " + w).strip()
    lines.append(cur)
    x0, y0 = 90, 420 - (1 - k) * 60
    h = 116 + 86 * len(lines)
    box = [x0, y0, W - 200, y0 + h]
    d.rounded_rectangle([box[0] + 10, box[1] + 14, box[2] + 10, box[3] + 14], radius=22, fill=(0, 0, 0, 150))
    d.rounded_rectangle(box, radius=22, fill=(244, 236, 214, 255), outline=(40, 30, 30, 255), width=5)
    head = f"RÈGLE N°{n}" if n else "LA RÈGLE"
    hw = fh.getlength(head) + 40
    d.rounded_rectangle([x0 + 34, y0 + 26, x0 + 34 + hw, y0 + 86], radius=12, fill=(200, 40, 45, 255))
    d.text((x0 + 54, y0 + 30), head, font=fh, fill=WHITE)
    for i, ln in enumerate(lines):
        d.text((x0 + 40, y0 + 108 + i * 86), ln, font=ft, fill=(30, 24, 28))
    if k < 1:
        layer.putalpha(layer.getchannel("A").point(lambda v: int(v * k)))
    frame.paste(layer, (0, 0), layer)


def draw_counter(frame, label, value, bump):
    """Compteur en haut à gauche (ex. PASSAGERS 3) : il monte avec la tension."""
    d = ImageDraw.Draw(frame)
    fl, fv = font(38), font(int(84 * (1 + 0.25 * max(0.0, 1 - bump / 0.4))))
    d.text((70, 120), label, font=fl, fill=(230, 230, 235), stroke_width=4, stroke_fill=(0, 0, 0))
    d.text((70, 168), str(value), font=fv, fill=(235, 60, 60) if bump < 1.2 else WHITE,
           stroke_width=6, stroke_fill=(0, 0, 0))


MOODS = {"bleu": ((70, 110, 200), 0.22, 1.0), "rouge": ((210, 40, 40), 0.30, 0.92),
         "noir": ((20, 20, 40), 0.45, 0.72)}


def grade_mood(fr, mood):
    """Lumière qui suit la peur : bleu, puis rouge, puis noir."""
    if mood not in MOODS:
        return fr
    col, amt, bright = MOODS[mood]
    from PIL import ImageChops, ImageEnhance
    tinted = ImageChops.multiply(fr, Image.new("RGB", fr.size, tuple(min(255, c + 90) for c in col)))
    fr = Image.blend(fr, tinted, amt * 2)
    return ImageEnhance.Brightness(fr).enhance(bright) if bright != 1.0 else fr


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
    if voice.engine_name() in ("chatterbox", "parler") and len(clips) >= 5:
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
    if voice.engine_name() in ("chatterbox", "parler"):
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


def _noise(h, w, scale, seed):
    """Bruit doux (valeurs 0..1) : grille aléatoire agrandie."""
    rnd = np.random.default_rng(seed)
    small = rnd.random((max(2, h // scale), max(2, w // scale))).astype(np.float32)
    im = Image.fromarray((small * 255).astype(np.uint8)).resize((w, h), Image.BICUBIC)
    return np.asarray(im).astype(np.float32) / 255


def polish(img, seed=0):
    """Embellit un décor dessiné (demande de Fio, 07/11 : « améliorer les décors ») :
    matière peinte, rayons de lumière, ombres dans les coins, étalonnage ciné, grain."""
    img = img.convert("RGB")
    w, h = img.size
    a = np.asarray(img).astype(np.float32) / 255
    lum = a.max(axis=2)
    # 1. matière : variations douces + fines (aspect peint, plus de surfaces plates)
    tex = 0.75 * _noise(h, w, 160, seed) + 0.25 * _noise(h, w, 40, seed + 1)
    a = a * (0.94 + 0.12 * tex[..., None])
    # 2. relief : renforce le contraste local (objets plus détachés)
    loc = np.asarray(img.filter(ImageFilter.GaussianBlur(w * 0.006))).astype(np.float32) / 255
    a = np.clip(a + (a - loc) * 0.35, 0, 1)
    # 3. rayons de lumière depuis les zones claires (lampes, lune, fenêtres)
    hi = np.clip((lum - 0.72) / 0.28, 0, 1)
    hi_img = Image.fromarray((hi * 255).astype(np.uint8))
    rays = np.zeros((h, w), np.float32)
    if hi.max() > 0:
        cy, cx = np.unravel_index(np.argmax(np.asarray(hi_img.filter(ImageFilter.GaussianBlur(20)))), (h, w))
    else:
        cy, cx = h // 3, w // 2
    for k, s in enumerate((1.04, 1.09, 1.16, 1.26, 1.4)):
        z = hi_img.resize((int(w * s), int(h * s)), Image.BILINEAR)
        x0 = int(cx * s - cx)
        y0 = int(cy * s - cy)
        z = z.crop((x0, y0, x0 + w, y0 + h)).filter(ImageFilter.GaussianBlur(w * 0.01 * (k + 1)))
        rays += np.asarray(z).astype(np.float32) / 255 * (0.5 / (k + 1))
    glowcol = np.array([1.0, 0.85, 0.7])
    a = 1 - (1 - a) * (1 - np.clip(rays, 0, 1)[..., None] * 0.6 * glowcol)
    # 4. étalonnage : ombres bleu-violet, hautes lumières chaudes, contraste
    l2 = a.mean(axis=2, keepdims=True)
    a = a + (1 - l2) * np.array([-0.02, -0.01, 0.05]) * 0.8 + l2 * np.array([0.05, 0.02, -0.03])
    a = np.clip((a - 0.5) * 1.12 + 0.5, 0, 1)
    # 4b. ambiance douce et sombre (inspirée de la vidéo de référence de Fio, 07/11) :
    # couleurs moins saturées, hautes lumières adoucies, tout un peu plus sombre
    l3 = a.mean(axis=2, keepdims=True)
    a = l3 + (a - l3) * 0.72
    a = np.where(a > 0.7, 0.7 + (a - 0.7) * 0.55, a) * 0.92
    # 5. vignette
    yy, xx = np.mgrid[0:h, 0:w].astype(np.float32)
    r = np.sqrt(((xx - w / 2) / (w / 2)) ** 2 + ((yy - h / 2) / (h / 2)) ** 2)
    a = a * (1 - np.clip(r - 0.55, 0, 1) * 0.55)[..., None]
    # 6. grain fixe
    g = np.random.default_rng(seed + 7).normal(0, 0.018, (h, w, 1)).astype(np.float32)
    a = np.clip(a + g, 0, 1)
    return Image.fromarray((a * 255).astype(np.uint8))


def compose(b, cache):
    """Renvoie (décor, [personnages, personnages yeux fermés]) en deux calques pour la profondeur."""
    key = json.dumps([b.get("scene", "flou"), b.get("params", {}), b.get("char"), b.get("char2")], sort_keys=True)
    if key in cache:
        return cache[key]
    scene = b.get("scene", "flou")
    bg = bloom(SCENES[scene](b.get("params", {})).convert("RGB"), (0.15 if scene == "ia" else 0.55) if scene in NEW_SCENES else 0.12)
    if scene != "ia" and not (scene == "flou" and b.get("params", {}).get("of") == "ia") and b.get("polish", True):
        bg = polish(bg, sum(map(ord, scene)))
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


def voice_cfg_tempo():
    import voice
    return voice.CONFIG.get("tempo", 1.3)


def render(ep, out):
    os.environ.setdefault("VOICE_TEMPO", str(ep.get("voice_tempo", voice_cfg_tempo())))
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
    last, last_p = None, {}
    for b in beats:
        sc = b.get("scene", "flou")
        if sc != "flou":
            last, last_p = sc, b.get("params", {})
        elif last and "of" not in b.get("params", {}) and "MORT" not in b.get("text", "").upper():
            extra = {k: last_p[k] for k in ("prompt", "seed") if k in last_p} if last == "ia" else {}
            b["params"] = dict(b.get("params", {}), of=last, **extra)
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
    counter_label = ep.get("counter_label")   # ex. "PASSAGERS" (None = pas de compteur)
    counter, counter_t = ep.get("counter_start", 1), 99.0
    mood = ep.get("mood")            # "bleu" / "rouge" / "noir", change avec "mood" sur un plan
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
        mood = b.get("mood", mood)
        if "count" in b and b["count"] != counter:
            counter, counter_t = b["count"], 0.0
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
            fr = grade_mood(fr, mood)
            particles(fr, b, bi, lt)
            if lt < 0.1 and bi > 0:
                fr = fr.filter(ImageFilter.GaussianBlur(14 * (1 - lt / 0.1)))
            if b.get("choice"):
                c = b["choice"]
                cnt = str(max(1, c["countdown"] - int(lt))) if c.get("countdown") else None
                prev = beats[bi - 1].get("choice") if bi > 0 else None
                same = bool(prev) and (prev["a"], prev["b"]) == (c["a"], c["b"])
                draw_choice(fr, c["a"], c["b"], lt, c.get("picked"), cnt, enter=not same)
            if b.get("rule"):
                draw_rule_card(fr, b["rule"], lt)
            if caps:
                j = max([x for x in range(len(caps)) if starts[x] <= lt] or [0])
                draw_caption(fr, caps[j], lt - starts[j], max(b.get("text_y", 0.68), 0.235) if lives is not None else b.get("text_y", 0.68))
            draw_clock(fr, clock + lt)
            if counter_label:
                draw_counter(fr, counter_label, counter, counter_t + lt)
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
        counter_t += b["dur"]
        t0 += b["dur"]
    proc.stdin.close()
    proc.wait()
    R.build_audio(total, events, wav, voice_track(beats, clips, total, tmp) if clips else None)
    subprocess.run(["ffmpeg", "-loglevel", "error", "-y", "-i", os.path.join(tmp, "v.mp4"), "-i", wav,
                    "-c:v", "copy",
                    # volume au standard TikTok/Instagram (-14 LUFS) : ni trop bas, ni saturé
                    "-af", "loudnorm=I=-14:TP=-1.5:LRA=11,aresample=44100",
                    "-c:a", "aac", "-b:a", "160k", "-shortest", "-movflags", "+faststart", out], check=True)


if __name__ == "__main__":
    with open(sys.argv[1]) as fh:
        render(json.load(fh), sys.argv[2])
