"""Moteur de rendu des épisodes « APRÈS LA FIN ».

Usage : python3 engine/render.py episodes/ep01.json videos/ep01.mp4

Un épisode est une liste de « beats » (plans) décrits en JSON. Le moteur
dessine les décors en dessin vectoriel plat, anime le personnage bâton,
les sous-titres, l'horloge, et génère le son (ambiance + bruitages).
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

W, H, FPS = 1080, 1920, 30
SS = 2  # suréchantillonnage des calques statiques
FONT = "/usr/share/fonts/opentype/inter/InterDisplay-Black.otf"
FONT_HUD = "/usr/share/fonts/opentype/inter/Inter-ExtraBold.otf"
RED = (235, 45, 45)
WHITE = (255, 255, 255)
SR = 44100


def font(path, size):
    return ImageFont.truetype(path, size)


def lerp(a, b, t):
    return a + (b - a) * t


def ease_out(t):
    return 1 - (1 - t) ** 3


def mix(c1, c2, t):
    return tuple(int(lerp(a, b, t)) for a, b in zip(c1, c2))


def gradient(w, h, top, bottom):
    t = np.linspace(0, 1, h)[:, None, None]
    arr = np.array(top)[None, None, :] * (1 - t) + np.array(bottom)[None, None, :] * t
    return Image.fromarray(np.repeat(arr, w, axis=1).astype(np.uint8), "RGB")


def glow(img, center, radius, color, strength=0.8):
    w, h = img.size
    yy, xx = np.mgrid[0:h, 0:w]
    d = np.sqrt((xx - center[0]) ** 2 + (yy - center[1]) ** 2) / radius
    a = np.clip(1 - d, 0, 1) ** 2 * strength
    base = np.asarray(img).astype(np.float32)
    col = np.array(color, np.float32)[None, None, :]
    out = base * (1 - a[..., None]) + col * a[..., None]
    return Image.fromarray(np.clip(out, 0, 255).astype(np.uint8), "RGB")


# ---------------------------------------------------------------- décors

def skyline(d, w, base_y, color, seed, scale=1.0, windows=None):
    rnd = random.Random(seed)
    x = -20
    while x < w:
        bw = int(rnd.randint(70, 170) * scale)
        bh = int(rnd.randint(200, 620) * scale)
        top = base_y - bh
        pts = [(x, base_y), (x, top)]
        # sommet cassé
        steps = rnd.randint(2, 4)
        for i in range(1, steps + 1):
            px = x + bw * i / (steps + 1)
            pts.append((px, top + rnd.randint(-10, 70) * scale))
        pts += [(x + bw, top + rnd.randint(0, 60) * scale), (x + bw, base_y)]
        d.polygon(pts, fill=color)
        if windows:
            for wy in range(int(top + 60 * scale), int(base_y - 30), int(46 * scale)):
                for wx in range(int(x + 16 * scale), int(x + bw - 20 * scale), int(36 * scale)):
                    if rnd.random() < 0.08:
                        d.rectangle([wx, wy, wx + 14 * scale, wy + 20 * scale], fill=windows)
        x += bw + rnd.randint(-10, 25)


def smoke(img, seed, color, n=7, y0=0.2, y1=0.6):
    w, h = img.size
    layer = Image.new("RGBA", (w, h), (0, 0, 0, 0))
    d = ImageDraw.Draw(layer)
    rnd = random.Random(seed)
    for _ in range(n):
        cx = rnd.uniform(0, w)
        cy = rnd.uniform(h * y0, h * y1)
        r = rnd.uniform(w * 0.15, w * 0.35)
        d.ellipse([cx - r, cy - r * 0.5, cx + r, cy + r * 0.5], fill=color + (rnd.randint(50, 110),))
    layer = layer.filter(ImageFilter.GaussianBlur(w * 0.04))
    img.paste(layer, (0, 0), layer)


SKIES = {
    "rouge": ((40, 8, 12), (210, 70, 30), (255, 150, 60)),
    "nuit": ((8, 10, 28), (40, 40, 80), (120, 110, 160)),
    "vert": ((5, 25, 12), (60, 170, 70), (170, 255, 120)),
    "gris": ((25, 25, 30), (90, 85, 85), (170, 160, 150)),
}


def scene_city(p):
    w, h = W * SS, H * SS
    top, bot, sun = SKIES[p.get("sky", "rouge")]
    img = gradient(w, h, top, bot)
    img = glow(img, (w * 0.6, h * 0.5), w * 0.7, sun, 0.7)
    smoke(img, 3, (20, 10, 10), 8, 0.25, 0.55)
    d = ImageDraw.Draw(img)
    skyline(d, w, h * 0.68, mix(top, (0, 0, 0), 0.4), 11, 1.8, windows=(255, 170, 60))
    skyline(d, w, h * 0.74, (12, 8, 10), 7, 2.4)
    d.rectangle([0, h * 0.74, w, h], fill=(14, 10, 12))
    # route fissurée
    d.polygon([(w * 0.42, h * 0.74), (w * 0.58, h * 0.74), (w * 0.95, h), (w * 0.05, h)], fill=(30, 26, 28))
    rnd = random.Random(5)
    for _ in range(6):
        x = rnd.uniform(w * 0.3, w * 0.7)
        y = rnd.uniform(h * 0.78, h * 0.95)
        d.line([(x, y), (x + rnd.uniform(-90, 90), y + rnd.uniform(20, 80))], fill=(10, 8, 10), width=8)
    if p.get("figure"):
        # silhouette immobile dans la rue : [x, taille]
        fx, fs = p["figure"]
        silhouette(d, w * fx, h * 0.9, h * 0.3 * fs)
    if p.get("orb"):
        # lumière verte flottante : [x, y] (fractions de l'écran)
        ox, oy = p["orb"]
        img = glow(img, (w * ox, h * oy), w * 0.35, (90, 255, 110), 0.55)
        d = ImageDraw.Draw(img)
        d.ellipse([w * ox - 34, h * oy - 34, w * ox + 34, h * oy + 34], fill=(200, 255, 200))
    return img


def silhouette(d, x, foot_y, height, col=(4, 3, 5)):
    """Silhouette noire debout, bras le long du corps."""
    hr = height * 0.11
    top = foot_y - height
    lw = max(6, int(height * 0.045))
    d.ellipse([x - hr, top, x + hr, top + 2 * hr], fill=col)
    neck, hip = top + 2 * hr, top + height * 0.58
    d.line([(x, neck), (x, hip)], fill=col, width=lw)
    for sx in (-1, 1):
        d.line([(x, neck + hr * 0.6), (x + sx * hr * 1.1, hip + hr * 0.4)], fill=col, width=lw)
        d.line([(x, hip), (x + sx * hr * 0.8, foot_y)], fill=col, width=lw)
        # deux yeux pâles
        d.ellipse([x + sx * hr * 0.4 - hr * 0.12, top + hr * 0.85, x + sx * hr * 0.4 + hr * 0.12, top + hr * 1.1], fill=(235, 235, 220))


def scene_bunker(p):
    w, h = W * SS, H * SS
    sky = p.get("sky", "nuit")
    top, bot, sun = SKIES[sky]
    img = gradient(w, h, (26, 24, 30), (12, 11, 14))
    d = ImageDraw.Draw(img)
    # fenêtre
    wx0, wy0, wx1, wy1 = w * 0.18, h * 0.12, w * 0.82, h * 0.42
    win = gradient(int(wx1 - wx0), int(wy1 - wy0), top, bot)
    win = glow(win, (win.width * 0.5, win.height * 0.9), win.width * 0.8, sun, 0.6)
    wd = ImageDraw.Draw(win)
    skyline(wd, win.width, win.height, (8, 8, 12), 21, 1.2)
    img.paste(win, (int(wx0), int(wy0)))
    if sky == "vert":
        img = glow(img, (w * 0.5, h * 0.3), w * 0.9, (90, 230, 90), 0.35)
        d = ImageDraw.Draw(img)
    if p.get("light"):
        # lumière blanche qui approche derrière la fenêtre (0 à 1)
        k = p["light"]
        img = glow(img, (w * 0.62, h * 0.3), w * (0.25 + 0.5 * k), (240, 240, 210), 0.35 + 0.5 * k)
        d = ImageDraw.Draw(img)
    fr = (55, 50, 58)
    d.rectangle([wx0 - 24, wy0 - 24, wx1 + 24, wy1 + 24], outline=fr, width=40)
    d.line([(w * 0.5, wy0), (w * 0.5, wy1)], fill=fr, width=26)
    d.line([(wx0, (wy0 + wy1) / 2), (wx1, (wy0 + wy1) / 2)], fill=fr, width=26)
    # planches clouées
    d.polygon([(wx0 - 40, wy0 + 120), (wx1 + 40, wy0 + 40), (wx1 + 40, wy0 + 120), (wx0 - 40, wy0 + 200)], fill=(70, 50, 38))
    # sol + table + radio
    d.rectangle([0, h * 0.72, w, h], fill=(20, 18, 22))
    d.rectangle([w * 0.58, h * 0.6, w * 0.95, h * 0.625], fill=(60, 44, 34))
    d.rectangle([w * 0.61, h * 0.625, w * 0.635, h * 0.74], fill=(48, 36, 28))
    d.rectangle([w * 0.9, h * 0.625, w * 0.925, h * 0.74], fill=(48, 36, 28))
    d.rounded_rectangle([w * 0.66, h * 0.545, w * 0.88, h * 0.6], radius=30, fill=(80, 70, 60))
    d.ellipse([w * 0.68, h * 0.553, w * 0.75, h * 0.592], fill=(30, 28, 26))
    d.rectangle([w * 0.77, h * 0.56, w * 0.86, h * 0.575], fill=(255, 190, 90))
    if p.get("dark"):
        # toutes les lumières éteintes (0 à 1)
        img = Image.blend(img, Image.new("RGB", img.size, (0, 0, 0)), p["dark"])
    return img


def scene_door(p):
    w, h = W * SS, H * SS
    lightc = (120, 255, 120) if p.get("sky") == "vert" else (255, 200, 120)
    img = gradient(w, h, (22, 20, 26), (8, 8, 10))
    d = ImageDraw.Draw(img)
    x0, x1, y0, y1 = w * 0.18, w * 0.82, h * 0.12, h * 0.86
    d.rectangle([x0 - 40, y0 - 40, x1 + 40, y1], fill=(40, 38, 44))
    d.rectangle([x0, y0, x1, y1 - 30], fill=(70, 74, 80))
    for i in range(1, 4):
        yy = y0 + (y1 - y0) * i / 4
        d.line([(x0, yy), (x1, yy)], fill=(55, 58, 64), width=10)
    for yy in np.linspace(y0 + 60, y1 - 90, 6):
        d.ellipse([x0 + 30, yy, x0 + 54, yy + 24], fill=(40, 42, 46))
        d.ellipse([x1 - 54, yy, x1 - 30, yy + 24], fill=(40, 42, 46))
    d.rounded_rectangle([x1 - 160, h * 0.5, x1 - 60, h * 0.53], radius=14, fill=(160, 150, 130))
    # verrou
    d.rectangle([x0 + 40, h * 0.45, x0 + 260, h * 0.48], fill=(120, 110, 100))
    # lumière sous la porte
    d.rectangle([x0, y1 - 30, x1, y1], fill=lightc)
    img = glow(img, (w * 0.5, y1), w * 0.6, lightc, 0.45)
    d = ImageDraw.Draw(img)
    d.rectangle([0, y1, w, h], fill=(16, 14, 18))
    img = glow(img, (w * 0.5, y1 + 40), w * 0.45, lightc, 0.3)
    return img


def scene_radio(p):
    w, h = W * SS, H * SS
    img = gradient(w, h, (30, 22, 18), (10, 8, 8))
    img = glow(img, (w * 0.5, h * 0.48), w * 0.8, (255, 160, 70), 0.35)
    d = ImageDraw.Draw(img)
    x0, x1, y0, y1 = w * 0.1, w * 0.9, h * 0.32, h * 0.64
    d.rounded_rectangle([x0, y0, x1, y1], radius=90, fill=(110, 80, 58))
    d.rounded_rectangle([x0 + 30, y0 + 30, x1 - 30, y1 - 30], radius=70, outline=(80, 58, 42), width=14)
    d.rounded_rectangle([x0 + 80, y0 + 90, w * 0.55, y1 - 90], radius=40, fill=(40, 32, 26))
    for yy in np.arange(y0 + 130, y1 - 110, 46):
        d.line([(x0 + 110, yy), (w * 0.53, yy)], fill=(70, 56, 44), width=18)
    d.rounded_rectangle([w * 0.6, y0 + 100, x1 - 80, y0 + 220], radius=20, fill=(255, 200, 110))
    for i in range(9):
        xx = w * 0.62 + i * (x1 - 100 - w * 0.62) / 8
        d.line([(xx, y0 + 120), (xx, y0 + (170 if i % 2 else 200))], fill=(90, 60, 30), width=6)
    d.line([(w * 0.7, y0 + 106), (w * 0.7, y0 + 214)], fill=RED, width=10)
    for cx in (w * 0.66, w * 0.8):
        d.ellipse([cx - 70, y1 - 260, cx + 70, y1 - 120], fill=(60, 44, 32))
        d.line([(cx, y1 - 190), (cx + 40, y1 - 240)], fill=(200, 180, 150), width=12)
    d.line([(x1 - 120, y0), (x1 + 60, h * 0.12)], fill=(150, 150, 150), width=16)
    d.rectangle([0, y1 + 40, w, h], fill=(30, 22, 18))
    return img


def scene_dark(p):
    w, h = W * SS, H * SS
    img = gradient(w, h, (12, 6, 8), (2, 2, 4))
    return glow(img, (w * 0.5, h * 0.5), w * 0.7, tuple(p.get("glow", (90, 10, 10))), 0.5)


def scene_hide(p):
    # sous la table : vue de dessous, lumière verte au loin
    w, h = W * SS, H * SS
    img = gradient(w, h, (10, 12, 12), (4, 4, 6))
    img = glow(img, (w * 0.5, h * 0.62), w * 0.7, (90, 220, 90), 0.35)
    d = ImageDraw.Draw(img)
    d.rectangle([0, 0, w, h * 0.2], fill=(46, 34, 26))
    d.rectangle([w * 0.06, h * 0.2, w * 0.13, h], fill=(38, 28, 22))
    d.rectangle([w * 0.87, h * 0.2, w * 0.94, h], fill=(38, 28, 22))
    d.rectangle([0, h * 0.8, w, h], fill=(14, 13, 16))
    return img


def scene_notebook(p):
    # carnet ouvert sur une table, éclairé à la lampe
    w, h = W * SS, H * SS
    img = gradient(w, h, (34, 24, 18), (10, 8, 6))
    img = glow(img, (w * 0.5, h * 0.55), w * 0.75, (255, 180, 90), 0.4)
    d = ImageDraw.Draw(img)
    x0, x1, y0, y1 = w * 0.08, w * 0.92, h * 0.42, h * 0.84
    d.rectangle([x0 - 20, y0 - 20, x1 + 20, y1 + 20], fill=(70, 40, 30))
    for a, b in ((x0, w * 0.5 - 6), (w * 0.5 + 6, x1)):
        d.rectangle([a, y0, b, y1], fill=(225, 214, 186))
        rnd = random.Random(int(a))
        for yy in np.arange(y0 + 90, y1 - 40, 64):
            d.line([(a + 30, yy), (b - 30, yy)], fill=(170, 180, 200), width=4)
            xx = a + 50
            end = b - rnd.uniform(60, 260)
            while xx < end:
                ln = rnd.uniform(40, 130)
                d.line([(xx, yy - 18), (min(end, xx + ln), yy - 14 + rnd.uniform(-6, 6))], fill=(40, 40, 70), width=7)
                xx += ln + 26
    d.line([(w * 0.5, y0), (w * 0.5, y1)], fill=(120, 100, 80), width=14)
    if p.get("red"):
        # dernière ligne soulignée en rouge
        d.line([(w * 0.55, y1 - 110), (x1 - 40, y1 - 100)], fill=RED, width=14)
    return img


SCENES = {
    "notebook": scene_notebook,
    "city": scene_city, "bunker": scene_bunker, "door": scene_door,
    "radio": scene_radio, "dark": scene_dark, "hide": scene_hide,
}

# ---------------------------------------------------------------- personnage


def character(expr="normal", hoodie=(230, 120, 30), pose="stand", blink=False):
    """Personnage bâton : grosse tête noire ronde, sweat à capuche coloré."""
    s = SS
    w, h = 520 * s, 1000 * s
    img = Image.new("RGBA", (w, h), (0, 0, 0, 0))
    d = ImageDraw.Draw(img)
    cx = w / 2
    blk = (10, 10, 12, 255)
    hood = tuple(hoodie) + (255,)
    dark = tuple(int(c * 0.7) for c in hoodie) + (255,)
    if pose == "crouch":
        d.line([(cx - 60 * s, 760 * s), (cx - 130 * s, 900 * s), (cx - 60 * s, 990 * s)], fill=blk, width=26 * s, joint="curve")
        d.line([(cx + 60 * s, 760 * s), (cx + 130 * s, 900 * s), (cx + 60 * s, 990 * s)], fill=blk, width=26 * s, joint="curve")
        body = [cx - 150 * s, 470 * s, cx + 150 * s, 800 * s]
    else:
        d.line([(cx - 50 * s, 760 * s), (cx - 60 * s, 990 * s)], fill=blk, width=28 * s)
        d.line([(cx + 50 * s, 760 * s), (cx + 60 * s, 990 * s)], fill=blk, width=28 * s)
        body = [cx - 140 * s, 420 * s, cx + 140 * s, 790 * s]
    d.rounded_rectangle(body, radius=90 * s, fill=hood)
    d.rounded_rectangle([body[0] + 60 * s, body[1] + 200 * s, body[2] - 60 * s, body[1] + 280 * s], radius=30 * s, fill=dark)
    # bras
    if pose == "crouch":
        d.line([(cx - 120 * s, 520 * s), (cx - 60 * s, 380 * s)], fill=blk, width=24 * s)
        d.line([(cx + 120 * s, 520 * s), (cx + 60 * s, 380 * s)], fill=blk, width=24 * s)
    else:
        d.line([(cx - 130 * s, 470 * s), (cx - 170 * s, 700 * s)], fill=blk, width=24 * s)
        d.line([(cx + 130 * s, 470 * s), (cx + 170 * s, 700 * s)], fill=blk, width=24 * s)
    # capuche + tête
    hy = 330 * s if pose != "crouch" else 380 * s
    d.ellipse([cx - 190 * s, hy - 210 * s, cx + 190 * s, hy + 170 * s], fill=dark)
    d.ellipse([cx - 165 * s, hy - 190 * s, cx + 165 * s, hy + 140 * s], fill=blk)
    ey = hy - 40 * s
    for ex in (cx - 62 * s, cx + 62 * s):
        if blink or expr == "closed":
            d.line([(ex - 34 * s, ey), (ex + 34 * s, ey)], fill=WHITE, width=10 * s)
        elif expr == "scared":
            d.ellipse([ex - 50 * s, ey - 52 * s, ex + 50 * s, ey + 52 * s], fill=WHITE)
            d.ellipse([ex - 13 * s, ey - 13 * s, ex + 13 * s, ey + 13 * s], fill=blk)
        elif expr == "stare":
            # yeux grands ouverts, pupilles minuscules, ne cligne jamais
            d.ellipse([ex - 46 * s, ey - 46 * s, ex + 46 * s, ey + 46 * s], fill=WHITE)
            d.ellipse([ex - 7 * s, ey - 7 * s, ex + 7 * s, ey + 7 * s], fill=blk)
        elif expr == "suspicious":
            d.ellipse([ex - 40 * s, ey - 26 * s, ex + 40 * s, ey + 26 * s], fill=WHITE)
            d.ellipse([ex - 4 * s, ey - 16 * s, ex + 26 * s, ey + 16 * s], fill=blk)
            d.rectangle([ex - 44 * s, ey - 34 * s, ex + 44 * s, ey - 10 * s], fill=blk)
        else:
            d.ellipse([ex - 38 * s, ey - 38 * s, ex + 38 * s, ey + 38 * s], fill=WHITE)
            d.ellipse([ex - 14 * s, ey - 10 * s, ex + 16 * s, ey + 20 * s], fill=blk)
    if expr == "scared":
        d.ellipse([cx - 22 * s, hy + 50 * s, cx + 22 * s, hy + 100 * s], fill=WHITE)
    return img.resize((w // s, h // s), Image.LANCZOS)


# ---------------------------------------------------------------- texte

def draw_caption(frame, text, t, y=0.66, size=150):
    """Sous-titre géant ; les mots entre *astérisques* sont en rouge."""
    words = text.split()
    # mots en rouge : tout ce qui est entre deux astérisques
    reds, on = set(), False
    for wd in words:
        if wd.startswith("*"):
            on = True
        if on:
            reds.add(wd)
        if wd.count("*") == 2 or (wd.count("*") == 1 and not wd.startswith("*")):
            on = False
    f = font(FONT, size)
    while True:
        lines, cur = [], []
        for wd in words:
            test = " ".join(x.replace("*", "") for x in cur + [wd])
            if f.getlength(test) > W - 110 and cur:
                lines.append(cur)
                cur = [wd]
            else:
                cur.append(wd)
        lines.append(cur)
        if len(lines) <= 3 or size < 70:
            break
        size -= 10
        f = font(FONT, size)
    pop = 0.7 + 0.3 * ease_out(min(1, t / 0.12))
    layer = Image.new("RGBA", (W, H), (0, 0, 0, 0))
    d = ImageDraw.Draw(layer)
    lh = size * 1.08
    y0 = H * y - lh * len(lines) / 2
    for i, ln in enumerate(lines):
        clean = " ".join(x.replace("*", "") for x in ln)
        x = (W - f.getlength(clean)) / 2
        for wd in ln:
            col = RED if wd in reds else WHITE
            wd2 = wd.replace("*", "")
            d.text((x + 6, y0 + i * lh + 8), wd2, font=f, fill=(0, 0, 0, 160))
            d.text((x, y0 + i * lh), wd2, font=f, fill=col, stroke_width=8, stroke_fill=(0, 0, 0))
            x += f.getlength(wd2 + " ")
    if pop < 1:
        nw, nh = int(W * pop), int(H * pop)
        small = layer.resize((nw, nh), Image.BILINEAR)
        layer = Image.new("RGBA", (W, H), (0, 0, 0, 0))
        layer.paste(small, ((W - nw) // 2, int(H * y - H * y * pop)))
    frame.paste(layer, (0, 0), layer)


def draw_hud(frame, day, clock_s, subtitle):
    d = ImageDraw.Draw(frame)
    hh, rem = divmod(int(clock_s) % 86400, 3600)
    mm, ss = divmod(rem, 60)
    txt = f"{hh:02d}:{mm:02d}:{ss:02d}"
    f = font(FONT, 108)
    d.text(((W - f.getlength(txt)) / 2, 150), txt, font=f, fill=WHITE, stroke_width=6, stroke_fill=(0, 0, 0))
    f2 = font(FONT_HUD, 34)
    sub = f"JOUR {day}  ·  {subtitle}".upper()
    d.text(((W - f2.getlength(sub)) / 2, 280), sub, font=f2, fill=(230, 230, 230), stroke_width=3, stroke_fill=(0, 0, 0))


def draw_choice(frame, a, b, t, picked=None, count=None):
    d = ImageDraw.Draw(frame)
    f = font(FONT, 70)
    fl = font(FONT, 140)
    for i, (lab, txt, col) in enumerate((("A", a, (200, 40, 40)), ("B", b, (40, 90, 200)))):
        k = ease_out(min(1, max(0, (t - i * 0.15) / 0.3)))
        y0 = 560 + i * 520
        x_off = (1 - k) * (-W if i == 0 else W)
        box = [80 + x_off, y0, W - 80 + x_off, y0 + 440]
        dim = picked is not None and picked != lab
        fill = mix(col, (30, 30, 30), 0.7) if dim else col
        d.rounded_rectangle(box, radius=50, fill=fill, outline=WHITE if picked == lab else (0, 0, 0), width=14 if picked == lab else 6)
        d.text((box[0] + 50, y0 + 40), lab, font=fl, fill=WHITE, stroke_width=6, stroke_fill=(0, 0, 0))
        words, lines, cur = txt.split(), [], ""
        for wd in words:
            if f.getlength((cur + " " + wd).strip()) > 760:
                lines.append(cur)
                cur = wd
            else:
                cur = (cur + " " + wd).strip()
        lines.append(cur)
        for j, ln in enumerate(lines):
            d.text((box[0] + 50, y0 + 220 + j * 82), ln, font=f, fill=WHITE, stroke_width=4, stroke_fill=(0, 0, 0))
    if count is not None:
        fc = font(FONT, 160)
        d.text(((W - fc.getlength(count)) / 2, 1560), count, font=fc, fill=WHITE, stroke_width=8, stroke_fill=(0, 0, 0))


# ---------------------------------------------------------------- effets

_GRAIN = [np.random.default_rng(i).normal(0, 5, (H // 2, W // 2, 1)).astype(np.float32) for i in range(6)]
_yy, _xx = np.mgrid[0:H, 0:W]
_VIG = (1 - 0.55 * np.clip(((_xx - W / 2) / (W * 0.75)) ** 2 + ((_yy - H / 2) / (H * 0.7)) ** 2, 0, 1))[..., None].astype(np.float32)


def finish(frame, n, glitch=0.0, vhs=False, flash=0.0, flash_level=255):
    a = np.asarray(frame.convert("RGB")).astype(np.float32)
    a *= _VIG
    g = _GRAIN[n % len(_GRAIN)]
    a += np.repeat(np.repeat(g, 2, 0), 2, 1)
    if glitch > 0:
        rnd = np.random.default_rng(n)
        for _ in range(int(6 * glitch) + 1):
            y = rnd.integers(0, H - 80)
            hgt = rnd.integers(10, 80)
            a[y:y + hgt] = np.roll(a[y:y + hgt], rnd.integers(-80, 80), axis=1)
        a[..., 0] = np.roll(a[..., 0], int(14 * glitch), axis=1)
        a[..., 2] = np.roll(a[..., 2], -int(14 * glitch), axis=1)
    if vhs:
        a[::4] *= 0.7
        y = (n * 37) % H
        a[y:y + 30] = a[y:y + 30] * 0.4 + 120
        a[..., 1] *= 0.92
    if flash > 0:
        a = a * (1 - flash) + flash_level * flash
    return np.clip(a, 0, 255).astype(np.uint8)


# ---------------------------------------------------------------- son

def tone(f, dur, vol=0.3, decay=0.0):
    t = np.arange(int(SR * dur)) / SR
    s = np.sin(2 * np.pi * f * t) * vol
    if decay:
        s *= np.exp(-t * decay)
    return s


def noise(dur, vol=0.3, decay=0.0, seed=0):
    t = np.arange(int(SR * dur)) / SR
    s = np.random.default_rng(seed).uniform(-1, 1, len(t)) * vol
    if decay:
        s *= np.exp(-t * decay)
    return s


def add(*parts):
    n = max(len(p) for p in parts)
    out = np.zeros(n)
    for p in parts:
        out[:len(p)] += p
    return out


def lowpass(s, k=40):
    return np.convolve(s, np.ones(k) / k, mode="same")


SFX = {
    "knock": lambda: np.concatenate([add(lowpass(noise(0.12, 1.4, 40), 30), tone(90, 0.12, 0.8, 35)), np.zeros(int(SR * 0.16))] * 3),
    "boom": lambda: add(lowpass(noise(1.6, 1.0, 2.5, 1), 120) * 2, tone(45, 1.6, 0.9, 2)),
    "glitch": lambda: np.sign(np.sin(2 * np.pi * np.cumsum(np.random.default_rng(2).uniform(80, 1400, int(SR * 0.6))) / SR)) * 0.35,
    "rewind": lambda: add(np.sin(2 * np.pi * np.cumsum(np.linspace(1800, 200, int(SR * 1.2))) / SR) * 0.25, noise(1.2, 0.08, 0, 3)),
    "radio": lambda: lowpass(noise(2.5, 0.25, 0, 4), 6) * (0.6 + 0.4 * np.sin(np.arange(int(SR * 2.5)) / SR * 2 * np.pi * 7)),
    "hit": lambda: add(tone(55, 1.0, 1.0, 4), lowpass(noise(0.3, 0.6, 12, 5), 20)),
    "tick": lambda: tone(1800, 0.03, 0.25, 120),
    "whoosh": lambda: lowpass(noise(0.5, 0.5, 0, 6), 25) * np.hanning(int(SR * 0.5)),
    "heart": lambda: np.concatenate([tone(55, 0.12, 1.0, 25), np.zeros(int(SR * 0.1)), tone(50, 0.12, 0.8, 25), np.zeros(int(SR * 0.6))]),
}


def build_audio(total, events, path, voice_track=None):
    n = int(total * SR)
    t = np.arange(n) / SR
    # ambiance : drone grave qui respire + souffle
    amb = 0.10 * np.sin(2 * np.pi * 48 * t) * (0.7 + 0.3 * np.sin(2 * np.pi * 0.1 * t))
    amb += 0.05 * np.sin(2 * np.pi * 72.5 * t)
    amb += lowpass(np.random.default_rng(9).uniform(-1, 1, n), 200) * 0.25
    out = amb
    for at, name, vol in events:
        s = SFX[name]() * vol
        i = int(at * SR)
        j = min(n, i + len(s))
        if i < n:
            out[i:j] += s[: j - i]
    out = np.tanh(out * 1.2) * 0.85
    if voice_track is not None:
        # on baisse l'ambiance pendant que la voix parle
        env = np.convolve(np.abs(voice_track[:n]) > 0.02, np.ones(SR // 5) / (SR // 5), mode="same")
        out = out * (1 - 0.45 * np.clip(env * 3, 0, 1)) + voice_track[:n] * 1.6
        out = np.clip(out, -1, 1)
    pcm = (out * 32767).astype(np.int16)
    with wave.open(path, "wb") as wf:
        wf.setnchannels(1)
        wf.setsampwidth(2)
        wf.setframerate(SR)
        wf.writeframes(pcm.tobytes())


# ---------------------------------------------------------------- rendu

def prepare_voice(beats):
    """Synthétise la voix off de chaque plan et allonge les plans trop courts."""
    import voice
    clips = {}
    for i, b in enumerate(beats):
        if b.get("type") == "rewind":
            continue
        line = b.get("voice", b.get("text", ""))
        if not line:
            continue
        audio = voice.synth(line)
        clips[i] = audio
        if voice.TIGHT:
            # plan calé sur la voix : pas de blanc entre les phrases
            b["dur"] = round(max(len(audio) / SR + 0.18, 0.9), 2)
        else:
            need = round(len(audio) / SR + 0.35, 2)
            if b["dur"] < need:
                b["dur"] = need
    print(f"voix off : {voice.engine_name()}, {len(clips)} répliques")
    return clips


def voice_track(beats, clips, total, tmp):
    import voice
    track = np.zeros(int(total * SR) + SR, np.float32)
    t0 = 0.0
    for i, b in enumerate(beats):
        if i in clips:
            a = clips[i]
            j = int((t0 + (0.04 if voice.TIGHT else 0.12)) * SR)
            track[j:j + len(a)] += a[: len(track) - j]
        t0 += b["dur"]
    return voice.megaphone(track, tmp)


def render(ep, out):
    beats = ep["beats"]
    clips = prepare_voice(beats) if ep.get("voiceover", True) else {}
    total = sum(b["dur"] for b in beats)
    print(f"durée totale : {total:.1f} s")
    tmp = tempfile.mkdtemp()
    wav = os.path.join(tmp, "a.wav")
    proc = subprocess.Popen(
        ["ffmpeg", "-loglevel", "error", "-y", "-f", "rawvideo", "-pix_fmt", "rgb24", "-s", f"{W}x{H}",
         "-r", str(FPS), "-i", "-", "-c:v", "libx264", "-preset", "slow", "-crf", "30",
         "-pix_fmt", "yuv420p", os.path.join(tmp, "v.mp4")],
        stdin=subprocess.PIPE)
    bg_cache, char_cache, recorded, rec_clock = {}, {}, {}, {}
    events = []
    clock = ep.get("clock_start", 3 * 3600 + 12 * 60)
    n, t0 = 0, 0.0
    for b in beats:
        if "sfx" in b:
            for s in b["sfx"]:
                name, off, vol = (s + [0, 1.0])[:3] if isinstance(s, list) else (s, 0, 1.0)
                events.append((t0 + off, name, vol))
        nf = int(round(b["dur"] * FPS))
        if b.get("type") == "rewind":
            src = recorded.get(b["of"], [])
            step = max(1, len(src) // nf) if src else 1
            seq = src[::-1][::step] if src else []
            for i in range(nf):
                a = seq[min(i, len(seq) - 1)] if seq else np.zeros((H, W, 3), np.uint8)
                fr = Image.fromarray(a)
                d = ImageDraw.Draw(fr)
                f = font(FONT, 105)
                txt = "<< ON REMBOBINE"
                if (i // 8) % 2 == 0:
                    d.text(((W - f.getlength(txt)) / 2, H * 0.45), txt, font=f, fill=WHITE, stroke_width=8, stroke_fill=(0, 0, 0))
                draw_hud(fr, ep["day"], lerp(clock, rec_clock.get(b["of"], clock), i / nf), ep["subtitle"])
                proc.stdin.write(finish(fr, n, glitch=0.3, vhs=True).tobytes())
                n += 1
            clock = rec_clock.get(b["of"], clock)
            t0 += b["dur"]
            continue
        key = json.dumps([b.get("scene", "dark"), b.get("params", {})], sort_keys=True)
        if key not in bg_cache:
            big = SCENES[b.get("scene", "dark")](b.get("params", {}))
            bg_cache[key] = big.resize((int(W * 1.12), int(H * 1.12)), Image.LANCZOS)
        bg = bg_cache[key]
        rec = recorded.setdefault(b["record"], []) if b.get("record") else None
        if b.get("record"):
            rec_clock.setdefault(b["record"], clock)
        for i in range(nf):
            lt = i / FPS
            k = i / max(1, nf - 1)
            z = lerp(1.0, b.get("zoom", 1.06), k)
            cw, chh = int(W * 1.12 / z), int(H * 1.12 / z)
            ox = (bg.width - cw) // 2
            oy = (bg.height - chh) // 2
            sx = sy = 0
            if b.get("shake"):
                amp = b["shake"] * (1 - k * 0.5)
                sx, sy = int(random.uniform(-amp, amp)), int(random.uniform(-amp, amp))
            fr = bg.crop((ox + sx, oy + sy, ox + sx + cw, oy + sy + chh)).resize((W, H), Image.BILINEAR).convert("RGBA")
            for ch in [c for c in (b.get("char"), b.get("char2")) if c]:
                blink = ch.get("expr", "normal") == "normal" and (i % 75) in (60, 61, 62)
                ck = (ch.get("expr", "normal"), ch.get("pose", "stand"), blink, tuple(ch.get("hoodie", (230, 120, 30))))
                if ck not in char_cache:
                    char_cache[ck] = character(ck[0], hoodie=ck[3], pose=ck[1], blink=blink)
                cimg = char_cache[ck]
                sc = ch.get("scale", 1.0) * (1 + 0.012 * math.sin(lt * 3))
                cimg2 = cimg.resize((int(cimg.width * sc), int(cimg.height * sc)), Image.BILINEAR)
                tx = random.randint(-4, 4) if ch.get("tremble") else 0
                cx = int(W * ch.get("x", 0.5) - cimg2.width / 2) + sx + tx
                cy = int(H * ch.get("y", 0.95) - cimg2.height)
                fr.paste(cimg2, (cx, cy), cimg2)
            if b.get("choice"):
                c = b["choice"]
                cnt = None
                if c.get("countdown"):
                    cnt = str(max(1, c["countdown"] - int(lt)))
                draw_choice(fr, c["a"], c["b"], lt, c.get("picked"), cnt)
            if b.get("text"):
                draw_caption(fr, b["text"], lt, b.get("text_y", 0.66), b.get("text_size", 150))
            draw_hud(fr, ep["day"], clock + lt, ep["subtitle"])
            if b.get("tick", False) and i % FPS == 0:
                events.append((t0 + lt, "tick", 0.6))
            fl = 0.0
            if b.get("flash_in"):
                fl = max(0.0, 1 - lt / 0.25)
            g = b.get("glitch", 0.0)
            if b.get("glitch_end"):
                g = max(g, max(0.0, (lt - (b["dur"] - 0.4)) / 0.4))
            # jamais d'écran blanc au tout début : le premier plan s'ouvre depuis le noir
            arr = finish(fr, n, glitch=g, flash=fl, flash_level=0 if t0 == 0 else 255)
            if rec is not None:
                rec.append(arr)
            proc.stdin.write(arr.tobytes())
            n += 1
        clock += b["dur"]
        t0 += b["dur"]
    proc.stdin.close()
    proc.wait()
    build_audio(total, events, wav, voice_track(beats, clips, total, tmp) if clips else None)
    subprocess.run(["ffmpeg", "-loglevel", "error", "-y", "-i", os.path.join(tmp, "v.mp4"), "-i", wav,
                    "-c:v", "copy", "-c:a", "aac", "-b:a", "160k", "-shortest", "-movflags", "+faststart", out], check=True)


if __name__ == "__main__":
    with open(sys.argv[1]) as fh:
        render(json.load(fh), sys.argv[2])
