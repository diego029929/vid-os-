// Style « Nuit & téléphone » : tout le dessin (SVG/HTML). engine/nuit.py appelle seek(t) pour chaque image.
// Données injectées avant ce fichier : EP (épisode), BEATS ([{t0, t1, ...plan}]), WORDS ([[a, b, mot, couleur]]), AMP (bouche, 1 valeur par image), FPS.
'use strict';
const VW = 1080, VH = 1920;
const cam = document.getElementById('cam'), sub = document.getElementById('sub');
const rnd = s => { const x = Math.sin(s * 999.13 + 7.7) * 43758.5453; return x - Math.floor(x); };
const ease = x => x <= 0 ? 0 : x >= 1 ? 1 : 1 - Math.pow(1 - x, 3);
const svg = (inner, style = '') => `<svg width="${VW}" height="${VH}" viewBox="0 0 ${VW} ${VH}" style="position:absolute;inset:0;${style}">${inner}</svg>`;
const DEFS = `<defs>
 <radialGradient id="glow"><stop offset="0" stop-color="#fff" stop-opacity=".35"/><stop offset="1" stop-color="#fff" stop-opacity="0"/></radialGradient>
 <radialGradient id="warm"><stop offset="0" stop-color="#ffe7a3" stop-opacity=".55"/><stop offset="1" stop-color="#ffe7a3" stop-opacity="0"/></radialGradient>
 <radialGradient id="cold"><stop offset="0" stop-color="#9fd0ff" stop-opacity=".5"/><stop offset="1" stop-color="#9fd0ff" stop-opacity="0"/></radialGradient>
 <radialGradient id="redg"><stop offset="0" stop-color="#ff3b3b" stop-opacity=".45"/><stop offset="1" stop-color="#ff3b3b" stop-opacity="0"/></radialGradient>
 <linearGradient id="sky" x1="0" y1="0" x2="0" y2="1"><stop offset="0" stop-color="#0b0a24"/><stop offset=".55" stop-color="#2b2366"/><stop offset="1" stop-color="#3a2f78"/></linearGradient>
 <linearGradient id="wall" x1="0" y1="0" x2="0" y2="1"><stop offset="0" stop-color="#1c1840"/><stop offset="1" stop-color="#2c2660"/></linearGradient>
 <linearGradient id="cone" x1="0" y1="0" x2="0" y2="1"><stop offset="0" stop-color="#ffe7a3" stop-opacity=".45"/><stop offset="1" stop-color="#ffe7a3" stop-opacity="0"/></linearGradient>
 <linearGradient id="sea" x1="0" y1="0" x2="0" y2="1"><stop offset="0" stop-color="#1d2a66"/><stop offset="1" stop-color="#0a0f2a"/></linearGradient>
</defs>`;
let FL = 1; // lumière qui clignote (1 = allumée)
const moon = (x, y) => `<circle cx="${x}" cy="${y}" r="190" fill="url(#glow)"/><circle cx="${x}" cy="${y}" r="62" fill="#e9e6f5"/>`;
const win = (x, y, w, h, t) => `<rect x="${x}" y="${y}" width="${w}" height="${h}" rx="6" fill="#0d0b28" stroke="#3c3478" stroke-width="10"/>
  <circle cx="${x + w * 0.7}" cy="${y + h * 0.3}" r="${Math.min(w, h) * 0.12}" fill="#e9e6f5" opacity=".9"/>
  <line x1="${x + w / 2}" y1="${y}" x2="${x + w / 2}" y2="${y + h}" stroke="#3c3478" stroke-width="8"/><line x1="${x}" y1="${y + h / 2}" x2="${x + w}" y2="${y + h / 2}" stroke="#3c3478" stroke-width="8"/>`;
const door = (x, y, w, h, c = '#3b2f6e', open = 0) => `<rect x="${x}" y="${y}" width="${w}" height="${h}" rx="8" fill="${c}" stroke="#14112c" stroke-width="10"/>
  <rect x="${x + w * 0.15}" y="${y + h * 0.08}" width="${w * 0.7}" height="${h * 0.36}" rx="6" fill="none" stroke="#14112c" stroke-opacity=".5" stroke-width="6"/>
  <rect x="${x + w * 0.15}" y="${y + h * 0.52}" width="${w * 0.7}" height="${h * 0.38}" rx="6" fill="none" stroke="#14112c" stroke-opacity=".5" stroke-width="6"/>
  <circle cx="${x + w * 0.82}" cy="${y + h * 0.52}" r="12" fill="#e2b24a"/>${open ? `<rect x="${x}" y="${y}" width="${w * open}" height="${h}" fill="#05040c"/>` : ''}`;
const floor = (y, c1 = '#2a2450', c2 = '#141127') => `<rect y="${y}" width="${VW}" height="70" fill="${c1}"/><rect y="${y + 70}" width="${VW}" height="${VH - y}" fill="${c2}"/>`;
const lamp = (x, y, on) => `<rect x="${x - 3}" y="0" width="6" height="${y}" fill="#0a0820"/><path d="M${x - 50} ${y + 40} L${x - 22} ${y} h44 L${x + 50} ${y + 40}z" fill="#0a0820"/>
  <circle cx="${x}" cy="${y + 40}" r="${260}" fill="url(#warm)" opacity="${on}"/><ellipse cx="${x}" cy="${y + 46}" rx="34" ry="8" fill="#ffe7a3" opacity="${on}"/>`;

