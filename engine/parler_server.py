"""Petit serveur Parler-TTS : lit une requête JSON par ligne sur stdin
({"text", "desc", "seed", "out"}), écrit le WAV et répond « ok » sur stdout.
Lancé par engine/voice.py avec le Python de l'environnement Parler
(voir engine/setup_parler.sh), pour garder le modèle chargé entre les répliques."""
import json
import sys

import soundfile as sf
import torch
from parler_tts import ParlerTTSForConditionalGeneration
from transformers import AutoTokenizer

M = "parler-tts/parler-tts-mini-multilingual-v1.1"
model = ParlerTTSForConditionalGeneration.from_pretrained(M)
tok = AutoTokenizer.from_pretrained(M)
dtok = AutoTokenizer.from_pretrained(model.config.text_encoder._name_or_path)
print("pret", flush=True)
for raw in sys.stdin:
    req = json.loads(raw)
    torch.manual_seed(int(req.get("seed", 1)))
    a = model.generate(input_ids=dtok(req["desc"], return_tensors="pt").input_ids,
                       prompt_input_ids=tok(req["text"], return_tensors="pt").input_ids)
    sf.write(req["out"], a.cpu().numpy().squeeze(), model.config.sampling_rate)
    print("ok", flush=True)
