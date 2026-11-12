"""Films de fruits ANIMÉS sur le GPU gratuit de Kaggle (2× T4, ≈ 30 h/semaine).

Usage : python3 engine/kaggle_film.py episodes/film-NNN.json /tmp/film-NNN-clips
  → envoie un notebook à Kaggle (compte de Fio, secret KAGGLE_API_TOKEN), attend,
    récupère shot-XX.png (image) et shot-XX.mp4 (clip animé 4 s, 480×864) par plan.
Ensuite : python3 engine/film_anim.py episodes/film-NNN.json /tmp/film-NNN-clips /tmp/film-NNN.mp4

Modèles (gratuits, non restreints) : Tongyi-MAI/Z-Image-Turbo (images, bf16, ≈ 2 min/plan)
et Lightricks/LTX-Video-0.9.5 (image → vidéo, ≈ 3 min/plan). D'abord toutes les images, puis tous
les clips (un seul gros modèle en mémoire : la RAM Kaggle est limitée). ≈ 75 min pour 15 plans.
Champs JSON utilisés : cast[x].look (description complète EN ANGLAIS du perso, tête de fruit
comprise), shots[i].who / off / scene (décor + action, en anglais) / motion (facultatif).
"""
import json
import os
import subprocess
import sys
import time

USER = os.environ.get("KAGGLE_USERNAME", "diediefer")
# Style de l'exemple de Fio (12/11) : vraie photo (décor, corps, vêtements) + tête = vase en verre
# en forme de fruit avec, dedans, un visage de dessin animé 3D de la couleur du fruit.
STYLE = ("Photorealistic cinematic photograph, shot on 35mm, natural soft light, real location, sharp details,"
         " vertical 9:16. ")
# Fio (12/11) : « fais pas trop bouger les personnages, ça les fait bugger » → presque immobile.
MOTION = (" Static camera, locked-off shot. The character stays almost still and only talks: small mouth"
          " movements, blinking eyes, a very slight head tilt. No walking, no hand gestures, no camera movement.")

KERNEL = r'''
import subprocess, sys, json, time, os
subprocess.run("pip install -q -U diffusers transformers accelerate sentencepiece imageio imageio-ffmpeg", shell=True)
SHOTS = json.loads(%(shots)r)
W = "/kaggle/working"
IMG = r"""
import json, torch, time, sys
from diffusers import ZImagePipeline
SHOTS = json.loads(sys.argv[1])
pipe = ZImagePipeline.from_pretrained("Tongyi-MAI/Z-Image-Turbo", torch_dtype=torch.bfloat16, device_map="balanced")
for i, s in enumerate(SHOTS):
    t = time.time()
    im = pipe(s["img"], num_inference_steps=9, guidance_scale=0.0, width=576, height=1024, generator=torch.manual_seed(s["seed"])).images[0]
    im.save(f"/kaggle/working/shot-{i:02d}.png")
    print("img", i, round(time.time() - t), flush=True)
"""
VID = r"""
import json, torch, time, sys, os
from diffusers import LTXImageToVideoPipeline
from diffusers.utils import export_to_video
from PIL import Image
SHOTS = json.loads(sys.argv[1])
v = LTXImageToVideoPipeline.from_pretrained("Lightricks/LTX-Video-0.9.5", torch_dtype=torch.float16)
v.enable_model_cpu_offload(gpu_id=1)
for i, s in enumerate(SHOTS):
    p = f"/kaggle/working/shot-{i:02d}.png"
    while not os.path.exists(p):
        time.sleep(5)
    time.sleep(2)
    t = time.time()
    fr = v(image=Image.open(p).convert("RGB").resize((480, 864)), prompt=s["vid"],
           negative_prompt="worst quality, fast motion, large movement, camera shake, inconsistent motion, blurry, jittery, distorted, morphing, deformed face, extra limbs",
           width=480, height=864, num_frames=97, num_inference_steps=40, decode_timestep=0.05, decode_noise_scale=0.025,
           generator=torch.Generator("cuda:1").manual_seed(s["seed"])).frames[0]
    export_to_video(fr, f"/kaggle/working/shot-{i:02d}.mp4", fps=24)
    print("vid", i, round(time.time() - t), flush=True)
"""
open(W + "/img.py", "w").write(IMG)
open(W + "/vid.py", "w").write(VID)
arg = json.dumps(SHOTS)
# d'abord toutes les images (Z-Image réparti sur les 2 GPU), puis les clips : un seul gros modèle en mémoire à la fois
ra = subprocess.run([sys.executable, W + "/img.py", arg]).returncode
rb = subprocess.run([sys.executable, W + "/vid.py", arg]).returncode
print("FIN", ra, rb, flush=True)
for f in ("img.py", "vid.py"):
    os.remove(W + "/" + f)
'''


def build_shots(spec):
    out = []
    for i, sh in enumerate(spec["shots"]):
        c = spec["cast"].get(sh.get("who"), {})
        if sh.get("off") or not c:
            img = STYLE + sh["scene"] + ". No people."
            vid = img + " Static camera, almost no movement, only light flickers softly."
        else:
            img = STYLE + c["look"] + " " + sh["scene"]
            vid = img + " " + sh.get("motion", MOTION)
        out.append({"img": img, "vid": vid, "seed": int(sh.get("seed", 0)) * 100 + i})
    return out


def run(spec_path, out_dir, slug=None):
    spec = json.load(open(spec_path))
    slug = slug or "fruits-" + os.path.splitext(os.path.basename(spec_path))[0]
    kdir = os.path.join(out_dir, "_kernel")
    os.makedirs(kdir, exist_ok=True)
    open(os.path.join(kdir, "run.py"), "w").write(KERNEL % {"shots": json.dumps(build_shots(spec))})
    json.dump({"id": f"{USER}/{slug}", "title": slug, "code_file": "run.py", "language": "python",
               "kernel_type": "script", "is_private": True, "enable_gpu": True, "enable_internet": True,
               "dataset_sources": [], "competition_sources": [], "kernel_sources": []},
              open(os.path.join(kdir, "kernel-metadata.json"), "w"))
    subprocess.run(["kaggle", "kernels", "push", "-p", kdir], check=True)
    t0 = time.time()
    while True:
        time.sleep(30)
        st = subprocess.run(["kaggle", "kernels", "status", f"{USER}/{slug}"], capture_output=True, text=True).stdout
        print(f"  Kaggle : {st.strip().split()[-1]} ({(time.time() - t0) / 60:.0f} min)", file=sys.stderr, flush=True)
        if any(k in st for k in ("COMPLETE", "ERROR", "CANCEL")):
            break
    subprocess.run(["kaggle", "kernels", "output", f"{USER}/{slug}", "-p", out_dir], check=False)
    n = len(spec["shots"])
    missing = [i for i in range(n) if not os.path.exists(os.path.join(out_dir, f"shot-{i:02d}.mp4"))]
    print(f"OK clips : {n - len(missing)}/{n}" + (f", manquants {missing}" if missing else ""))
    return missing


if __name__ == "__main__":
    sys.exit(1 if run(sys.argv[1], sys.argv[2]) else 0)