// ------------------------------------------------------------------ décors
function city(off, flick) {
  let s = `<rect width="${VW}" height="${VH}" fill="url(#sky)"/>${moon(760 - off * 0.05, 420)}`;
  for (const [layer, base, par, col, wc] of [[0, 1080, 0.25, '#231d52', '#4b3f8a'], [1, 1180, 0.6, '#1a1540', '#f2c86b']]) {
    for (let i = 0; i < 26; i++) {
      const w = 120 + rnd(i + layer * 50) * 140, h = 250 + rnd(i * 3 + layer * 7) * 420, x = ((i * 150 - off * par) % 3900 + 3900) % 3900 - 300;
      s += `<rect x="${x}" y="${base - h}" width="${w}" height="${h + 200}" fill="${col}"/>`;
      for (let r = 0; r < h / 70 - 1; r++) for (let c = 0; c < w / 50 - 1; c++) if (rnd(i * 97 + r * 13 + c * 7 + layer) > 0.55)
        s += `<rect x="${x + 20 + c * 48}" y="${base - h + 30 + r * 68}" width="24" height="30" fill="${wc}" opacity="${layer ? 0.9 : 0.5}"/>`;
    }
  }
  for (let i = 0; i < 4; i++) {
    const x = ((i * 520 + 200 - off) % 2080 + 2080) % 2080 - 300, on = flick && i == 1 ? FL : 1;
    s += `<polygon points="${x + 60},1050 ${x - 160},1560 ${x + 280},1560" fill="url(#cone)" opacity="${on}"/>
      <rect x="${x + 50}" y="1030" width="14" height="530" fill="#0a0820"/><rect x="${x + 20}" y="1030" width="80" height="16" fill="#0a0820"/>
      <rect x="${x + 40}" y="1044" width="40" height="8" fill="#ffe7a3" opacity="${on}"/><ellipse cx="${x + 60}" cy="1565" rx="230" ry="38" fill="#ffe7a3" opacity="${0.12 * on}"/>`;
  }
  s += `<rect y="1540" width="${VW}" height="70" fill="#2a2450"/><rect y="1610" width="${VW}" height="400" fill="#141127"/>`;
  for (let i = 0; i < 8; i++) { const x = ((i * 200 - off * 1.2) % 1600 + 1600) % 1600 - 200; s += `<rect x="${x}" y="1760" width="110" height="12" fill="#3a3560"/>`; }
  return s;
}
const DECORS = {
  rue: (P, t, off) => city(off, P.flicker),
  chambre: (P, t) => `<rect width="${VW}" height="${VH}" fill="url(#wall)"/>${win(600, 520, 300, 380, t)}
    <rect x="150" y="620" width="200" height="260" rx="6" fill="#3a2f78" opacity=".6"/><rect x="170" y="640" width="160" height="220" fill="#4b3f8a" opacity=".5"/>
    ${floor(1540)}<rect x="40" y="1330" width="560" height="230" rx="30" fill="#4a3f8f"/><rect x="40" y="1290" width="200" height="90" rx="30" fill="#e8ecf5"/>
    <rect x="40" y="1400" width="560" height="160" rx="20" fill="#5d52a8"/><rect x="760" y="1360" width="200" height="200" rx="10" fill="#2c2660"/>
    <rect x="830" y="1250" width="60" height="110" fill="#2c2660"/><path d="M800 1250 h120 l-30 -80 h-60z" fill="#e8d18a" opacity="${0.6 + 0.4 * FL}"/>
    <circle cx="860" cy="1220" r="300" fill="url(#warm)" opacity="${0.8 * FL}"/>`,
  couloir: (P, t) => { let s = `<rect width="${VW}" height="${VH}" fill="#16132f"/><polygon points="0,300 1080,300 760,820 320,820" fill="#1f1b42"/>
    <polygon points="0,1700 1080,1700 760,1060 320,1060" fill="#26214f"/><polygon points="0,300 320,820 320,1060 0,1700" fill="#221d4a"/>
    <polygon points="1080,300 760,820 760,1060 1080,1700" fill="#221d4a"/><rect x="320" y="820" width="440" height="240" fill="#07061a"/>`;
    for (let i = 0; i < 3; i++) { const k = 0.35 + i * 0.22, on = (P.flicker && i == 1) ? FL : 1;
      s += `<rect x="${540 - 140 * (1 - k * 0.9)}" y="${300 + 520 * k * 0.95}" width="${280 * (1 - k * 0.9)}" height="${14 * (1 - k * 0.6)}" fill="#dff2ff" opacity="${on}"/>
        <ellipse cx="540" cy="${330 + 520 * k}" rx="${420 * (1 - k * 0.8)}" ry="${200 * (1 - k * 0.8)}" fill="url(#cold)" opacity="${on * 0.7}"/>`;
      s += `<polygon points="${60 + i * 95},${520 + i * 160} ${150 + i * 70},${600 + i * 120} ${150 + i * 70},${1250 - i * 60} ${60 + i * 95},${1420 - i * 110}" fill="#3b2f6e" stroke="#14112c" stroke-width="6"/>`;
      s += `<polygon points="${1020 - i * 95},${520 + i * 160} ${930 - i * 70},${600 + i * 120} ${930 - i * 70},${1250 - i * 60} ${1020 - i * 95},${1420 - i * 110}" fill="#3b2f6e" stroke="#14112c" stroke-width="6"/>`; }
    return s; },
  salon: (P, t) => `<rect width="${VW}" height="${VH}" fill="url(#wall)"/>${win(120, 520, 320, 420, t)}
    <rect x="600" y="760" width="380" height="240" rx="12" fill="#07061a" stroke="#2c2660" stroke-width="12"/>
    <rect x="618" y="778" width="344" height="204" fill="#9fd0ff" opacity="${0.15 + 0.25 * Math.abs(Math.sin(t * 9)) * FL}"/>
    <circle cx="790" cy="880" r="420" fill="url(#cold)" opacity="${0.5 * FL}"/>${floor(1540)}
    <rect x="80" y="1300" width="620" height="260" rx="40" fill="#4a3f8f"/><rect x="80" y="1230" width="620" height="140" rx="40" fill="#5d52a8"/>
    <rect x="760" y="1420" width="240" height="140" rx="10" fill="#2c2660"/>`,
  cuisine: (P, t) => `<rect width="${VW}" height="${VH}" fill="url(#wall)"/>${win(380, 500, 320, 330, t)}
    <rect x="0" y="1140" width="${VW}" height="40" fill="#5d52a8"/><rect x="0" y="1180" width="${VW}" height="380" fill="#3b2f6e"/>
    ${[0, 1, 2, 3].map(i => `<rect x="${30 + i * 260}" y="1220" width="230" height="300" rx="10" fill="#4a3f8f"/><rect x="${125 + i * 260}" y="1240" width="40" height="10" rx="5" fill="#e2b24a"/>`).join('')}
    <rect x="820" y="620" width="230" height="520" rx="16" fill="#cfd3e8"/><rect x="820" y="820" width="230" height="10" fill="#9aa0bf"/>
    <rect x="40" y="560" width="280" height="160" rx="10" fill="#3b2f6e"/>${floor(1560)}
    ${lamp(540, 260, FL)}`,
  escalier: (P, t) => { let s = `<rect width="${VW}" height="${VH}" fill="url(#wall)"/>`;
    for (let i = 0; i < 9; i++) s += `<rect x="${i * 120}" y="${1540 - i * 110}" width="${VW - i * 120}" height="110" fill="${i % 2 ? '#3b2f6e' : '#342a63'}"/><rect x="${i * 120}" y="${1540 - i * 110}" width="${VW - i * 120}" height="14" fill="#5d52a8"/>`;
    s += `<line x1="0" y1="1300" x2="1080" y2="310" stroke="#14112c" stroke-width="16"/>`;
    for (let i = 0; i < 9; i++) s += `<line x1="${i * 120 + 40}" y1="${1263 - i * 110}" x2="${i * 120 + 40}" y2="${1420 - i * 110}" stroke="#14112c" stroke-width="8"/>`;
    return s + lamp(820, 330, P.flicker ? FL : 1) + floor(1650); },
  foret: (P, t) => { let s = `<rect width="${VW}" height="${VH}" fill="url(#sky)"/>${moon(300, 420)}`;
    for (const [n, col, base, sc] of [[9, '#211b4d', 1250, 0.7], [7, '#120f2e', 1500, 1.1]]) for (let i = 0; i < n; i++) { const x = i * (VW / (n - 1)) + rnd(i + n) * 60 - 30, h = 700 * sc + rnd(i * 5) * 200;
      s += `<rect x="${x - 14 * sc}" y="${base - 120}" width="${28 * sc}" height="160" fill="${col}"/>`;
      for (let k = 0; k < 4; k++) s += `<polygon points="${x},${base - h + k * h * 0.2} ${x - 110 * sc - k * 25},${base - h * 0.55 + k * h * 0.2} ${x + 110 * sc + k * 25},${base - h * 0.55 + k * h * 0.2}" fill="${col}"/>`; }
    s += `<rect y="1500" width="${VW}" height="420" fill="#0d0b22"/>`;
    for (let i = 0; i < 3; i++) s += `<ellipse cx="${((i * 420 + t * 30) % 1500) - 200}" cy="${1420 + i * 40}" rx="420" ry="60" fill="#8f86c9" opacity=".08"/>`;
    return s; },
  station: (P, t) => `${city(0, false)}<rect y="900" width="${VW}" height="700" fill="#141127" opacity=".55"/>
    <rect x="60" y="900" width="960" height="70" rx="8" fill="#e8ecf5"/><rect x="60" y="960" width="960" height="18" fill="#e0202a"/>
    <rect x="120" y="978" width="840" height="20" fill="#dff2ff" opacity="${FL}"/><rect x="0" y="990" width="${VW}" height="560" fill="url(#cold)" opacity="${0.55 * FL}"/>
    ${[260, 760].map(x => `<rect x="${x}" y="1240" width="120" height="300" rx="10" fill="#e8ecf5"/><rect x="${x + 18}" y="1270" width="84" height="60" fill="#0b1020"/><text x="${x + 60}" y="1312" font-size="34" fill="#ff3b3b" text-anchor="middle" font-family="monospace">88.8</text>`).join('')}
    <rect x="150" y="978" width="16" height="560" fill="#9aa0bf"/><rect x="910" y="978" width="16" height="560" fill="#9aa0bf"/>
    <rect y="1540" width="${VW}" height="380" fill="#1a1636"/>`,
  mer: (P, t) => { let s = `<rect width="${VW}" height="${VH}" fill="url(#sky)"/>${moon(700, 560)}<rect y="1050" width="${VW}" height="600" fill="url(#sea)"/>`;
    for (let i = 0; i < 9; i++) s += `<rect x="${600 + Math.sin(t * 2 + i) * 30}" y="${1080 + i * 40}" width="${200 - i * 15}" height="8" fill="#e9e6f5" opacity="${0.5 - i * 0.04}"/>`;
    const a = t * 1.2; s += `<rect x="170" y="700" width="80" height="350" fill="#e8ecf5"/><rect x="170" y="800" width="80" height="40" fill="#e0202a"/><rect x="170" y="920" width="80" height="40" fill="#e0202a"/>
      <rect x="160" y="650" width="100" height="60" fill="#ffe7a3"/><polygon points="210,680 ${210 + Math.cos(a) * 900},${680 - 150} ${210 + Math.cos(a) * 900},${680 + 150}" fill="#ffe7a3" opacity="${0.12 + 0.1 * Math.abs(Math.cos(a))}"/>
      <path d="M0 1560 Q540 1480 1080 1560 V1920 H0z" fill="#2c2448"/>`; return s; },
  hopital: (P, t) => { let s = `<rect width="${VW}" height="${VH}" fill="#1d2440"/>`;
    for (let r = 0; r < 12; r++) for (let c = 0; c < 9; c++) s += `<rect x="${c * 120 + 4}" y="${900 + r * 60 + 4}" width="112" height="52" fill="#26304f"/>`;
    s += `<rect y="880" width="${VW}" height="20" fill="#3a4670"/>${win(120, 420, 260, 380, t)}${win(700, 420, 260, 380, t)}
      <rect x="300" y="1240" width="520" height="40" rx="10" fill="#cfd3e8"/><rect x="300" y="1190" width="140" height="60" rx="20" fill="#e8ecf5"/>
      <rect x="310" y="1280" width="14" height="260" fill="#9aa0bf"/><rect x="796" y="1280" width="14" height="260" fill="#9aa0bf"/><rect x="300" y="1140" width="14" height="140" fill="#9aa0bf"/>
      ${lamp(540, 180, P.flicker ? FL : 1)}${floor(1560, '#3a4670', '#151a30')}`; return s; },
  cave: (P, t) => { let s = `<rect width="${VW}" height="${VH}" fill="#1a1530"/>`;
    for (let r = 0; r < 26; r++) for (let c = -1; c < 8; c++) s += `<rect x="${c * 150 + (r % 2) * 75 + 4}" y="${r * 60 + 4}" width="142" height="52" rx="4" fill="#241d44"/>`;
    const sw = Math.sin(t * 1.5) * 6;
    s += `<line x1="540" y1="0" x2="${540 + sw}" y2="520" stroke="#0a0820" stroke-width="5"/><circle cx="${540 + sw}" cy="545" r="28" fill="#ffe7a3" opacity="${FL}"/><circle cx="${540 + sw}" cy="545" r="520" fill="url(#warm)" opacity="${0.8 * FL}"/>
      <rect x="80" y="1300" width="260" height="240" fill="#4a3a2a"/><rect x="120" y="1180" width="200" height="130" fill="#5a4632"/><rect x="760" y="1360" width="240" height="180" fill="#4a3a2a"/>
      ${floor(1540, '#2a2340', '#110e22')}`; return s; },
  voiture: (P, t) => { let s = `<rect width="${VW}" height="${VH}" fill="#07061a"/><rect x="0" y="380" width="${VW}" height="760" fill="url(#sky)"/>`;
    s += `<polygon points="540,620 100,1140 980,1140" fill="#1a1636"/>`; for (let i = 0; i < 6; i++) { const k = ((i * 0.2 + t * 0.8) % 1.2); s += `<rect x="${540 - 6 - k * 40}" y="${640 + k * k * 420}" width="${12 + k * 80}" height="${10 + k * 30}" fill="#ffe7a3" opacity=".8"/>`; }
    s += `<path d="M0 380 Q540 300 1080 380 V420 Q540 360 0 420z" fill="#0b0a1c"/><rect y="1100" width="${VW}" height="820" fill="#110e24"/>
      <path d="M0 1140 Q540 1060 1080 1140 V1300 H0z" fill="#1d1838"/><circle cx="330" cy="1330" r="190" fill="none" stroke="#2c2660" stroke-width="40"/>
      <rect x="640" y="1180" width="180" height="70" rx="10" fill="#0b1020"/><text x="730" y="1230" font-size="40" fill="#ff7a1a" text-anchor="middle" font-family="monospace">3:00</text>
      <rect x="0" y="380" width="60" height="760" fill="#0b0a1c"/><rect x="1020" y="380" width="60" height="760" fill="#0b0a1c"/>`;
    if (P.pluie) for (let i = 0; i < 40; i++) s += `<circle cx="${rnd(i) * VW}" cy="${400 + ((rnd(i * 3) * 700 + t * 120 * (1 + rnd(i))) % 700)}" r="${4 + rnd(i * 7) * 6}" fill="#9fd0ff" opacity=".35"/>`;
    return s; },
  sdb: (P, t) => { let s = `<rect width="${VW}" height="${VH}" fill="#1c2346"/>`;
    for (let r = 0; r < 30; r++) for (let c = 0; c < 9; c++) s += `<rect x="${c * 120 + 3}" y="${r * 64 + 3}" width="114" height="58" fill="#232c55"/>`;
    s += `<rect x="290" y="420" width="500" height="560" rx="20" fill="#9fb2d9" stroke="#cfd3e8" stroke-width="14"/><rect x="310" y="440" width="460" height="520" rx="12" fill="#3a4a7a"/>
      ${P.reflet ? `<g opacity=".9"><circle cx="540" cy="700" r="110" fill="#05040c"/><circle cx="505" cy="705" r="11" fill="#fff"/><circle cx="575" cy="705" r="11" fill="#fff"/></g>` : ''}
      <rect x="320" y="1060" width="440" height="80" rx="20" fill="#e8ecf5"/><rect x="500" y="1140" width="80" height="400" fill="#cfd3e8"/>${lamp(540, 200, P.flicker ? FL : 1)}${floor(1560, '#2c3766', '#141a33')}`; return s; },
  // --- décors « Vice » (clips GTA 6, 19/11) : plage au coucher de soleil, chambre de joueur
  vice: (P, t, off) => { let s = `<defs><linearGradient id="vsky" x1="0" y1="0" x2="0" y2="1"><stop offset="0" stop-color="#2a0f4f"/><stop offset=".45" stop-color="#c2307a"/><stop offset=".75" stop-color="#ff8a3d"/><stop offset="1" stop-color="#ffc86b"/></linearGradient>
    <linearGradient id="vsun" x1="0" y1="0" x2="0" y2="1"><stop offset="0" stop-color="#ffe36b"/><stop offset="1" stop-color="#ff4f7b"/></linearGradient></defs>
    <rect width="${VW}" height="${VH}" fill="url(#vsky)"/><circle cx="540" cy="900" r="300" fill="url(#vsun)"/>`;
    for (let i = 0; i < 6; i++) s += `<rect x="200" y="${930 + i * 38}" width="680" height="${6 + i * 4}" fill="#c2307a"/>`;
    for (let i = 0; i < 18; i++) { const w = 70 + rnd(i) * 90, h = 120 + rnd(i * 3) * 330, x = ((i * 70 - off * 0.3) % 1300 + 1300) % 1300 - 110;
      s += `<rect x="${x}" y="${1180 - h}" width="${w}" height="${h}" fill="#3a1450" opacity=".85"/>`;
      for (let r = 0; r < h / 60 - 1; r++) if (rnd(i * 31 + r) > 0.5) s += `<rect x="${x + 14}" y="${1180 - h + 24 + r * 58}" width="${w - 28}" height="10" fill="#ff7ad9" opacity=".7"/>`; }
    s += `<rect y="1180" width="${VW}" height="260" fill="#3b1d6e"/>`;
    for (let i = 0; i < 10; i++) s += `<rect x="${(i * 137 + Math.sin(t * 1.5 + i) * 40 + 1080) % 1080}" y="${1200 + i * 22}" width="${160 - i * 8}" height="6" fill="#ffb36b" opacity="${0.6 - i * 0.04}"/>`;
    s += `<path d="M0 1440 Q540 1400 1080 1440 V1920 H0z" fill="#f2c27b"/><rect y="1600" width="${VW}" height="320" fill="#e0a862"/>`;
    const palm = (x, y, sc, sw) => { let q = `<path d="M${x} ${y} Q${x + 30 * sc} ${y - 300 * sc} ${x + 10 * sc} ${y - 620 * sc}" stroke="#1a0b2e" stroke-width="${26 * sc}" fill="none"/>`;
      const tx = x + 10 * sc, ty = y - 620 * sc;
      for (let k = 0; k < 7; k++) { const a = -Math.PI * (0.05 + k * 0.15) + sw; q += `<path d="M${tx} ${ty} Q${tx + Math.cos(a) * 180 * sc} ${ty + Math.sin(a) * 180 * sc - 60 * sc} ${tx + Math.cos(a) * 330 * sc} ${ty + Math.sin(a) * 200 * sc + 90 * sc}" stroke="#1a0b2e" stroke-width="${30 * sc}" fill="none" stroke-linecap="round"/>`; }
      return q; };
    s += palm(110, 1700, 1.25, Math.sin(t * 1.3) * 0.05) + palm(980, 1640, 1.0, Math.sin(t * 1.1 + 1) * 0.05);
    return s; },
  gamer: (P, t) => { const tv = 0.85 + 0.15 * Math.sin(t * 3);
    let s = `<rect width="${VW}" height="${VH}" fill="#140c2e"/><rect x="0" y="0" width="${VW}" height="60" fill="#ff3fa4" opacity=".55"/>
    <rect x="110" y="430" width="860" height="520" rx="18" fill="#05040c" stroke="#2c2660" stroke-width="16"/>
    <svg x="126" y="446" width="828" height="488" viewBox="0 400 1080 1200" preserveAspectRatio="xMidYMid slice"><g opacity="${tv}">${DECORS.vice(P, t, t * 40)}</g></svg>
    ${P.chargement !== undefined ? `<rect x="250" y="880" width="580" height="22" rx="11" fill="#05040c" opacity=".7"/><rect x="250" y="880" width="${580 * Math.min(1, P.chargement + t * 0.04)}" height="22" rx="11" fill="#fff"/>` : ''}
    <ellipse cx="540" cy="700" rx="700" ry="520" fill="#ff5fa8" opacity="${0.1 * tv}"/>
    <rect x="200" y="950" width="680" height="40" fill="#24184d"/><rect x="450" y="990" width="180" height="40" fill="#1a1238"/>
    ${floor(1540, '#2a1b55', '#120a26')}<rect x="560" y="1050" width="420" height="40" rx="8" fill="#3b2a78"/><rect x="600" y="1090" width="20" height="450" fill="#24184d"/><rect x="920" y="1090" width="20" height="450" fill="#24184d"/>
    <rect x="860" y="900" width="70" height="150" rx="16" fill="#e8ecf5"/><rect x="845" y="1035" width="100" height="15" rx="6" fill="#cfd3e8"/><rect x="890" y="920" width="10" height="110" rx="5" fill="#2f7bff" opacity="${0.6 + 0.4 * Math.sin(t * 4)}"/>`;
    return s; },
  noir: () => `<rect width="${VW}" height="${VH}" fill="#05040c"/>`,
};

