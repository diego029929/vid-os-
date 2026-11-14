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


# ---- 14/11 : animation plus vivante (Fio : « refais les séries avec de meilleures animations ») ----

def whip(fr, amount):
    """Transition « whip pan » : l'image arrive en glissant avec un flou de mouvement.
    amount = fraction de la largeur (signe = sens)."""
    if abs(amount) < 0.004:
        return fr
    w, h = fr.size
    a = np.asarray(fr, np.float32)
    shift = int(amount * w)
    acc = np.zeros_like(a)
    k = 7
    for j in range(k):
        acc += np.roll(a, int(shift * (0.4 + 0.6 * j / (k - 1))), axis=1)
    return Image.fromarray(np.clip(acc / k, 0, 255).astype(np.uint8))


def passant(fr, lt, dur, opt, seed):
    """Une silhouette sombre aux yeux rouges traverse le fond du plan.
    opt = true ou {"y": pied en fraction de hauteur, "h": taille, "sens": 1/-1, "yeux": true}."""
    o = opt if isinstance(opt, dict) else {}
    w, h = fr.size
    sens = o.get("sens", 1 if seed % 2 == 0 else -1)
    k = min(1.0, lt / max(0.5, dur * 1.1))
    x = (-0.15 + 1.3 * k) if sens > 0 else (1.15 - 1.3 * k)
    x *= w
    hh = o.get("h", 0.30) * h
    foot = o.get("y", 0.80) * h
    bob = abs(math.sin(lt * 5.5)) * hh * 0.025
    lay = Image.new("RGBA", (w, h), (0, 0, 0, 0))
    d = ImageDraw.Draw(lay)
    r = hh * 0.11
    top = foot - hh - bob
    col = (6, 5, 10, 235)
    d.ellipse([x - r, top, x + r, top + 2 * r], fill=col)
    sw = math.sin(lt * 5.5) * hh * 0.06
    d.polygon([(x - hh * 0.17, foot - hh * 0.45 - bob), (x - hh * 0.11, top + 1.8 * r), (x + hh * 0.11, top + 1.8 * r),
               (x + hh * 0.17, foot - hh * 0.45 - bob)], fill=col)
    for dx in (-1, 1):   # jambes qui marchent
        d.polygon([(x + dx * hh * 0.03, foot - hh * 0.46 - bob), (x + dx * hh * 0.12, foot - hh * 0.46 - bob),
                   (x + dx * sw + hh * 0.05, foot), (x + dx * sw - hh * 0.05, foot)], fill=col)
    lay = lay.filter(ImageFilter.GaussianBlur(max(1, hh * 0.008)))
    if o.get("yeux", True):
        d2 = ImageDraw.Draw(lay)
        e = r * 0.16
        for dx in (-0.35, 0.35):
            cx, cy = x + dx * r, top + r * 0.95
            d2.ellipse([cx - e, cy - e * 0.7, cx + e, cy + e * 0.7], fill=(255, 50, 40, 255))
    out = fr.convert("RGBA")
    out.alpha_composite(lay)
    return fr.paste(out.convert("RGB"))


def lightning(fr, lt, seed):
    """Éclair : deux flashs blancs bleutés rapides au début du plan, puis l'image retombe."""
    v = 0.0
    for t0, p in ((0.05, 0.85), (0.22, 0.55)):
        if t0 <= lt < t0 + 0.09:
            v = max(v, p * (1 - (lt - t0) / 0.09))
    if v <= 0:
        return fr
    a = np.asarray(fr, np.float32)
    a = a + (np.array([210, 225, 255], np.float32) - a) * v
    return Image.fromarray(np.clip(a, 0, 255).astype(np.uint8))
