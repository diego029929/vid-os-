"""Relief « 3D » pour les décors dessinés (demande de Fio, 09/11 : « fais les images en 3D,
il n'y a aucun relief »).

Tout est gratuit et tourne sur le CPU :
1. une carte de profondeur est estimée pour chaque décor par le petit modèle libre
   Depth Anything V2 Small (Hugging Face, licence Apache 2.0, ≈ 1 s par décor) ;
   s'il n'est pas disponible, on retombe sur une profondeur simple (bas = proche) ;
2. `sculpt` éclaire le décor comme un vrai volume : ombres de contact dans les coins,
   ombres portées des objets, arêtes éclairées côté lumière, brume au loin ;
3. `warp` déplace chaque pixel selon sa profondeur pendant le plan : le premier plan
   bouge plus que le fond (vraie parallaxe, effet « photo 3D »).
Le style dessiné est gardé : on n'ajoute aucune image générée.
"""
import os

import numpy as np
from PIL import Image, ImageFilter

_pipe = None
_warned = False


def _model():
    global _pipe, _warned
    if _pipe is None and os.environ.get("RELIEF_DEPTH", "model") == "model":
        try:
            from transformers import pipeline
            _pipe = pipeline("depth-estimation", model="depth-anything/Depth-Anything-V2-Small-hf", device="cpu")
        except Exception as e:  # pas de torch / pas de réseau : profondeur simple
            if not _warned:
                print(f"relief : modèle de profondeur indisponible ({type(e).__name__}), profondeur simple")
                _warned = True
            _pipe = False
    return _pipe or None


