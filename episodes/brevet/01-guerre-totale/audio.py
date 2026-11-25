# Musique + bruitages (tout synthétisé en code, rien à télécharger) + mixage avec la voix.
# Les repères viennent de web/words.js (écrit par voix.py) : rien à recaler à la main.
import json, re, unicodedata
import numpy as np, soundfile as sf
from scipy import signal

SR = 44100
js = open('web/words.js').read()
WORDS = json.loads(re.search(r'const WORDS=(.*?);\n', js).group(1))
LINES = json.loads(re.search(r'const LINES=(.*?);\n', js).group(1))
VO_END = float(re.search(r'const VO_END=([\d.]+)', js).group(1))
DUR = VO_END + 1.2
N = int(DUR * SR)
START = [0] + [l[0] - .06 for l in LINES[1:]]
nrm = lambda s: re.sub(r'[^a-z0-9]', '', unicodedata.normalize('NFD', s.lower()).encode('ascii', 'ignore').decode())
def at(li, m, k=0):
    c = [w for w in WORDS if w['line'] == li and nrm(w['w']).startswith(nrm(m))]
    return c[min(k, len(c) - 1)]['s'] if c else START[li]

rng = np.random.default_rng(3)
T = lambda n: np.arange(n) / SR
def place(buf, x, at_s, g=1.0):
    i = int(at_s * SR); j = min(len(buf), i + len(x))
    if 0 <= i < len(buf): buf[i:j] += x[:j - i] * g
def bp(x, lo, hi): b, a = signal.butter(2, [lo / (SR / 2), min(hi / (SR / 2), .99)], 'band'); return signal.lfilter(b, a, x)
def lp(x, f): b, a = signal.butter(2, f / (SR / 2), 'low'); return signal.lfilter(b, a, x)
def hp(x, f): b, a = signal.butter(2, f / (SR / 2), 'high'); return signal.lfilter(b, a, x)
midi = lambda m: 440 * 2 ** ((m - 69) / 12)

# ---------------- bruitages ----------------
def whoosh(dur=.35):
    n = int(dur * SR); x = rng.standard_normal(n); k = np.linspace(0, 1, n)
    return (bp(x, 250, 1200) * (1 - k) + bp(x, 1500, 6000) * k) * np.sin(np.pi * k) ** 1.5 * 1.6
def thud(f0=70, dur=.35, g=1):
    n = int(dur * SR); t = T(n); f = f0 * (1 + 1.5 * np.exp(-t * 30))
    return (np.sin(2 * np.pi * np.cumsum(f) / SR) * np.exp(-t * 12) + lp(rng.standard_normal(n), 900) * np.exp(-t * 40) * .6) * g
def stamp(): return thud(60, .5, 1) + hp(rng.standard_normal(int(.5 * SR)), 1500) * np.exp(-T(int(.5 * SR)) * 50) * .5
def pop(f=600):
    n = int(.12 * SR); t = T(n); return np.sin(2 * np.pi * np.cumsum(f * (1 + 20 * t)) / SR) * np.exp(-t * 40)
def chime(f=1760, dur=.8):
    n = int(dur * SR); t = T(n)
    return (np.sin(2 * np.pi * f * t) + .5 * np.sin(2 * np.pi * f * 2.01 * t)) * np.exp(-t * 6) * np.minimum(1, t / .003) * .5
def clank(f0=300):
    n = int(.4 * SR); t = T(n); x = sum(a * np.sin(2 * np.pi * f0 * r * t) * np.exp(-t * d) for r, a, d in [(1, 1, 14), (2.7, .6, 18), (5.2, .3, 25)])
    return x * .5 + hp(rng.standard_normal(n), 2500) * np.exp(-t * 80) * .4
def paper():
    n = int(.45 * SR); t = T(n); return bp(rng.standard_normal(n), 2000, 8000) * (0.4 + .6 * np.abs(np.sin(2 * np.pi * 14 * t))) * np.sin(np.pi * t / .45) * .6
def horn(dur=1.1):
    n = int(dur * SR); t = T(n); ph = np.cumsum(np.full(n, 98.0)) / SR
    x = lp((2 * (ph % 1) - 1) + .6 * (2 * ((ph * 1.5) % 1) - 1), 700)
    return x * np.minimum(1, t / .08) * np.minimum(1, (dur - t) / .2) * .5
def rain_bed(dur):
    n = int(dur * SR); return lp(hp(rng.standard_normal(n), 1200), 7000) * .12
def tick():
    n = int(.04 * SR); t = T(n); return hp(rng.standard_normal(n), 3000) * np.exp(-t * 200) * .8

sfx = np.zeros(N)
for i in range(1, len(LINES)):
    if i not in (7, 8, 10): place(sfx, whoosh(.36), START[i] - .22, .32)
