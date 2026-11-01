"""Moteur des vidéos « fruits » (style 3D façon Pixar, voix des personnages,
sous-titres karaoké en gros caractères).

Usage : python3 fruits/render.py fruits/episodes/f001.json sortie.mp4

Étapes :
1. une image IA par plan (Pollinations, gratuit ; Hugging Face en secours si
   HF_TOKEN est défini), en 9:16 ;
2. une voix edge-tts par personnage, avec le minutage de chaque mot ;
3. montage ffmpeg : zoom lent / panoramique sur chaque image, sous-titres
   ASS (2 à 3 mots, majuscules, mots clés en couleur), titre « PARTIE N ».
"""
import hashlib
import json
import os
import random
import shutil
import subprocess
import sys
import tempfile
import time
import urllib.parse
import urllib.request

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import tts  # noqa: E402

ROOT = os.path.dirname(os.path.abspath(__file__))
W, H, FPS = 1080, 1920, 30
GAP = 0.12            # silence entre deux répliques
TAIL = 0.6            # silence final
FONT_DIR = os.path.join(ROOT, "assets")
FONT_NAME = "Anton"
HL_COLOR = "&H00F2E77F&"   # cyan clair (BGR) comme dans les vidéos tendance
STYLE = ("3D animated movie still in the style of Pixar and DreamWorks, "
         "highly detailed CGI render, expressive cartoon faces, soft cinematic lighting, "
         "shallow depth of field, vibrant colors, vertical 9:16 composition, "
         "characters are anthropomorphic fruits with arms, legs and clothes, no text, no watermark")
CACHE = os.environ.get("FRUITS_IMG_CACHE", os.path.join(tempfile.gettempdir(), "fruits_img_cache"))


# ---------------------------------------------------------------- images IA

def build_prompt(ep, shot):
    cast = [ep["characters"][c]["look"] for c in shot.get("cast", []) if c in ep["characters"]]
    parts = [shot["action"]]
    if cast:
        parts.append("Characters: " + "; ".join(cast))
    if shot.get("setting"):
        parts.append("Setting: " + shot["setting"])
    parts.append(ep.get("style", STYLE))
    return ". ".join(parts)


def _get(url, headers=None, data=None, timeout=180):
    req = urllib.request.Request(url, data=data, headers=headers or {})
    with urllib.request.urlopen(req, timeout=timeout) as r:
        return r.read()


def _pollinations(prompt, seed):
    q = urllib.parse.quote(prompt[:1800], safe="")
    params = f"width=768&height=1344&model=flux&nologo=true&private=true&seed={seed}"
    token = os.environ.get("POLLINATIONS_TOKEN")
    headers = {"User-Agent": "vid-os-fruits/1.0"}
    urls = []
    if token:
        headers["Authorization"] = f"Bearer {token}"
        urls.append(f"https://gen.pollinations.ai/image/{q}?{params}")
    urls.append(f"https://image.pollinations.ai/prompt/{q}?{params}")
    last = None
    for url in urls:
        try:
            return _get(url, headers)
        except Exception as exc:
            last = exc
    raise RuntimeError(last)


def _huggingface(prompt, seed):
    token = os.environ["HF_TOKEN"]
    body = json.dumps({"inputs": prompt[:1500], "parameters": {
        "width": 768, "height": 1344, "num_inference_steps": 4, "seed": seed}}).encode()
    return _get("https://router.huggingface.co/hf-inference/models/black-forest-labs/FLUX.1-schnell",
                {"Authorization": f"Bearer {token}", "Content-Type": "application/json",
                 "Accept": "image/png"}, body)


def _cloudflare(prompt, seed):
    """Workers AI (offre gratuite : 10 000 neurones par jour, ~150 images FLUX)."""
    import base64
    acc, tok = os.environ["CF_ACCOUNT_ID"], os.environ["CF_API_TOKEN"]
    body = json.dumps({"prompt": prompt[:2000], "steps": 8, "seed": seed}).encode()
    raw = _get(f"https://api.cloudflare.com/client/v4/accounts/{acc}/ai/run/@cf/black-forest-labs/flux-1-schnell",
               {"Authorization": f"Bearer {tok}", "Content-Type": "application/json"}, body)
    res = json.loads(raw)
    if not res.get("success", True) or "result" not in res:
        raise RuntimeError(str(res.get("errors"))[:300])
    return base64.b64decode(res["result"]["image"])


