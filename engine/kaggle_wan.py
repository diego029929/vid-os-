"""Plans vidéo réalistes « façon Higgsfield », 100 % gratuits, sur le GPU de Kaggle (2× T4).

Chaîne : Z-Image-Turbo (image photo-réaliste de départ) → Wan 2.2 I2V A14B (GGUF Q4_K_M)
+ LoRA Lightning 4 pas (lightx2v), dans ComfyUI, un serveur par GPU.

Usage : python3 engine/kaggle_wan.py shots.json OUT_DIR [slug]
  shots.json = [{"img": "prompt image (anglais)", "vid": "prompt mouvement/caméra", "seed": 1}, ...]
  → OUT_DIR/shot-XX.png + shot-XX.mp4 (480×832, 16 i/s, 65 images ≈ 4 s)
"""
import json
import os
import subprocess
import sys
import time

USER = os.environ.get("KAGGLE_USERNAME", "diediefer")
LENGTH = int(os.environ.get("WAN_LENGTH", "65"))

KERNEL = r'''
import subprocess, sys, json, time, os, threading, urllib.request, glob, shutil
T0 = time.time()
def log(*a):
    print(f"[{(time.time()-T0)/60:5.1f} min]", *a, flush=True)
SHOTS = json.loads(%(shots)r)
LENGTH = %(length)d
W = "/kaggle/working"
C = "/tmp/ComfyUI"

# 1) en arrière-plan : ComfyUI + modèles Wan (≈ 29 Go, hors /kaggle/working limité à 20 Go)
def setup():
    subprocess.run(f"git clone -q --depth 1 https://github.com/comfyanonymous/ComfyUI {C} && "
                   f"git clone -q --depth 1 https://github.com/city96/ComfyUI-GGUF {C}/custom_nodes/ComfyUI-GGUF && "
                   f"pip install -q -r {C}/requirements.txt gguf hf_transfer", shell=True)
    from huggingface_hub import hf_hub_download
    os.environ["HF_HUB_ENABLE_HF_TRANSFER"] = "1"
    files = [("QuantStack/Wan2.2-I2V-A14B-GGUF", "HighNoise/Wan2.2-I2V-A14B-HighNoise-Q4_K_M.gguf", "unet"),
             ("QuantStack/Wan2.2-I2V-A14B-GGUF", "LowNoise/Wan2.2-I2V-A14B-LowNoise-Q4_K_M.gguf", "unet"),
             ("Comfy-Org/Wan-2.2", "split_files/text_encoders/umt5_xxl_fp8_e4m3fn_scaled.safetensors", "text_encoders"),
             ("Comfy-Org/Wan-2.2", "split_files/vae/wan_2.1_vae.safetensors", "vae"),
             ("Comfy-Org/Wan-2.2", "split_files/loras/wan2.2_i2v_lightx2v_4steps_lora_v1_high_noise.safetensors", "loras"),
             ("Comfy-Org/Wan-2.2", "split_files/loras/wan2.2_i2v_lightx2v_4steps_lora_v1_low_noise.safetensors", "loras")]
    for repo, f, sub in files:
        p = hf_hub_download(repo, f, local_dir="/tmp/hf")
        d = f"{C}/models/{sub}"
        os.makedirs(d, exist_ok=True)
        os.replace(p, f"{d}/{os.path.basename(f)}")
        log("téléchargé", os.path.basename(f))
th = threading.Thread(target=setup)
th.start()

# 2) images de départ (Z-Image-Turbo réparti sur les 2 GPU, processus séparé pour libérer la mémoire)
subprocess.run("pip install -q -U diffusers transformers accelerate sentencepiece", shell=True)
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
open("/tmp/img.py", "w").write(IMG)
log("images : début")
subprocess.run([sys.executable, "/tmp/img.py", json.dumps(SHOTS)])
log("images : fin")
th.join()
os.makedirs(f"{C}/input", exist_ok=True)
for i in range(len(SHOTS)):
    if os.path.exists(f"{W}/shot-{i:02d}.png"):
        shutil.copy(f"{W}/shot-{i:02d}.png", f"{C}/input/shot-{i:02d}.png")

# 3) deux serveurs ComfyUI, un par GPU
servers = []
for g in (0, 1):
    port = 8188 + g
    lf = open(f"/tmp/comfy{g}.log", "w")
    pr = subprocess.Popen([sys.executable, "main.py", "--port", str(port), "--cuda-device", str(g),
                           "--output-directory", f"/tmp/out{g}", "--input-directory", f"{C}/input"],
                          cwd=C, stdout=lf, stderr=subprocess.STDOUT)
    servers.append((g, port, pr))
def up(port):
    try:
        urllib.request.urlopen(f"http://127.0.0.1:{port}/system_stats", timeout=5)
        return True
    except Exception:
        return False
for _ in range(120):
    if all(up(p) for _, p, _ in servers):
        break
    time.sleep(5)
log("serveurs prêts :", [up(p) for _, p, _ in servers])

NEG = "static, frozen, blurry, low quality, distorted face, deformed hands, extra limbs, morphing, flicker, watermark, text artifacts"
def graph(i, s):
    return {
     "1": {"class_type": "UnetLoaderGGUF", "inputs": {"unet_name": "Wan2.2-I2V-A14B-HighNoise-Q4_K_M.gguf"}},
     "2": {"class_type": "UnetLoaderGGUF", "inputs": {"unet_name": "Wan2.2-I2V-A14B-LowNoise-Q4_K_M.gguf"}},
     "3": {"class_type": "LoraLoaderModelOnly", "inputs": {"model": ["1", 0], "lora_name": "wan2.2_i2v_lightx2v_4steps_lora_v1_high_noise.safetensors", "strength_model": 1.0}},
     "4": {"class_type": "LoraLoaderModelOnly", "inputs": {"model": ["2", 0], "lora_name": "wan2.2_i2v_lightx2v_4steps_lora_v1_low_noise.safetensors", "strength_model": 1.0}},
     "5": {"class_type": "ModelSamplingSD3", "inputs": {"model": ["3", 0], "shift": 5.0}},
     "6": {"class_type": "ModelSamplingSD3", "inputs": {"model": ["4", 0], "shift": 5.0}},
     "7": {"class_type": "CLIPLoader", "inputs": {"clip_name": "umt5_xxl_fp8_e4m3fn_scaled.safetensors", "type": "wan"}},
     "8": {"class_type": "CLIPTextEncode", "inputs": {"text": s["vid"], "clip": ["7", 0]}},
     "9": {"class_type": "CLIPTextEncode", "inputs": {"text": NEG, "clip": ["7", 0]}},
     "10": {"class_type": "VAELoader", "inputs": {"vae_name": "wan_2.1_vae.safetensors"}},
     "11": {"class_type": "LoadImage", "inputs": {"image": f"shot-{i:02d}.png"}},
     "12": {"class_type": "WanImageToVideo", "inputs": {"positive": ["8", 0], "negative": ["9", 0], "vae": ["10", 0], "start_image": ["11", 0], "width": 480, "height": 832, "length": LENGTH, "batch_size": 1}},
     "13": {"class_type": "KSamplerAdvanced", "inputs": {"model": ["5", 0], "add_noise": "enable", "noise_seed": s["seed"], "steps": 4, "cfg": 1.0, "sampler_name": "euler", "scheduler": "simple", "positive": ["12", 0], "negative": ["12", 1], "latent_image": ["12", 2], "start_at_step": 0, "end_at_step": 2, "return_with_leftover_noise": "enable"}},
     "14": {"class_type": "KSamplerAdvanced", "inputs": {"model": ["6", 0], "add_noise": "disable", "noise_seed": s["seed"], "steps": 4, "cfg": 1.0, "sampler_name": "euler", "scheduler": "simple", "positive": ["12", 0], "negative": ["12", 1], "latent_image": ["13", 0], "start_at_step": 2, "end_at_step": 10000, "return_with_leftover_noise": "disable"}},
     "15": {"class_type": "VAEDecode", "inputs": {"samples": ["14", 0], "vae": ["10", 0]}},
     "16": {"class_type": "SaveImage", "inputs": {"images": ["15", 0], "filename_prefix": f"shot-{i:02d}"}},
    }

import imageio_ffmpeg
FF = imageio_ffmpeg.get_ffmpeg_exe()
queue = [i for i in range(len(SHOTS)) if os.path.exists(f"{C}/input/shot-{i:02d}.png")]
lock = threading.Lock()
def worker(g, port, pr):
    while True:
        with lock:
            if not queue:
                return
            i = queue.pop(0)
        t = time.time()
        try:
            req = urllib.request.Request(f"http://127.0.0.1:{port}/prompt", data=json.dumps({"prompt": graph(i, SHOTS[i])}).encode(),
                                         headers={"Content-Type": "application/json"})
            pid = json.loads(urllib.request.urlopen(req, timeout=60).read())["prompt_id"]
            while True:
                time.sleep(10)
                if pr.poll() is not None:
                    raise RuntimeError("serveur mort")
                h = json.loads(urllib.request.urlopen(f"http://127.0.0.1:{port}/history/{pid}", timeout=30).read())
                if pid in h:
                    st = h[pid].get("status", {})
                    if st.get("status_str") == "error":
                        raise RuntimeError(json.dumps(st)[:1500])
                    if h[pid].get("outputs"):
                        break
            subprocess.run([FF, "-y", "-loglevel", "error", "-framerate", "16", "-pattern_type", "glob", "-i", f"/tmp/out{g}/shot-{i:02d}_*.png",
                            "-c:v", "libx264", "-crf", "16", "-pix_fmt", "yuv420p", f"{W}/shot-{i:02d}.mp4"], check=True)
            log(f"clip {i} OK sur GPU {g} en {round(time.time()-t)} s")
        except Exception as e:
            log(f"clip {i} ÉCHEC GPU {g} :", repr(e)[:1500])
            if pr.poll() is not None:
                with lock:
                    queue.insert(0, i)
                return
ths = [threading.Thread(target=worker, args=s) for s in servers]
[t.start() for t in ths]
[t.join() for t in ths]
for g in (0, 1):
    print(f"--- fin du journal ComfyUI GPU {g} ---")
    print(open(f"/tmp/comfy{g}.log").read()[-3000:])
log("FIN")
'''