// ------------------------------------------------------------------ personnages
function perso(x, y, sc, t, etat, col, opt = {}) {
  const walk = etat == 'marche', ring = etat == 'sonne', peur = etat == 'peur', dos = etat == 'dos';
  const bob = walk ? Math.abs(Math.sin(t * 7)) * -14 : Math.sin(t * 2 + x) * 4, leg = walk ? Math.sin(t * 7) * 26 : 0;
  const shake = ring ? Math.sin(t * 90) * 3 : peur ? Math.sin(t * 40) * 2 : 0, glow = ring ? 0.6 + 0.4 * Math.sin(t * 12) : 0.25;
  const dark = shade(col, -0.18), mouth = opt.bouche || 0, tel = opt.tel !== false;
  const blink = (t * 0.7 + x) % 3.2 < 0.12;
  let eyes;
  if (dos) eyes = '';
  else if (peur) eyes = `<circle cx="-22" cy="0" r="17" fill="#fff"/><circle cx="22" cy="0" r="17" fill="#fff"/><circle cx="-22" cy="2" r="7" fill="#000"/><circle cx="22" cy="2" r="7" fill="#000"/>`;
  else if (blink) eyes = `<rect x="-40" y="0" width="36" height="5" fill="#fff"/><rect x="4" y="0" width="36" height="5" fill="#fff"/>`;
  else eyes = `<path d="M-40 -2 h36 v8 a18 8 0 0 1 -36 0z" fill="#fff"/><path d="M4 -2 h36 v8 a18 8 0 0 1 -36 0z" fill="#fff"/><circle cx="-20" cy="4" r="6" fill="#000"/><circle cx="24" cy="4" r="6" fill="#000"/>`;
  const m = mouth > 0.05 && !dos ? `<ellipse cx="0" cy="32" rx="${9 + 6 * mouth}" ry="${3 + 12 * mouth}" fill="#fff" opacity=".9"/>` : '';
  const hair = opt.cheveux ? `<path d="M-78 -10 Q-80 -86 0 -86 Q80 -86 78 -10 L84 110 L56 110 L58 0 Q0 -40 -58 0 L-56 110 L-84 110z" fill="${opt.cheveux === true ? '#3a2416' : opt.cheveux}"/>` : '';
  return `<g transform="translate(${x + shake},${y + bob}) scale(${sc})">
   <ellipse cx="0" cy="185" rx="80" ry="14" fill="#000" opacity=".35"/>
   <rect x="${-38 + leg}" y="150" width="34" height="34" rx="10" fill="#e8ecf5"/><rect x="${6 - leg}" y="150" width="34" height="34" rx="10" fill="#e8ecf5"/>
   ${hair}<rect x="-62" y="40" width="124" height="128" rx="40" fill="${col}"/><rect x="-34" y="112" width="68" height="34" rx="12" fill="${dark}"/>
   <circle cx="0" cy="0" r="74" fill="${col}"/>${dos ? '' : `<circle cx="0" cy="2" r="60" fill="#0d0d16" stroke="${shade(col, 0.45)}" stroke-width="4"/>`}${eyes}${m}
   ${tel && !dos ? `<rect x="-26" y="68" width="52" height="84" rx="10" fill="#0b1020"/><rect x="-21" y="74" width="42" height="72" rx="7" fill="#7fb4ff" opacity="${glow + 0.3}"/>
   <circle cx="-30" cy="120" r="14" fill="${dark}"/><circle cx="30" cy="120" r="14" fill="${dark}"/>` : ''}
   ${ring ? `<path d="M-56 80 l-14 -8 M-58 104 l-18 0 M-56 128 l-14 8 M56 80 l14 -8 M58 104 l18 0 M56 128 l14 8" stroke="#bfe3ff" stroke-width="5" stroke-linecap="round" opacity="${glow}"/>` : ''}
   ${tel && !dos ? `<ellipse cx="0" cy="110" rx="140" ry="160" fill="#7fb4ff" opacity="${glow * 0.08}"/>` : ''}</g>`;
}
function ombre(x, y, sc, a, t) {
  return `<g opacity="${a}" transform="translate(${x + Math.sin(t * 0.8) * 4},${y}) scale(${sc})">
   <circle cx="0" cy="0" r="74" fill="#05040c"/><rect x="-66" y="40" width="132" height="150" rx="40" fill="#05040c"/>
   <circle cx="-22" cy="4" r="7" fill="#fff" opacity=".9"/><circle cx="22" cy="4" r="7" fill="#fff" opacity=".9"/></g>`;
}
function shade(hex, k) {
  const n = parseInt(hex.slice(1), 16); let r = n >> 16, g = (n >> 8) & 255, b = n & 255;
  const f = v => Math.round(k < 0 ? v * (1 + k) : v + (255 - v) * k);
  return '#' + [f(r), f(g), f(b)].map(v => Math.max(0, Math.min(255, v)).toString(16).padStart(2, '0')).join('');
}

