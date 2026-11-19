"""« Edit » TikTok (19/11, clips GTA 6) : vraies images officielles coupées sur le beat, zooms, flashs, sans voix.

Usage : python3 engine/edit.py episodes/<f>.json OUT.mp4
JSON :
  "source": "chemin/vers/video.mp4" (vidéo officielle téléchargée, voir ROUTINE.md § 1 ter)
  "bandes": 0.0556                 → coupe les bandes noires (ici 120 px en haut et en bas d'une source 2160p)
  "bpm": 130, "graine": 1          → son d'edit fait maison (engine/beat.py), longueur = durée des plans
  "plans": [{"t": 12.3, "temps": 2, "x": 0.5, "flash": true, "lent": false}, ...]
     t = début dans la source (s), temps = durée en temps du beat (1 = une noire), x = cadrage 9:16 (0 gauche → 1 droite),
     flash = éclair blanc à la coupe, entier = image entière sur fond flou (logo), lent = ralenti ×0.5 (prend 2× moins de source)
     ou {"image": "chemin.jpg", "temps": 2, "x": 0.5} pour une capture officielle (zoom lent)
  "textes": [{"de": 0, "a": 8, "txt": "GTA 6 EST SORTI", "couleur": "#ffffff"}]  (de / a en temps du beat)
Les 2 premières mesures (8 temps) sont l'intro du beat ; le « drop » arrive au temps 8 : y mettre un flash.
"""
import json
import os
import subprocess
import sys
import tempfile

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(HERE)
FONT = os.path.join(ROOT, "assets", "fonts", "Anton-Regular.ttf")
W, H, FPS = 1080, 1920, 30


def run(cmd):
    subprocess.run(cmd, check=True)


def plan(p, beat, out, base_dir):
    dur = p["temps"] * beat
    x = p.get("x", 0.5)
    punch = f"(1+{p.get('punch', 0.12)}*exp(-t*9))"
    crop = f"crop={W}:{H}:(iw-{W})*{x}:(ih-{H})/2"
    fx = []
    if p.get("flash"):
        fx.append("fade=t=in:st=0:d=0.18:color=white")
    if p.get("noir_fin"):
        fx.append(f"fade=t=out:st={dur - 0.5:.3f}:d=0.5")
    look = "eq=contrast=1.08:saturation=1.15"
    if "image" in p:
        img = p["image"] if os.path.isabs(p["image"]) else os.path.join(base_dir, p["image"])
        z = f"(1.05+0.08*t/{dur:.3f})"
        vf = f"scale=w=-2:h='{H}*{z}':eval=frame,{crop},{look}," + ",".join(fx + ["format=yuv420p"])
        run(["ffmpeg", "-loglevel", "error", "-y", "-loop", "1", "-framerate", str(FPS), "-t", f"{dur:.3f}", "-i", img,
             "-vf", vf.rstrip(","), "-r", str(FPS), "-an", "-c:v", "libx264", "-preset", "veryfast", "-crf", "18", out])
        return
    src = p["source"]
    speed = 0.5 if p.get("lent") else 1.0
    bars = p.get("bandes", 0)  # bandes noires du format cinéma (part de la hauteur en haut ET en bas)
    pre = f"crop=iw:ih*{1 - 2 * bars:.4f}:0:ih*{bars:.4f}," if bars else ""
    if p.get("entier"):  # image entière (logo…) sur fond flou
        vf = (f"setpts=PTS/{speed},{pre}split[a][b];[a]scale=-2:{H},crop={W}:{H},boxblur=30:2,eq=brightness=-0.15[bg];"
              f"[b]scale={W}:-2[fg];[bg][fg]overlay=0:(H-h)/2,scale=w=-2:h='{H}*{punch}':eval=frame,{crop},"
              + ",".join(fx + ["format=yuv420p"]))
    else:
        vf = (f"setpts=PTS/{speed},{pre}scale=w=-2:h='{H}*{punch}':eval=frame,{crop},{look},"
              + ",".join(fx + ["format=yuv420p"]))
    run(["ffmpeg", "-loglevel", "error", "-y", "-ss", f"{p['t']:.3f}", "-t", f"{dur * speed + 0.1:.3f}", "-i", src,
         "-vf", vf.rstrip(","), "-t", f"{dur:.3f}", "-r", str(FPS), "-an",
         "-c:v", "libx264", "-preset", "veryfast", "-crf", "18", out])


def esc(s):
    return s.replace("\\", "\\\\").replace(":", "\\:").replace("'", "’").replace("%", "\\%")


def build(ep_path, out):
    sys.path.insert(0, HERE)
    import beat as beatmod
    ep = json.load(open(ep_path))
    base_dir = os.path.dirname(os.path.abspath(ep_path))
    bpm = ep.get("bpm", 130)
    b = 60 / bpm
    tmp = tempfile.mkdtemp()
    parts = []
    for i, p in enumerate(ep["plans"]):
        p = dict(p)
        if "image" not in p:
            p.setdefault("source", ep["source"])
            p.setdefault("bandes", ep.get("bandes", 0))
        f = os.path.join(tmp, f"p{i:02d}.mp4")
        plan(p, b, f, base_dir)
        parts.append(f)
        print(f"plan {i + 1}/{len(ep['plans'])}", flush=True)
    lst = os.path.join(tmp, "l.txt")
    open(lst, "w").write("".join(f"file '{f}'\n" for f in parts))
    total_beats = sum(p["temps"] for p in ep["plans"])
    total = total_beats * b
    mesures = int(-(-total_beats // 4))
    music = os.path.join(tmp, "beat.wav")
    beatmod.write(music, beatmod.make(bpm, mesures, ep.get("graine", 1)))
    draw = []
    for t in ep.get("textes", []):
        a, z = t["de"] * b, t["a"] * b
        size = t.get("taille", 110)
        y = t.get("y", 0.2)
        draw.append(f"drawtext=fontfile={FONT}:text='{esc(t['txt'])}':fontsize={size}:fontcolor={t.get('couleur', 'white')}"
                    f":borderw=8:bordercolor=black:x=(w-tw)/2:y=h*{y}:enable='between(t,{a:.3f},{z:.3f})'")
    vf = ",".join(draw) if draw else "null"
    run(["ffmpeg", "-loglevel", "error", "-y", "-f", "concat", "-safe", "0", "-i", lst, "-i", music,
         "-vf", vf, "-af", f"afade=t=out:st={total - 0.6:.3f}:d=0.6,loudnorm=I=-14:TP=-1.5,aresample=44100,alimiter=limit=0.7:level=false",
         "-t", f"{total:.3f}", "-c:v", "libx264", "-preset", "medium", "-crf", "20", "-pix_fmt", "yuv420p",
         "-c:a", "aac", "-b:a", "192k", "-movflags", "+faststart", out])
    print(f"OK {out} ({total:.1f} s)")


if __name__ == "__main__":
    build(sys.argv[1], sys.argv[2])
