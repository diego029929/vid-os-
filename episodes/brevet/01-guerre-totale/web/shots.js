// ---------- Brevet histoire n°1 : « La Première Guerre mondiale, une guerre totale » ----------
// Un plan par phrase de script.json ; les temps viennent de words.js (voix.py), rien à recaler à la main.
const C = (base, extra) => Object.assign({}, base, extra);
const walkLegs = (t, sp = 9, amp = .55) => ({ L: [Math.sin(t * sp) * amp + .05, -Math.max(0, Math.sin(t * sp + 1)) * .7], R: [-Math.sin(t * sp) * amp + .05, -Math.max(0, -Math.sin(t * sp + 1)) * .7] });
const walkArms = (t, sp = 9, amp = .6) => ({ L: [.3 - Math.sin(t * sp) * amp, -.3], R: [.3 + Math.sin(t * sp) * amp, -.3] });
const handheld = (t, a = 4) => shake(t * .35, a, 1, 2);
const sitLegs = { L: [1.45, -1.5], R: [1.35, -1.45] };

// mots affichés (on colle la ponctuation isolée au mot d'avant)
const WD = [];
WORDS.forEach(w => { if (!/[\p{L}\p{N}]/u.test(w.w) && WD.length) { WD[WD.length - 1].w += w.w; WD[WD.length - 1].e = w.e; } else WD.push(Object.assign({}, w)); });
const nrm = s => s.toLowerCase().normalize('NFD').replace(/[̀-ͯ]/g, '').replace(/[^a-z0-9]/g, '');
const START = LINES.map((l, i) => i === 0 ? 0 : l[0] - .06);
// temps (relatif au plan) du mot qui commence par `m` dans la phrase `li`
function at(li, m, k = 0) {
  const c = WD.filter(w => w.line === li && nrm(w.w).startsWith(nrm(m)));
  const w = c[Math.min(k, c.length - 1)];
  return w ? w.s - START[li] : 0;
}
const SHOTS = [];
function shot(li, tr, draw) { SHOTS.push({ li, tr, draw }); }

// 0 — accroche : le poilu dans la tranchée, « GUERRE TOTALE ? » tamponné
shot(0, 'whip', (ctx, lt, t) => {
  const hh = handheld(t, 3);
  const cam = { x: 540 + hh[0], y: 900 + hh[1], z: 1.04 + lt * .03, r: Math.sin(t * .5) * .006 };
  applyCam(ctx, cam, .1); frontSky(ctx, t);
  applyCam(ctx, cam, .35); barbedWire(ctx, -300, 1400, 640, t);
  applyCam(ctx, cam, 1); trenchWall(ctx, 700, 1900, t);
  const look = kf(lt, [[0, [-.9, 0]], [.7, [-.9, 0]], [.9, [.9, 0]], [1.6, [.9, 0]], [1.8, [0, -.2]]]);
  const k = inv(at(0, 'guerre', 1) - .1, at(0, 'guerre', 1) + .25, lt);
  drawStick(ctx, C(POILU, {
    x: 540, y: 2070, s: 1450, bob: Math.sin(t * 3) * .004, headTilt: Math.sin(t * 1.4) * .03, shadow: false,
    arms: { L: [.3, -.1], R: [.35, -.15] }, face: k > 0 ? { eyes: 'wide', mouth: 'o', browUp: 1, look: [0, -.4] } : { eyes: 'normal', mouth: 'flat', look, browAng: -.15 },
  }));
  rain(ctx, t, .5);
  for (const [qx, qy, d] of [[200, 420, .15], [880, 380, .45]]) { const a = inv(d, d + .25, lt); bigLabel(ctx, '?', qx, qy + Math.sin(t * 4 + qx) * 10, 170, '#ffe14d', a, (qx - 540) * .0006); }
  ctx.setTransform(1, 0, 0, 1, 0, 0);
  if (k > 0) { ctx.save(); ctx.translate(540, 700); ctx.rotate(-.08); const s = 2.4 - 1.4 * backOut(k); ctx.scale(s, s); ctx.globalAlpha = clamp(k * 2.5);
    rrect(ctx, -440, -150, 880, 300, 26); ctx.fillStyle = 'rgba(246,241,232,.92)'; ctx.fill(); ctx.lineWidth = 18; ctx.strokeStyle = '#d0302a'; ctx.stroke();
    text(ctx, 'GUERRE', 0, -55, 118, '#d0302a', '#d0302a', 0, 'Poppins', 700); text(ctx, 'TOTALE ?', 0, 70, 118, '#d0302a', '#d0302a', 0, 'Poppins', 700); ctx.restore(); }
});

