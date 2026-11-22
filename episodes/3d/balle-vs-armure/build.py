import json, re, wave
L = []
for i in range(5):
    with wave.open(f"audio/p{i}.wav") as wf: L.append(wf.getnframes()/wf.getframerate())
GAP, T0 = 0.28, 0.15
st = []; t = T0
for d in L: st.append(t); t += d + GAP
END = st[4] + L[4] + 0.7
caps = [[(0,"Si tu tirais"),(0.64,"sur une armure"),(1.2,"de chevalier")],
        [(0,"Beaucoup pensent"),(0.5,"que la balle"),(0.98,"s'écraserait dessus")],
        [(0,"FAUX."),(0.42,"L'armure était faite"),(1.66,"pour bloquer"),(2.18,"les épées"),(2.66,"et les coups de masse")],
        [(0,"Mais une simple"),(0.48,"flèche"),(0.9,"pouvait déjà"),(1.38,"la percer")],
        [(0,"Alors une balle ?"),(1.02,"Elle passerait"),(1.54,"à travers"),(1.88,"sans aucun problème")]]
C = []
for i, cs in enumerate(caps):
    for k,(o,txt) in enumerate(cs):
        c = [round(st[i]+o,2), txt]
        if k == len(cs)-1: c.append(round(st[i]+L[i]+0.05,2))
        C.append(c)
b = lambda i: st[i]-0.1   # cut slightly before each sentence
W = [[0, b(1), 0, 2.42], [b(1), b(2), 2.42, 6.0],
     [b(2), st[2]+2.3, 6.6, 9.9], [st[2]+2.3, b(3), 10.68, 13.2],
     [b(3), st[3]+0.6, 19.6, 21.8], [st[3]+0.6, b(4), 21.9, 25.2],
     [b(4), END, 25.4, 29.45]]
W = [[round(x,3) for x in w] for w in W]
c = b(2)
FADES = [[round(c-0.14,3), round(c-0.03,3), round(c+0.03,3), round(c+0.14,3)]]
js = open("src/shots.js").read()
js = re.sub(r"export const DURATION = [\d.]+;", f"export const DURATION = {END:.2f};\nexport const WARP = {json.dumps(W)};", js)
js = re.sub(r"export const CAPTIONS = \[.*?\n\];", "export const CAPTIONS = " + json.dumps(C, ensure_ascii=False) + ";", js, flags=re.S)
js = re.sub(r"export const FADES = .*?;\n", f"export const FADES = {json.dumps(FADES)};\n", js)
open("src/shots.js","w").write(js)
json.dump({"st": st, "L": L, "END": END, "W": W}, open("audio/timeline.json","w"))
print(END, st, W)
