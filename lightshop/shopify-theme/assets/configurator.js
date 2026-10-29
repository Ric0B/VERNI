/* Lamp configurator: shape, size, colour, base/cable, extras, live price and live 3D.
   Geometry is the same radial field r(theta, z) as design/lampgen.py and design/formlabor.html;
   a size is a uniform scale of that field, so printability (wall angle) is the same at every size.
   Runs inside the Shopify section (sections/configurator.liquid, which passes real variant IDs and
   prices) and as a standalone preview (no cart, default prices). Needs three.js r128. */
(function () {
  'use strict';
  const root = document.querySelector('[data-configurator]');
  if (!root) return;

  const TAU = Math.PI * 2;
  const clamp = (x, a, b) => Math.min(b, Math.max(a, x));
  const smooth = (a, b, x) => { const t = clamp((x - a) / (b - a), 0, 1); return t * t * (3 - 2 * t); };
  const collar = (z, p) => p.collar > 0 ? smooth(p.collar, p.collar + p.collar_blend, z) : 1;

  // ---------- geometry (field functions identical to lampgen.py; korb profile identical to korb.py)
  const FIELDS = {
    aare: { p: { height: 320, r_base: 88, r_belly: 104, belly_power: 1.2, ribs: 48, twist: 0.12, rib_depth: 4.5, rib_sharpness: 0.7, collar: 10, collar_blend: 14 },
      f(th, z, p) { const t = z / p.height; const prof = p.r_base + (p.r_belly - p.r_base) * Math.pow(Math.sin(Math.PI * clamp(t, 0, 1)), p.belly_power);
        let rib = Math.sin(p.ribs * (th + TAU * p.twist * t)); rib = Math.sign(rib) * Math.pow(Math.abs(rib), p.rib_sharpness);
        const amp = p.rib_depth * (0.35 + 0.65 * Math.sin(Math.PI * clamp(t, 0, 1))); return prof + amp * rib * collar(z, p); } },
    grat: { p: { height: 300, r_base: 98, r_top: 84, bulge: 14, sides: 14, folds: 3, fold_angle: 0.38, collar: 10, collar_blend: 14 },
      f(th, z, p) { const h = p.height, k = p.sides, t = z / h; const zig = 2 * Math.abs(((t * p.folds) % 1) - 0.5);
        const rot = p.fold_angle * (zig - 0.5) * collar(z, p); const seg = TAU / k; const a = ((th + rot) % seg + seg) % seg - seg / 2;
        const poly = Math.cos(Math.PI / k) / Math.cos(a); const prof = p.r_base + (p.r_top - p.r_base) * t + p.bulge * Math.sin(Math.PI * clamp(t, 0, 1));
        return prof * (1 + (poly - 1) * collar(z, p)); } },
    bise: { p: { height: 320, r_mid: 92, r_swing: 10, n: 20, turns: 2.0, amp: 5.0, collar: 10, collar_blend: 14 },
      f(th, z, p) { const t = z / p.height; const prof = p.r_mid - p.r_swing * Math.cos(Math.PI * (2 * t - 1));
        const w = Math.sin(p.n * th + TAU * p.turns * t) * Math.cos(p.n * th - TAU * p.turns * t); return prof + p.amp * w * collar(z, p); } },
    firn: { pendant: true, flip: true, p: { height: 200, r_top: 34, r_rim: 150, bell_power: 1.6, pleats: 96, pleat_depth: 3.2, pleat_growth: 1.4, pleat_wave: 2.5, collar: 12, collar_blend: 18 },
      f(th, z, p) { const h = p.height, t = clamp(z / h, 0, 1); const prof = p.r_top + (p.r_rim - p.r_top) * Math.pow(Math.sin(t * Math.PI / 2), p.bell_power);
        const pleat = Math.sin(p.pleats * th + p.pleat_wave * Math.sin(3 * th) * t); return prof + p.pleat_depth * Math.pow(t, p.pleat_growth) * pleat * collar(z, p); } },
    korb: { pendant: true, woven: true, p: { height: 230, r0: 118, rb: 140, rc: 30, zb: 80, cell: 9, amp: 3.9, bands: [[0, 4], [80, 81.6], [150, 151.6], [218, 230]] },
      f(th, z, p) { if (z <= p.zb) return p.r0 + (p.rb - p.r0) * Math.sin(Math.PI / 2 * Math.max(0, z) / p.zb);
        const zc0 = p.height - 12; if (z <= zc0) return p.rb - (p.rb - p.rc) * smooth(0, 1, (z - p.zb) / (zc0 - p.zb)); return p.rc; } },
  };

  // ---------- default catalogue (CHF). The Shopify section overrides prices and adds variant IDs.
  const DEFAULTS = {
    currency: 'CHF', locale: 'de-CH',
    lead: 'Gedruckt nach deiner Bestellung in der Schweiz. Versand in 5–8 Werktagen.',
    designs: [
      { key: 'aare', title: 'Aare', kind: 'Tischleuchte', note: '48 Rippen, eine Achteldrehung',
        sizes: [{ code: 'S', scale: 0.7, price: 139 }, { code: 'M', scale: 0.85, price: 169 }, { code: 'L', scale: 1, price: 199 }] },
      { key: 'grat', title: 'Grat', kind: 'Tischleuchte', note: '14 Kanten, dreimal gefaltet',
        sizes: [{ code: 'S', scale: 0.7, price: 179 }, { code: 'M', scale: 0.85, price: 219 }, { code: 'L', scale: 1, price: 259 }] },
      { key: 'bise', title: 'Bise', kind: 'Tischleuchte · Atelier', note: 'Zwei Spiralen, ein Gewebe',
        sizes: [{ code: 'S', scale: 0.7, price: 189 }, { code: 'M', scale: 0.85, price: 229 }, { code: 'L', scale: 1, price: 269 }] },
      { key: 'firn', title: 'Firn', kind: 'Pendelleuchte', note: '96 Falten öffnen sich zum Rand',
        sizes: [{ code: 'S', scale: 0.7, price: 149 }, { code: 'M', scale: 0.85, price: 189 }, { code: 'L', scale: 1, price: 229 }] },
      { key: 'korb', title: 'Korb', kind: 'Pendelleuchte · gewoben', note: 'Ohne Slicer gedruckt: ein durchgehender Faden',
        sizes: [{ code: 'S', scale: 0.6, price: 169 }, { code: 'M', scale: 0.8, price: 219 }, { code: 'L', scale: 1, price: 269 }] },
    ],
    colours: [
      { key: 'nebel', name: 'Nebelweiss', hex: '#ece9e1' },
      { key: 'kalk', name: 'Kalkgrau', hex: '#b9b6ad' },
      { key: 'bernstein', name: 'Bernstein', hex: '#d98a2b' },
      { key: 'ziegel', name: 'Ziegel', hex: '#b5533a' },
      { key: 'salbei', name: 'Salbei', hex: '#9fae8c' },
      { key: 'gletscher', name: 'Gletscherblau', hex: '#8fb4c4' },
      { key: 'rauch', name: 'Rauch', hex: '#56524d' },
    ],
    twoTone: { price: 25, splits: [{ key: '13', name: 'unteres Drittel', at: 1 / 3 }, { key: '12', name: 'Mitte', at: 0.5 }, { key: '23', name: 'oberes Drittel', at: 2 / 3 }] },
    bases: [
      { key: 'schwarz', name: 'Sockel Schwarz', hex: '#1c1f21', price: 0 },
      { key: 'weiss', name: 'Sockel Kalkweiss', hex: '#e6e4de', price: 0 },
      { key: 'eiche', name: 'Sockel Eiche massiv', hex: '#b48a5a', price: 59, addon: 'oak' },
    ],
    canopies: [
      { key: 'schwarz', name: 'Baldachin Schwarz', hex: '#1c1f21', price: 0 },
      { key: 'weiss', name: 'Baldachin Weiss', hex: '#e6e4de', price: 0 },
    ],
    cables: [
      { key: 'schwarz', name: 'Schwarz', hex: '#1c1f21' },
      { key: 'leinen', name: 'Leinen', hex: '#d9d1bf' },
      { key: 'rost', name: 'Rost', hex: '#9a4b2c' },
      { key: 'tanne', name: 'Tanne', hex: '#3d5244' },
    ],
    lengths: [{ key: '150', name: '1.5 m', price: 0 }, { key: '300', name: '3 m', price: 12, addon: 'cable' }],
    dimmer: { price: 29, addon: 'dimmer' },
    engraving: { price: 19, max: 14, addon: 'engraving' },
    addons: {},   // Shopify: { oak: {id, price}, cable: {...}, dimmer: {...}, engraving: {...}, twotone: {...} }
  };

  const ext = (() => { const n = root.querySelector('script[data-configurator-data]'); try { return n ? JSON.parse(n.textContent) : {}; } catch (e) { return {}; } })();
  const DATA = Object.assign({}, DEFAULTS, ext.settings || {});
  // product data from Shopify: { designs: { aare: { variants: [{id, title, price, available}] } }, addons: {...} }
  if (ext.designs) for (const d of DATA.designs) { const x = ext.designs[d.key]; if (!x) continue;
    d.product = x.url; for (const s of d.sizes) { const v = (x.variants || []).find(v => String(v.title).trim().toUpperCase().startsWith(s.code));
      if (v) { s.id = v.id; s.price = v.price / 100; s.available = v.available; } } }
  if (ext.addons) { DATA.addons = {}; for (const [k, v] of Object.entries(ext.addons)) if (v && v.id) DATA.addons[k] = { id: v.id, price: v.price / 100 }; }
  const addonPrice = (key, fallback) => DATA.addons[key] ? DATA.addons[key].price : fallback;
  if (DATA.addons.twotone) DATA.twoTone.price = DATA.addons.twotone.price;
  const shop = !!ext.designs;

  const money = v => new Intl.NumberFormat(DATA.locale, { style: 'currency', currency: DATA.currency, minimumFractionDigits: v % 1 ? 2 : 0, maximumFractionDigits: 2 }).format(v);
  const $ = sel => root.querySelector(sel);

  // ---------- state (also kept in the URL hash, so a configuration can be shared)
  const S = { design: 'aare', size: 'M', colour: 'nebel', two: false, colour2: 'bernstein', split: '12', base: 'schwarz', canopy: 'schwarz', cable: 'schwarz', length: '150', dimmer: false, engrave: '' };
  const KEYS = Object.keys(S);
  function readHash() {
    const h = decodeURIComponent(location.hash.replace(/^#/, '')); if (!h.startsWith('cfg=')) return;
    h.slice(4).split(';').forEach(kv => { const [k, v] = kv.split(':'); if (!KEYS.includes(k)) return;
      S[k] = typeof S[k] === 'boolean' ? v === '1' : v; });
    if (!DATA.designs.find(d => d.key === S.design)) S.design = 'aare';
  }
  function writeHash() {
    const s = KEYS.map(k => k + ':' + (typeof S[k] === 'boolean' ? (S[k] ? 1 : 0) : S[k])).join(';');
    history.replaceState(null, '', '#cfg=' + encodeURIComponent(s));
  }

  const design = () => DATA.designs.find(d => d.key === S.design);
  const size = () => design().sizes.find(s => s.code === S.size) || design().sizes[1];
  const isPendant = () => !!FIELDS[S.design].pendant;
  const byKey = (list, k) => list.find(x => x.key === k) || list[0];

  // ---------- dimensions per design (scale 1), sampled once
  const DIMS = {};
  for (const d of DATA.designs) { const F = FIELDS[d.key], p = F.p; let rmax = 0;
    for (let j = 0; j <= 40; j++) for (let i = 0; i < 180; i++) rmax = Math.max(rmax, F.f(i / 180 * TAU, j / 40 * p.height, p));
    DIMS[d.key] = { h: p.height, d: 2 * rmax }; }
  const dimText = (key, scale) => `${Math.round(DIMS[key].h * scale / 10)} × Ø ${Math.round(DIMS[key].d * scale / 10)} cm`;

  // ---------- three.js
  const view = $('.cfg-view'), canvas = $('.cfg-canvas');
  let renderer = null;
  try { renderer = new THREE.WebGLRenderer({ canvas, antialias: true, alpha: true }); renderer.setClearColor(0x000000, 0); }
  catch (e) { view.insertAdjacentHTML('beforeend', '<p class="cfg-nogl">Die 3D-Vorschau braucht WebGL. Konfigurieren und bestellen geht trotzdem.</p>'); }
  const scene = new THREE.Scene(), cam = new THREE.PerspectiveCamera(28, 1, 10, 20000), group = new THREE.Group(); scene.add(group);
  const hex3 = h => { const c = new THREE.Color(h); return new THREE.Vector3(Math.pow(c.r, 2.2), Math.pow(c.g, 2.2), Math.pow(c.b, 2.2)); };
  const mat = new THREE.ShaderMaterial({
    side: THREE.DoubleSide, extensions: { derivatives: true },
    uniforms: { uOn: { value: 1 }, uLight: { value: new THREE.Vector3() }, uH: { value: 300 }, uKey: { value: new THREE.Vector3(-0.6, 0.5, 0.8).normalize() },
      uC1: { value: hex3('#ece9e1') }, uC2: { value: hex3('#d98a2b') }, uSplit: { value: 2 }, uFlip: { value: 0 },
      uWoven: { value: 0 }, uWaves: { value: 97.5 }, uCellH: { value: 7.8 }, uBands: { value: [new THREE.Vector2(), new THREE.Vector2(), new THREE.Vector2(), new THREE.Vector2()] } },
    vertexShader: 'varying vec3 vN; varying vec3 vP; varying vec3 vW; varying float vZ; varying float vT; attribute float zz; attribute float tt;' +
      'void main(){ vZ = zz; vT = tt; vN = normalize(normalMatrix*normal); vec4 w = modelMatrix*vec4(position,1.); vW = w.xyz; vec4 mv = viewMatrix*w; vP = mv.xyz; gl_Position = projectionMatrix*mv; }',
    fragmentShader: `uniform float uOn; uniform vec3 uLight; uniform float uH; uniform vec3 uKey; uniform vec3 uC1; uniform vec3 uC2; uniform float uSplit; uniform float uFlip;
      uniform float uWoven; uniform float uWaves; uniform float uCellH; uniform vec2 uBands[4];
      varying vec3 vN; varying vec3 vP; varying vec3 vW; varying float vZ; varying float vT;
      void main(){
        if (uWoven > 0.5) {
          bool band = false; for (int i = 0; i < 4; i++) { if (vZ >= uBands[i].x && vZ <= uBands[i].y) band = true; }
          if (!band) { float p = vT * uWaves; float a = abs(fract(p + vZ / uCellH) - 0.5); float b = abs(fract(p - vZ / uCellH) - 0.5);
            float w = 0.5 - 0.075; float fa = fwidth(p + vZ / uCellH); if (max(a, b) < w - fa) discard; } }
        vec3 n = normalize(vN); vec3 v = normalize(-vP); bool back = !gl_FrontFacing; if(back) n = -n;
        float zN = uFlip > 0.5 ? 1.0 - vZ / uH : vZ / uH;
        vec3 albedo = zN > uSplit ? uC2 : uC1; float layer = 0.94 + 0.06*sin(vZ*6.2831/1.1);
        vec3 key = normalize((viewMatrix*vec4(uKey,0.)).xyz); float diff = max(dot(n,key),0.); float fill = 0.5+0.5*n.y; float rim = pow(1.-max(dot(n,v),0.),3.);
        vec3 day = pow(albedo, vec3(0.8))*1.1; vec3 studio = day*(0.38 + 0.62*diff + 0.22*fill) + 0.10*rim;
        vec3 L = normalize(vW - uLight); float d = length(vW - uLight); vec3 nw = normalize(cross(dFdx(vW), dFdy(vW))); if(dot(nw, vW-uLight) < 0.) nw = -nw;
        float through = max(dot(nw, L), 0.); float fall = 1.0/(1.0 + pow(d/(uH*0.55), 2.2));
        float lum = dot(albedo, vec3(0.2126,0.7152,0.0722)); vec3 hue = albedo / max(max(albedo.r, albedo.g), max(albedo.b, 0.02));
        vec3 tint = mix(vec3(1.0,0.72,0.40), hue*vec3(1.0,0.93,0.82), 0.8) * mix(0.35, 1.0, clamp(lum*3.0, 0.0, 1.0));
        vec3 glow = tint*(0.06 + 1.5*pow(through,1.6))*fall; if(back) glow *= 2.2;
        vec3 col = mix(studio, albedo*0.04 + glow, uOn)*layer;
        col = col*(2.51*col+0.03)/(col*(2.43*col+0.59)+0.14);
        gl_FragColor = vec4(pow(clamp(col,0.,1.), vec3(1./2.2)), 1.); }`,
  });
  const solid = c => new THREE.MeshBasicMaterial({ color: c });
  const baseMesh = new THREE.Mesh(new THREE.CylinderGeometry(1, 1, 1, 96), solid(0x1c1f21));
  const cableMesh = new THREE.Mesh(new THREE.CylinderGeometry(2.2, 2.2, 1, 8), solid(0x1c1f21));
  const canopyMesh = new THREE.Mesh(new THREE.CylinderGeometry(60, 60, 22, 64), solid(0x1c1f21));
  let shade = null, built = '', yaw = 0.5, pitch = 0.16;

  function build() {
    const d = design(), sz = size(), F = FIELDS[d.key], s = sz.scale, p = F.p, H = p.height * s;
    const key = d.key + s;
    if (key !== built) {
      // NT + 1 columns: the last repeats the first (theta = 2 pi), so the woven phase (tt) never wraps inside a triangle
      const NT = F.woven ? 720 : 400, C = NT + 1, DZ = 2 * s, nz = Math.ceil(H / DZ) + 1, n = nz * C;
      const pos = new Float32Array(n * 3), zz = new Float32Array(n), tt = new Float32Array(n);
      for (let j = 0; j < nz; j++) { const z = Math.min(j * DZ, H);
        for (let i = 0; i < C; i++) { const th = (i % NT) / NT * TAU, r = s * F.f(th, z / s, p), k = j * C + i;
          pos[3 * k] = r * Math.cos(th); pos[3 * k + 1] = z; pos[3 * k + 2] = -r * Math.sin(th); zz[k] = z; tt[k] = i / NT; } }
      const idx = []; for (let j = 0; j < nz - 1; j++) for (let i = 0; i < NT; i++) { const a = j * C + i, b = a + 1, c = a + C, e = b + C; idx.push(a, e, b, a, c, e); }
      const g = new THREE.BufferGeometry(); g.setAttribute('position', new THREE.BufferAttribute(pos, 3)); g.setAttribute('zz', new THREE.BufferAttribute(zz, 1));
      g.setAttribute('tt', new THREE.BufferAttribute(tt, 1)); g.setIndex(idx); g.computeVertexNormals();
      if (shade) { group.remove(shade); shade.geometry.dispose(); }
      shade = new THREE.Mesh(g, mat); group.add(shade); built = key;
      if (F.flip) { shade.rotation.x = Math.PI; shade.position.y = H; } else { shade.rotation.x = 0; shade.position.y = 0; }
      mat.uniforms.uFlip.value = F.flip ? 1 : 0; mat.uniforms.uH.value = H; mat.uniforms.uWoven.value = F.woven ? 1 : 0;
      if (F.woven) { const rref = p.rb * s; mat.uniforms.uWaves.value = Math.floor(TAU * rref / p.cell) + 0.5; mat.uniforms.uCellH.value = 2 * p.amp * s;
        p.bands.forEach((b, i) => mat.uniforms.uBands.value[i].set(b[0] * s, b[1] * s)); }
      group.userData = { h: H, r: DIMS[d.key].d * s / 2 };
    }
    const c1 = byKey(DATA.colours, S.colour), c2 = byKey(DATA.colours, S.colour2), sp = byKey(DATA.twoTone.splits, S.split);
    mat.uniforms.uC1.value.copy(hex3(c1.hex)); mat.uniforms.uC2.value.copy(hex3(c2.hex)); mat.uniforms.uSplit.value = S.two ? sp.at : 2;
    [baseMesh, cableMesh, canopyMesh].forEach(m => group.remove(m));
    const { h: Hh, r } = group.userData;
    if (isPendant()) {
      const cab = byKey(DATA.cables, S.cable), can = byKey(DATA.canopies, S.canopy), len = 520;
      cableMesh.material.color.set(cab.hex); cableMesh.scale.set(1, len, 1); cableMesh.position.y = Hh + len / 2; group.add(cableMesh);
      canopyMesh.material.color.set(can.hex); canopyMesh.position.y = Hh + len + 11; group.add(canopyMesh);
      mat.uniforms.uLight.value.set(0, F.flip ? Hh * 0.62 : Hh * 0.45, 0);
    } else {
      const b = byKey(DATA.bases, S.base); baseMesh.material.color.set(b.hex); baseMesh.scale.set(r * 0.78, 24, r * 0.78); baseMesh.position.y = -12; group.add(baseMesh);
      mat.uniforms.uLight.value.set(0, Hh * 0.45, 0);
    }
    frame();
  }

  function frame() {
    if (!renderer) return;
    const w = view.clientWidth, h = view.clientHeight; if (!w || !h) return;
    renderer.setPixelRatio(Math.min(2, window.devicePixelRatio || 1)); renderer.setSize(w, h, false);
    cam.aspect = w / h; cam.updateProjectionMatrix();
    const { h: H, r } = group.userData; const pend = isPendant();
    const fitH = pend ? H + 300 : H + 50, mid = pend ? H * 0.5 + 140 : H / 2 - 12;
    const dist = Math.max(fitH * 1.25, r * 2.6 / cam.aspect) / (2 * Math.tan(THREE.MathUtils.degToRad(14)));
    cam.position.set(Math.sin(yaw) * Math.cos(pitch) * dist, mid + Math.sin(pitch) * dist, Math.cos(yaw) * Math.cos(pitch) * dist);
    cam.lookAt(0, mid, 0); renderer.render(scene, cam);
  }

  // drag to turn
  let drag = null;
  view.addEventListener('pointerdown', e => { if (e.target.closest('button')) return; drag = [e.clientX, e.clientY, yaw, pitch]; view.setPointerCapture(e.pointerId); });
  view.addEventListener('pointermove', e => { if (!drag) return; yaw = drag[2] - (e.clientX - drag[0]) * 0.008; pitch = clamp(drag[3] + (e.clientY - drag[1]) * 0.004, -0.2, 0.7); frame(); });
  view.addEventListener('pointerup', () => { drag = null; });
  new ResizeObserver(frame).observe(view);

  // ---------- UI
  function chips(name, items, cur, label, extra) {
    return items.map(it => `<label class="cfg-chip${extra ? ' ' + extra(it) : ''}"><input type="radio" name="${name}" value="${it.key}"${it.key === cur ? ' checked' : ''}>${label(it)}</label>`).join('');
  }
  const swatch = it => `<span class="cfg-sw" style="--c:${it.hex}"></span><span>${it.name}</span>`;

  function render() {
    const d = design(), pend = isPendant();
    $('[data-step="design"]').innerHTML = DATA.designs.map(x => `<label class="cfg-card"><input type="radio" name="design" value="${x.key}"${x.key === S.design ? ' checked' : ''}>
      <span class="cfg-card-t">${x.title}</span><span class="cfg-card-k">${x.kind}</span><span class="cfg-card-p">ab ${money(Math.min(...x.sizes.map(s => s.price)))}</span></label>`).join('');
    $('[data-step="size"]').innerHTML = d.sizes.map(s => `<label class="cfg-chip cfg-size${s.available === false ? ' is-out' : ''}"><input type="radio" name="size" value="${s.code}"${s.code === S.size ? ' checked' : ''}${s.available === false ? ' disabled' : ''}>
      <b>${s.code}</b><span>${dimText(d.key, s.scale)}</span><span class="cfg-dim">${money(s.price)}</span></label>`).join('');
    $('[data-step="colour"]').innerHTML = chips('colour', DATA.colours, S.colour, swatch, () => 'cfg-swatch');
    $('[data-step="two"]').innerHTML = `<label class="cfg-check"><input type="checkbox" name="two"${S.two ? ' checked' : ''}> Zweifarbig <span class="cfg-dim">+ ${money(DATA.twoTone.price)}</span></label>` +
      (S.two ? `<div class="cfg-sub"><p class="cfg-hint">Zweite Farbe</p><div class="cfg-row">${chips('colour2', DATA.colours, S.colour2, swatch, () => 'cfg-swatch')}</div>
        <p class="cfg-hint">Farbwechsel bei</p><div class="cfg-row">${chips('split', DATA.twoTone.splits, S.split, it => it.name)}</div></div>` : '');
    $('[data-step="mount"]').innerHTML = pend
      ? `<p class="cfg-hint">Baldachin</p><div class="cfg-row">${chips('canopy', DATA.canopies, S.canopy, swatch, () => 'cfg-swatch')}</div>
         <p class="cfg-hint">Textilkabel</p><div class="cfg-row">${chips('cable', DATA.cables, S.cable, swatch, () => 'cfg-swatch')}</div>
         <p class="cfg-hint">Kabellänge</p><div class="cfg-row">${chips('length', DATA.lengths, S.length, it => it.name + (it.price ? ` <span class="cfg-dim">+ ${money(addonPrice(it.addon, it.price))}</span>` : ''))}</div>`
      : `<p class="cfg-hint">Sockel</p><div class="cfg-row">${chips('base', DATA.bases, S.base, it => swatch(it) + (it.price ? ` <span class="cfg-dim">+ ${money(addonPrice(it.addon, it.price))}</span>` : ''), () => 'cfg-swatch')}</div>
         <p class="cfg-hint">Textilkabel mit Schalter</p><div class="cfg-row">${chips('cable', DATA.cables, S.cable, swatch, () => 'cfg-swatch')}</div>`;
    $('[data-step="mount-title"]').textContent = pend ? 'Aufhängung' : 'Sockel und Kabel';
    $('[data-step="extras"]').innerHTML = `<label class="cfg-check"><input type="checkbox" name="dimmer"${S.dimmer ? ' checked' : ''}> Schnurdimmer <span class="cfg-dim">+ ${money(addonPrice('dimmer', DATA.dimmer.price))}</span></label>
      <label class="cfg-field"><span>Gravur ${pend ? 'im Baldachin' : 'unter dem Sockel'} <span class="cfg-dim">+ ${money(addonPrice('engraving', DATA.engraving.price))}</span></span>
      <input type="text" name="engrave" maxlength="${DATA.engraving.max}" value="${S.engrave.replace(/"/g, '&quot;')}" placeholder="z. B. Initialen oder Datum" autocomplete="off"></label>`;
    $('.cfg-title').textContent = d.title; $('.cfg-kind').textContent = d.kind + ' · ' + dimText(d.key, size().scale);
    $('.cfg-note').textContent = d.note;
    summary(); build(); writeHash();
  }

  function lines() {
    const d = design(), sz = size(), pend = isPendant(), out = [];
    out.push({ label: `${d.title} ${sz.code}, ${byKey(DATA.colours, S.colour).name}`, price: sz.price, id: sz.id });
    if (S.two) out.push({ label: `Zweifarbig: ${byKey(DATA.colours, S.colour2).name}, ${byKey(DATA.twoTone.splits, S.split).name}`, price: DATA.twoTone.price, addon: 'twotone' });
    if (!pend) { const b = byKey(DATA.bases, S.base); if (b.price) out.push({ label: b.name, price: addonPrice(b.addon, b.price), addon: b.addon }); }
    if (pend) { const l = byKey(DATA.lengths, S.length); if (l.price) out.push({ label: 'Kabel ' + l.name, price: addonPrice(l.addon, l.price), addon: l.addon }); }
    if (S.dimmer) out.push({ label: 'Schnurdimmer', price: addonPrice('dimmer', DATA.dimmer.price), addon: 'dimmer' });
    if (S.engrave.trim()) out.push({ label: `Gravur «${S.engrave.trim()}»`, price: addonPrice('engraving', DATA.engraving.price), addon: 'engraving' });
    return out;
  }

  function summary() {
    const L = lines(), total = L.reduce((a, l) => a + l.price, 0);
    $('.cfg-lines').innerHTML = L.map(l => `<li><span>${l.label.replace(/</g, '&lt;')}</span><span>${money(l.price)}</span></li>`).join('');
    $('.cfg-total').textContent = money(total);
    $('.cfg-total-mobile').textContent = money(total);
    $('.cfg-lead').textContent = DATA.lead;
  }

  function properties() {
    const d = design(), sz = size(), pend = isPendant(), p = { Farbe: byKey(DATA.colours, S.colour).name };
    if (S.two) { p['Zweite Farbe'] = byKey(DATA.colours, S.colour2).name; p['Farbwechsel'] = byKey(DATA.twoTone.splits, S.split).name; }
    if (pend) { p['Baldachin'] = byKey(DATA.canopies, S.canopy).name; p['Kabellänge'] = byKey(DATA.lengths, S.length).name; }
    else p['Sockel'] = byKey(DATA.bases, S.base).name;
    p['Kabel'] = byKey(DATA.cables, S.cable).name;
    if (S.dimmer) p['Dimmer'] = 'Ja';
    if (S.engrave.trim()) p['Gravur'] = S.engrave.trim();
    // for the workshop, hidden from the customer: how to print this shade
    p['_Druck'] = d.key === 'korb' ? `python3 korb.py --scale ${sz.scale} && python3 make_3mf.py out/korb/korb.gcode`
      : `python3 lampgen.py ${d.key} --scale ${sz.scale} --res fine` + (d.key === 'firn' ? ' --set r_rim=150' : '');
    p['_Konfiguration'] = location.href;
    return p;
  }

  async function addToCart(btn) {
    const L = lines(), msg = $('.cfg-msg');
    if (!shop || !L[0].id) { msg.textContent = shop ? 'Diese Grösse ist im Shop noch nicht angelegt.' : 'Vorschau: Im Shop legt dieser Knopf die Lampe mit allen Optionen in den Warenkorb, und der Link der Seite speichert deine Konfiguration.'; return; }
    const missing = L.filter(l => l.addon && !DATA.addons[l.addon]);
    if (missing.length) { msg.textContent = 'Eine Option ist im Shop noch nicht verknüpft: ' + missing.map(l => l.label).join(', '); return; }
    const ref = Math.random().toString(36).slice(2, 8).toUpperCase(), props = properties(); props['_Ref'] = ref;
    const items = [{ id: L[0].id, quantity: 1, properties: props }].concat(L.filter(l => l.addon).map(l => ({ id: DATA.addons[l.addon].id, quantity: 1, properties: { 'Für': `${design().title} ${size().code}`, '_Ref': ref } })));
    btn.disabled = true; msg.textContent = 'Wird in den Warenkorb gelegt …';
    try {
      const r = await fetch((window.Shopify && Shopify.routes ? Shopify.routes.root : '/') + 'cart/add.js', { method: 'POST', headers: { 'Content-Type': 'application/json', Accept: 'application/json' }, body: JSON.stringify({ items }) });
      if (!r.ok) throw new Error((await r.json()).description || r.status);
      location.href = (window.Shopify && Shopify.routes ? Shopify.routes.root : '/') + 'cart';
    } catch (e) { msg.textContent = 'Das hat nicht geklappt: ' + e.message; btn.disabled = false; }
  }

  root.addEventListener('change', e => {
    const t = e.target; if (!t.name || !KEYS.includes(t.name)) return;
    if (t.type === 'checkbox') S[t.name] = t.checked; else S[t.name] = t.value;
    if (t.name === 'design' && !design().sizes.find(s => s.code === S.size)) S.size = 'M';
    render();
    const again = root.querySelector(`[name="${t.name}"]${t.type === 'radio' ? `[value="${t.value}"]` : ''}`); if (again) again.focus({ preventScroll: true });
  });
  root.addEventListener('input', e => { if (e.target.name === 'engrave') { S.engrave = e.target.value; summary(); writeHash(); } });
  $('.cfg-light').addEventListener('click', e => { const on = mat.uniforms.uOn.value < 0.5; mat.uniforms.uOn.value = on ? 1 : 0; view.classList.toggle('is-day', !on);
    e.currentTarget.setAttribute('aria-pressed', String(on)); e.currentTarget.textContent = on ? 'Licht aus' : 'Licht an'; frame(); });
  root.querySelectorAll('.cfg-add').forEach(b => b.addEventListener('click', () => addToCart(b)));

  readHash(); render();
})();