// 1 — « pas seulement sur le front » : on recule et on découvre tout le pays derrière
function countryStrip(ctx, t, hi = 0) {
  groundStrip(ctx, 1000, '#8fb565'); groundStrip(ctx, 1000, '#8fb565');
  // le front : bande de boue à gauche
  ctx.fillStyle = '#7a5a3e'; ctx.fillRect(-900, 980, 900, 1200); barbedWire(ctx, -880, -80, 1000, t); sandbagRow(ctx, -900, 0, 990, 7);
  for (let i = 0; i < 4; i++) { const x = -760 + i * 200; drawStick(ctx, C(POILU, { x, y: 1200, s: 260, shadow: false, face: { eyes: 'normal', mouth: 'flat', look: [-1, 0] } })); }
  // l'arrière : champs, maisons, route, usine
  field(ctx, 120, 1060, 360, 170); field(ctx, 520, 1100, 300, 150, '#b9d66e'); field(ctx, 160, 1300, 420, 160, '#e2c96f');
  house(ctx, 880, 1080, .9); house(ctx, 1080, 1100, .75, '#f2e6cf', '#a9472f'); house(ctx, 700, 1290, .8);
  ctx.fillStyle = '#d8cba8'; ctx.fillRect(-100, 1480, 2600, 90); for (let x = -100; x < 2500; x += 120) line(ctx, x, 1525, x + 60, 1525, 6, '#f6efdc');
  factory(ctx, 1600, 1250, .85, t, 0); house(ctx, 2050, 1100, .9); field(ctx, 1950, 1300, 380, 160);
}
shot(1, 'whip', (ctx, lt, t) => {
  const hh = handheld(t, 3);
  const p = ease(inv(at(1, 'seulement') - .2, at(1, 'front'), lt));
  const cam = { x: lerp(-420, 380, p) + hh[0], y: lerp(1100, 1230, p) + hh[1], z: lerp(1.45, .78, p), r: 0 };
  applyCam(ctx, cam, .1); frontSky(ctx, t, '#8ec5ea', '#f3e9c8');
  applyCam(ctx, cam, .2); drawCloud(ctx, 200 + t * 8, 380, 110, 1); drawCloud(ctx, 1100 + t * 6, 300, 90, 2);
  applyCam(ctx, cam, 1); countryStrip(ctx, t);
  sign(ctx, -460, 900, 1.0, 'LE FRONT', -.04, '#e0b25a');
  const a = inv(at(1, 'seulement'), at(1, 'seulement') + .3, lt);
  if (a > 0) for (const [x, y, d] of [[350, 960, 0], [960, 900, .15], [1600, 760, .3]]) bigLabel(ctx, '!', x, y - 120, 150, '#ffe14d', inv(d, d + .25, lt - at(1, 'seulement')));
});

