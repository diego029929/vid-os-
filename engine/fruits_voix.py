"""Voix d'un essai « fruits » : une réplique par plan, une voix par personnage (Chatterbox, gratuit).

Usage : python3 engine/fruits_voix.py lignes.json OUT_DIR
  lignes.json = [{"ref": "ref-tom.wav", "text": "..."}, ...]  (un élément par plan)
  → OUT_DIR/voix.wav + OUT_DIR/starts.txt (début de chaque plan, en s)
"""
import json
import os
import sys

import numpy as np

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import voice  # noqa: E402

GAP = 0.25


def main(lines_path, out):
    lines = json.load(open(lines_path))
    parts, starts, t = [], [], 0.0
    for ln in lines:
        voice.CB_REF = os.path.join(voice.ROOT, "assets", "ref", ln["ref"])
        voice.CB_EXAG = ln.get("exag", 0.7)
        voice.RETRY = ln.get("retry", 0)
        a = voice.synth(ln["text"])
        starts.append(round(t, 2))
        parts += [a, np.zeros(int(GAP * voice.SR), np.float32)]
        t += len(a) / voice.SR + GAP
        print(f"{t:5.1f} s  {ln['text']}", flush=True)
    voice.write_wav(os.path.join(out, "voix.wav"), np.concatenate(parts + [np.zeros(int(0.8 * voice.SR), np.float32)]))
    open(os.path.join(out, "starts.txt"), "w").write(",".join(str(s) for s in starts))


if __name__ == "__main__":
    main(*sys.argv[1:])
