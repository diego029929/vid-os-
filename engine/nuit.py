"""Style « Nuit & téléphone » (choisi par Fio le 15/11) : dessin plat 2D de nuit, perso à capuche,
écrans de téléphone redessinés, horloge en haut, cartes de règle, choix final, sous-titres karaoké.

Une seule commande fait tout : voix (Chatterbox, voix de la routine), calage des sous-titres (Whisper
small), bruitages, dessin (engine/nuit.js filmé par Playwright) et MP4 final.

Usage : python3 engine/nuit.py episodes/<f>.json OUT.mp4 [--brouillon]
  --brouillon : pas de voix (durée estimée), 10 images/s → planche rapide pour vérifier le dessin.
Format du JSON : voir ROUTINE.md § « Style Nuit & téléphone ».
"""
import json
import os
import re
import subprocess
import sys
import tempfile
import unicodedata

import numpy as np

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(HERE)
FONT = os.path.join(ROOT, "assets", "fonts", "Anton-Regular.ttf")
W, H = 1080, 1920
GAP = 0.25          # silence entre deux plans
END_HOLD = 1.6      # le choix final reste un peu à l'écran

CSS = """@font-face{font-family:Anton;src:url('file://FONTPATH')}
*{margin:0;padding:0;box-sizing:border-box}
html,body{width:1080px;height:1920px;overflow:hidden;background:#0b0a22;font-family:-apple-system,'Inter','Helvetica Neue',Arial,sans-serif}
#cam{position:absolute;inset:0}
.layer{position:absolute;inset:0}
#clock{position:absolute;top:70px;left:0;right:0;text-align:center;color:#fff;z-index:20}
#clock .lieu{font-size:26px;letter-spacing:4px;font-weight:700;opacity:.85}
#clock .lieu b{color:#ff3b3b;font-size:30px}
#clock .t{text-shadow:0 0 18px #000,0 0 6px #000;font-size:76px;font-weight:800;letter-spacing:2px;font-variant-numeric:tabular-nums;margin-top:6px}
#sub{position:absolute;left:40px;right:40px;top:1590px;text-align:center;font-family:Anton;font-size:124px;color:#fff;
  -webkit-text-stroke:8px #000;paint-order:stroke fill;text-shadow:0 8px 0 rgba(0,0,0,.6);z-index:30;line-height:1.05;text-transform:uppercase}
#sub .r{color:#ff3b3b}#sub .y{color:#ffd23b}
.phone{position:absolute;left:250px;top:330px;width:580px;height:1180px;border-radius:90px;background:#111427;border:14px solid #2b2f45;
  box-shadow:0 0 120px rgba(80,120,255,.25),0 30px 80px rgba(0,0,0,.7)}
.phone .scr{position:absolute;inset:18px;border-radius:70px;overflow:hidden;background:linear-gradient(#1d2b5a,#101a3c)}
.phone .isl{position:absolute;top:26px;left:50%;transform:translateX(-50%);width:170px;height:46px;border-radius:30px;background:#000;z-index:3}
.phone .sb{position:absolute;top:34px;left:56px;right:56px;display:flex;justify-content:space-between;color:#fff;font-size:28px;font-weight:700;z-index:2}
.btn{position:absolute;width:150px;height:150px;border-radius:50%;display:flex;align-items:center;justify-content:center;color:#fff;font-size:64px}
.bubble{position:absolute;max-width:430px;padding:24px 30px;border-radius:38px;color:#fff;font-size:36px;line-height:1.25}
.card{position:absolute;inset:0;background:radial-gradient(circle at 50% 45%,#5a0b10 0%,#1a0306 55%,#070102 100%)}
.choice{position:absolute;left:110px;right:110px;min-height:150px;padding:10px 30px;border-radius:80px;display:flex;align-items:center;justify-content:center;
  font-family:Anton;font-size:66px;color:#fff;text-transform:uppercase;text-align:center;line-height:1.05}
"""


def strip_marks(s):
    return re.sub(r"[*#]", "", s)


def norm(w):
    w = unicodedata.normalize("NFD", w.lower())
    return re.sub(r"[^a-z0-9]", "", "".join(c for c in w if unicodedata.category(c) != "Mn"))


NUM = {"un": "1", "une": "1", "deux": "2", "trois": "3", "quatre": "4", "cinq": "5", "six": "6", "sept": "7",
       "huit": "8", "neuf": "9", "dix": "10"}


def script_words(text):
    """Mots du sous-titre avec leur couleur : *mot* = rouge, #mot# = jaune (plusieurs mots possibles)."""
    out, color = [], ""
    for tok in re.findall(r"[*#]|[^\s*#]+", text):
        if tok in "*#":
            color = "" if color else ("r" if tok == "*" else "y")
            continue
        if out and tok in ".,!?:;…":  # ponctuation isolée : collée au mot d'avant
            out[-1][0] += tok
            continue
        out.append([tok, color])
    return out