def run(shots_path, out_dir, slug="wan-essai"):
    shots = json.load(open(shots_path))
    kdir = os.path.join(out_dir, "_kernel")
    os.makedirs(kdir, exist_ok=True)
    open(os.path.join(kdir, "run.py"), "w").write(KERNEL % {"shots": json.dumps(shots), "length": LENGTH})
    json.dump({"id": f"{USER}/{slug}", "title": slug, "code_file": "run.py", "language": "python",
               "kernel_type": "script", "is_private": True, "enable_gpu": True, "enable_internet": True,
               "dataset_sources": [], "competition_sources": [], "kernel_sources": []},
              open(os.path.join(kdir, "kernel-metadata.json"), "w"))
    subprocess.run(["kaggle", "kernels", "push", "-p", kdir], check=True)
    t0 = time.time()
    while True:
        time.sleep(60)
        st = subprocess.run(["kaggle", "kernels", "status", f"{USER}/{slug}"], capture_output=True, text=True).stdout
        print(f"  Kaggle : {st.strip().split()[-1] if st.strip() else '?'} ({(time.time() - t0) / 60:.0f} min)", flush=True)
        if any(k in st for k in ("COMPLETE", "ERROR", "CANCEL")):
            break
    subprocess.run(["kaggle", "kernels", "output", f"{USER}/{slug}", "-p", out_dir], check=False)
    missing = [i for i in range(len(shots)) if not os.path.exists(os.path.join(out_dir, f"shot-{i:02d}.mp4"))]
    print(f"OK clips : {len(shots) - len(missing)}/{len(shots)}" + (f", manquants {missing}" if missing else ""))
    return missing


if __name__ == "__main__":
    sys.exit(1 if run(*sys.argv[1:]) else 0)