// 2 — les tranchées, 1914-1918
shot(2, 'whip', (ctx, lt, t) => {
  const hh = handheld(t, 4);
  const cam = { x: 540 + lt * 22 + hh[0], y: 1060 + hh[1], z: 1.0 + lt * .025, r: 0 };
  applyCam(ctx, cam, .1); frontSky(ctx, t, '#8a9aa8', '#cdbf9e');
  applyCam(ctx, cam, .3); barbedWire(ctx, -300, 1500, 560, t);
  applyCam(ctx, cam, 1); trenchWall(ctx, 600, 1560, t);
  // 3 poilus : un de garde, un assis, un qui grelotte
  drawStick(ctx, C(POILU, { x: 230, y: 1600, s: 600, face: { eyes: 'normal', mouth: 'flat', look: [-.4, -.8] }, arms: { L: [2.2, -.4], R: [2.0, -.2] }, lean: -.06 }));
  drawStick(ctx, C(POILU, { x: 560, y: 1640, s: 560, legs: sitLegs, squash: .82, face: { eyes: 'half', mouth: 'frown' }, arms: { L: [.9, -1.6], R: [.9, -1.6] } }));
  const sh = Math.sin(t * 40) * .01;
  drawStick(ctx, C(POILU, { x: 880, y: 1620, s: 580, lean: sh, face: { eyes: 'normal', mouth: 'teeth', browAng: -.3, look: [-.3, 0] }, arms: { L: [.9, -2.3], R: [.9, -2.3] } }));
  rain(ctx, t, 1, 120);
  applyCam(ctx, cam, 1);
  const k = inv(at(2, '1914') - .1, at(2, '1914') + .3, lt);
  if (k > 0) { ctx.save(); ctx.translate(560, 470 + (1 - backOut(k)) * -300); sign(ctx, 0, 0, 1.25, '1914-1918', -.05, '#f2d27a'); ctx.restore(); }
  const m = inv(at(2, 'millions'), at(2, 'millions') + .5, lt);
  if (m > 0) { ctx.save(); ctx.setTransform(1, 0, 0, 1, 0, 0); pill(ctx, 540, 720, 560, 110, '#2a4f9e', 'DES MILLIONS', 66, m); ctx.restore(); }
});

// 3 — derrière eux : l'arrière travaille pour le front
shot(3, 'whip', (ctx, lt, t) => {
  const hh = handheld(t, 3);
  const p = ease(clamp(lt / (LINES[3][1] - START[3] + .2)));
  const cam = { x: lerp(-300, 1650, p) + hh[0], y: 1150 + hh[1], z: .78, r: 0 };
  applyCam(ctx, cam, .1); frontSky(ctx, t, '#8ec5ea', '#f3e9c8');
  applyCam(ctx, cam, .2); drawCloud(ctx, 300 + t * 8, 360, 110, 3); drawCloud(ctx, 1300 + t * 6, 280, 90, 4);
  applyCam(ctx, cam, 1); countryStrip(ctx, t);
  // camions qui montent au front avec des obus
  for (let i = 0; i < 3; i++) { const x = 2300 - ((t * 260 + i * 700) % 2300); truck(ctx, x, 1545, .9); for (let j = 0; j < 3; j++) shell(ctx, x - 90 + j * 40, 1460, .28); }
  // trains de flèches vers le front
  for (let i = 0; i < 5; i++) { const x = 1900 - ((t * 300 + i * 420) % 2100); ctx.save(); ctx.globalAlpha = .9; path(ctx, [[x, 1650], [x + 70, 1620], [x + 70, 1680]]); fillStroke(ctx, '#ffe14d', 5); ctx.restore(); }
  const k = inv(at(3, 'pays') - .1, at(3, 'pays') + .3, lt);
  ctx.setTransform(1, 0, 0, 1, 0, 0);
  pill(ctx, 540, 520, 600, 130, '#c8432f', "L'ARRIÈRE", 76, k);
  if (k > 0) text(ctx, '(tout ce qui est loin du front)', 540, 640, 38, '#fff', INK, 9, 'Poppins', 700);
});

