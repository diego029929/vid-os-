"""Style « Nuit & téléphone » : dessin plat 2D de nuit, perso à capuche, écrans de téléphone redessinés,
horloge en haut, carte de règle, choix final, sous-titres karaoké (mots clés rouges / jaunes).

Tout est dessiné en HTML/SVG et filmé image par image avec Playwright (gratuit, sans IA).

Usage : python3 engine/nuit.py episode.json voix.wav words.json starts OUT.mp4
  episode.json = {"lieu": "RUE", "heure": "02:59:52", "rouge": [...], "jaune": [...],
                  "plans": [{"type": "rue_marche"}, {"type": "appel", "nom": "Moi"}, ...]}
  types : rue_marche, rue_sonne, rue_peur, appel, sms, regle, choix
  starts = début de chaque plan en s (« 0,2.8,... »), un par plan
"""
import json
import os
import subprocess
import sys

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
FONT = os.path.join(ROOT, "assets", "fonts", "Anton-Regular.ttf")
FPS = 30
W, H = 1080, 1920

HTML = r"""<!doctype html><html><head><meta charset="utf-8"><style>
@font-face{font-family:Anton;src:url('file://%(font)s')}
*{margin:0;padding:0;box-sizing:border-box}
html,body{width:1080px;height:1920px;overflow:hidden;background:#0b0a22;font-family:-apple-system,'Inter','Helvetica Neue',Arial,sans-serif}
#cam{position:absolute;inset:0;transform-origin:50%% 55%%}
.layer{position:absolute;inset:0}
#clock{position:absolute;top:70px;left:0;right:0;text-align:center;color:#fff;z-index:20}
#clock .lieu{font-size:26px;letter-spacing:4px;font-weight:700;opacity:.85}
#clock .lieu b{color:#ff3b3b;font-size:30px}
#clock .t{font-size:76px;font-weight:800;letter-spacing:2px;font-variant-numeric:tabular-nums;margin-top:6px}
#sub{position:absolute;left:40px;right:40px;top:1590px;text-align:center;font-family:Anton;font-size:128px;color:#fff;
  -webkit-text-stroke:8px #000;paint-order:stroke fill;text-shadow:0 8px 0 rgba(0,0,0,.6);z-index:30;line-height:1.05;text-transform:uppercase}
#sub .r{color:#ff3b3b}#sub .y{color:#ffd23b}
.phone{position:absolute;left:250px;top:330px;width:580px;height:1180px;border-radius:90px;background:#111427;border:14px solid #2b2f45;
  box-shadow:0 0 120px rgba(80,120,255,.25),0 30px 80px rgba(0,0,0,.7)}
.phone .scr{position:absolute;inset:18px;border-radius:70px;overflow:hidden;background:linear-gradient(#1d2b5a,#101a3c)}
.phone .isl{position:absolute;top:26px;left:50%%;transform:translateX(-50%%);width:170px;height:46px;border-radius:30px;background:#000;z-index:3}
.phone .sb{position:absolute;top:34px;left:56px;right:56px;display:flex;justify-content:space-between;color:#fff;font-size:28px;font-weight:700;z-index:2}
.btn{position:absolute;width:150px;height:150px;border-radius:50%%;display:flex;align-items:center;justify-content:center;color:#fff;font-size:64px}
.bubble{position:absolute;left:40px;max-width:420px;padding:24px 30px;border-radius:38px;background:#2d3350;color:#fff;font-size:36px;line-height:1.25}
.card{position:absolute;inset:0;background:radial-gradient(circle at 50%% 45%%,#5a0b10 0%%,#1a0306 55%%,#070102 100%%)}
.choice{position:absolute;left:150px;right:150px;height:150px;border-radius:80px;display:flex;align-items:center;justify-content:center;
  font-family:Anton;font-size:72px;color:#fff;text-transform:uppercase}
</style></head><body><div id="cam"></div><div id="clock"><div class="lieu"><b>●</b> NUIT 1 · <span id="lieu"></span></div><div class="t" id="tm"></div></div>
<div id="sub"></div>
<script>
const EP = %(ep)s, STARTS = %(starts)s, WORDS = %(words)s, TOTAL = %(total)f;
const cam = document.getElementById('cam'), sub = document.getElementById('sub');
function rnd(s){let x=Math.sin(s*999.13)*43758.5453;return x-Math.floor(x)}
const ease = x => x<0?0:x>1?1:1-Math.pow(1-x,3);
// --- décor de rue (ville, lampadaires, lune) en SVG, largeur 3240 pour le défilement
function city(off, flick){
  let s = `<svg width="1080" height="1920" viewBox="0 0 1080 1920" style="position:absolute;inset:0">
  <defs><radialGradient id="moon"><stop offset="0" stop-color="#fff" stop-opacity=".35"/><stop offset="1" stop-color="#fff" stop-opacity="0"/></radialGradient>
  <linearGradient id="sky" x1="0" y1="0" x2="0" y2="1"><stop offset="0" stop-color="#0b0a24"/><stop offset=".55" stop-color="#2b2366"/><stop offset="1" stop-color="#3a2f78"/></linearGradient>
  <linearGradient id="cone" x1="0" y1="0" x2="0" y2="1"><stop offset="0" stop-color="#ffe7a3" stop-opacity=".45"/><stop offset="1" stop-color="#ffe7a3" stop-opacity="0"/></linearGradient></defs>
  <rect width="1080" height="1920" fill="url(#sky)"/>
  <circle cx="${760-off*0.05}" cy="420" r="190" fill="url(#moon)"/><circle cx="${760-off*0.05}" cy="420" r="62" fill="#e9e6f5"/>`;
  // immeubles lointains puis proches
  for (const [layer,base,par,col,win] of [[0,1080,0.25,'#231d52','#4b3f8a'],[1,1180,0.6,'#1a1540','#f2c86b']]){
    for(let i=0;i<26;i++){
      const w=120+rnd(i+layer*50)*140, h=250+rnd(i*3+layer*7)*420, x=(i*150 - off*par)%%3000 - 300;
      s+=`<rect x="${x}" y="${base-h}" width="${w}" height="${h+200}" fill="${col}"/>`;
      for(let r=0;r<h/70-1;r++)for(let c=0;c<w/50-1;c++){ if(rnd(i*97+r*13+c*7+layer)>0.55)
        s+=`<rect x="${x+20+c*48}" y="${base-h+30+r*68}" width="24" height="30" fill="${win}" opacity="${layer?0.9:0.5}"/>`;}
    }
  }
  // lampadaires
  for(let i=0;i<4;i++){ const x=((i*520+200 - off)%%2080+2080)%%2080-300; const on = flick && i==1 ? (Math.sin(off*0.7)>0.2?1:0.15):1;
    s+=`<polygon points="${x+60},1050 ${x-160},1560 ${x+280},1560" fill="url(#cone)" opacity="${on}"/>
        <rect x="${x+50}" y="1030" width="14" height="530" fill="#0a0820"/><rect x="${x+20}" y="1030" width="80" height="16" fill="#0a0820"/>
        <rect x="${x+40}" y="1044" width="40" height="8" fill="#ffe7a3" opacity="${on}"/>
        <ellipse cx="${x+60}" cy="1565" rx="230" ry="38" fill="#ffe7a3" opacity="${0.12*on}"/>`;}
  s+=`<rect y="1540" width="1080" height="70" fill="#2a2450"/><rect y="1610" width="1080" height="400" fill="#141127"/>`;
  for(let i=0;i<8;i++){const x=((i*200-off*1.2)%%1600+1600)%%1600-200; s+=`<rect x="${x}" y="1760" width="110" height="12" fill="#3a3560"/>`;}
  return s+`</svg>`;
}
// --- perso à capuche
function hero(x, y, t, mode){
  const walk = mode=='marche', bob = walk? Math.abs(Math.sin(t*7))*-14 : Math.sin(t*2)*4;
  const leg = walk? Math.sin(t*7)*26 : 0, ring = mode=='sonne', scared = mode=='peur';
  const shake = ring? Math.sin(t*90)*3 : (scared? Math.sin(t*40)*2:0);
  const eyesY = scared? 0 : 4, eh = scared? 30 : 16;
  const glow = ring? 0.6+0.4*Math.sin(t*12) : 0.25;
  return `<svg width="1080" height="1920" style="position:absolute;inset:0"><g transform="translate(${x+shake},${y+bob}) scale(1.6)">
   <ellipse cx="0" cy="185" rx="80" ry="14" fill="#000" opacity=".35"/>
   <rect x="${-38+leg}" y="150" width="34" height="34" rx="10" fill="#e8ecf5"/><rect x="${6-leg}" y="150" width="34" height="34" rx="10" fill="#e8ecf5"/>
   <rect x="-62" y="40" width="124" height="128" rx="40" fill="#22b3a0"/>
   <rect x="-34" y="112" width="68" height="34" rx="12" fill="#1b9585"/>
   <circle cx="0" cy="0" r="74" fill="#22b3a0"/>
   <circle cx="0" cy="2" r="60" fill="#0d0d16" stroke="#7ff3e4" stroke-width="4" opacity=".98"/>
   ${scared?`<circle cx="-22" cy="${eyesY}" r="17" fill="#fff"/><circle cx="22" cy="${eyesY}" r="17" fill="#fff"/><circle cx="-22" cy="${eyesY+2}" r="7" fill="#000"/><circle cx="22" cy="${eyesY+2}" r="7" fill="#000"/>`
   :`<path d="M-40 ${eyesY-6} h36 v${eh/2} a18 ${eh/2} 0 0 1 -36 0z" fill="#fff"/><path d="M4 ${eyesY-6} h36 v${eh/2} a18 ${eh/2} 0 0 1 -36 0z" fill="#fff"/>
     <circle cx="-20" cy="${eyesY}" r="6" fill="#000"/><circle cx="24" cy="${eyesY}" r="6" fill="#000"/>`}
   <rect x="-26" y="68" width="52" height="84" rx="10" fill="#0b1020"/><rect x="-21" y="74" width="42" height="72" rx="7" fill="#7fb4ff" opacity="${glow+0.3}"/>
   <circle cx="-30" cy="120" r="14" fill="#1b9585"/><circle cx="30" cy="120" r="14" fill="#1b9585"/>
   ${ring?`<path d="M-56 80 l-14 -8 M-58 104 l-18 0 M-56 128 l-14 8 M56 80 l14 -8 M58 104 l18 0 M56 128 l14 8" stroke="#bfe3ff" stroke-width="5" stroke-linecap="round" opacity="${glow}"/>`:''}
   <ellipse cx="0" cy="110" rx="140" ry="160" fill="#7fb4ff" opacity="${glow*0.08}"/>
  </g></svg>`;
}
function shadowFig(x,y,a){
  return `<svg width="1080" height="1920" style="position:absolute;inset:0;opacity:${a}"><g transform="translate(${x},${y}) scale(1.75)">
   <circle cx="0" cy="0" r="74" fill="#05040c"/><rect x="-66" y="40" width="132" height="150" rx="40" fill="#05040c"/>
   <circle cx="-22" cy="4" r="7" fill="#fff" opacity=".9"/><circle cx="22" cy="4" r="7" fill="#fff" opacity=".9"/>
   <rect x="-22" y="76" width="44" height="72" rx="8" fill="#7fb4ff" opacity=".8"/><ellipse cx="0" cy="110" rx="90" ry="110" fill="#7fb4ff" opacity=".07"/></g></svg>`;
}
function phone(inner, lt){
  return `<div class="phone"><div class="scr"><div class="isl"></div><div class="sb"><span>3:00</span><span>▮▮▮ ▭</span></div>${inner}</div></div>`;
}
function appel(t, nom){
  const p = 1+0.06*Math.sin(t*8);
  return phone(`<div style="position:absolute;top:150px;left:0;right:0;text-align:center;color:#cfd6ff;font-size:32px">appel mobile…</div>
   <div style="position:absolute;top:220px;left:50%%;transform:translateX(-50%%) scale(${p});width:220px;height:220px;border-radius:50%%;background:#22b3a0;border:6px solid #7ff3e4;display:flex;align-items:center;justify-content:center">
     <svg width="160" height="160" viewBox="-80 -80 160 160"><circle r="62" fill="#0d0d16"/><path d="M-40 -8 h34 v8 a17 8 0 0 1 -34 0z M6 -8 h34 v8 a17 8 0 0 1 -34 0z" fill="#fff"/></svg></div>
   <div style="position:absolute;top:480px;left:0;right:0;text-align:center;color:#fff;font-size:70px;font-weight:800">${nom}</div>
   <div style="position:absolute;top:575px;left:0;right:0;text-align:center;color:#aab3e0;font-size:34px">06 41 27 93 08 · ton numéro</div>
   <div class="btn" style="left:70px;top:860px;background:#ff3b30">✕</div><div class="btn" style="right:70px;top:860px;background:#34c759;transform:rotate(${Math.sin(t*20)*12}deg)">✆</div>`);
}
function sms(t, lignes){
  let h = `<div style="position:absolute;top:110px;left:0;right:0;text-align:center;color:#fff"><div style="width:90px;height:90px;margin:0 auto;border-radius:50%%;background:#22b3a0;border:4px solid #7ff3e4"></div>
   <div style="font-size:30px;margin-top:10px;font-weight:700">Moi</div></div>`;
  let y = 330;
  lignes.forEach((l,i)=>{ const at = 0.2 + i*0.9;
    if (t < at) return;
    if (t < at+0.6) { h += `<div class="bubble" style="top:${y}px;font-size:48px;letter-spacing:6px">• • •</div>`; y+=140; return; }
    const a = ease((t-at-0.6)/0.2);
    h += `<div class="bubble" style="top:${y}px;opacity:${a};transform:scale(${0.8+0.2*a});transform-origin:left">${l}</div>`; y += 60 + 46*Math.ceil(l.length/20);
  });
  return phone(h + `<div style="position:absolute;bottom:40px;left:40px;right:40px;height:80px;border-radius:40px;border:2px solid #3a4170;color:#59608a;font-size:30px;padding:20px 30px">Message</div>`);
}
function regle(t, n, txt){
  const a = ease(t/0.25), s = 0.85+0.15*a;
  return `<div class="card"></div><div style="position:absolute;top:760px;left:0;right:0;text-align:center;transform:scale(${s});opacity:${a}">
    <span style="display:inline-block;background:#e0202a;color:#fff;font-family:Anton;font-size:84px;padding:6px 40px;border-radius:14px;border:4px solid #ff8a8f">RÈGLE N°${n}</span>
    <div style="font-family:Anton;color:#fff;font-size:118px;margin-top:40px;line-height:1.05;text-transform:uppercase">${txt}</div></div>`;
}
function choix(t, a1, a2){
  const p = k => ease((t-0.15*k)/0.3);
  return `<div class="card" style="background:radial-gradient(circle at 50%% 45%%,#1a1747,#07061a)"></div>
   <div style="position:absolute;top:520px;left:0;right:0;text-align:center;color:#fff;font-size:44px;letter-spacing:6px;font-weight:800;opacity:${p(0)}">À TOI DE CHOISIR</div>
   <div class="choice" style="top:640px;background:#ff7a1a;box-shadow:0 0 60px #ff7a1a88;transform:scale(${0.7+0.3*p(1)});opacity:${p(1)}">1 · ${a1}</div>
   <div style="position:absolute;top:840px;left:0;right:0;text-align:center;color:#aab;font-size:46px;font-weight:800;opacity:${p(2)}">OU</div>
   <div class="choice" style="top:940px;background:#2f7bff;box-shadow:0 0 60px #2f7bff88;transform:scale(${0.7+0.3*p(3)});opacity:${p(3)}">2 · ${a2}</div>`;
}
// --- sous-titres : morceaux de 1-2 mots
const MW = (()=>{const m=[];for(const w of WORDS){const x=w[2].trim();if(m.length&&(x.startsWith("'")||m[m.length-1][2].endsWith("'")))m[m.length-1]=[m[m.length-1][0],w[1],m[m.length-1][2].trim()+x];else m.push([w[0],w[1],x])}return m})();
const CH = (()=>{const out=[];let cur=[];for(const w of MW){cur.push(w);const txt=w[2].trim();if(cur.length==2||/[.,!?:]$/.test(txt)){out.push(cur);cur=[]}}if(cur.length)out.push(cur);return out})();
const RED = new Set(EP.rouge||[]), YEL = new Set(EP.jaune||[]);
function subs(t){
  for(let i=0;i<CH.length;i++){const c=CH[i],a=c[0][0],b=Math.min(i+1<CH.length?CH[i+1][0][0]:c[c.length-1][1]+0.4,c[c.length-1][1]+0.5);
    if(t>=a&&t<b){const k=ease((t-a)/0.09);
      return `<span style="display:inline-block;transform:scale(${0.8+0.2*k})">`+c.map(w=>{const x=w[2].trim(),key=x.toLowerCase().replace(/[.,!?:]/g,'');
        return RED.has(key)?`<span class="r">${x}</span>`:YEL.has(key)?`<span class="y">${x}</span>`:x}).join(' ').replace(/[.,]$/,'')+`</span>`;}}
  return '';
}
function hms(base, t){const [h,m,s]=base.split(':').map(Number);let x=h*3600+m*60+s+Math.floor(t);
  return [Math.floor(x/3600)%%24,Math.floor(x/60)%%60,x%%60].map(v=>String(v).padStart(2,'0')).join(':')}
window.seek = function(t){
  let k=0; for(let i=0;i<STARTS.length;i++) if(t>=STARTS[i]) k=i;
  const P = EP.plans[k], lt = t-STARTS[k], ty = P.type;
  let html='', zoom=1, cx=0;
  if (ty.startsWith('rue')){
    const off = ty=='rue_marche' ? t*90 : STARTS[1]*90;
    html = city(off, ty=='rue_peur');
    if (ty=='rue_peur') html += shadowFig(300, 1330, ease((lt-0.15)/0.5)*0.95);
    html += hero(ty=='rue_peur'?600:540, 1260, t, {rue_marche:'marche',rue_sonne:'sonne',rue_peur:'peur'}[ty]);
    zoom = ty=='rue_sonne' ? 1+0.25*ease(lt/1.5) : ty=='rue_peur' ? 1.05+0.04*lt : 1.02;
  } else if (ty=='appel'){ html = city(STARTS[1]*90,false)+`<div class="layer" style="background:rgba(5,4,15,.55)"></div>`+appel(lt, P.nom||'Moi'); zoom = 0.9+0.1*ease(lt/0.3)+0.01*lt;
  } else if (ty=='sms'){ html = city(STARTS[1]*90,false)+`<div class="layer" style="background:rgba(5,4,15,.55)"></div>`+sms(lt, P.lignes); zoom = 0.9+0.1*ease(lt/0.3)+0.01*lt;
  } else if (ty=='regle'){ html = regle(lt, P.n, P.txt);
  } else if (ty=='choix'){ html = choix(lt, P.a1, P.a2); }
  cam.innerHTML = html;
  cam.style.transform = `scale(${zoom})`;
  document.getElementById('clock').style.display = (ty=='regle'||ty=='choix')?'none':'block';
  document.getElementById('lieu').textContent = EP.lieu;
  document.getElementById('tm').textContent = hms(EP.heure, t);
  sub.innerHTML = subs(t);
  sub.style.top = (ty=='choix') ? '1250px' : '1590px';
};
</script></body></html>"""


