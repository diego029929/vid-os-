import sys, os, json, tempfile
sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "..", "..", "engine"))
import numpy as np, voice
OUT = sys.argv[1]
phr = json.load(open(os.path.join(OUT, "script.json")))
durs = []
with tempfile.TemporaryDirectory() as tmp:
    for i, p in enumerate(phr):
        a = voice.megaphone(voice.synth(p), tmp)
        voice.write_wav(os.path.join(OUT, "audio", f"p{i}.wav"), a)
        durs.append(len(a) / voice.SR); print(i, round(durs[-1], 2), p)
json.dump(durs, open(os.path.join(OUT, "audio", "durs.json"), "w"))