// 4 — l'usine : des obus jour et nuit
shot(4, 'whip', (ctx, lt, t) => {
  const hh = handheld(t, 3);
  const cam = { x: 540 + hh[0], y: 1000 + hh[1], z: 1.02 + lt * .03, r: 0 };
  const night = ease(inv(at(4, 'nuit') - .1, at(4, 'nuit') + .4, lt));
  ctx.setTransform(1, 0, 0, 1, 0, 0); ctx.fillStyle = mix('#e2b98a', '#4a3a52', night); ctx.fillRect(0, 0, W, H);
  applyCam(ctx, cam, 1);
  // grande fenêtre : soleil puis lune
  rrect(ctx, 220, 200, 640, 420, 12); fillStroke(ctx, mix('#9fd3f2', '#1d2550', night), 10);
  ctx.save(); rrect(ctx, 220, 200, 640, 420, 12); ctx.clip();
  if (night < 1) { drawSun(ctx, 420, 360 + night * 300, 70, t, 1 - night); }
  if (night > 0) { circle(ctx, 680, 560 - night * 230, 62); fillStroke(ctx, '#f4f0d8', 8); circle(ctx, 705, 545 - night * 230, 52); ctx.fillStyle = '#1d2550'; ctx.fill(); }
  ctx.restore();
  line(ctx, 540, 200, 540, 620, 10); line(ctx, 220, 410, 860, 410, 10);
  // piles d'obus
  // tapis roulant
  rrect(ctx, -100, 1150, 1300, 70, 30); fillStroke(ctx, '#5a5560', 7);
  for (let x = -100; x < 1200; x += 70) { const xx = x + (t * 140) % 70; circle(ctx, xx, 1185, 18); fillStroke(ctx, '#8a8592', 4); }
  for (let i = 0; i < 6; i++) { const x = ((t * 140 + i * 230) % 1380) - 120; shell(ctx, x, 1140, .5); }
  drawStick(ctx, C(OUVRIERE, { x: 300, y: 1560, s: 560, face: { eyes: 'normal', mouth: 'flat', look: [.6, .5] }, arms: { L: { ik: [.25, -.62] }, R: { ik: [.4, -.55 + Math.abs(Math.sin(t * 6)) * .1] } } }));
  drawStick(ctx, C({ cols: ['#5f6f86', '#5f6f86'], hat: 'hair', hatCol: '#cfcfcf', belt: false }, { x: 800, y: 1600, s: 580, flip: -1, face: { eyes: 'normal', mouth: 'flat', look: [.6, .5] }, arms: { L: { ik: [.3, -.6] }, R: { ik: [.35, -.58] } } }));
  if (night > 0) { ctx.save(); ctx.setTransform(1, 0, 0, 1, 0, 0); ctx.globalCompositeOperation = 'multiply'; ctx.fillStyle = `rgba(70,60,120,${.35 * night})`; ctx.fillRect(0, 0, W, H); ctx.restore(); applyCam(ctx, cam, 1); for (const lx of [300, 800]) { lightShaft(ctx, lx, 700, 40, 360, 900, .25 * night); } }
  ctx.setTransform(1, 0, 0, 1, 0, 0);
  const kj = inv(at(4, 'jour') - .05, at(4, 'jour') + .25, lt);
  pill(ctx, 540, 820, 560, 120, mix('#f2a72a', '#2a3f8f', night), night > .5 ? 'LA NUIT AUSSI' : 'LE JOUR', 64, kj);
});

// 5 — les femmes remplacent les hommes partis au front
shot(5, 'whip', (ctx, lt, t) => {
  const hh = handheld(t, 3);
  const cam = { x: 540 + hh[0], y: 1000 + hh[1], z: 1.0 + lt * .03, r: 0 };
  ctx.setTransform(1, 0, 0, 1, 0, 0); ctx.fillStyle = '#e2b98a'; ctx.fillRect(0, 0, W, H);
  applyCam(ctx, cam, 1);
  ctx.fillStyle = '#c99a6a'; ctx.fillRect(-500, 1560, 2100, 900);
  // machine (tour) au centre
  rrect(ctx, 380, 1150, 360, 420, 16); fillStroke(ctx, '#5f6a78', 8); rrect(ctx, 420, 1190, 280, 120, 10); fillStroke(ctx, '#8b96a4', 6);
  circle(ctx, 560, 1420, 70); fillStroke(ctx, '#3c4450', 7); ctx.save(); ctx.translate(560, 1420); ctx.rotate(t * 3); line(ctx, -60, 0, 60, 0, 10, '#c9ced6'); line(ctx, 0, -60, 0, 60, 10, '#c9ced6'); ctx.restore();
  const tOut = .15;
  const px = kf(lt, [[0, 760], [tOut, 760], [tOut + 1.4, -260]], x => x);
  const walking = lt > tOut;
  drawStick(ctx, C(POILU, { x: px, y: 1640, s: 560, flip: -1, legs: walking ? walkLegs(t, 10) : undefined, arms: walking ? { L: [.3, -.3], R: [2.7, .2 + Math.sin(t * 9) * .2] } : undefined, face: { eyes: 'normal', mouth: walking ? 'smile' : 'flat', look: [.8, 0] } }));
  const tIn = at(5, 'remplacent') - .3;
  const wx = kf(lt, [[0, 1350], [tIn, 1350], [tIn + 1.1, 820]], easeOut);
  const arrived = lt > tIn + 1.1;
  drawStick(ctx, C(OUVRIERE, { x: wx, y: 1640, s: 580, flip: -1, legs: !arrived && lt > tIn ? walkLegs(t, 10) : undefined, arms: arrived ? { L: { ik: [.42, -.62] }, R: { ik: [.5, -.5] } } : undefined, face: { eyes: 'normal', mouth: arrived ? 'grin' : 'smile', browAng: .25, look: [1, 0] } }));
  ctx.setTransform(1, 0, 0, 1, 0, 0);
  const k = inv(at(5, 'remplacent'), at(5, 'remplacent') + .3, lt);
  pill(ctx, 540, 520, 760, 130, '#c8432f', 'LES MUNITIONNETTES', 66, k);
  if (k > 0) text(ctx, 'ouvrières des usines d’armes', 540, 650, 40, '#fff', INK, 9, 'Poppins', 700);
});