def _placeholder(prompt, path):
    """Image de test (FAKE_IMAGES=1) : dégradé coloré, pas d'appel réseau."""
    h = hashlib.md5(prompt.encode()).digest()
    c1 = f"0x{h[0]:02x}{h[1]:02x}{h[2]:02x}"
    c2 = f"0x{h[3]:02x}{h[4]:02x}{h[5]:02x}"
    subprocess.run(["ffmpeg", "-v", "error", "-y", "-f", "lavfi", "-i",
                    f"gradients=s=768x1344:c0={c1}:c1={c2}:x0=0:y0=0:x1=768:y1=1344:d=1",
                    "-frames:v", "1", path], check=True)


def fetch_image(prompt, seed, path):
    os.makedirs(CACHE, exist_ok=True)
    key = hashlib.sha1(f"{seed}|{prompt}".encode()).hexdigest()
    cached = os.path.join(CACHE, key + ".jpg")
    if os.path.exists(cached):
        shutil.copy(cached, path)
        return "cache"
    if os.environ.get("FAKE_IMAGES") == "1":
        _placeholder(prompt, cached)
        shutil.copy(cached, path)
        return "test"
    providers = []
    if os.environ.get("CF_ACCOUNT_ID") and os.environ.get("CF_API_TOKEN"):
        providers.append(("cloudflare", _cloudflare))
    providers.append(("pollinations", _pollinations))
    if os.environ.get("HF_TOKEN"):
        providers.append(("huggingface", _huggingface))
    errors = []
    for attempt in range(5):
        for name, fn in providers:
            try:
                data = fn(prompt, seed)
                if len(data) < 20000:
                    raise RuntimeError(f"image trop petite ({len(data)} o)")
                raw = cached + ".raw"
                with open(raw, "wb") as fh:
                    fh.write(data)
                subprocess.run(["ffmpeg", "-v", "error", "-y", "-i", raw, "-q:v", "2", cached], check=True)
                os.remove(raw)
                shutil.copy(cached, path)
                return name
            except Exception as exc:
                errors.append(f"{name}: {exc}")
        time.sleep(8 + 10 * attempt)
    raise RuntimeError("aucune image générée :\n" + "\n".join(errors[-6:]))


# ---------------------------------------------------------------- sous-titres