def main(ep_path, audio, words_path, starts, out):
    ep = json.load(open(ep_path))
    words = json.load(open(words_path))
    starts = [float(x) for x in starts.split(",")]
    total = float(subprocess.run(["ffprobe", "-v", "error", "-show_entries", "format=duration", "-of", "csv=p=0", audio],
                                 capture_output=True, text=True).stdout)
    html = HTML % {"font": FONT, "ep": json.dumps(ep, ensure_ascii=False), "starts": json.dumps(starts),
                   "words": json.dumps(words, ensure_ascii=False), "total": total}
    tmp = out + ".html"
    open(tmp, "w").write(html)
    from playwright.sync_api import sync_playwright
    n = int(total * FPS)
    ff = subprocess.Popen(["ffmpeg", "-y", "-loglevel", "error", "-f", "image2pipe", "-framerate", str(FPS), "-i", "-", "-i", audio,
                           "-filter_complex", "[1:a]loudnorm=I=-14:TP=-1.5,aresample=44100,alimiter=limit=0.7[a]",
                           "-map", "0:v", "-map", "[a]", "-c:v", "libx264", "-crf", "18", "-preset", "medium", "-pix_fmt", "yuv420p",
                           "-c:a", "aac", "-b:a", "192k", "-shortest", "-movflags", "+faststart", out], stdin=subprocess.PIPE)
    with sync_playwright() as p:
        exe = os.environ.get("CHROME", "/opt/pw-browsers/chromium")
        b = p.chromium.launch(executable_path=exe if os.path.exists(exe) else None, args=["--no-sandbox"])
        pg = b.new_page(viewport={"width": W, "height": H})
        pg.goto("file://" + os.path.abspath(tmp))
        pg.wait_for_timeout(500)
        for i in range(n):
            pg.evaluate(f"seek({i / FPS})")
            ff.stdin.write(pg.screenshot(type="jpeg", quality=92))
            if i % 150 == 0:
                print(f"image {i}/{n}", flush=True)
        b.close()
    ff.stdin.close()
    ff.wait()
    os.remove(tmp)
    print("OK", out)


if __name__ == "__main__":
    main(*sys.argv[1:])