// 6 — journaux censurés + propagande
shot(6, 'whip', (ctx, lt, t) => {
  const hh = handheld(t, 3);
  const cam = { x: 540 + hh[0], y: 960 + hh[1], z: 1.0 + lt * .02, r: 0 };
  ctx.setTransform(1, 0, 0, 1, 0, 0);
  const g = ctx.createRadialGradient(540, 900, 100, 540, 900, 1300); g.addColorStop(0, '#6f86b8'); g.addColorStop(1, '#2a3156'); ctx.fillStyle = g; ctx.fillRect(0, 0, W, H);
  applyCam(ctx, cam, 1);
  const inN = easeOut(clamp(lt / .35));
  const stamp = inv(at(6, 'censures') - .05, at(6, 'censures') + .3, lt);
  const tp = at(6, 'propagande') - .15;
  const pin = easeOut(inv(tp, tp + .4, lt));
  newspaper(ctx, 540 - pin * 160, 860 + (1 - inN) * 900, 1.15 - pin * .15, -.05 - pin * .08, stamp);
  if (pin > 0) poster(ctx, 1500 - pin * 840, 920, 1.0, .07, t);
  const v = inv(at(6, 'victoire') - .05, at(6, 'victoire') + .3, lt);
  if (v > 0) for (let i = 0; i < 5; i++) { const a = i / 5 * TAU + t; sparkle(ctx, 660 + Math.cos(a) * 380, 900 + Math.sin(a) * 470, 40 * v, v); }
});

// 7 — les colonies envoient des soldats
shot(7, 'cut', (ctx, lt, t) => {
  const hh = handheld(t, 3);
  const cam = { x: 540 + hh[0], y: 960 + hh[1], z: 1.0, r: 0 };
  applyCam(ctx, cam, .1); drawSky(ctx, '#7cc0ea', '#f6e7c0', -300, 800);
  applyCam(ctx, cam, .2); drawCloud(ctx, 300 + t * 8, 300, 100, 5); drawCloud(ctx, 900 + t * 6, 220, 80, 6);
  applyCam(ctx, cam, 1); sea(ctx, 700, t);
  coast(ctx, 170, 1000, 300, 360, '#d9b66a', null, 1);
  coast(ctx, 930, 880, 300, 330, '#8fbf6a', null, -1);
  for (const [lx, ly, lab] of [[175, 700, 'COLONIES'], [905, 600, 'FRANCE']]) { rrect(ctx, lx - 160, ly - 42, 320, 84, 18); fillStroke(ctx, '#fff', 6); text(ctx, lab, lx, ly + 2, 48, INK, INK, 0, 'Poppins', 700); }
  // trajet en pointillés
  ctx.save(); ctx.setLineDash([22, 18]); ctx.lineDashOffset = -t * 60; ctx.lineWidth = 8; ctx.strokeStyle = 'rgba(255,255,255,.9)';
  ctx.beginPath(); ctx.moveTo(230, 1200); ctx.quadraticCurveTo(540, 1330, 880, 1080); ctx.stroke(); ctx.restore();
  const p = ease(clamp(lt / (LINES[7][1] - START[7] + .4)));
  const bx = lerp(390, 690, p), by = lerp(1210, 1130, p) + Math.sin(p * Math.PI) * 60;
  ctx.save(); ctx.translate(bx, by); ctx.scale(.58, .58);
  for (let i = 0; i < 4; i++) drawStick(ctx, C(TIRAILLEUR, { x: -220 + i * 120, y: -160, s: 170, shadow: false, face: { eyes: 'normal', mouth: 'flat', look: [1, 0] } }));
  steamer(ctx, 0, 0, 1, t); ctx.restore();
  const k = inv(at(7, 'soldats') - .1, at(7, 'soldats') + .3, lt);
  ctx.setTransform(1, 0, 0, 1, 0, 0);
  if (k > 0) { text(ctx, 'Afrique, Indochine, Madagascar…', 540, 1620, 42, '#fff', INK, 10, 'Poppins', 700); }
});

