"""Images des « films de fruits » : SDXL-Turbo sur CPU (gratuit, local) + détection du visage.

Usage (dans le venv /tmp/sdenv, voir ROUTINE.md) :
  /tmp/sdenv/bin/python engine/film_images.py episodes/film-NNN.json /tmp/film-NNN-img
Écrit shot-XX.png (576×1024) et faces.json ({"shot-XX.png": [x, y, w, h] ou null}).
Une image sans visage, avec plusieurs visages (le perso en double) ou en très gros plan
est refaite avec une autre graine (4 essais).
"""
import json
import os
import sys
import time

import cv2
import torch
from diffusers import StableDiffusionXLPipeline

STYLE = "3D animated movie still, cinematic lighting, highly detailed, "


def main(spec_path, out):
    spec = json.load(open(spec_path))
    os.makedirs(out, exist_ok=True)
    torch.set_num_threads(os.cpu_count() or 4)
    pipe = StableDiffusionXLPipeline.from_pretrained("stabilityai/sdxl-turbo", torch_dtype=torch.float32)
    det = cv2.CascadeClassifier(cv2.data.haarcascades + "haarcascade_frontalface_default.xml")
    faces_path = os.path.join(out, "faces.json")
    faces = json.load(open(faces_path)) if os.path.exists(faces_path) else {}
    for i, sh in enumerate(spec["shots"]):
        name = f"shot-{i:02d}.png"
        if name in faces and os.path.exists(os.path.join(out, name)):
            continue
        who = sh.get("who")
        look = spec["cast"][who]["look"] if who in spec["cast"] and not sh.get("off") else None
        if look:
            prompt = STYLE + f"solo portrait, only one person, medium close-up shot from the waist up of {look} looking at the camera, {sh['action'] + ', ' if sh.get('action') else ''}{sh['lieu']}"
        else:
            prompt = STYLE + sh["lieu"] + ", no people"
        best = None
        for k in range(4):
            seed = sh.get("seed", 0) * 100 + i * 7 + k
            t = time.time()
            im = pipe(prompt=prompt, num_inference_steps=2, guidance_scale=0.0, width=576, height=1024,
                      generator=torch.manual_seed(seed)).images[0]
            if not look:
                best = (im, None)
                break
            g = cv2.cvtColor(cv2.cvtColor(__import__("numpy").asarray(im), cv2.COLOR_RGB2BGR), cv2.COLOR_BGR2GRAY)
            f = det.detectMultiScale(g, 1.1, 5, minSize=(50, 50))
            f = [r for r in f if r[1] + r[3] / 2 < 1024 * 0.55]  # un visage est en haut de l'image (sinon fausse détection)
            print(f"  {name} essai {k + 1} : {len(f)} visage(s), {time.time() - t:.0f} s", file=sys.stderr, flush=True)
            if len(f):
                x, y, w, h = max(f, key=lambda r: r[2] * r[3])  # le plus grand visage = le perso
                cand = (im, [int(x), int(y), int(w), int(h)])
                if best is None:
                    best = cand
                if len(f) == 1 and w < 576 * 0.25:  # un seul perso, pas trop gros plan : parfait
                    best = cand
                    break
        if best is None:
            best = (im, [576 // 2 - 70, 230, 140, 140])  # au pire : tête au centre-haut
        best[0].save(os.path.join(out, name))
        faces[name] = best[1]
        json.dump(faces, open(faces_path, "w"))
    print("OK images", out)


if __name__ == "__main__":
    main(sys.argv[1], sys.argv[2])