// ------------------------------------------------------------------ écrans de téléphone
function phone(inner, heure) {
  return `<div class="phone"><div class="scr"><div class="isl"></div><div class="sb"><span>${heure}</span><span>▮▮▮ ▭</span></div>${inner}</div></div>`;
}
const avatar = (sz, col) => `<div style="width:${sz}px;height:${sz}px;border-radius:50%;background:${col};border:${sz / 30}px solid ${shade(col, 0.45)};display:flex;align-items:center;justify-content:center;margin:0 auto">
  <svg width="${sz * 0.72}" height="${sz * 0.72}" viewBox="-80 -80 160 160"><circle r="62" fill="#0d0d16"/><path d="M-40 -8 h34 v8 a17 8 0 0 1 -34 0z M6 -8 h34 v8 a17 8 0 0 1 -34 0z" fill="#fff"/></svg></div>`;
const esc = s => String(s).replace(/&/g, '&amp;').replace(/</g, '&lt;');
const TEL = {
  appel: (T, t) => `<div style="position:absolute;top:150px;left:0;right:0;text-align:center;color:#cfd6ff;font-size:32px">appel mobile…</div>
    <div style="position:absolute;top:220px;left:0;right:0;transform:scale(${1 + 0.06 * Math.sin(t * 8)})">${T.inconnu ? `<div style="width:220px;height:220px;border-radius:50%;background:#3a4170;margin:0 auto;color:#fff;font-size:120px;font-weight:800;line-height:220px;text-align:center">?</div>` : avatar(220, T.couleur || HERO.couleur)}</div>
    <div style="position:absolute;top:480px;left:0;right:0;text-align:center;color:#fff;font-size:70px;font-weight:800">${esc(T.nom || 'Inconnu')}</div>
    <div style="position:absolute;top:575px;left:0;right:0;text-align:center;color:#aab3e0;font-size:34px">${esc(T.num || 'numéro masqué')}</div>
    <div class="btn" style="left:70px;top:860px;background:#ff3b30">✕</div><div class="btn" style="right:70px;top:860px;background:#34c759;transform:rotate(${Math.sin(t * 20) * 12}deg)">✆</div>`,
  sms: (T, t) => {
    let h = `<div style="position:absolute;top:110px;left:0;right:0;text-align:center;color:#fff">${T.inconnu ? `<div style="width:90px;height:90px;border-radius:50%;background:#3a4170;margin:0 auto;font-size:50px;font-weight:800;line-height:90px">?</div>` : avatar(90, T.couleur || HERO.couleur)}
      <div style="font-size:30px;margin-top:10px;font-weight:700">${esc(T.de || 'Inconnu')}</div></div>`;
    let y = 330; const moi = new Set(T.moi || []);
    (T.lignes || []).forEach((l, i) => { const at = 0.15 + i * (T.rythme || 0.9);
      if (t < at) return;
      const mine = moi.has(i), side = mine ? 'right:40px;background:#2f7bff;' : 'left:40px;background:#2d3350;';
      if (!mine && t < at + 0.5) { h += `<div class="bubble" style="top:${y}px;${side}font-size:48px;letter-spacing:6px">• • •</div>`; y += 140; return; }
      const a = ease((t - at - (mine ? 0 : 0.5)) / 0.2);
      h += `<div class="bubble" style="top:${y}px;${side}opacity:${a};transform:scale(${0.8 + 0.2 * a});transform-origin:${mine ? 'right' : 'left'}">${esc(l)}</div>`;
      y += 70 + 46 * Math.ceil(l.length / 20); });
    return h + `<div style="position:absolute;bottom:40px;left:40px;right:40px;height:80px;border-radius:40px;border:2px solid #3a4170;color:#59608a;font-size:30px;padding:20px 30px">Message</div>`;
  },
  notif: (T, t) => { const a = ease((t - 0.2) / 0.25);
    return `<div style="position:absolute;top:150px;left:0;right:0;text-align:center;color:#dfe4ff;font-size:32px">${esc(T.date || 'samedi 15 novembre')}</div>
    <div style="position:absolute;top:190px;left:0;right:0;text-align:center;color:#fff;font-size:170px;font-weight:800;letter-spacing:-4px">${esc(T.heure || '3:00')}</div>
    <div style="position:absolute;top:470px;left:30px;right:30px;padding:24px;border-radius:34px;background:rgba(255,255,255,.14);color:#fff;opacity:${a};transform:translateY(${(1 - a) * -40}px)">
      <div style="display:flex;justify-content:space-between;font-size:24px;opacity:.85"><b>${esc(T.app || 'MESSAGES')}</b><span>maintenant</span></div>
      <div style="font-size:32px;font-weight:800;margin-top:8px">${esc(T.titre || '')}</div><div style="font-size:30px;margin-top:4px;line-height:1.25">${esc(T.texte || '')}</div></div>`; },
  localiser: (T, t) => { let g = ''; for (let i = 0; i < 9; i++) g += `<line x1="${i * 70}" y1="0" x2="${i * 70}" y2="700" stroke="#2a3a7a" stroke-width="14"/><line x1="0" y1="${i * 90}" x2="560" y2="${i * 90}" stroke="#2a3a7a" stroke-width="14"/>`;
    const k = ease(t / 2.5), px = 140 + 280 * k, py = 560 - 300 * Math.min(1, k * 1.3);
    return `<div style="position:absolute;top:100px;left:40px;color:#fff;font-size:44px;font-weight:800">Localiser</div>
    <svg style="position:absolute;top:180px;left:0" width="560" height="700"><rect width="560" height="700" fill="#16224f"/>${g}
     <path d="M140 560 L140 ${Math.max(py, 260)} L${px} ${Math.max(py, 260)}" stroke="#ff3b3b" stroke-width="10" fill="none"/>
     <circle cx="420" cy="260" r="22" fill="#2f7bff" stroke="#fff" stroke-width="6"/><text x="420" y="225" font-size="26" fill="#fff" text-anchor="middle">Toi</text>
     <circle cx="${px}" cy="${Math.max(py, 260)}" r="18" fill="#e8ecf5" stroke="#9aa0bf" stroke-width="5"/></svg>
    <div style="position:absolute;top:900px;left:30px;right:30px;padding:24px;border-radius:30px;background:#1d2547;color:#fff;font-size:32px"><b>${esc(T.titre || 'Objet inconnu')}</b><br><span style="opacity:.7;font-size:26px">${esc(T.texte || 'Se déplace avec toi')}</span></div>`; },
  photo: (T, t) => `<div style="position:absolute;top:100px;left:40px;color:#fff;font-size:40px;font-weight:800">Photos</div>
    <div style="position:absolute;top:170px;left:20px;right:20px;height:760px;overflow:hidden;border-radius:20px">
      <svg width="1080" height="1920" viewBox="0 0 1080 1920" style="position:absolute;left:-270px;top:-480px;transform:scale(.5);transform-origin:540px 960px">${DEFS}${(DECORS[T.vue] || DECORS.chambre)(T, 0, 0)}
      ${T.ombre ? ombre(380, 1180, 2.2, 1, t) : ''}</svg></div>
    <div style="position:absolute;top:960px;left:40px;color:#aab3e0;font-size:30px">${esc(T.legende || 'Aujourd\'hui, 3:00')}</div>`,
};