// 8 — bilan : près de 10 millions de soldats morts (ton sérieux, pas d'effet)
shot(8, 'cut', (ctx, lt, t) => {
  const cam = { x: 540, y: 960, z: 1.0 + lt * .03, r: 0 };
  ctx.setTransform(1, 0, 0, 1, 0, 0);
  const g = ctx.createLinearGradient(0, 0, 0, 1100); g.addColorStop(0, '#3a3d55'); g.addColorStop(1, '#a88f8a'); ctx.fillStyle = g; ctx.fillRect(0, 0, W, H);
  applyCam(ctx, cam, 1);
  ctx.fillStyle = '#5f6e58'; ctx.fillRect(-500, 1000, 2100, 1500);
  const rows = 9, dur = LINES[8][1] - START[8];
  for (let r = 0; r < rows; r++) {
    const y = 1010 + r * r * 9 + r * 40, sc = .35 + r * .12, n = 9 + Math.max(0, 6 - r);
    for (let i = 0; i < n; i++) { const x = 540 + (i - (n - 1) / 2) * (1200 / n) * (1 + r * .08); cross(ctx, x, y, sc, inv(r * .12 + i * .01, r * .12 + i * .01 + .3, lt)); }
  }
  ctx.setTransform(1, 0, 0, 1, 0, 0);
  const c = easeOut(inv(.2, Math.max(1, dur - .2), lt));
  const n = Math.round(c * 10000000);
  text(ctx, n.toLocaleString('fr-FR').replace(/ | /g, ' '), 540, 440, 150, '#fff', INK, 16, 'Poppins', 700);
  text(ctx, 'soldats morts', 540, 580, 64, '#f0e6e0', INK, 10, 'Poppins', 700);
  text(ctx, '(environ, tous pays confondus)', 540, 670, 36, '#e3d8d4', INK, 8, 'Poppins', 700);
});

