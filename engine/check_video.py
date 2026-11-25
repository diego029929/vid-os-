"""Contrôle automatique d'une vidéo finie, avant de la publier (ffmpeg seulement, gratuit).

Usage : python3 engine/check_video.py video.mp4 [--min 25] [--max 100]

Vérifie :
- format 1080x1920, durée dans la fourchette (épisode 75-100 s, SURVIS 25-45 s) ;
- volume (LUFS) proche de -14, sans saturation ;
- pas d'image blanche ni noire au début (règle de Fio : pas de fond blanc) ;
- pas d'écran noir de plus de 1 s, pas de silence de plus de 1,5 s ;
- taille < 100 Mo (raw.githubusercontent).
Code de sortie 1 si un problème bloquant est trouvé : ne pas publier, corriger.
"""
import argparse
import json
import os
import re
import subprocess
import sys


def run(args):
    return subprocess.run(args, capture_output=True, text=True).stderr


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("video")
    ap.add_argument("--min", type=float, default=25)
    ap.add_argument("--max", type=float, default=100)
    a = ap.parse_args()
    v = a.video
    pb = json.loads(subprocess.run(["ffprobe", "-v", "error", "-show_streams", "-show_format", "-of", "json", v],
                                   capture_output=True, text=True).stdout)
    vid = next(s for s in pb["streams"] if s["codec_type"] == "video")
    has_audio = any(s["codec_type"] == "audio" for s in pb["streams"])
    dur = float(pb["format"]["duration"])
    size = os.path.getsize(v) / 1e6
    bad, info = [], []

    if (vid["width"], vid["height"]) != (1080, 1920):
        bad.append(f"format {vid['width']}x{vid['height']} (attendu 1080x1920)")
    if not a.min <= dur <= a.max:
        bad.append(f"durée {dur:.1f} s hors de {a.min:.0f}-{a.max:.0f} s")
    if size > 95:
        bad.append(f"fichier trop lourd : {size:.0f} Mo")
    info.append(f"{dur:.1f} s, {size:.1f} Mo")

    # volume
    if not has_audio:
        bad.append("pas de son")
    else:
        e = run(["ffmpeg", "-nostats", "-i", v, "-af", "ebur128=peak=true", "-f", "null", "-"])
        lufs = float(re.findall(r"I:\s+(-?[\d.]+) LUFS", e)[-1])
        peak = float(re.findall(r"Peak:\s+(-?[\d.inf]+) dBFS", e)[-1])
        info.append(f"volume {lufs:.1f} LUFS, crête {peak:.1f} dB")
        if not -17 <= lufs <= -11:
            bad.append(f"volume {lufs:.1f} LUFS (viser -14)")
        if peak > -0.5:
            bad.append(f"son saturé (crête {peak:.1f} dB)")
        s = run(["ffmpeg", "-nostats", "-i", v, "-af", "silencedetect=n=-45dB:d=1.5", "-f", "null", "-"])
        sil = re.findall(r"silence_start: ([\d.]+)", s)
        if sil:
            bad.append(f"silence de plus de 1,5 s à {', '.join(sil[:3])} s")

    # première image : ni blanche ni noire
    e = run(["ffmpeg", "-nostats", "-i", v, "-vf", "select=eq(n\\,0),signalstats,metadata=print", "-frames:v", "1",
             "-f", "null", "-"])
    m = re.search(r"YAVG=([\d.]+)", e)
    if m:
        y = float(m.group(1))
        info.append(f"luminosité 1re image {y:.0f}/255")
        if y > 200:
            bad.append("première image presque blanche")
        elif y < 8:
            bad.append("première image noire (accroche invisible)")

    # écrans noirs
    e = run(["ffmpeg", "-nostats", "-i", v, "-vf", "blackdetect=d=1.0:pix_th=0.06", "-an", "-f", "null", "-"])
    blk = re.findall(r"black_start:([\d.]+)", e)
    if blk:
        bad.append(f"écran noir de plus de 1 s à {', '.join(blk[:3])} s")

    print("contrôle vidéo : " + " ; ".join(info))
    for b in bad:
        print("  PROBLÈME : " + b)
    print("contrôle vidéo : " + ("À CORRIGER, ne pas publier" if bad else "OK"))
    return 1 if bad else 0


if __name__ == "__main__":
    sys.exit(main())