// ------------------------------------------------------------------ objets plein écran
const OBJ = {
  porte: (O, t) => { const k = O.toc ? Math.max(0, Math.sin(t * 22)) * (t % 1.2 < 0.6 ? 1 : 0) * 8 : 0;
    return svg(`${DEFS}<rect width="${VW}" height="${VH}" fill="url(#wall)"/><g transform="translate(${k},0)">${door(290, 380, 500, 1160, '#3b2f6e', O.ouverte ? ease(t / 1.5) * 0.4 : 0)}</g>
     <rect x="290" y="1530" width="500" height="10" fill="#ffe7a3" opacity="${O.lumiere ? 0.8 * FL : 0}"/>${floor(1540)}`); },
  lettre: (O, t) => `<div class="layer" style="background:#0b0a22"></div><div style="position:absolute;left:150px;right:150px;top:420px;height:900px;background:#efe7d2;transform:rotate(-3deg);box-shadow:0 30px 80px #000;padding:80px 60px;font-family:'Comic Sans MS','Bradley Hand',cursive;font-size:64px;color:#1b1b2b;line-height:1.3">${esc(O.texte || '')}</div>`,
  cassette: (O, t) => svg(`<rect width="${VW}" height="${VH}" fill="#0b0a22"/><rect x="190" y="700" width="700" height="440" rx="30" fill="#2c2660" stroke="#5d52a8" stroke-width="10"/>
     <rect x="260" y="760" width="560" height="130" rx="10" fill="#efe7d2"/><text x="540" y="845" font-size="56" text-anchor="middle" fill="#1b1b2b" font-family="cursive">${esc(O.texte || 'N°9')}</text>
     ${[400, 680].map(x => `<circle cx="${x}" cy="990" r="70" fill="#14112c"/><g transform="rotate(${t * 200},${x},990)"><path d="M${x - 50} 990 h100 M${x} 940 v100" stroke="#e8ecf5" stroke-width="12"/></g>`).join('')}`),
  horloge: (O, t) => { const [h, m] = (O.heure || '3:00').split(':').map(Number), am = (m + t * 2) * 6, ah = (h % 12) * 30 + m * 0.5;
    return svg(`<rect width="${VW}" height="${VH}" fill="#0b0a22"/><circle cx="540" cy="900" r="330" fill="#e8ecf5" stroke="#14112c" stroke-width="22"/>
     ${Array.from({ length: 12 }, (_, i) => `<rect x="534" y="600" width="12" height="44" fill="#14112c" transform="rotate(${i * 30},540,900)"/>`).join('')}
     <rect x="532" y="720" width="16" height="190" rx="8" fill="#14112c" transform="rotate(${ah},540,900)"/><rect x="535" y="630" width="10" height="280" rx="5" fill="#e0202a" transform="rotate(${am},540,900)"/><circle cx="540" cy="900" r="18" fill="#14112c"/>`); },
  photo: (O, t) => `<div class="layer" style="background:#0b0a22"></div><div style="position:absolute;left:170px;right:170px;top:440px;height:900px;background:#f2f0ea;transform:rotate(${2 + Math.sin(t) * 0.5}deg);box-shadow:0 30px 80px #000;padding:36px 36px 150px">
    <div style="position:relative;width:100%;height:100%;overflow:hidden"><svg width="1080" height="1920" viewBox="0 0 1080 1920" style="position:absolute;left:-270px;top:-600px;transform:scale(.5);transform-origin:540px 960px;filter:sepia(.5)">${DEFS}${(DECORS[O.vue] || DECORS.mer)(O, 0, 0)}${O.ombre ? ombre(700, 1180, 2, ease(t / 2), t) : ''}</svg></div>
    <div style="position:absolute;bottom:40px;left:0;right:0;text-align:center;font-family:cursive;font-size:52px;color:#333">${esc(O.texte || '')}</div></div>`,
};