def depth(img):
    """Profondeur 0 (loin) .. 1 (proche), même taille que l'image, en float32."""
    w, h = img.size
    p = _model()
    if p is not None:
        d = np.asarray(p(img.convert("RGB"))["predicted_depth"], dtype=np.float32).squeeze()
        lo, hi = np.percentile(d, 1), np.percentile(d, 99)
        d = np.clip((d - lo) / max(1e-6, hi - lo), 0, 1)
        if d.shape != (h, w):
            d = np.asarray(Image.fromarray(d.astype(np.float32), "F").resize((w, h), Image.BILINEAR), np.float32)
    else:
        d = np.repeat(np.linspace(0, 1, h, dtype=np.float32)[:, None] ** 1.6, w, axis=1)
    # adoucit les marches entre deux plats (sinon la parallaxe « déchire » les bords)
    return _blur(d, max(2, w // 300))


def _box(a, r, axis):
    c = np.cumsum(np.pad(a, [(r + 1, r) if i == axis else (0, 0) for i in range(2)], mode="edge"), axis=axis)
    hi = np.take(c, np.arange(2 * r + 1, c.shape[axis]), axis=axis)
    lo = np.take(c, np.arange(0, c.shape[axis] - 2 * r - 1), axis=axis)
    return (hi - lo) / (2 * r + 1)


def _blur(a, r):
    """Flou gaussien approché (3 boîtes) en flottant : pas d'escaliers dans les dégradés."""
    r = max(1, int(round(r * 0.6)))
    for _ in range(3):
        a = _box(_box(a, r, 0), r, 1)
    return a.astype(np.float32)


def sculpt(img, d, light=(255, 170, 110), strength=1.5):
    """Donne du volume au décor à partir de sa profondeur `d`."""
    a = np.asarray(img.convert("RGB"), dtype=np.float32) / 255
    h, w = d.shape
    s = strength
    # 1. ombres de contact (occlusion) : un point plus loin que ses voisins est dans l'ombre
    ao = np.clip((_blur(d, w * 0.035) - d) * 4.0, 0, 1) + np.clip((_blur(d, w * 0.012) - d) * 5.0, 0, 1)
    shade = 1 - np.clip(ao * 0.5 * s, 0, 0.8)
    keep = np.clip((a.max(axis=2) - 0.5) / 0.25, 0, 1)   # lampes, lune, soleil gardent leur éclat
    # 2. ombres portées : un objet proche cache la lumière (venant d'en haut à gauche)
    ox, oy = int(w * 0.022), int(w * 0.03)
    sd = np.zeros_like(d)
    sd[oy:, ox:] = d[:-oy, :-ox]
    cast = _blur(np.clip((sd - d - 0.04) * 6, 0, 1), w * 0.012)
    shade *= 1 - np.clip(cast * 0.45 * s, 0, 0.75)
    # 3. arêtes et faces : éclairage depuis la pente de la profondeur
    ds = _blur(d, w * 0.004)
    gy, gx = np.gradient(ds * w * 0.06)
    nz = 1 / np.sqrt(gx * gx + gy * gy + 1)
    lam = (-gx * -0.55 + -gy * -0.65) * nz + nz * 0.52          # lumière en haut à gauche
    lit = np.clip(lam - 0.52, -0.6, 0.8)
    shade = shade * (1 - keep) + keep
    lit = lit * (1 - keep)
    col = np.array(light, np.float32) / 255
    rim = np.clip(lit, 0, None)[..., None] * (0.35 * s) * (0.5 + 0.5 * col)
    a = a * shade[..., None] * (1 + np.clip(lit, None, 0)[..., None] * 0.6 * s) + rim * (0.15 + a)
    # 4. profondeur de l'air : le loin est plus doux et brumeux, le proche plus contrasté
    far = (1 - d)[..., None]
    haze = a.reshape(-1, 3)[d.reshape(-1) < np.percentile(d, 15)].mean(axis=0) if (d < 0.3).any() else a.mean((0, 1))
    hz = far * 0.2 * min(s, 1.2) * (1 - keep[..., None])
    a = a * (1 - hz) + haze * hz
    m = a.mean(axis=2, keepdims=True)
    k3 = keep[..., None]
    a = m + (a - m) * (1 + (d[..., None] - 0.5) * 0.3 * s * (1 - k3))
    a = a * (0.95 + 0.12 * d[..., None] * (1 - k3) + 0.05 * k3)
    return Image.fromarray((np.clip(a, 0, 1) * 255).astype(np.uint8))


def warp(bg, d, box, out_size, shift, dolly, grid=(27, 48)):
    """Recadre `bg` sur `box` (x0, y0, x1, y1) vers `out_size` en déplaçant chaque point
    selon sa profondeur `d` : décalage `shift` (dx, dy, en pixels de sortie, pour le plus
    proche) et `dolly` (zoom en plus pour le proche). Maillage PIL (rapide, en C)."""
    W, H = out_size
    x0, y0, x1, y1 = box
    sx, sy = (x1 - x0) / W, (y1 - y0) / H
    gx, gy = grid
    us = np.linspace(0, W, gx + 1)
    vs = np.linspace(0, H, gy + 1)
    bh, bw = d.shape
    # profondeur aux nœuds du maillage (prise à l'endroit d'origine du nœud)
    ix = np.clip((x0 + us * sx).astype(int), 0, bw - 1)
    iy = np.clip((y0 + vs * sy).astype(int), 0, bh - 1)
    k = d[iy][:, ix] - 0.35                      # le fond lointain reste presque fixe
    f = 1 / (1 + dolly * k)
    X = x0 + (W / 2 + (us[None, :] - W / 2) * f - shift[0] * k) * sx
    Y = y0 + (H / 2 + (vs[:, None] - H / 2) * f - shift[1] * k) * sy
    mesh = []
    for j in range(gy):
        for i in range(gx):
            mesh.append(((int(us[i]), int(vs[j]), int(us[i + 1]), int(vs[j + 1])),
                         (X[j, i], Y[j, i], X[j + 1, i], Y[j + 1, i],
                          X[j + 1, i + 1], Y[j + 1, i + 1], X[j, i + 1], Y[j, i + 1])))
    return bg.transform((W, H), Image.MESH, mesh, Image.BILINEAR)


def volume(hc, side=-1, color=(255, 170, 110)):
    """Personnage en volume : chaque partie (tête, sweat) est bombée comme un objet rond,
    éclairée du côté de la lumière, avec un reflet sur la tête et de l'ombre dans les creux."""
    a = np.asarray(hc, dtype=np.float32) / 255
    h, w = a.shape[:2]
    if w < 8 or h < 8:
        return hc
    al = a[..., 3]
    rgb = a[..., :3]
    cloth = ((rgb.max(axis=2) - rgb.min(axis=2)) > 0.15).astype(np.float32) * (al > 0.5)
    head = (al > 0.5) * (1 - cloth)
    r = max(3, w * 0.12)
    # hauteur : bombé dans chaque partie (fort au centre, nul au bord)
    hgt = np.sqrt(np.clip(_blur(cloth, r) * cloth, 0, 1)) * 0.8 + np.sqrt(np.clip(_blur(head, r * 1.3) * head, 0, 1))
    hgt = _blur(hgt, max(1, w * 0.006))
    gy, gx = np.gradient(hgt * w * 0.02)
    # la tête est une boule : normales de sphère exactes (centre et rayon de la tête)
    f8 = 8
    sm = np.asarray(Image.fromarray((head * 255).astype(np.uint8)).resize((max(1, w // f8), max(1, h // f8)), Image.BOX),
                    np.float32) / 255 > 0.9                 # sans les bras/jambes fins
    if sm.sum() > 8:
        ys, xs = np.nonzero(sm)
        cx, cy = (xs.mean() + 0.5) * w / sm.shape[1], (ys.mean() + 0.5) * h / sm.shape[0]
        rr = np.sqrt(sm.sum() / np.pi) * (w / sm.shape[1]) * 1.05
        yy, xx = np.mgrid[0:h, 0:w].astype(np.float32)
        nx, ny = (xx - cx) / rr, (yy - cy) / rr
        ball = head * (nx * nx + ny * ny < 1.1)
        hz = np.sqrt(np.clip(1 - nx * nx - ny * ny, 0.02, 1))
        gx = np.where(ball > 0, -nx / hz, gx)
        gy = np.where(ball > 0, -ny / hz, gy)
    nz = 1 / np.sqrt(gx * gx + gy * gy + 1)
    lx, ly, lz = 0.55 * side, -0.55, 0.63
    lam = np.clip((-gx * lx - gy * ly + lz) * nz, 0, 1)        # face tournée vers la lumière
    diff = 0.4 + 0.9 * lam ** 1.5
    # reflet : point brillant (tête en plastique/peinture brillante)
    rx, ry, rz = lx, ly, lz + 1
    n = np.sqrt(rx * rx + ry * ry + rz * rz)
    spec = np.clip((-gx * rx - gy * ry + rz) * nz / n, 0, 1) ** 34
    col = np.array(color, np.float32) / 255
    out = rgb * diff[..., None] + (spec * (0.6 * head + 0.25 * cloth))[..., None] * (0.6 + 0.4 * col)
    # liseré de lumière sur la tête noire côté lampe, ombre interne côté opposé
    out += (head * 0.16 * lam ** 4)[..., None] * (0.4 + 0.6 * col)
    res = np.concatenate([np.clip(out, 0, 1), al[..., None]], axis=2)
    return Image.fromarray((res * 255).astype(np.uint8), "RGBA")
