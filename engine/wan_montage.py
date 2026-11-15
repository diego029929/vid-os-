"""Montage d'un épisode à partir des clips Wan (engine/kaggle_wan.py) : 1 clip par plan,
coupes franches calées sur la voix, sous-titres 1-2 mots (police Anton, mots clés en rouge).

Usage : python3 engine/wan_montage.py CLIPS_DIR words.json audio OUT.mp4 t0,t1,...,tN [mots,rouges]
  words.json = [[début, fin, "mot"], ...] (Whisper, horodatage par mot)
  t0..tN     = début de chaque plan (s) ; le dernier plan va jusqu'à la fin de l'audio.
"""
import json
import os
import subprocess
import sys
import tempfile

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
FONT_DIR = os.path.join(ROOT, "assets", "fonts")


def dur(p):
    return float(subprocess.run(["ffprobe", "-v", "error", "-show_entries", "format=duration", "-of", "csv=p=0", p],
                                capture_output=True, text=True).stdout)


def ts(t):
    return f"{int(t // 3600)}:{int(t % 3600 // 60):02d}:{t % 60:05.2f}"


def ass(words, red, path):
    head = ("[Script Info]\nScriptType: v4.00+\nPlayResX: 1080\nPlayResY: 1920\n\n[V4+ Styles]\n"
            "Format: Name, Fontname, Fontsize, PrimaryColour, SecondaryColour, OutlineColour, BackColour, Bold, Italic, "
            "Underline, StrikeOut, ScaleX, ScaleY, Spacing, Angle, BorderStyle, Outline, Shadow, Alignment, MarginL, MarginR, MarginV, Encoding\n"
            "Style: S,Anton,104,&H00FFFFFF,&H00FFFFFF,&H00000000,&H64000000,0,0,0,0,100,100,1,0,1,7,3,2,150,150,640,1\n\n"
            "[Events]\nFormat: Layer, Start, End, Style, Name, MarginL, MarginR, MarginV, Effect, Text\n")
    # mots collés (« t'arrêtes », « C'est ») puis morceaux de 2 mots max, coupés à la ponctuation
    merged = []
    for a, b, w in words:
        if merged and (w.startswith("'") or merged[-1][2].endswith("'")):
            merged[-1] = [merged[-1][0], b, merged[-1][2] + w.strip()]
        else:
            merged.append([a, b, w.strip()])
    chunks, cur = [], []
    for m in merged:
        cur.append(m)
        if len(cur) == 2 or m[2][-1:] in ".,!?:":
            chunks.append(cur)
            cur = []
    if cur:
        chunks.append(cur)
    lines = []
    for i, c in enumerate(chunks):
        a = c[0][0]
        b = chunks[i + 1][0][0] if i + 1 < len(chunks) else c[-1][1] + 0.4
        b = min(b, c[-1][1] + 0.5)
        txt = " ".join(w for _, _, w in c).upper().strip(" .,")
        out = []
        for w in txt.split():
            key = w.strip(".,!?:").lower()
            out.append("{\\c&H2A2AE6&}" + w + "{\\c&HFFFFFF&}" if key in red else w)
        pop = "{\\fscx80\\fscy80\\t(0,90,\\fscx100\\fscy100)}"
        lines.append(f"Dialogue: 0,{ts(a)},{ts(b)},S,,0,0,0,,{pop}{' '.join(out)}")
    open(path, "w").write(head + "\n".join(lines) + "\n")


def main(clips, words_path, audio, out, starts, red=""):
    starts = [float(x) for x in starts.split(",")]
    red = {w.lower() for w in red.split(",") if w}
    total = dur(audio)
    tmp = tempfile.mkdtemp()
    parts = []
    for k, t0 in enumerate(starts):
        t1 = starts[k + 1] if k + 1 < len(starts) else total
        d = t1 - t0
        src = os.path.join(clips, f"shot-{k:02d}.mp4")
        slow = max(1.0, d / max(dur(src) - 0.05, 0.1))  # clip trop court : on le ralentit un peu
        p = os.path.join(tmp, f"p{k:02d}.mp4")
        vf = (f"setpts={slow:.3f}*PTS,scale=1108:1920:flags=lanczos,crop=1080:1920,fps=30,"
              "eq=contrast=1.06:saturation=0.92,noise=alls=6:allf=t,vignette=PI/5")
        subprocess.run(["ffmpeg", "-y", "-loglevel", "error", "-i", src, "-t", f"{d:.3f}", "-vf", vf, "-an",
                        "-c:v", "libx264", "-crf", "17", "-preset", "medium", "-pix_fmt", "yuv420p", p], check=True)
        parts.append(p)
    lst = os.path.join(tmp, "list.txt")
    open(lst, "w").write("".join(f"file '{p}'\n" for p in parts))
    sub = os.path.join(tmp, "subs.ass")
    ass(json.load(open(words_path)), red, sub)
    subprocess.run(["ffmpeg", "-y", "-loglevel", "error", "-f", "concat", "-safe", "0", "-i", lst, "-i", audio,
                    "-vf", f"ass={sub}:fontsdir={FONT_DIR}", "-map", "0:v", "-map", "1:a", "-c:v", "libx264", "-crf", "18",
                    "-preset", "medium", "-pix_fmt", "yuv420p", "-c:a", "aac", "-b:a", "192k", "-shortest",
                    "-movflags", "+faststart", out], check=True)
    print("OK", out, round(dur(out), 1), "s")


if __name__ == "__main__":
    main(*sys.argv[1:])