def align(script, heard, t0, t1):
    """Cale les mots du script sur les mots entendus par Whisper (dans [t0, t1])."""
    import difflib
    a = [NUM.get(norm(w), norm(w)) for w, _ in script]
    b = [NUM.get(norm(w), norm(w)) for _, _, w in heard]
    times = [None] * len(script)
    for blk in difflib.SequenceMatcher(None, a, b, autojunk=False).get_matching_blocks():
        for k in range(blk.size):
            times[blk.a + k] = (heard[blk.b + k][0], heard[blk.b + k][1])
    n, i = len(script), 0
    while i < n:  # mots non reconnus : répartis entre les voisins, au prorata des lettres
        if times[i] is not None:
            i += 1
            continue
        j = i
        while j < n and times[j] is None:
            j += 1
        a0 = times[i - 1][1] if i > 0 else t0
        a1 = times[j][0] if j < n else t1
        lens = [max(1, len(script[k][0])) for k in range(i, j)]
        tot, acc = sum(lens), a0
        for k, ln in zip(range(i, j), lens):
            d = max(0.05, (a1 - a0)) * ln / tot
            times[k] = (acc, acc + d)
            acc += d
        i = j
    return [[round(s, 3), round(e, 3), w, c] for (w, c), (s, e) in zip(script, times)]


SFX = {  # bruitages synthétisés (gratuit) : expression ffmpeg aevalsrc, durée
    "vibre": ("0.35*sin(2*PI*150*t)*lt(mod(t\\,0.5)\\,0.3)", 1.5),
    "sonnerie": ("0.18*(sin(2*PI*880*t)+sin(2*PI*1320*t))*lt(mod(t\\,0.6)\\,0.3)", 1.8),
    "toc": ("0.9*sin(2*PI*85*t)*exp(-28*mod(t\\,0.32))*lt(t\\,0.96)", 1.0),
    "boom": ("0.9*sin(2*PI*48*t)*exp(-2.5*t)", 1.8),
    "message": ("0.25*sin(2*PI*1200*t)*exp(-12*t)", 0.5),
    "souffle": ("0.4*(random(0)-0.5)*sin(PI*t/1.2)", 1.2),
}


def sfx_wav(name, path):
    expr, d = SFX[name]
    subprocess.run(["ffmpeg", "-y", "-loglevel", "error", "-f", "lavfi", "-i", f"aevalsrc={expr}:s=44100:d={d}",
                    "-af", "lowpass=f=2500" if name == "souffle" else "anull", path], check=True)