def ass_time(t):
    t = max(0.0, t)
    h = int(t // 3600)
    m = int(t % 3600 // 60)
    s = t % 60
    return f"{h}:{m:02d}:{s:05.2f}"


def chunk_words(words, max_words=3, max_chars=18):
    chunks, cur = [], []
    for w in words:
        cur.append(w)
        txt = " ".join(x["w"] for x in cur)
        if len(cur) >= max_words or len(txt) >= max_chars or w["w"][-1:] in ",.!?…:;":
            chunks.append(cur)
            cur = []
    if cur:
        if chunks and len(cur) == 1 and len(" ".join(x["w"] for x in chunks[-1] + cur)) <= max_chars + 4 \
                and len(chunks[-1]) < max_words + 1:
            chunks[-1].extend(cur)
        else:
            chunks.append(cur)
    return chunks


def _norm(s):
    return "".join(ch for ch in s.lower() if ch.isalnum())


def ass_escape(s):
    return s.replace("\\", "").replace("{", "(").replace("}", ")")


def build_ass(events, part_label, path):
    head = f"""[Script Info]
ScriptType: v4.00+
PlayResX: {W}
PlayResY: {H}
WrapStyle: 2
ScaledBorderAndShadow: yes

[V4+ Styles]
Format: Name, Fontname, Fontsize, PrimaryColour, SecondaryColour, OutlineColour, BackColour, Bold, Italic, Underline, StrikeOut, ScaleX, ScaleY, Spacing, Angle, BorderStyle, Outline, Shadow, Alignment, MarginL, MarginR, MarginV, Encoding
Style: Sub,{FONT_NAME},128,&H00FFFFFF,&H00FFFFFF,&H00000000,&H80000000,0,0,0,0,100,100,1,0,1,7,3,5,60,60,0,1
Style: Part,{FONT_NAME},96,&H00FFFFFF,&H00FFFFFF,&H00000000,&HA0000000,0,0,0,0,100,100,2,0,1,6,2,8,60,60,170,1

[Events]
Format: Layer, Start, End, Style, Name, MarginL, MarginR, MarginV, Effect, Text
"""
    lines = [head]
    if part_label:
        lines.append(f"Dialogue: 1,{ass_time(0)},{ass_time(2.6)},Part,,0,0,0,,"
                     f"{{\\fad(0,300)}}{ass_escape(part_label.upper())}\n")
    y = int(H * 0.60)
    for ev in events:
        txt = ev["text"]
        lines.append(f"Dialogue: 0,{ass_time(ev['start'])},{ass_time(ev['end'])},Sub,,0,0,0,,"
                     f"{{\\pos({W // 2},{y})\\fscx88\\fscy88\\t(0,90,\\fscx100\\fscy100)}}{txt}\n")
    with open(path, "w", encoding="utf-8") as fh:
        fh.writelines(lines)


# ---------------------------------------------------------------- montage

def render_shot(img, dur, out, idx):
    frames = max(1, int(round(dur * FPS)))
    mode = idx % 4
    z_end = 1.13
    if mode == 0:      # zoom avant centré
        z = f"1+{z_end - 1}*on/{frames}"
        x, y = "iw/2-(iw/zoom/2)", "ih/2-(ih/zoom/2)"
    elif mode == 1:    # zoom arrière
        z = f"{z_end}-{z_end - 1}*on/{frames}"
        x, y = "iw/2-(iw/zoom/2)", "ih/2-(ih/zoom/2)"
    elif mode == 2:    # panoramique gauche → droite
        z = "1.12"
        x, y = f"(iw-iw/zoom)*on/{frames}", "ih/2-(ih/zoom/2)"
    else:              # zoom avant vers le haut (visages)
        z = f"1.04+{z_end - 1.04}*on/{frames}"
        x, y = "iw/2-(iw/zoom/2)", "(ih/2-(ih/zoom/2))*0.6"
    vf = (f"scale={W * 2}:{H * 2}:force_original_aspect_ratio=increase,crop={W * 2}:{H * 2},"
          f"zoompan=z='{z}':x='{x}':y='{y}':d={frames}:s={W}x{H}:fps={FPS},"
          f"eq=saturation=1.08:contrast=1.03,format=yuv420p")
    subprocess.run(["ffmpeg", "-v", "error", "-y", "-loop", "1", "-i", img, "-vf", vf,
                    "-frames:v", str(frames), "-c:v", "libx264", "-preset", "veryfast",
                    "-crf", "20", "-r", str(FPS), out], check=True)


def main(ep_path, out_path):
    with open(ep_path, encoding="utf-8") as fh:
        ep = json.load(fh)
    work = tempfile.mkdtemp(prefix="fruits_")
    seed0 = int(ep.get("seed", random.randint(1, 10 ** 6)))
    t = 0.0
    events, audio_parts, shots_timeline = [], [], []
    shot_idx = 0
    line_no = 0
    print(f"épisode : {ep.get('title')}")
    for si, scene in enumerate(ep["scenes"]):
        shots = scene.get("shots") or [{"action": scene["action"]}]
        for sh in shots:
            sh.setdefault("cast", scene.get("cast", []))
            sh.setdefault("setting", scene.get("setting", ""))
        # répartit les répliques sur les plans de la scène (champ "shot" sinon équitable)
        n_lines = len(scene["lines"])
        for li, line in enumerate(scene["lines"]):
            line.setdefault("shot", min(len(shots) - 1, li * len(shots) // max(1, n_lines)))
        shot_start = {k: None for k in range(len(shots))}
        shot_end = {}
        for line in scene["lines"]:
            ch = ep["characters"][line["who"]]
            wav = os.path.join(work, f"l{line_no:03d}.wav")
            dur, words = tts.speak(line["text"], ch["voice"], wav, ch.get("rate", "+0%"),
                                   ch.get("pitch", "+0Hz"), ch.get("tempo", 1.0))
            line_no += 1
            audio_parts.append((wav, dur))
            k = line["shot"]
            if shot_start[k] is None:
                shot_start[k] = t
            hl = {_norm(x) for x in line.get("hl", [])}
            chunks = chunk_words(words)
            for ci, ch_words in enumerate(chunks):
                st = t + ch_words[0]["start"]
                en = t + (chunks[ci + 1][0]["start"] if ci + 1 < len(chunks) else dur + GAP * 0.5)
                parts = []
                for w in ch_words:
                    word = ass_escape(w["w"].upper())
                    if _norm(w["w"]) in hl:
                        parts.append(f"{{\\c{HL_COLOR}}}{word}{{\\c&H00FFFFFF&}}")
                    else:
                        parts.append(word)
                events.append({"start": st, "end": en, "text": " ".join(parts)})
            t += dur + GAP
            shot_end[k] = t
        # plans sans réplique : on les colle au plan précédent
        for k in range(len(shots)):
            if shot_start[k] is None:
                continue
            shots_timeline.append({"shot": shots[k], "start": shot_start[k],
                                   "end": shot_end[k], "scene": si, "k": k})
    total = t + TAIL
    # recale les plans bout à bout
    for i, s in enumerate(shots_timeline):
        s["start"] = 0.0 if i == 0 else shots_timeline[i - 1]["end"]
    shots_timeline[-1]["end"] = total
    print(f"durée totale : {total:.1f} s, {len(shots_timeline)} plans, {line_no} répliques")

    # images
    clips = []
    for i, s in enumerate(shots_timeline):
        prompt = build_prompt(ep, s["shot"])
        img = os.path.join(work, f"img{i:02d}.jpg")
        src = fetch_image(prompt, seed0 + 101 * s["scene"] + s["k"], img)
        print(f"  image {i + 1}/{len(shots_timeline)} ({src})")
        clip = os.path.join(work, f"clip{i:02d}.mp4")
        render_shot(img, s["end"] - s["start"], clip, i)
        clips.append(clip)

    # vidéo muette
    lst = os.path.join(work, "clips.txt")
    with open(lst, "w") as fh:
        fh.writelines(f"file '{c}'\n" for c in clips)
    silent = os.path.join(work, "silent.mp4")
    subprocess.run(["ffmpeg", "-v", "error", "-y", "-f", "concat", "-safe", "0", "-i", lst,
                    "-c", "copy", silent], check=True)

    # piste audio : répliques + silences
    gap = os.path.join(work, "gap.wav")
    subprocess.run(["ffmpeg", "-v", "error", "-y", "-f", "lavfi", "-i",
                    f"anullsrc=r={tts.SR}:cl=mono", "-t", str(GAP), gap], check=True)
    alst = os.path.join(work, "audio.txt")
    with open(alst, "w") as fh:
        for wav, _ in audio_parts:
            fh.write(f"file '{wav}'\nfile '{gap}'\n")
    voice = os.path.join(work, "voice.wav")
    subprocess.run(["ffmpeg", "-v", "error", "-y", "-f", "concat", "-safe", "0", "-i", alst,
                    "-af", f"apad=whole_dur={total:.3f}", voice], check=True)

    ass = os.path.join(work, "subs.ass")
    build_ass(events, ep.get("part_label", ""), ass)
    music = ep.get("music")
    cmd = ["ffmpeg", "-v", "error", "-y", "-i", silent, "-i", voice]
    vf = f"ass={ass}:fontsdir={FONT_DIR}"
    if music and os.path.exists(os.path.join(ROOT, music)):
        cmd += ["-stream_loop", "-1", "-i", os.path.join(ROOT, music),
                "-filter_complex",
                f"[0:v]{vf}[v];[2:a]volume=0.10[m];[1:a][m]amix=inputs=2:duration=first:normalize=0[a]",
                "-map", "[v]", "-map", "[a]"]
    else:
        cmd += ["-vf", vf, "-map", "0:v", "-map", "1:a"]
    cmd += ["-t", f"{total:.3f}", "-c:v", "libx264", "-preset", "medium", "-crf", "19",
            "-pix_fmt", "yuv420p", "-c:a", "aac", "-b:a", "192k", "-ar", "44100",
            "-movflags", "+faststart", out_path]
    subprocess.run(cmd, check=True)
    shutil.rmtree(work, ignore_errors=True)
    print(f"vidéo prête : {out_path} ({total:.1f} s)")


if __name__ == "__main__":
    main(sys.argv[1], sys.argv[2])