// ------------------------------------------------------------------ cartes
function regle(t, n, txt, label) { const a = ease(t / 0.25);
  return `<div class="card"></div><div style="position:absolute;top:700px;left:60px;right:60px;text-align:center;transform:scale(${0.85 + 0.15 * a});opacity:${a}">
    <span style="display:inline-block;background:#e0202a;color:#fff;font-family:Anton;font-size:84px;padding:6px 40px;border-radius:14px;border:4px solid #ff8a8f">${label ? esc(label) : 'RÈGLE N°' + n}</span>
    <div style="font-family:Anton;color:#fff;font-size:112px;margin-top:40px;line-height:1.05;text-transform:uppercase">${esc(txt).replace(/\n/g, '<br>')}</div></div>`; }
function choix(t, a1, a2) { const p = k => ease((t - 0.15 * k) / 0.3);
  return `<div class="card" style="background:radial-gradient(circle at 50% 45%,#1a1747,#07061a)"></div>
   <div style="position:absolute;top:480px;left:0;right:0;text-align:center;color:#fff;font-size:44px;letter-spacing:6px;font-weight:800;opacity:${p(0)}">À TOI DE CHOISIR</div>
   <div class="choice" style="top:600px;background:#ff7a1a;box-shadow:0 0 60px #ff7a1a88;transform:scale(${0.7 + 0.3 * p(1)});opacity:${p(1)}">1 · ${esc(a1)}</div>
   <div style="position:absolute;top:${600 + 190 + Math.max(0, (a1.length - 14)) * 2}px;left:0;right:0;text-align:center;color:#aab;font-size:46px;font-weight:800;opacity:${p(2)}">OU</div>
   <div class="choice" style="top:880px;background:#2f7bff;box-shadow:0 0 60px #2f7bff88;transform:scale(${0.7 + 0.3 * p(3)});opacity:${p(3)}">2 · ${esc(a2)}</div>
   <div style="position:absolute;top:1120px;left:0;right:0;text-align:center;color:#cfd6ff;font-size:40px;font-weight:700;opacity:${p(4)}">${esc(EP.vote || 'Le plus de votes décide la suite')}</div>`; }

