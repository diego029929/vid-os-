"""Son d'edit gratuit fait maison (style phonk / drift) : 808 qui glisse, cloche (cowbell), charleston, clap.
100 % synthétisé par le code → aucun droit d'auteur. Utilisé par engine/edit.py (clips GTA 6, 19/11).

Usage : python3 engine/beat.py OUT.wav [--bpm 130] [--mesures 10] [--graine 1]
Structure : 2 mesures d'intro (cloche seule + filtre), puis le « drop » (tout), dernière mesure = coupure.
"""
import sys
import wave

import numpy as np

SR = 44100


def _env(n, a=0.002, d=0.2):
    t = np.arange(n) / SR
    return np.minimum(1, t / a) * np.exp(-t / d)


def kick(n):
    t = np.arange(n) / SR
    f = 50 + 120 * np.exp(-t * 35)
    return np.sin(2 * np.pi * np.cumsum(f) / SR) * _env(n, 0.001, 0.25)


def b808(n, f0, f1=None):
    """Basse 808 qui glisse de f0 vers f1, saturée."""
    t = np.arange(n) / SR
    f = f0 if f1 is None else f1 + (f0 - f1) * np.exp(-t * 6)
    x = np.sin(2 * np.pi * np.cumsum(np.full(n, 1.0) * f) / SR)
    return np.tanh(2.5 * x) * _env(n, 0.003, 0.9) * 0.8


def cowbell(n, f):
    t = np.arange(n) / SR
    x = np.sign(np.sin(2 * np.pi * f * t)) * 0.5 + np.sign(np.sin(2 * np.pi * f * 1.48 * t)) * 0.5
    x = np.convolve(x, np.ones(6) / 6, mode="same")  # adoucit
    return x * _env(n, 0.001, 0.12) * 0.35


def hat(n, rng, d=0.03):
    x = rng.standard_normal(n)
    x = np.diff(np.concatenate([[0], x]))  # aigu
    return x * _env(n, 0.0005, d) * 0.12


def clap(n, rng):
    x = rng.standard_normal(n)
    e = np.zeros(n)
    for k in (0, 0.01, 0.02):
        i = int(k * SR)
        e[i:] += _env(n - i, 0.0005, 0.08 if k == 0.02 else 0.01)
    return np.convolve(x, [1, -0.6], mode="same") * e * 0.35


def make(bpm=130, mesures=10, graine=1):
    rng = np.random.default_rng(graine)
    beat = 60 / bpm
    s16 = beat / 4
    n = int(mesures * 4 * beat * SR) + SR
    out = np.zeros(n)

    def add(x, t, g=1.0):
        i = int(t * SR)
        j = min(n, i + len(x))
        out[i:j] += g * x[: j - i]

    # mélodie de cloche (notes en Hz, 16 doubles-croches par mesure, 0 = silence), mineur, typique phonk
    A, C, D, E, G = 440.0, 523.3, 587.3, 659.3, 784.0
    mel = [A, 0, A, C, 0, A, D, 0, C, 0, A, 0, G / 2, 0, A, 0,
           A, 0, A, C, 0, A, E, 0, D, 0, C, 0, A, 0, 0, 0]
    bass = [(0, 55.0, None, 6), (6, 55.0, 41.2, 4), (10, 65.4, None, 6)]  # (pas, f0, glisse vers, durée en pas)
    for m in range(mesures):
        t0 = m * 4 * beat
        drop = m >= 2
        last = m == mesures - 1
        for k in range(16):
            f = mel[(m % 2) * 16 + k]
            if f and not (last and k >= 8):
                add(cowbell(int(0.2 * SR), f), t0 + k * s16, 1.0 if drop else 0.7)
        if not drop:
            # intro : charleston léger + montée
            for k in range(0, 16, 2):
                add(hat(int(0.05 * SR), rng), t0 + k * s16, 0.6 + 0.4 * m)
            if m == 1:
                for k in range(8):
                    add(clap(int(0.12 * SR), rng), t0 + 2 * beat + k * s16 / 1, 0.3 + k * 0.1)
            continue
        if last:
            add(kick(int(0.4 * SR)), t0)
            add(b808(int(1.5 * SR), 55.0, 41.2), t0)
            continue
        for k in (0, 6, 10):  # grosse caisse
            add(kick(int(0.4 * SR)), t0 + k * s16)
        for st, f0, f1, d in bass:
            add(b808(int(d * s16 * SR), f0, f1), t0 + st * s16)
        for k in (4, 12):  # clap
            add(clap(int(0.15 * SR), rng), t0 + k * s16)
        for k in range(16):  # charleston, avec roulements
            add(hat(int(0.04 * SR), rng), t0 + k * s16, 1.0 if k % 2 == 0 else 0.6)
            if k in (14, 15) and m % 2:
                for r in range(3):
                    add(hat(int(0.02 * SR), rng, 0.01), t0 + k * s16 + r * s16 / 3, 0.7)
    out = np.tanh(out * 1.2)
    out = out / (np.abs(out).max() + 1e-9) * 0.89
    return out[: int(mesures * 4 * beat * SR + 1.0 * SR)].astype(np.float32)


def write(path, x):
    st = np.repeat((np.clip(x, -1, 1) * 32767).astype(np.int16)[:, None], 2, axis=1)
    with wave.open(path, "wb") as w:
        w.setnchannels(2)
        w.setsampwidth(2)
        w.setframerate(SR)
        w.writeframes(st.tobytes())


if __name__ == "__main__":
    a = sys.argv[1:]
    opt = lambda k, d: type(d)(a[a.index(k) + 1]) if k in a else d
    write(a[0], make(opt("--bpm", 130), opt("--mesures", 10), opt("--graine", 1)))
    print("OK", a[0])
