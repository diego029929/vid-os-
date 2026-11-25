"""Voix off + minutage des mots pour une vidéo « brevet » (style stick-figure).

    python3 episodes/brevet/voix.py episodes/brevet/<dossier> [--refaire 3,5]

Lit <dossier>/script.json ([{"texte": affiché, "voix": lu}]), fait chaque phrase avec la voix
du dépôt (engine/voice.py : Pocket TTS « estelle »), la vérifie avec Whisper, puis écrit :
  audio/phrase_NN.wav   une phrase (gardée : --refaire ne refait que les numéros donnés)
  audio/vo.wav          la voix complète (44,1 kHz, effet « leger » de la config)
  web/words.js          WORDS = mots AFFICHÉS avec leurs temps (sous-titres + plans)
  audio/verif.txt       texte lu / texte entendu par Whisper, phrase par phrase
"""
import json, os, re, sys, difflib
import numpy as np, soundfile as sf

ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
sys.path.insert(0, os.path.join(ROOT, "engine"))
import voice  # noqa: E402

DIR = os.path.abspath(sys.argv[1])
REFAIRE = set()
if "--refaire" in sys.argv:
    REFAIRE = {int(x) for x in sys.argv[sys.argv.index("--refaire") + 1].split(",")}
SR = voice.SR
lines = json.load(open(os.path.join(DIR, "script.json")))
os.makedirs(os.path.join(DIR, "audio"), exist_ok=True)
os.makedirs(os.path.join(DIR, "web"), exist_ok=True)

import whisper  # noqa: E402
asr = whisper.load_model(os.environ.get("WHISPER", "small"))
norm = lambda s: re.sub(r"[^a-z0-9àâçéèêëîïôûùüÿœ' ]", " ", s.lower()).split()


def entendu(a):
    x = np.interp(np.linspace(0, len(a) - 1, int(len(a) * 16000 / SR)), np.arange(len(a)), a).astype(np.float32)
    r = asr.transcribe(x, language="fr", word_timestamps=True, fp16=False)
    mots = [(w["word"].strip(), w["start"], w["end"]) for s in r["segments"] for w in s["words"]]
    return r["text"].strip(), mots


def score(lu, txt):
    return difflib.SequenceMatcher(a=norm(lu), b=norm(txt)).ratio()


phrases = []
for i, L in enumerate(lines):
    f = os.path.join(DIR, "audio", f"phrase_{i:02d}.wav")
    if os.path.exists(f) and i not in REFAIRE:
        a, _ = sf.read(f, dtype="float32")
        txt, mots = entendu(a)
    else:
        best = None
        for essai in range(3):  # 3 tirages au plus, on garde le plus fidèle
            a = voice.synth(L["voix"])
            txt, mots = entendu(a)
            sc = score(L["voix"], txt)
            if best is None or sc > best[0]:
                best = (sc, a, txt, mots)
            if sc > .93:
                break
        _, a, txt, mots = best
        sf.write(f, a, SR)
    phrases.append((a, txt, mots))

# assemblage : petit silence entre les phrases, plus long après une question
track, t, WORDS, verif = [], 0.0, [], []
for i, (L, (a, txt, mots)) in enumerate(zip(lines, phrases)):
    track.append(a)
    dur = len(a) / SR
    aff = L["texte"].split()
    # temps des mots affichés : ceux de Whisper si le compte tombe juste, sinon au prorata des lettres
    if len(mots) == len(aff):
        tm = [(s, e) for _, s, e in mots]
    else:
        s0 = mots[0][1] if mots else 0.0
        e0 = mots[-1][2] if mots else dur
        poids = np.array([len(w) + 2 for w in aff], float)
        bords = s0 + np.concatenate([[0], np.cumsum(poids)]) / poids.sum() * (e0 - s0)
        tm = list(zip(bords[:-1], bords[1:]))
    for w, (s, e) in zip(aff, tm):
        WORDS.append({"w": w, "s": round(t + s, 3), "e": round(t + e, 3), "line": i})
    sc = score(L["voix"], txt)
    verif.append(f"{i:02d} [{sc:.2f}] {'OK ' if sc > .9 else '?? '} lu : {L['voix']}\n            entendu : {txt}")
    pause = .45 if L["texte"].rstrip().endswith("?") else .22
    track.append(np.zeros(int(pause * SR), np.float32))
    t += dur + pause

vo = np.concatenate(track)
import tempfile  # noqa: E402
with tempfile.TemporaryDirectory() as d:
    vo = voice.megaphone(vo, d)
sf.write(os.path.join(DIR, "audio", "vo.wav"), vo, SR)
LINES = [[min(w["s"] for w in WORDS if w["line"] == i), max(w["e"] for w in WORDS if w["line"] == i)] for i in range(len(lines))]
open(os.path.join(DIR, "web", "words.js"), "w").write(
    "const WORDS=" + json.dumps(WORDS, ensure_ascii=False) + ";\nconst LINES=" + json.dumps(LINES) +
    ";\nconst VO_END=" + str(round(len(vo) / SR, 3)) + ";\n")
open(os.path.join(DIR, "audio", "verif.txt"), "w").write("\n".join(verif) + "\n")
print("\n".join(verif))
print(f"durée voix : {len(vo) / SR:.1f} s")