// ------------------------------------------------------------------ sous-titres
const CH = (() => { const out = []; let cur = [];
  for (const w of WORDS) { cur.push(w); if (cur.length == 2 || /[.,!?:;…]$/.test(w[2])) { out.push(cur); cur = []; } }
  if (cur.length) out.push(cur); return out; })();
function subs(t) {
  for (let i = 0; i < CH.length; i++) { const c = CH[i], a = c[0][0], b = Math.min(i + 1 < CH.length ? CH[i + 1][0][0] : c[c.length - 1][1] + 0.4, c[c.length - 1][1] + 0.5);
    if (t >= a && t < b) { const k = ease((t - a) / 0.09);
      return `<span style="display:inline-block;transform:scale(${0.8 + 0.2 * k})">` + c.map(w => { const x = esc(w[2].replace(/[.,;:]+$/, ''));
        return w[3] == 'r' ? `<span class="r">${x}</span>` : w[3] == 'y' ? `<span class="y">${x}</span>` : x; }).join(' ') + `</span>`; } }
  return '';
}
function hms(base, t) { const [h, m, s] = base.split(':').map(Number); const x = h * 3600 + m * 60 + s + Math.floor(t);
  return [Math.floor(x / 3600) % 24, Math.floor(x / 60) % 60, x % 60].map(v => String(v).padStart(2, '0')).join(':'); }

// ------------------------------------------------------------------ une image
const AMB = { nuit: '', rouge: 'hue-rotate(115deg) saturate(1.5) brightness(.95)', vert: 'hue-rotate(-140deg) saturate(.9) brightness(.92)',
  bleu: 'hue-rotate(-40deg) saturate(1.25)', sepia: 'sepia(.9) saturate(1.2) contrast(1.1) brightness(.92)',
  nb: 'grayscale(1) contrast(1.35) brightness(.95)', vhs: 'sepia(.35) saturate(1.6) contrast(1.2) hue-rotate(-20deg) blur(.7px)' };
