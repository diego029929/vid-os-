// ---------- décors et objets 1914-1918 (style stick-figure : aplats, contour encre) ----------
const POILU = { cols: ['#7f9cc6', '#7f9cc6'], hat: 'adrian', hatCol: '#6d85a8', belt: true };
const OUVRIERE = { cols: ['#8c5b3c', '#8c5b3c'], hat: 'scarf', hatCol: '#c8432f', belt: false };
const ELEVE = { cols: ['#3f7fd8', '#3f7fd8'], hat: 'hair', hatCol: '#3a2a22', belt: false };
const TIRAILLEUR = { cols: ['#c9a66b', '#c9a66b'], hat: 'adrian', hatCol: '#a88c58', belt: true };

function groundStrip(ctx, y, col, h = 2000) { ctx.fillStyle = col; ctx.fillRect(-2000, y, 5080, h); }

// ciel du front : gris-ocre, nuages bas
function frontSky(ctx, t, top = '#9fb2c2', bot = '#e8d9b8') {
  drawSky(ctx, top, bot, -400, 1100);
}
function sandbag(ctx, x, y, w, h, col = '#c9b07a') {
  ctx.beginPath(); ctx.ellipse(x, y, w / 2, h / 2, 0, 0, TAU); fillStroke(ctx, col, 4);
  line(ctx, x - w * .3, y - h * .05, x - w * .3, y + h * .25, 3, 'rgba(60,40,20,.5)');
}
function sandbagRow(ctx, x0, x1, y, seed = 1) {
  const R = rng(seed);
  for (let x = x0, i = 0; x < x1; x += 92, i++) sandbag(ctx, x + (R() - .5) * 8, y + (i % 2) * 6, 104, 52, i % 3 ? '#c9b07a' : '#bba06a');
  for (let x = x0 + 46; x < x1; x += 92) sandbag(ctx, x, y - 40, 104, 52, '#d3bb86');
}
function barbedWire(ctx, x0, x1, y, t = 0) {
  for (let x = x0; x <= x1; x += 220) { line(ctx, x, y + 10, x + 14, y - 120, 9, '#5a4632'); line(ctx, x + 60, y + 10, x + 40, y - 110, 9, '#5a4632'); }
  ctx.strokeStyle = '#3a3238'; ctx.lineWidth = 4; ctx.beginPath();
  for (let x = x0; x <= x1; x += 6) { const yy = y - 70 + Math.sin(x * .09) * 26 + Math.sin(x * .023) * 10; x === x0 ? ctx.moveTo(x, yy) : ctx.lineTo(x, yy); } ctx.stroke();
  ctx.beginPath();
  for (let x = x0; x <= x1; x += 6) { const yy = y - 30 + Math.sin(x * .07 + 2) * 22; x === x0 ? ctx.moveTo(x, yy) : ctx.lineTo(x, yy); } ctx.stroke();
}
// tranchée vue de face : paroi de boue + planches + sacs de sable en haut
function trenchWall(ctx, top, bottom, t, o = {}) {
  ctx.fillStyle = '#7a5a3e'; ctx.fillRect(-2000, top, 5080, bottom - top + 2000);
  // planches verticales
  for (let x = -600, i = 0; x < 1700; x += 150, i++) { rrect(ctx, x, top + 40, 132, bottom - top, 6); fillStroke(ctx, i % 2 ? '#8e6844' : '#996f48', 5); line(ctx, x + 66, top + 60, x + 66, bottom, 3, 'rgba(50,30,15,.35)'); }
  // poteaux
  for (let x = -520; x < 1700; x += 450) { rrect(ctx, x, top - 10, 34, bottom - top + 20, 6); fillStroke(ctx, '#5e4128', 5); }
  sandbagRow(ctx, -700, 1800, top + 10, 3);
  // caillebotis (sol en bois)
  ctx.fillStyle = '#5a3f2a'; ctx.fillRect(-2000, bottom, 5080, 2000);
  for (let x = -700; x < 1800; x += 70) { rrect(ctx, x, bottom + 8, 56, 50, 4); fillStroke(ctx, '#8a6a46', 4); }
  ctx.fillStyle = 'rgba(40,30,20,.35)'; ctx.fillRect(-2000, bottom + 60, 5080, 2000);
}
function rain(ctx, t, a = 1, n = 90, seed = 4) {
  if (a <= 0) return; const R = rng(seed); ctx.save(); ctx.setTransform(1, 0, 0, 1, 0, 0); ctx.globalAlpha = a * .55;
  ctx.strokeStyle = '#dfe8f2'; ctx.lineWidth = 3;
  for (let i = 0; i < n; i++) { const x = (R() * 1300 + t * 120) % 1300 - 100, y = (R() * 2100 + t * (1500 + R() * 400)) % 2100 - 100; ctx.beginPath(); ctx.moveTo(x, y); ctx.lineTo(x - 12, y + 50); ctx.stroke(); }
  ctx.restore();
}
// obus : douille laiton + ceinture cuivre + ogive
function shell(ctx, x, y, s, rot = 0, tint = 0) {
  ctx.save(); ctx.translate(x, y); ctx.rotate(rot); ctx.scale(s, s);
  rrect(ctx, -40, -60, 80, 150, 8); fillStroke(ctx, mix('#d9b04a', '#2a2020', tint), 6);
  ctx.save(); rrect(ctx, -40, -60, 80, 150, 8); ctx.clip(); ctx.fillStyle = 'rgba(80,50,0,.22)'; ctx.fillRect(12, -70, 40, 170); ctx.fillStyle = 'rgba(255,255,255,.3)'; ctx.fillRect(-30, -60, 12, 150); ctx.restore();
  rrect(ctx, -44, -78, 88, 22, 5); fillStroke(ctx, mix('#b8653a', '#2a2020', tint), 5);
  ctx.beginPath(); ctx.moveTo(-38, -78); ctx.bezierCurveTo(-38, -150, -10, -200, 0, -212); ctx.bezierCurveTo(10, -200, 38, -150, 38, -78); ctx.closePath(); fillStroke(ctx, mix('#8a8f98', '#1a1a20', tint), 6);
  ctx.save(); ctx.beginPath(); ctx.moveTo(-38, -78); ctx.bezierCurveTo(-38, -150, -10, -200, 0, -212); ctx.bezierCurveTo(10, -200, 38, -150, 38, -78); ctx.closePath(); ctx.clip(); ctx.fillStyle = 'rgba(20,20,40,.22)'; ctx.fillRect(8, -220, 40, 150); ctx.restore();
  ctx.restore();
}
// usine : bâtiment en briques, toit en dents de scie, cheminées qui fument
function factory(ctx, x, y, s, t, night = 0) {
  ctx.save(); ctx.translate(x, y); ctx.scale(s, s);
  for (const [cx, h] of [[-170, 430], [150, 360]]) {
    rrect(ctx, cx - 34, -h, 68, h, 6); fillStroke(ctx, '#9c4a36', 6);
    rrect(ctx, cx - 42, -h - 10, 84, 26, 6); fillStroke(ctx, '#6e3426', 5);
    for (let k = 0; k < 4; k++) { const ph = (t * .45 + k * .25) % 1; puff(ctx, cx + ph * 120 + Math.sin(ph * 6) * 10, -h - 40 - ph * 330, 40 + ph * 70, t, night ? '#7d7a86' : '#d7d2c8', 20 + k, (1 - ph) * .95); }
  }
  ctx.beginPath(); ctx.moveTo(-300, 0); ctx.lineTo(-300, -160);
  for (let i = 0; i < 4; i++) { ctx.lineTo(-300 + i * 150, -260); ctx.lineTo(-300 + i * 150 + 150, -160); }
  ctx.lineTo(300, 0); ctx.closePath(); fillStroke(ctx, '#b85a3e', 6);
  ctx.save(); ctx.clip(); ctx.strokeStyle = 'rgba(80,30,20,.35)'; ctx.lineWidth = 3;
  for (let yy = -250; yy < 0; yy += 26) { ctx.beginPath(); ctx.moveTo(-310, yy); ctx.lineTo(310, yy); ctx.stroke(); }
  ctx.fillStyle = 'rgba(40,10,10,.2)'; ctx.fillRect(100, -300, 260, 320); ctx.restore();
  for (let i = 0; i < 4; i++) { rrect(ctx, -260 + i * 140, -130, 90, 80, 6); fillStroke(ctx, night ? '#ffd66b' : '#bfe0f0', 5); line(ctx, -215 + i * 140, -130, -215 + i * 140, -50, 4); }
  rrect(ctx, -50, -60, 100, 60, 4); fillStroke(ctx, '#5a3324', 5);
  ctx.restore();
}
function house(ctx, x, y, s, col = '#efe2c6', roof = '#c4553c') {
  ctx.save(); ctx.translate(x, y); ctx.scale(s, s);
  rrect(ctx, -90, -120, 180, 120, 4); fillStroke(ctx, col, 6);
  path(ctx, [[-110, -116], [0, -200], [110, -116]]); fillStroke(ctx, roof, 6);
  rrect(ctx, -60, -90, 40, 40, 3); fillStroke(ctx, '#bfe0f0', 4); rrect(ctx, 20, -70, 40, 70, 3); fillStroke(ctx, '#8a5a3a', 4);
  ctx.restore();
}
function field(ctx, x, y, w, h, col = '#d9c36a') {
  rrect(ctx, x, y, w, h, 12); fillStroke(ctx, col, 5);
  ctx.save(); rrect(ctx, x, y, w, h, 12); ctx.clip(); for (let k = x - h; k < x + w; k += 34) line(ctx, k, y + h, k + h * .6, y, 4, 'rgba(120,90,30,.35)'); ctx.restore();
}
function truck(ctx, x, y, s, col = '#6e7f5a') {
  ctx.save(); ctx.translate(x, y); ctx.scale(s, s);
  rrect(ctx, -130, -110, 170, 90, 8); fillStroke(ctx, '#c9b98e', 6);
  rrect(ctx, 40, -90, 80, 70, 8); fillStroke(ctx, col, 6); rrect(ctx, 60, -80, 40, 30, 4); fillStroke(ctx, '#bfe0f0', 4);
  rrect(ctx, -135, -30, 260, 22, 6); fillStroke(ctx, '#4a4a46', 5);
  for (const wx of [-90, 80]) { circle(ctx, wx, -6, 30); fillStroke(ctx, '#2c2a2e', 6); circle(ctx, wx, -6, 11); fillStroke(ctx, '#9a9aa2', 4); }
  ctx.restore();
}
// journal censuré : colonnes avec des trous blancs (les articles coupés)
function newspaper(ctx, x, y, s, rot, stampK = 0) {
  ctx.save(); ctx.translate(x, y); ctx.rotate(rot); ctx.scale(s, s);
  rrect(ctx, -300, -400, 600, 800, 10); fillStroke(ctx, '#f3ead6', 8);
  ctx.save(); rrect(ctx, -300, -400, 600, 800, 10); ctx.clip(); ctx.fillStyle = 'rgba(120,90,40,.12)'; ctx.fillRect(100, -400, 300, 800); ctx.restore();
  text(ctx, 'LE JOURNAL', 0, -330, 78, INK, INK, 0, 'Lora', 700);
  line(ctx, -260, -280, 260, -280, 6); text(ctx, '12 AOÛT 1916', 0, -252, 26, INK, INK, 0, 'Lora', 600); line(ctx, -260, -228, 260, -228, 4);
  const blanks = [[0, 2, 4], [1, 3], [0, 5]];
  for (let c = 0; c < 3; c++) for (let r = 0; r < 7; r++) {
    const cx = -255 + c * 172, cy = -200 + r * 82;
    if (blanks[c].includes(r)) { ctx.save(); ctx.setLineDash([10, 8]); rrect(ctx, cx, cy, 150, 64, 4); ctx.lineWidth = 3; ctx.strokeStyle = 'rgba(60,40,30,.45)'; ctx.stroke(); ctx.restore(); continue; }
    for (let l = 0; l < 4; l++) line(ctx, cx, cy + 8 + l * 16, cx + (l === 3 ? 90 : 150), cy + 8 + l * 16, 6, 'rgba(40,30,30,.55)');
  }
  if (stampK > 0) {
    const k = backOut(clamp(stampK)); ctx.save(); ctx.translate(30, 40); ctx.rotate(-.22); ctx.scale(2.2 - 1.2 * k, 2.2 - 1.2 * k); ctx.globalAlpha = clamp(stampK * 3);
    rrect(ctx, -250, -70, 500, 140, 14); ctx.lineWidth = 16; ctx.strokeStyle = '#d0302a'; ctx.stroke();
    text(ctx, 'CENSURÉ', 0, 6, 104, '#d0302a', '#d0302a', 0, 'Poppins', 700); ctx.restore();
  }
  ctx.restore();
}
// affiche de propagande (slogan réel de 1916, domaine public)
function poster(ctx, x, y, s, rot, t) {
  ctx.save(); ctx.translate(x, y); ctx.rotate(rot); ctx.scale(s, s);
  rrect(ctx, -280, -400, 560, 800, 8); fillStroke(ctx, '#f6edd8', 8);
  ctx.save(); rrect(ctx, -280, -400, 560, 800, 8); ctx.clip();
  const g = ctx.createLinearGradient(0, -400, 0, 400); g.addColorStop(0, '#f2c66a'); g.addColorStop(1, '#e98a4a'); ctx.fillStyle = g; ctx.fillRect(-280, -400, 560, 800);
  ctx.translate(0, 0); ctx.rotate(-.5 + Math.sin(t * 2) * .02); for (let i = 0; i < 14; i++) { ctx.rotate(TAU / 14); path(ctx, [[-40, 0], [40, 0], [0, 900]]); ctx.fillStyle = 'rgba(255,255,255,.16)'; ctx.fill(); }
  ctx.restore();
  drawStick(ctx, C(POILU, { x: 0, y: 260, s: 520, shadow: false, arms: { L: [.5, -.2], R: [2.7, .1] }, face: { eyes: 'normal', mouth: 'grin', browAng: .3, look: [0, -.5] } }));
  rrect(ctx, -260, 270, 520, 110, 8); fillStroke(ctx, '#2a4f9e', 6);
  text(ctx, 'ON LES AURA !', 0, 326, 72, '#fff', INK, 0, 'Poppins', 700);
  ctx.restore();
}
// bateau à vapeur (transport de troupes)
function steamer(ctx, x, y, s, t) {
  ctx.save(); ctx.translate(x, y + Math.sin(t * 2.2) * 6); ctx.rotate(Math.sin(t * 1.7) * .015); ctx.scale(s, s);
  for (let k = 0; k < 4; k++) { const ph = (t * .5 + k * .25) % 1; puff(ctx, 60 - ph * 260, -330 - ph * 180, 34 + ph * 60, t, '#d4d0c8', 40 + k, (1 - ph) * .9); }
  rrect(ctx, 30, -330, 70, 150, 6); fillStroke(ctx, '#c8432f', 6); rrect(ctx, 30, -330, 70, 26, 4); fillStroke(ctx, '#2a2428', 5);
  rrect(ctx, -170, -200, 300, 90, 8); fillStroke(ctx, '#f3ecdf', 6);
  for (let i = 0; i < 5; i++) { circle(ctx, -135 + i * 55, -155, 13); fillStroke(ctx, '#bfe0f0', 4); }
  ctx.beginPath(); ctx.moveTo(-360, -120); ctx.lineTo(380, -120); ctx.lineTo(320, 0); ctx.lineTo(-310, 0); ctx.closePath(); fillStroke(ctx, '#3a4a6a', 7);
  line(ctx, -350, -100, 370, -100, 8, '#f3ecdf');
  ctx.restore();
}
function sea(ctx, y, t, cols = ['#7fc4dc', '#3f8fbf']) {
  const g = ctx.createLinearGradient(0, y, 0, y + 1200); g.addColorStop(0, cols[0]); g.addColorStop(1, cols[1]); ctx.fillStyle = g; ctx.fillRect(-2000, y, 5080, 3000);
  ctx.strokeStyle = 'rgba(255,255,255,.5)'; ctx.lineWidth = 5;
  for (let r = 0; r < 9; r++) { const yy = y + 40 + r * 90 + r * r * 6; ctx.beginPath(); for (let x = -400; x < 1500; x += 10) { const v = yy + Math.sin(x * .02 + t * 2 + r) * (6 + r); x === -400 ? ctx.moveTo(x, v) : ctx.lineTo(x, v); } ctx.stroke(); }
}
function coast(ctx, x, y, w, h, col, label, flip = 1) {
  ctx.save(); ctx.translate(x, y); ctx.scale(flip, 1);
  ctx.beginPath(); ctx.moveTo(-w, h); ctx.lineTo(-w, -h * .3); ctx.quadraticCurveTo(-w * .3, -h, 0, -h * .55); ctx.quadraticCurveTo(w * .25, -h * .2, w * .1, h); ctx.closePath(); fillStroke(ctx, col, 7);
  ctx.restore();
  if (label) { const lx = x + flip * -w * .45; rrect(ctx, lx - 150, y - h * .35 - 40, 300, 80, 16); fillStroke(ctx, '#fff', 6); text(ctx, label, lx, y - h * .35, 46, INK, INK, 0, 'Poppins', 700); }
}
function cross(ctx, x, y, s, a = 1) {
  if (a <= 0) return; ctx.save(); ctx.globalAlpha = a; ctx.translate(x, y); ctx.scale(s, s);
  rrect(ctx, -9, -90, 18, 100, 3); fillStroke(ctx, '#f4f1ea', 4); rrect(ctx, -34, -68, 68, 16, 3); fillStroke(ctx, '#f4f1ea', 4);
  ctx.restore();
}
function sign(ctx, x, y, s, str, rot = 0, col = '#c9a46a') {
  ctx.save(); ctx.translate(x, y); ctx.rotate(rot); ctx.scale(s, s);
  rrect(ctx, -12, -20, 24, 260, 4); fillStroke(ctx, '#6a4a2e', 5);
  rrect(ctx, -230, -110, 460, 110, 10); fillStroke(ctx, col, 7);
  text(ctx, str, 0, -54, 62, INK, INK, 0, 'Poppins', 700);
  ctx.restore();
}
function bigLabel(ctx, str, x, y, size, fill, k = 1, rot = 0) {
  if (k <= 0) return; ctx.save(); ctx.translate(x, y); ctx.rotate(rot); const sc = backOut(clamp(k)); ctx.scale(sc, sc);
  ctx.shadowColor = 'rgba(0,0,0,.35)'; ctx.shadowBlur = 20; ctx.shadowOffsetY = 8;
  text(ctx, str, 0, 0, size, fill, INK, size * .16, 'Poppins', 700); ctx.shadowColor = 'transparent';
  text(ctx, str, 0, 0, size, fill, INK, 0, 'Poppins', 700); ctx.restore();
}
function pill(ctx, x, y, w, h, fill, str, size, k = 1) {
  if (k <= 0) return; ctx.save(); ctx.translate(x, y); const sc = backOut(clamp(k)); ctx.scale(sc, sc);
  rrect(ctx, -w / 2, -h / 2, w, h, h / 2); fillStroke(ctx, fill, 8); text(ctx, str, 0, 4, size, '#fff', INK, 0, 'Poppins', 700); ctx.restore();
}
// icônes du récapitulatif
function iconBadge(ctx, x, y, r, k, fill, drawIn) {
  if (k <= 0) return; ctx.save(); ctx.translate(x, y); const sc = backOut(clamp(k)); ctx.scale(sc, sc);
  circle(ctx, 0, 0, r); fillStroke(ctx, fill, 9); ctx.save(); circle(ctx, 0, 0, r - 6); ctx.clip(); drawIn(ctx); ctx.restore(); circle(ctx, 0, 0, r); fillStroke(ctx, null, 9);
  ctx.restore();
}