# 0 accroche
place(sfx, rain_bed(START[1]), 0, .9)
place(sfx, pop(520), .15, .3); place(sfx, pop(640), .45, .3)
place(sfx, stamp(), at(0, 'guerre', 1), .8)
# 1 on recule
place(sfx, whoosh(.9), at(1, 'seulement') - .2, .3)
for d in (0, .15, .3): place(sfx, pop(700 + d * 600), at(1, 'seulement') + d, .3)
# 2 tranchées
place(sfx, rain_bed(START[3] - START[2]), START[2], 1.0)
place(sfx, thud(80, .3, .7), at(2, '1914')); place(sfx, pop(600), at(2, 'millions'), .35)
# 3 l'arrière
place(sfx, pop(560), at(3, 'pays'), .4)
# 4 usine
for k in range(int((START[5] - START[4]) / .5)): place(sfx, clank(280 + (k % 3) * 40), START[4] + .2 + k * .5, .22)
place(sfx, pop(620), at(4, 'jour'), .35); place(sfx, chime(990, .9), at(4, 'nuit'), .3)
# 5 munitionnettes
place(sfx, pop(560), at(5, 'remplacent'), .4)
for k in range(5): place(sfx, tick(), at(5, 'femmes') + k * .18, .3)
# 6 journal + affiche
place(sfx, paper(), START[6] + .02, .6); place(sfx, stamp(), at(6, 'censures'), .8)
place(sfx, paper(), at(6, 'propagande') - .15, .6)
for d in (0, .08, .16): place(sfx, chime(2093 + d * 4000, .5), at(6, 'victoire') + d, .25)
# 7 bateau
place(sfx, horn(), START[7] + .3, .55)
# 8 bilan : un seul coup sourd, pas d'effet
place(sfx, thud(45, .9, 1), START[8] + .05, .55)
# 9 récap
for i in range(6): place(sfx, pop(500 + i * 90), START[9] + .3 + i * max(1.5, LINES[9][1] - START[9] - .3) / 6, .35)
# 10 fin
place(sfx, chime(1320, .7), at(10, 'oui'), .35); place(sfx, chime(1046, .7), at(10, 'non'), .35)

# ---------------- musique : pulsation douce de cordes (ré mineur), plus claire au récap ----------------
def pluck(f, dur=.5):
    n = int(dur * SR); t = T(n)
    x = sum(np.sin(2 * np.pi * f * h * t) * np.exp(-t * (6 + 4 * h)) / h for h in (1, 2, 3, 4))
    return bp(x, 120, 3500) * np.minimum(1, t / .003)
def strings(ms, dur, g=1.0):
    n = int(dur * SR); t = T(n); x = np.zeros(n)
    for m in ms:
        for d in (-.004, 0, .005):
            ph = np.cumsum(midi(m) * (1 + d) * (1 + .003 * np.sin(2 * np.pi * 5 * t))) / SR; x += 2 * (ph % 1) - 1
    return lp(x / (len(ms) * 3), 1100) * np.minimum(1, t / .5) * np.minimum(1, np.maximum(0, dur - t) / .5) * g
BEAT = 60 / 96
DM = [(38, (62, 65, 69)), (34, (62, 65, 70)), (36, (60, 64, 67)), (33, (61, 64, 69))]   # Dm Bb C A
DMAJ = [(38, (62, 66, 69)), (43, (62, 67, 71)), (45, (61, 64, 69)), (38, (62, 66, 69))]  # D G A D
music = np.zeros(N)
def bed(t0, t1, prog, g=1.0, pulse=True):
    t, bar = t0, 0
    while t < t1 - .1:
        root, ch = prog[bar % 4]; L = min(4 * BEAT, t1 - t)
        place(music, strings(ch, L + .3, .5), t, g); place(music, strings((root + 12,), L + .3, .35), t, g)
        if pulse:
            for b in range(4):
                if t + b * BEAT < t1: place(music, pluck(midi(root + 12 + (7 if b % 2 else 0)), .4), t + b * BEAT, g * .6)
        t += 4 * BEAT; bar += 1
bed(0, START[8], DM, 1.0)
place(music, strings((50, 57, 62), START[9] - START[8] + .4, .45), START[8])   # bilan : nappe seule
bed(START[9], DUR, DMAJ, 1.0)
music = lp(music, 6000)

# ---------------- voix + mixage ----------------
vo, vsr = sf.read('audio/vo.wav')
if vo.ndim > 1: vo = vo.mean(1)
if vsr != SR: vo = signal.resample_poly(vo, SR, vsr)
vo = hp(vo, 90); vo = vo / (np.max(np.abs(vo)) + 1e-9) * .9
VO = np.zeros(N); VO[:min(N, len(vo))] = vo[:N]
venv = lp(np.abs(VO), 6); duck = 1 - .6 * np.clip(venv / .05, 0, 1)
mix = VO + music * .2 * duck + sfx * .6
fade = np.ones(N); fl = int(.6 * SR); fade[-fl:] = np.linspace(1, 0, fl); mix *= fade
mix = mix / (np.max(np.abs(mix)) + 1e-9) * .89
sf.write('audio/mix.wav', np.stack([mix, mix], 1), SR)
print('mix ok', round(DUR, 2), 's')