def build(ep_path, out, draft=False):
    ep = json.load(open(ep_path))
    beats = ep["beats"]
    tmp = tempfile.mkdtemp()
    sys.path.insert(0, HERE)
    sr = 44100
    voice_track = None
    if draft:
        durs = [max(1.2, len(strip_marks(b["voice"])) / 20) for b in beats]
    else:
        import voice
        default_ref = voice.CB_REF
        parts, durs = [], []
        for b in beats:
            who = b.get("qui")
            info = ep.get("hero", {}) if who == "MOI" else ep.get("persos", {}).get(who, {}) if who else {}
            voice.CB_REF = os.path.join(ROOT, "assets", "ref", info["voix"]) if info.get("voix") else default_ref
            voice.RETRY = b.get("retry", 0)
            a = voice.synth(strip_marks(b["voice"]))
            parts += [a, np.zeros(int(GAP * voice.SR), np.float32)]
            durs.append(len(a) / voice.SR + GAP)
            print(f"voix {len(durs)}/{len(beats)} : {strip_marks(b['voice'])}", flush=True)
        voice.CB_REF = default_ref
        sr = voice.SR
        voice_track = np.concatenate(parts + [np.zeros(int(END_HOLD * sr), np.float32)])
    durs[-1] += END_HOLD
    starts = np.concatenate([[0], np.cumsum(durs)])
    total = float(starts[-1])

    heard = []
    if voice_track is not None:
        vpath = os.path.join(tmp, "voix.wav")
        voice.write_wav(vpath, voice_track)
        try:
            import whisper
            m = whisper.load_model("small")
            r = m.transcribe(vpath, language="fr", word_timestamps=True)
            heard = [[x["start"], x["end"], x["word"].strip()] for s in r["segments"] for x in s["words"]]
            del m
        except Exception as e:  # pas de Whisper : répartition au prorata
            print("Whisper indisponible, sous-titres au prorata :", e)
    words = []
    for k, b in enumerate(beats):
        t0 = float(starts[k])
        t1 = float(starts[k + 1]) - (GAP if k + 1 < len(beats) else END_HOLD + GAP)
        h = [w for w in heard if t0 - 0.3 <= w[0] < t1 + 0.1]
        words += align(script_words(b["voice"]), h, t0, t1)

    fps = 10 if draft else 30
    n = int(total * fps)
    if voice_track is not None:  # bouche : volume de la voix à chaque image
        hop = sr // fps
        amp = [float(np.sqrt(np.mean(voice_track[i * hop:(i + 1) * hop] ** 2) + 1e-12)) for i in range(n)]
        mx = max(amp) or 1
        amp = [round(min(1.0, a / mx * 1.6), 3) for a in amp]
    else:
        amp = [round(0.5 * (1 + float(np.sin(i))), 3) for i in range(n)]

    # bruitages : "sfx": "toc" ou ["toc", 0.4] (décalage en s) ; par défaut règle = boom, sms = message, appel = sonnerie
    mix = []
    for k, b in enumerate(beats):
        fx = b.get("sfx")
        tel = (b.get("tel") or {}).get("type")
        if fx is None:
            fx = "boom" if b.get("regle") else "message" if tel == "sms" else "sonnerie" if tel == "appel" else \
                "vibre" if b.get("hero") == "sonne" else None
        if fx:
            name, dt = (fx, 0.0) if isinstance(fx, str) else (fx[0], float(fx[1]))
            p = os.path.join(tmp, f"fx{k}.wav")
            sfx_wav(name, p)
            mix.append((p, float(starts[k]) + dt))

    data = {"EP": {k: v for k, v in ep.items() if k != "beats"},
            "BEATS": [dict(b, t0=float(starts[k]), t1=float(starts[k + 1])) for k, b in enumerate(beats)],
            "WORDS": words, "AMP": amp, "FPS": fps}
    page = os.path.join(tmp, "page.html")
    js = open(os.path.join(HERE, "nuit.js")).read()
    with open(page, "w") as f:
        f.write(f"<!doctype html><html><head><meta charset='utf-8'><style>{CSS.replace('FONTPATH', FONT)}</style></head><body>"
                "<div id='cam'></div><div id='clock'><div class='lieu'><b>●</b> <span id='etiq'></span> · <span id='lieu'></span></div>"
                "<div class='t' id='tm'></div></div><div id='sub'></div><script>"
                + "".join(f"const {k} = {json.dumps(v, ensure_ascii=False)};\n" for k, v in data.items())
                + js + "</script></body></html>")

    # audio : voix + nappe sombre + bruitages, -14 LUFS, crête < -2 dB
    audio = os.path.join(tmp, "mix.wav")
    ins = ["-f", "lavfi", "-i", f"anoisesrc=color=brown:amplitude=0.5:d={total:.2f}:r=44100"]
    ins += ["-i", vpath] if voice_track is not None else ["-f", "lavfi", "-i", f"anullsrc=r=44100:cl=mono:d={total:.2f}"]
    fl = ["[0:a]lowpass=f=180,volume=0.12[bed]", "[1:a]aresample=44100[v]"]
    labels = ["[bed]", "[v]"]
    for i, (p, at) in enumerate(mix):
        ins += ["-i", p]
        ms = int(at * 1000)
        fl.append(f"[{i + 2}:a]adelay={ms}|{ms},volume=0.8[f{i}]")
        labels.append(f"[f{i}]")
    fl.append("".join(labels) + f"amix=inputs={len(labels)}:normalize=0:duration=first,"
              "loudnorm=I=-14:TP=-2:LRA=11,aresample=44100,alimiter=limit=0.7:level=false[a]")
    subprocess.run(["ffmpeg", "-y", "-loglevel", "error", *ins, "-filter_complex", ";".join(fl), "-map", "[a]",
                    "-t", f"{total:.2f}", audio], check=True)

    from playwright.sync_api import sync_playwright
    ff = subprocess.Popen(["ffmpeg", "-y", "-loglevel", "error", "-f", "image2pipe", "-framerate", str(fps), "-i", "-", "-i", audio,
                           "-map", "0:v", "-map", "1:a", "-c:v", "libx264", "-crf", "18", "-preset", "medium", "-pix_fmt", "yuv420p",
                           "-r", "30", "-c:a", "aac", "-b:a", "192k", "-shortest", "-movflags", "+faststart", out], stdin=subprocess.PIPE)
    with sync_playwright() as p:
        exe = os.environ.get("CHROME", "/opt/pw-browsers/chromium")
        b = p.chromium.launch(executable_path=exe if os.path.isfile(exe) else None, args=["--no-sandbox"])
        pg = b.new_page(viewport={"width": W, "height": H})
        errs = []
        pg.on("pageerror", lambda e: errs.append(str(e)))
        pg.goto("file://" + page)
        pg.wait_for_timeout(400)
        for i in range(n):
            pg.evaluate(f"seek({i / fps})")
            ff.stdin.write(pg.screenshot(type="jpeg", quality=92))
            if errs:
                raise RuntimeError("erreur de dessin : " + errs[0])
            if i % (fps * 5) == 0:
                print(f"image {i}/{n}", flush=True)
        b.close()
    ff.stdin.close()
    ff.wait()
    print(f"OK {out} ({total:.1f} s)")
    return total


if __name__ == "__main__":
    args = [a for a in sys.argv[1:] if not a.startswith("--")]
    build(args[0], args[1], draft="--brouillon" in sys.argv)
