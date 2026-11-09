"""Animation « vraie vidéo » (demande de Fio, 09/11 : « il n'y a presque pas d'animation,
c'est juste des images, il faut donner l'impression que c'est une vidéo »).

Tout est gratuit, en numpy/PIL, et appliqué image par image :
- caméra à l'épaule : petit tremblement doux et continu (jamais d'image figée) ;
- personnage vivant : respiration, léger balancement, regard qui bouge (voir render2) ;
- lumières qui vacillent : lampes, fenêtres, lune, écrans respirent et clignotent parfois ;
- brume qui avance lentement devant le décor ;
- météo au choix : pluie, neige, cendres (`"meteo"` sur l'épisode ou sur un plan).
"""
import math

import numpy as np
from PIL import Image, ImageChops, ImageDraw, ImageFilter


def _n(t, seed):
    """Bruit doux entre -1 et 1 (somme de sinus déphasés)."""
    return (math.sin(t * 1.13 + seed) * 0.5 + math.sin(t * 2.71 + seed * 1.7) * 0.3
            + math.sin(t * 5.3 + seed * 2.3) * 0.2)


def handheld(t, seed, amp=7.0):
    """Décalage (dx, dy) de caméra à l'épaule, en pixels du décor."""
    return amp * _n(t, seed), amp * 0.8 * _n(t + 31.7, seed + 4.2)


def breath(t, seed, scared=False):
    """(étirement vertical, décalage x) du personnage : respiration + balancement.
    Peur : respiration rapide et tremblement."""
    if scared:
        s = 1 + 0.016 * math.sin(t * 2 * math.pi / 1.1 + seed) + 0.004 * math.sin(t * 37 + seed)
        return s, 3.0 * math.sin(t * 31 + seed) + 5 * _n(t, seed)
    return 1 + 0.011 * math.sin(t * 2 * math.pi / 3.2 + seed), 9 * _n(t * 0.6, seed + 1)


def look_index(t, seed):
    """Regard : 0 = devant, 2 = à gauche, 3 = à droite. Coup d'œil de temps en temps."""
    cyc = (t + (seed % 7) * 0.41) % 4.2
    if 1.6 < cyc < 2.3:
        return 2 if int(seed) % 2 else 3
    if 3.3 < cyc < 3.8:
        return 3 if int(seed) % 2 else 2
    return 0


def flicker_level(t, seed, nervous=False):
    """Intensité des lumières : respire doucement, avec parfois une coupure brève."""
    v = 0.5 + 0.5 * _n(t * 3.0, seed)
    period = 2.3 if nervous else 4.7
    ph = (t + seed * 0.37) % period
    if ph < 0.06 or (nervous and 0.12 < ph < 0.17):
        v -= 1.6                                   # micro-coupure (ampoule qui grésille)
    return v


def lights(fr, t, seed, nervous=False, amount=1.0):
    """Les zones lumineuses de l'image vacillent et rayonnent."""
    w, h = fr.size
    small = fr.resize((w // 8, h // 8), Image.BILINEAR)
    a = np.asarray(small, np.float32)
    lum = a.max(axis=2, keepdims=True)
    mask = np.clip((lum - 150) / 80, 0, 1) * a
    glow = Image.fromarray(mask.astype(np.uint8)).filter(ImageFilter.GaussianBlur(5)).resize((w, h), Image.BILINEAR)
    lv = flicker_level(t, seed, nervous) * amount * 0.55
    g = glow.point(lambda x: min(255, int(x * abs(lv))))
    return ImageChops.add(fr, g) if lv >= 0 else ImageChops.subtract(fr, g)


_fog = {}


def _fog_tex(w, h, seed):
    key = (w, h, seed)
    if key not in _fog:
        rnd = np.random.default_rng(seed)
        tw, th = w // 6, h // 6
        big = np.zeros((th, tw * 2), np.float32)
        for sc, wt in ((24, 0.6), (9, 0.3), (4, 0.1)):
            gw, gh = max(2, tw * 2 // sc), max(2, th // sc)
            g = rnd.random((gh, gw)).astype(np.float32)
            g[:, -1] = g[:, 0]                     # raccord pour boucler
            big += np.asarray(Image.fromarray((g * 255).astype(np.uint8)).resize((tw * 2, th), Image.BICUBIC),
                              np.float32) / 255 * wt
        big = np.clip((big - 0.45) * 2.2, 0, 1)
        _fog[key] = big
    return _fog[key]


def fog(fr, t, seed, amount=0.16, speed=14.0):
    """Brume qui glisse lentement (plus dense en bas de l'image)."""
    if amount <= 0:
        return fr
    w, h = fr.size
    tex = _fog_tex(w, h, seed)
    th, tw2 = tex.shape
    tw = tw2 // 2
    off = int(t * speed / 6) % tw
    m = tex[:, off:off + tw] * (0.35 + 0.65 * np.linspace(0, 1, th, dtype=np.float32) ** 0.8)[:, None] * amount
    mask = Image.fromarray(np.clip(m * 255, 0, 255).astype(np.uint8)).resize((w, h), Image.BILINEAR)
    avg = np.asarray(fr.resize((8, 8), Image.BOX), np.float32).reshape(-1, 3).mean(axis=0)
    col = tuple(int(c) for c in avg * 0.6 + np.array([110, 110, 135]) * 0.4)
    return Image.composite(Image.new("RGB", (w, h), col), fr, mask)


def weather(fr, kind, t, seed):
    """Pluie, neige ou cendres par-dessus l'image."""
    if kind not in ("pluie", "neige", "cendres"):
        return
    w, h = fr.size
    rnd = np.random.default_rng(seed)
    layer = Image.new("RGBA", (w, h), (0, 0, 0, 0))
    d = ImageDraw.Draw(layer)
    if kind == "pluie":
        n = 170
        x0, y0 = rnd.uniform(0, w, n), rnd.uniform(0, h, n)
        sp = rnd.uniform(1900, 2700, n)
        ln = rnd.uniform(40, 90, n)
        al = rnd.integers(50, 120, n)
        for i in range(n):
            y = (y0[i] + sp[i] * t) % (h + 100) - 50
            x = (x0[i] - 0.18 * sp[i] * t) % w
            d.line([(x, y), (x + ln[i] * 0.18, y + ln[i])], fill=(200, 210, 235, int(al[i])), width=2)
    else:
        n = 110 if kind == "neige" else 70
        x0, y0 = rnd.uniform(0, w, n), rnd.uniform(0, h, n)
        sp = rnd.uniform(60, 170, n) if kind == "neige" else rnd.uniform(-90, -30, n)
        r = rnd.uniform(3, 8, n)
        ph = rnd.uniform(0, 6.28, n)
        col = (240, 240, 255) if kind == "neige" else (255, 140, 60)
        for i in range(n):
            y = (y0[i] + sp[i] * t) % h
            x = (x0[i] + 30 * math.sin(t * 1.2 + ph[i])) % w
            d.ellipse([x - r[i], y - r[i], x + r[i], y + r[i]], fill=col + (170,))
        layer = layer.filter(ImageFilter.GaussianBlur(1.2))
    fr.paste(layer, (0, 0), layer)