const LIEUX = { rue: 'RUE', chambre: 'CHAMBRE', couloir: 'COULOIR', salon: 'SALON', cuisine: 'CUISINE', escalier: 'ESCALIER', foret: 'FORÊT', station: 'STATION', mer: 'PLAGE', hopital: 'HÔPITAL', cave: 'CAVE', voiture: 'VOITURE', sdb: 'SALLE DE BAIN', vice: 'VICE CITY', gamer: 'CHEZ TOI' };
let LIEU = (EP.beats0 || '');
for (const b of BEATS) if (b.lieu || b.vue) { LIEU = b.lieu || (EP.lieux || {})[b.vue] || LIEUX[b.vue] || ''; break; }
let LASTVUE = (BEATS.find(b => b.vue && !b.tel) || {}).vue || 'rue';
const HERO = Object.assign({ couleur: '#22b3a0' }, EP.hero || {});
let OFF = 0, lastT = 0;
window.seek = function (t) {
  let k = 0; for (let i = 0; i < BEATS.length; i++) if (t >= BEATS[i].t0) k = i;
  const P = BEATS[k], lt = t - P.t0, fi = Math.min(AMP.length - 1, Math.round(t * FPS));
  FL = P.flicker ? ((Math.sin(t * 23) + Math.sin(t * 7.3) > 0.6) ? 0.15 : 1) : 1;
  if ((P.hero || 'debout') == 'marche') OFF += (t - lastT) * 90; lastT = t;
  let html = '', zoom = 1, ox = 540, oy = 1000;
  const intro = ease(lt / 0.22);
  if (P.regle) html = regle(lt, P.regle.n, P.regle.txt, P.regle.label);
  else if (P.choix) html = choix(lt, P.choix.a, P.choix.b);
  else if (P.objet) { html = (OBJ[P.objet.type] || OBJ.porte)(P.objet, lt); zoom = 1.06 - 0.06 * intro + 0.012 * lt; }
  else {
    if (P.vue && !P.tel) LASTVUE = P.vue;
    const dec = DECORS[P.vue || LASTVUE] || DECORS.rue;
    let s = DEFS + dec(P, t, OFF);
    if (P.eclair && lt % 2.2 < 0.12) s += `<rect width="${VW}" height="${VH}" fill="#fff" opacity=".55"/>`;
    const om = P.ombre; if (om) { const o = om === true ? {} : om; s += ombre(VW * (o.x ?? 0.25), o.y ?? 1290, o.taille ?? 1.75, ease((lt - (o.delai ?? 0.2)) / 0.5) * 0.95, t); }
    for (const q of (P.persos || [])) { const d = (EP.persos || {})[q.nom] || {};
      s += perso(VW * (q.x ?? 0.3), q.y ?? 1250, q.taille ?? 1.55, t, q.etat || 'debout', d.couleur || '#e0607e', { cheveux: d.cheveux, tel: q.tel ?? false, bouche: P.qui == q.nom ? AMP[fi] : 0 }); }
    if ((P.hero || 'debout') != 'absent') s += perso(VW * (P.hx ?? 0.5), P.hy ?? 1260, P.ht ?? 1.6, t, P.hero || 'debout', HERO.couleur, { cheveux: HERO.cheveux, tel: P.tel_main ?? true, bouche: P.qui == 'MOI' ? AMP[fi] : 0 });
    if (P.pluie && P.vue != 'voiture') for (let i = 0; i < 70; i++) { const x = rnd(i) * VW, y = (rnd(i * 5) * VH + t * 1400) % VH; s += `<line x1="${x}" y1="${y}" x2="${x - 8}" y2="${y + 40}" stroke="#9fd0ff" stroke-width="3" opacity=".35"/>`; }
    if (P.neige) for (let i = 0; i < 70; i++) { const x = (rnd(i) * VW + Math.sin(t + i) * 30), y = (rnd(i * 5) * VH + t * 120) % VH; s += `<circle cx="${x}" cy="${y}" r="${4 + rnd(i) * 5}" fill="#fff" opacity=".7"/>`; }
    if (P.rouge_lum) s += `<rect width="${VW}" height="${VH}" fill="#ff1a1a" opacity="${0.12 + 0.06 * Math.sin(t * 3)}"/>`;
    html = svg(s);
    if (P.tel) html += `<div class="layer" style="background:rgba(5,4,15,.6)"></div>` + phone((TEL[P.tel.type] || TEL.sms)(P.tel, lt), P.tel.heure || EP.heure_tel || '3:00');
    const c = P.cadre || (P.tel ? 'tel' : 'large');
    if (c == 'gros') { zoom = 1.9 + 0.05 * lt; ox = VW * (P.hx ?? 0.5); oy = (P.hy ?? 1260) - 40; }
    else if (c == 'tel') { zoom = 0.9 + 0.1 * intro + 0.01 * lt; }
    else if (c == 'pousse') { zoom = 1 + 0.06 * lt; ox = VW * (P.hx ?? 0.5); oy = 1250; }
    else zoom = 1.02 + 0.015 * lt;
    if (P.hero == 'sonne' && c != 'gros') zoom = 1 + 0.25 * ease(lt / 1.5), ox = VW * (P.hx ?? 0.5), oy = 1250;
  }
  const pop = (P.regle || P.choix) ? 1 : 1.05 - 0.05 * intro;
  // ambiance (rotation du 21/11, engine/plan.py) : teinte des plans décor/objet ; téléphone, règle et choix restent nets
  const amb = P.ambiance || EP.ambiance || 'nuit';
  if (amb == 'vhs' && !P.tel && !P.regle && !P.choix) {
    let g = ''; for (let i = 0; i < 40; i++) g += `<rect x="0" y="${(rnd(i + Math.floor(t * 12)) * VH) | 0}" width="${VW}" height="${2 + rnd(i * 3) * 5}" fill="#fff" opacity="${0.04 + rnd(i * 7 + t) * 0.06}"/>`;
    html += `<svg width="${VW}" height="${VH}" style="position:absolute;inset:0;mix-blend-mode:screen">${g}<rect y="${(t * 260) % VH}" width="${VW}" height="70" fill="#fff" opacity=".06"/></svg>`;
  }
  cam.style.filter = (P.tel || P.regle || P.choix) ? '' : (AMB[amb] || '');
  cam.innerHTML = html;
  cam.style.transformOrigin = `${ox}px ${oy}px`;
  cam.style.transform = `scale(${zoom * pop})`;
  // 24/11, Fio : « enlève les titres en haut des vidéos » → horloge + étiquette cachées par défaut ("horloge": true pour les remettre)
  const showClock = !(P.regle || P.choix) && EP.horloge === true;
  document.getElementById('clock').style.display = showClock ? 'block' : 'none';
  if (P.lieu) LIEU = P.lieu; else if (P.vue && EP.lieux_auto !== false) LIEU = (EP.lieux || {})[P.vue] || LIEUX[P.vue] || LIEU;
  document.getElementById('lieu').textContent = LIEU || EP.lieu || '';
  document.getElementById('etiq').textContent = EP.etiquette || 'NUIT 1';
  document.getElementById('tm').textContent = hms(EP.heure || '03:00:00', t);
  // texte d'accroche écrit en haut de l'écran pendant les 3 premières secondes (21/11 : objectif 1 000 vues, retenir dès 0 s)
  const hk = document.getElementById('hook');
  if (hk) { const d = EP.texte_accroche_duree || 3.2, o = EP.texte_accroche && EP.accroche_haut === true && t < d + 0.3 ? Math.min(1, (d + 0.3 - t) / 0.3) : 0;
    hk.innerHTML = o ? `<span>${esc(EP.texte_accroche)}</span>` : ''; hk.style.opacity = o; }
  sub.innerHTML = subs(t);
  sub.style.top = P.choix ? '1290px' : P.regle ? '1300px' : '1590px';
};
