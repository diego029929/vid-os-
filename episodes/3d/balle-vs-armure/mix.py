import json, os, wave, subprocess, numpy as np
SR = 44100; X = os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "..", "..", ".claude", "skills", "sound-effects", "sfx") + "/"
T = json.load(open("audio/timeline.json")); END = T["END"]
out = np.zeros(int((END + 0.3) * SR), np.float32)
def load(p):
    r = subprocess.run(["ffmpeg","-v","error","-i",p,"-ac","1","-ar",str(SR),"-f","f32le","-"], capture_output=True, check=True)
    return np.frombuffer(r.stdout, np.float32)
def put(a, t, g):
    i = int(t * SR); a = a[: max(0, len(out) - i)]; out[i:i+len(a)] += a * g
rng = np.random.default_rng(1)
def gunshot():
    n = int(0.9*SR); t = np.arange(n)/SR
    noise = rng.standard_normal(n).astype(np.float32)
    crack = noise * np.exp(-t*38)
    boom = np.sin(2*np.pi*(55+60*np.exp(-t*20))*t) * np.exp(-t*7)
    tail = np.convolve(noise*np.exp(-t*6), np.ones(40)/40, 'same')
    return (0.8*crack + 0.9*boom + 0.5*tail).astype(np.float32)
def clang(base=420, dec=5):
    n = int(1.4*SR); t = np.arange(n)/SR; s = np.zeros(n)
    for k, a in zip([1, 2.76, 5.4, 8.93, 1.5], [1, .6, .4, .25, .5]): s += a*np.sin(2*np.pi*base*k*t)*np.exp(-t*dec*(1+k/4))
    s += rng.standard_normal(n)*np.exp(-t*60)*0.6
    return (s/np.abs(s).max()).astype(np.float32)
for i in range(5): put(load(f"audio/p{i}.wav"), T["st"][i], 1.0)
W = T["W"]
def nt(old):
    for a, b, c, d in W:
        if c <= old <= d: return a + (old - c) / (d - c) * (b - a)
    raise ValueError(old)
G = gunshot()
put(G, 0.05, 0.55); put(G, W[6][0] + 0.02, 0.55)
put(load(X+"whoosh/fs-169867-swoosh.ogg"), W[1][0] - 0.13, 0.35)
put(clang(900, 9), nt(5.37), 0.22)
put(load(X+"impact/fs-222517-dramatic-hit.ogg"), W[2][0] - 0.03, 0.45)
put(clang(380, 6), nt(8.0), 0.28)
put(clang(260, 4), nt(12.58), 0.32); put(load(X+"impact/kenney-impact-impactpunch-heavy-000.ogg"), nt(12.58), 0.4)
put(load(X+"whoosh/fs-683101-quick-woosh.ogg"), nt(21.0), 0.35)
put(load(X+"impact/kenney-impact-impactsoft-heavy-000.ogg"), nt(22.0), 0.5); put(clang(700, 10), nt(22.0), 0.15)
put(clang(500, 8), nt(26.45), 0.2); put(load(X+"impact/kenney-impact-impactpunch-heavy-001.ogg"), nt(26.45), 0.3)
put(load(X+"impact/kenney-impact-impactpunch-heavy-000.ogg"), nt(27.95), 0.3)
out /= max(1.0, np.abs(out).max() / 0.95)
with wave.open("audio/mix.wav","wb") as w:
    w.setnchannels(1); w.setsampwidth(2); w.setframerate(SR); w.writeframes((out*32767).astype(np.int16).tobytes())
print("ok", len(out)/SR)