// 9 — récap : une guerre totale = toute la société mobilisée
shot(9, 'whip', (ctx, lt, t) => {
  const cam = { x: 540, y: 960, z: 1.0 + lt * .02, r: Math.sin(t * .6) * .01 };
  ctx.setTransform(1, 0, 0, 1, 0, 0);
  const g = ctx.createRadialGradient(540, 900, 50, 540, 900, 1200); g.addColorStop(0, '#fff2b0'); g.addColorStop(.6, '#ffc94d'); g.addColorStop(1, '#f08a2a'); ctx.fillStyle = g; ctx.fillRect(0, 0, W, H);
  ctx.save(); ctx.translate(540, 760); ctx.rotate(t * .15); for (let i = 0; i < 16; i++) { ctx.rotate(TAU / 16); path(ctx, [[-60, 200], [60, 200], [0, 1400]]); ctx.fillStyle = 'rgba(255,255,255,.18)'; ctx.fill(); } ctx.restore();
  applyCam(ctx, cam, 1);
  const k0 = inv(0, .3, lt);
  ctx.save(); ctx.translate(540, 760); const s0 = backOut(k0); ctx.scale(s0, s0); circle(ctx, 0, 0, 215); fillStroke(ctx, '#c8432f', 12);
  text(ctx, 'GUERRE', 0, -40, 78, '#fff', INK, 0, 'Poppins', 700); text(ctx, 'TOTALE', 0, 50, 78, '#fff', INK, 0, 'Poppins', 700); ctx.restore();
  const icons = [
    ['SOLDATS', '#7f9cc6', c => drawStick(c, C(POILU, { x: 0, y: 160, s: 260, shadow: false }))],
    ['USINES', '#e8c04a', c => shell(c, 0, 70, .55)],
    ['FEMMES', '#e07a5a', c => drawStick(c, C(OUVRIERE, { x: 0, y: 160, s: 260, shadow: false, face: { mouth: 'grin' } }))],
    ['PROPAGANDE', '#f3ead6', c => { rrect(c, -55, -70, 110, 140, 6); fillStroke(c, '#f6edd8', 6); text(c, '!', 0, 0, 90, '#d0302a', INK, 0, 'Poppins', 700); }],
    ['COLONIES', '#7fc4dc', c => steamer(c, 0, 60, .26, t)],
  ];
  const span = Math.max(1.5, LINES[9][1] - START[9] - .3);
  icons.forEach(([lab, col, dr], i) => {
    const a = -Math.PI / 2 + i / 5 * TAU, R = 370;
    const x = 540 + Math.cos(a) * R, y = 760 + Math.sin(a) * R * 1.02;
    const k = inv(.3 + i * span / 6, .3 + i * span / 6 + .3, lt);
    line(ctx, 540 + Math.cos(a) * 225, 760 + Math.sin(a) * 230, x - Math.cos(a) * 110, y - Math.sin(a) * 110, 10 * clamp(k * 3), INK);
    iconBadge(ctx, x, y, 105, k, col, dr);
    if (k > 0) { ctx.save(); ctx.translate(x, y + 150); const s = backOut(clamp(k)); ctx.scale(s, s); text(ctx, lab, 0, 0, 40, '#fff', INK, 9, 'Poppins', 700); ctx.restore(); }
  });
});

// 10 — fin : tu saurais l'expliquer au brevet ? (la question boucle avec l'accroche)
shot(10, 'cut', (ctx, lt, t) => {
  const hh = handheld(t, 3);
  const cam = { x: 540 + hh[0], y: 1000 + hh[1], z: 1.0 + lt * .03, r: 0 };
  ctx.setTransform(1, 0, 0, 1, 0, 0); ctx.fillStyle = '#cfe6f5'; ctx.fillRect(0, 0, W, H);
  applyCam(ctx, cam, 1);
  rrect(ctx, 140, 220, 800, 420, 16); fillStroke(ctx, '#2f5a3e', 12);
  text(ctx, '1914-1918', 540, 330, 78, '#f4f1ea', INK, 0, 'Lora', 700);
  text(ctx, '= guerre totale', 540, 450, 70, '#f4f1ea', INK, 0, 'Lora', 600);
  ctx.fillStyle = '#d9b98a'; ctx.fillRect(-500, 1560, 2100, 900);
  rrect(ctx, 120, 1440, 840, 50, 10); fillStroke(ctx, '#a8703e', 7); line(ctx, 200, 1490, 200, 1700, 14); line(ctx, 880, 1490, 880, 1700, 14);
  const think = Math.sin(t * 5) * .15;
  drawStick(ctx, C(ELEVE, { x: 540, y: 1700, s: 640, face: { eyes: 'normal', mouth: 'smirk', look: [.4, -.7], browOne: 1 }, arms: { L: [.5, -.4], R: { ik: [.12 + think * .05, -.95], bend: -1 } } }));
  for (const [qx, qy, d] of [[200, 760, .1], [880, 720, .35]]) bigLabel(ctx, '?', qx, qy + Math.sin(t * 4 + qx) * 10, 150, '#ffe14d', inv(d, d + .25, lt));
  ctx.setTransform(1, 0, 0, 1, 0, 0);
  pill(ctx, 330, 900, 330, 140, '#2fa35b', 'OUI', 80, inv(at(10, 'oui') - .05, at(10, 'oui') + .25, lt));
  pill(ctx, 750, 900, 330, 140, '#d0302a', 'NON', 80, inv(at(10, 'non') - .05, at(10, 'non') + .25, lt));
});

// temps des plans
SHOTS.forEach((s, i) => { s.start = START[s.li]; s.end = i < SHOTS.length - 1 ? START[SHOTS[i + 1].li] : VO_END + 1.2; });
