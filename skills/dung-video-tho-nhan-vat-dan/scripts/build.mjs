// Sinh dự án HyperFrames từ plan.json + timeline.json: mỗi nhịp một composition, index.html giữ âm thanh.
// Chạy trong thư mục dự án video, sau `raw.py cut`: node <skill>/scripts/build.mjs
import fs from "node:fs";
import path from "node:path";
import { createRequire } from "node:module";
import { FACES, STAND, BUST, standing, bust } from "./presenter.mjs";

const read = (p) => JSON.parse(fs.readFileSync(p, "utf8"));
const project = read("project.json");
const plan = read("plan.json");
const timeline = read("timeline.json");
const src = project.source;
const PORTRAIT = project.format === "9:16";
const [W, H] = PORTRAIT ? [1080, 1920] : [1920, 1080];
const THEME = { accent: "#2563FF", bg: "#F4F6FB", ink: "#121826", ...project.theme };
const WHO = { hair: "ShortFour", skin: "#F1C7A0", hairColor: "#2A2320", top: "#121826", pants: "#FF5C7A", ...project.presenter };
const LABEL_PAUSE = plan.labels?.pause || "Tạm dừng";
const LABEL_FAST = plan.labels?.fast || "Tua nhanh";

const n = (v) => Math.round(v * 1000) / 1000;
const clamp = (v, a, b) => Math.min(b, Math.max(a, v));
const esc = (s) => String(s).replace(/&/g, "&amp;").replace(/</g, "&lt;").replace(/>/g, "&gt;").replace(/"/g, "&quot;");
const css = (o) => Object.entries(o).map(([k, v]) => `${k.replace(/[A-Z]/g, (c) => "-" + c.toLowerCase())}:${typeof v === "number" ? n(v) + "px" : v}`).join(";");
const box = ({ x, y, w, h }) => css({ left: x, top: y, width: w, height: h });
const SAMPLE = plan.labels?.sample ? `<div class="sample">${esc(plan.labels.sample)}</div>` : "";

// ---------- Bố cục ----------
const ASPECT = src.width / src.height;
function restStage() {
  let w = W, h = W / ASPECT;
  if (h > H) { h = H; w = H * ASPECT; }
  const y = h >= H ? 0 : PORTRAIT ? Math.max(0, H * 0.4 - h / 2) : (H - h) / 2;
  return { x: (W - w) / 2, y, w, h };
}
const REST = restStage();

// Lúc dừng hình: video thu nhỏ nhường chỗ, nhân vật đứng vào phần trống và không che nội dung.
function pauseLayout(side) {
  if (PORTRAIT) {
    const s = Math.min(1, (H * 0.5) / REST.h, (W - 80) / REST.w);
    const stage = { x: (W - REST.w * s) / 2, y: 90, s };
    return { stage, feet: { x: W / 2, y: H - 30 }, height: H - (90 + REST.h * s) - 150, capY: 90 + REST.h * s + 30 };
  }
  const s = 0.7, margin = 56;
  const sw = REST.w * s;
  const x = side === "left" ? W - margin - sw : margin;
  const free = side === "left" ? [0, x] : [x + sw, W];
  return { stage: { x, y: (H - REST.h * s) / 2, s }, feet: { x: (free[0] + free[1]) / 2, y: H - 34 }, height: H * 0.84, capY: H - 104 };
}

const stageBox = (r, p) => ({ x: p.x, y: p.y, w: r.w * p.s, h: r.h * p.s });

// ---------- Nhân vật ----------
const FEET_Y = 2520;
const STAND_CX = 750 / STAND.w;
const STAND_ASPECT = STAND.w / STAND.h;

// Tư thế gốc chỉ tay sang phải người xem. Đứng bên phải thì lật để chỉ vào video.
function presenterStand(id, { pose, side, feet, height }) {
  const w = height * STAND_ASPECT;
  const flip = side !== "left";
  const left = feet.x - w * (flip ? 1 - STAND_CX : STAND_CX);
  const top = feet.y - height * ((FEET_Y - STAND.y) / STAND.h);
  return {
    html: `<div class="pres" id="${id}-pres" data-layout-allow-overflow style="${css({ left, top, width: w, height })}"><div class="pres-body" id="${id}-body"><div class="fill" style="${flip ? "transform:scaleX(-1)" : ""}"><svg viewBox="${STAND.x} ${STAND.y} ${STAND.w} ${STAND.h}" width="${n(w)}" height="${n(height)}">${standing(pose, WHO, id)}</svg></div></div></div>`,
    left, top, w, flip,
  };
}

function presenterCorner(id, side) {
  const size = PORTRAIT ? 230 : 210;
  const m = PORTRAIT ? 40 : 44;
  const left = side === "left" ? m : W - m - size;
  const top = PORTRAIT ? REST.y + REST.h + 30 : H - m - size;
  return `<div class="corner" id="${id}-pres" style="${css({ left, top, width: size, height: size })}"><div class="corner-in" id="${id}-body" data-layout-allow-overflow style="background:${THEME.accent}"><svg viewBox="${BUST.x} ${BUST.y} ${BUST.w} ${BUST.h}" width="${size}" height="${size}">${bust(WHO, id)}</svg></div></div>`;
}

// Hai khung miệng theo độ to của giọng, kèm chớp mắt: đủ để nhân vật "nói" mà không tốn phí tạo video.
function mouthTweens(id, mouthPath, start, span) {
  const out = [];
  const show = (face, t) => out.push(`tl.set(".${id}-f-${face}",{opacity:1},${n(t)});`);
  const hide = (face, t) => out.push(`tl.set(".${id}-f-${face}",{opacity:0},${n(t)});`);
  const { rate, levels } = read(mouthPath);
  const blinkEvery = Math.round(rate * 3.4);
  let state = FACES.closed, run = 0;
  const frames = Math.min(levels.length, Math.ceil(span * rate));
  for (let i = 0; i < frames; i++) {
    let want = levels[i] > 28 ? FACES.open : FACES.closed;
    run = want === FACES.open ? run + 1 : 0;
    if (run > 5) { want = FACES.closed; run = 0; } // tiếng đều không làm miệng há cứng
    if (want === FACES.closed && i % blinkEvery < 2) want = FACES.blink;
    if (want !== state) {
      const t = start + i / rate;
      hide(state, t);
      show(want, t);
      state = want;
    }
  }
  if (state !== FACES.closed) { hide(state, start + frames / rate); show(FACES.closed, start + frames / rate); }
  return out.join("");
}

const breathe = (id, t, d) => {
  const cycle = 1.5;
  const count = Math.max(1, Math.floor(d / cycle) - 1);
  return `tl.to("#${id}-body",{scaleY:1.014,rotation:0.7,duration:${cycle},ease:"sine.inOut",repeat:${count},yoyo:true},${n(t)});`;
};

// ---------- Thời điểm ----------
function when(o, beat, info) {
  if (o.at != null) return +o.at;
  const speech = beat.vo || beat.say || "";
  const span = info.voice_len || info.duration;
  if (o.on) {
    const i = speech.toLowerCase().indexOf(String(o.on).toLowerCase());
    if (i < 0) throw new Error(`${beat.id}: không thấy cụm "${o.on}" trong lời đọc`);
    return info.vo_start + (span * i) / speech.length;
  }
  return info.vo_start;
}

function zoomTarget(rect, stage) {
  const [rx, ry, rw, rh] = rect.map((v) => v / 100);
  const s = clamp(Math.min(1 / rw, 1 / rh) * 0.86, 1.15, 2.6);
  return {
    x: clamp(stage.w * (0.5 - (rx + rw / 2) * s), stage.w * (1 - s), 0),
    y: clamp(stage.h * (0.5 - (ry + rh / 2) * s), stage.h * (1 - s), 0),
    s,
  };
}

// ---------- Âm thanh rời ----------
const sfxEvents = [];

// ---------- Chữ dưới video ----------
const LINE_MAX = PORTRAIT ? 32 : 44;
function captionChunks(text) {
  const out = [];
  let line = "";
  for (const word of text.trim().split(/\s+/)) {
    line = line ? `${line} ${word}` : word;
    if (line.length >= LINE_MAX || (line.length >= LINE_MAX / 2 && /[.!?,;:…]$/.test(word))) { out.push(line); line = ""; }
  }
  if (line && line.length < 14 && out.length) out[out.length - 1] += ` ${line}`;
  else if (line) out.push(line);
  return out;
}

function captions(id, beat, info, y) {
  const text = beat.vo || beat.say;
  if (!text || plan.captions === false || beat.captions === false) return "";
  const span = info.voice_len || info.duration - info.vo_start;
  const chunks = captionChunks(text);
  const total = chunks.reduce((a, c) => a + c.length, 0);
  let t = info.vo_start, html = "";
  chunks.forEach((c, i) => {
    const d = (span * c.length) / total;
    html += `<div class="clip cap" id="${id}-cap${i}" data-start="${n(t)}" data-duration="${n(d)}" style="top:${n(y)}px"><span>${esc(c)}</span></div>`;
    t += d;
  });
  return html;
}

// ---------- Lớp minh hoạ ----------
function highlightHTML(id, o, t, d, scale, stage) {
  const [x, y, w, h] = o.rect;
  const below = y + h < 78;
  const size = n(30 / scale);
  const anchor = x + w / 2 > 60 ? "right:0" : "left:0"; // nhãn nằm trong khung video, không tràn mép
  const label = o.label ? `<div class="hl-label" style="${anchor};${below ? "top:100%;margin-top:" + n(14 / scale) : "bottom:100%;margin-bottom:" + n(14 / scale)}px;font-size:${size}px;padding:${n(10 / scale)}px ${n(20 / scale)}px;border-radius:${n(14 / scale)}px">${esc(o.label)}</div>` : "";
  return `<div class="clip hl" id="${id}" data-start="${n(t)}" data-duration="${n(d)}" style="left:${x}%;top:${y}%;width:${w}%;height:${h}%"><div class="hl-in" id="${id}-in" style="border-width:${n(6 / scale)}px;border-radius:${n(14 / scale)}px">${label}</div></div>`;
}

const REGION_ALIGN = {
  center: ["center", "center"], left: ["center", "flex-start"], right: ["center", "flex-end"],
  top: ["flex-start", "center"], bottom: ["flex-end", "center"],
  "top-left": ["flex-start", "flex-start"], "top-right": ["flex-start", "flex-end"],
  "bottom-left": ["flex-end", "flex-start"], "bottom-right": ["flex-end", "flex-end"],
};

function imageHTML(id, o, t, d, region) {
  const file = o.file;
  if (!fs.existsSync(file)) throw new Error(`${id}: không thấy ảnh ${file}`);
  const [ai, jc] = REGION_ALIGN[o.pos || "center"] || REGION_ALIGN.center;
  const width = n((W * (o.w || 40)) / 100);
  const cap = o.caption ? `<div class="ov-cap">${esc(o.caption)}</div>` : "";
  return `<div class="clip ov" id="${id}" data-start="${n(t)}" data-duration="${n(d)}" style="${box(region)};align-items:${ai};justify-content:${jc}"><div class="ov-card" id="${id}-in" style="width:${width}px"><img id="${id}-img" src="${esc(file)}" alt="">${cap}</div></div>`;
}

const popIn = (sel, t) => `tl.fromTo("${sel}",{opacity:0,scale:0.86,y:24},{opacity:1,scale:1,y:0,duration:0.45,ease:"back.out(1.7)"},${n(t)});`;
const popOut = (sel, t) => `tl.to("${sel}",{opacity:0,y:12,duration:0.25,ease:"power2.in"},${n(t)});`;

// Zoom, khung chỉ và ảnh dùng chung cho nhịp chạy và nhịp dừng.
function effects(beat, info, stage, stageScale, base, frameRegion, endAt, pointFrom) {
  let inCam = "", over = "", js = "";
  const id = beat.id, global = info.start;
  const fx = beat.fx || [];
  const zooms = fx.filter((f) => f.kind === "zoom").map((f) => ({ ...f, t: when(f, beat, info) }));
  const scaleAt = (t) => {
    const z = zooms.find((f) => t >= f.t && t <= f.t + (f.hold ?? 1e9));
    return (z ? zoomTarget(z.rect, stage).s : 1) * stageScale;
  };
  zooms.forEach((z, i) => {
    const target = zoomTarget(z.rect, stage);
    const start = Math.max(base, z.t - 0.35);
    const out = Math.min(z.hold != null ? z.t + z.hold : Infinity, endAt - 0.72);
    js += `tl.to("#${id}-cam",{x:${n(target.x)},y:${n(target.y)},scale:${n(target.s)},duration:0.7,ease:"power2.inOut"},${n(start)});`;
    js += `tl.to("#${id}-cam",{x:0,y:0,scale:1,duration:0.65,ease:"power2.inOut"},${n(out)});`;
    sfxEvents.push({ t: global + start, k: "whoosh", v: 0.14 });
    const next = zooms[i + 1];
    if (next && next.t - 0.35 < out + 0.65) throw new Error(`${id}: hai zoom chồng nhau, thêm hold cho zoom trước`);
  });
  fx.forEach((f, i) => {
    if (f.kind === "zoom") return;
    const key = `${id}-fx${i}`;
    const t = Math.max(base, when(f, beat, info));
    const d = Math.max(0.8, Math.min(f.hold ?? endAt - t, endAt - t));
    if (f.kind === "highlight") {
      inCam += highlightHTML(key, f, t, d, scaleAt(t + 0.4), stage);
      js += `tl.fromTo("#${key}-in",{opacity:0,scale:1.05},{opacity:1,scale:1,duration:0.35,ease:"power3.out"},${n(t)});` + popOut(`#${key}-in`, t + d - 0.3);
      sfxEvents.push({ t: global + t, k: "tick", v: 0.3 });
      if (f.point) {
        if (zooms.length) throw new Error(`${id}: không dùng point cùng zoom trong một nhịp`);
        if (!pointFrom) throw new Error(`${id}: point chỉ dùng ở nhịp dừng hoặc khi có nhân vật đứng`);
        const [x, y, w, h] = f.rect.map((v) => v / 100);
        const s = pointFrom.stage;
        const onLeft = pointFrom.x < s.x + s.w * (x + w / 2);
        const tx = s.x + s.w * (onLeft ? x : x + w), ty = s.y + s.h * (y + h / 2);
        const mx = (pointFrom.x + tx) / 2, my = Math.min(pointFrom.y, ty) - 70;
        over += `<svg class="clip ptr" id="${key}-p" data-start="${n(t)}" data-duration="${n(d)}" width="${W}" height="${H}" viewBox="0 0 ${W} ${H}"><path id="${key}-l" pathLength="1" d="M${n(pointFrom.x)} ${n(pointFrom.y)} Q${n(mx)} ${n(my)} ${n(tx)} ${n(ty)}" fill="none" stroke="${THEME.accent}" stroke-width="6" stroke-dasharray="1" stroke-dashoffset="1"/></svg>`;
        js += `tl.to("#${key}-l",{strokeDashoffset:0,duration:0.4,ease:"power2.out"},${n(t + 0.05)});` + popOut(`#${key}-l`, t + d - 0.3);
      }
    } else if (f.kind === "image") {
      over += imageHTML(key, f, t, d, frameRegion);
      js += popIn(`#${key}-in`, t) + popOut(`#${key}-in`, t + d - 0.3);
      sfxEvents.push({ t: global + t, k: "pop", v: 0.3 });
    } else {
      throw new Error(`${id}: không có hiệu ứng ${f.kind}`);
    }
  });
  return { inCam, over, js };
}

// ---------- Nhịp ----------
function mediaHTML(id, beat, info) {
  if (info.clip) return `<video class="clip media" id="${id}-v" src="${info.clip}" data-start="0" data-duration="${info.duration}" muted playsinline></video>`;
  return `<img class="clip media" id="${id}-v" src="${info.still}" data-start="0" data-duration="${info.duration}" alt="">`;
}

function playBeat(beat, info) {
  const id = beat.id, D = info.duration;
  const fx = effects(beat, info, REST, 1, 0, REST, D, null);
  let html = "", js = fx.js;
  if (beat.presenter) {
    const side = beat.presenter.side || "right";
    html += presenterCorner(id, side);
    js += `tl.fromTo("#${id}-body",{scale:0.4,opacity:0},{scale:1,opacity:1,duration:0.4,ease:"back.out(1.8)"},0.05);`;
    js += `tl.to("#${id}-body",{scale:0.4,opacity:0,duration:0.25,ease:"power2.in"},${n(D - 0.32)});`;
    if (info.mouth) js += mouthTweens(id, info.mouth, info.vo_start, D - info.vo_start);
  }
  if (info.speed >= timeline.badge_from) {
    html += `<div class="pill" id="${id}-fast" style="${css({ left: REST.x + REST.w - 330, top: REST.y + 28, width: 302 })}">${esc(LABEL_FAST)} x${Math.round(info.speed * 10) / 10}</div>`;
  }
  const capY = PORTRAIT ? REST.y + REST.h + 24 : H - 104;
  html += fx.over + captions(id, beat, info, capY);
  return { body: `<div class="stage" id="${id}-stage" data-layout-allow-overflow style="${box(REST)}"><div class="cam" id="${id}-cam">${mediaHTML(id, beat, info)}${fx.inCam}</div>${SAMPLE}</div>${html}`, js };
}

function pauseBeat(beat, info) {
  const id = beat.id, D = info.duration, side = beat.presenter?.side || "right";
  const layout = pauseLayout(side);
  const p = layout.stage;
  const inner = stageBox(REST, p);
  const pose = beat.presenter?.pose || ((beat.fx || []).some((f) => f.point) ? "point" : "explain");
  const pres = presenterStand(id, { pose, side, feet: layout.feet, height: layout.height });
  const hand = { x: pres.left + pres.w * (pres.flip ? 0.08 : 0.92), y: pres.top + layout.height * 0.29, stage: inner };
  const endAt = D - 0.72;
  const fx = effects(beat, info, REST, p.s, 0.65, inner, endAt, hand);
  const offX = side === "left" ? -pres.w - 40 : W - pres.left + 40;
  const dx = PORTRAIT ? 0 : offX, dy = PORTRAIT ? H - pres.top : 0;
  const exit = D - 0.66;
  let js = "";
  js += `tl.to("#${id}-stage",{x:${n(p.x - REST.x)},y:${n(p.y - REST.y)},scale:${n(p.s)},borderRadius:${n(22 / p.s)},duration:0.6,ease:"power3.inOut"},0.04);`;
  js += `tl.fromTo("#${id}-pres",{x:${n(dx)},y:${n(dy)}},{x:0,y:0,duration:0.55,ease:"power3.out"},0.18);`;
  js += breathe(id, 0.7, D - 1.5);
  js += `tl.fromTo("#${id}-paused",{opacity:0,y:-10},{opacity:1,y:0,duration:0.3,ease:"power2.out"},0.5);`;
  js += `tl.to("#${id}-paused",{opacity:0,duration:0.2},${n(exit - 0.22)});`;
  js += `tl.to("#${id}-pres",{x:${n(dx)},y:${n(dy)},duration:0.42,ease:"power2.in"},${n(exit - 0.08)});`;
  js += `tl.to("#${id}-stage",{x:0,y:0,scale:1,borderRadius:0,duration:0.55,ease:"power3.inOut"},${n(exit)});`;
  if (info.mouth) js += mouthTweens(id, info.mouth, info.vo_start, info.voice_len);
  js += fx.js;
  sfxEvents.push({ t: info.start + 0.04, k: "whoosh", v: 0.18 });
  const pausePill = `<div class="pill" id="${id}-paused" style="${css({ left: inner.x + 22, top: inner.y + 22, width: 226 })}"><i></i><i></i>${esc(LABEL_PAUSE)}</div>`;
  return {
    body: `<div class="stage" id="${id}-stage" data-layout-allow-overflow style="${box(REST)}"><div class="cam" id="${id}-cam">${mediaHTML(id, beat, info)}${fx.inCam}</div>${SAMPLE}</div>${pres.html}${pausePill}${fx.over}${captions(id, beat, info, layout.capY)}`,
    js,
  };
}

function cutawayBeat(beat, info) {
  const id = beat.id, D = info.duration, side = beat.presenter?.side || "right";
  const items = beat.points || [];
  const pres = beat.presenter === false ? null
    : presenterStand(id, { pose: beat.presenter?.pose || "explain", side, feet: PORTRAIT ? { x: W / 2, y: H - 30 } : { x: side === "left" ? 300 : W - 300, y: H - 34 }, height: PORTRAIT ? H * 0.42 : H * 0.84 });
  const area = PORTRAIT ? { x: 70, y: 150, w: W - 140, h: H * 0.5 }
    : pres ? { x: side === "left" ? 620 : 100, y: 110, w: W - 720, h: H - 220 } : { x: 160, y: 110, w: W - 320, h: H - 220 };
  let js = info.start === 0 ? "" : popIn(`#${id}-title`, 0.15); // khung đầu là ảnh xem trước, chữ phải có sẵn
  if (pres) {
    if (info.start !== 0) js += `tl.fromTo("#${id}-pres",{y:${n(H - pres.top)}},{y:0,duration:0.5,ease:"power3.out"},0.05);`;
    js += breathe(id, 0.6, D - 1);
    if (info.mouth) js += mouthTweens(id, info.mouth, info.vo_start, info.voice_len);
  }
  let list = "";
  items.forEach((p, i) => {
    const o = typeof p === "string" ? { text: p } : p;
    const t = o.on || o.at != null ? when(o, beat, info) : info.vo_start + ((info.voice_len || D) * (i + 0.15)) / items.length;
    list += `<li id="${id}-pt${i}">${esc(o.text)}</li>`;
    js += `tl.fromTo("#${id}-pt${i}",{opacity:0,x:-24},{opacity:1,x:0,duration:0.4,ease:"power3.out"},${n(t)});`;
    sfxEvents.push({ t: info.start + t, k: "tick", v: 0.25 });
  });
  let img = "";
  if (beat.image) {
    if (!fs.existsSync(beat.image)) throw new Error(`${id}: không thấy ảnh ${beat.image}`);
    img = `<img class="cut-img" id="${id}-img" src="${esc(beat.image)}" alt="">`;
    js += popIn(`#${id}-img`, 0.45);
  }
  const paced = (i, count, share) => info.vo_start + ((info.voice_len || D) * share * i) / count;
  let extra = "";
  if (beat.flow) {
    const focus = beat.focus?.nodes;
    extra += `<div class="flow">${beat.flow.map((t, i) => `<div class="node" id="${id}-n${i}"><b>${i + 1}</b><span>${esc(t)}</span></div>`).join("")}</div>`;
    beat.flow.forEach((_, i) => {
      const t = focus ? 0.2 + i * 0.06 : paced(i, beat.flow.length, 0.78);
      js += popIn(`#${id}-n${i}`, t);
      if (!focus) sfxEvents.push({ t: info.start + t, k: "tick", v: 0.25 });
    });
    if (focus) {
      const t = when(beat.focus, beat, info);
      beat.flow.forEach((_, i) => {
        js += focus.includes(i) ? `tl.to("#${id}-n${i}",{scale:1.02,backgroundColor:"${THEME.accent}",color:"#fff",duration:0.35,ease:"power2.out"},${n(t)});` : `tl.to("#${id}-n${i}",{opacity:0.32,duration:0.35},${n(t)});`;
      });
      sfxEvents.push({ t: info.start + t, k: "pop", v: 0.3 });
    }
  }
  if (beat.big) {
    extra += `<div class="big">${beat.big.map((o, i) => `<div id="${id}-b${i}">${esc(o.text)}</div>`).join("")}</div>`;
    beat.big.forEach((o, i) => {
      const t = when(o, beat, info);
      js += popIn(`#${id}-b${i}`, t);
      sfxEvents.push({ t: info.start + t, k: "pop", v: 0.3 });
    });
  }
  if (beat.compare) {
    const card = (c, key) => `<div class="cmp-card" id="${id}-${key}"><b>${esc(c.title)}</b><ul>${c.items.map((x) => `<li>${esc(x)}</li>`).join("")}</ul></div>`;
    extra += `<div class="cmp">${card(beat.compare.before, "before")}${card(beat.compare.after, "after")}</div>`;
    js += popIn(`#${id}-before`, when(beat.compare.before, beat, info)) + popIn(`#${id}-after`, when(beat.compare.after, beat, info));
    sfxEvents.push({ t: info.start + when(beat.compare.after, beat, info), k: "pop", v: 0.3 });
  }
  if (beat.note) {
    extra += `<div class="cut-note" id="${id}-note">${esc(beat.note)}</div>`;
    js += popIn(`#${id}-note`, D * 0.55);
  }
  const body = `<div class="cut" style="${box(area)}"><div class="cut-title" id="${id}-title">${esc(beat.title || "")}</div>${list ? `<ul class="cut-list">${list}</ul>` : ""}${extra}${img}</div>${pres ? pres.html : ""}${captions(id, beat, info, PORTRAIT ? H * 0.53 : H - 104)}`;
  return { body, js };
}

function chapterBeat(beat, info) {
  const id = beat.id;
  sfxEvents.push({ t: info.start + 0.05, k: "chime", v: 0.16 });
  return {
    bg: THEME.accent,
    body: `<div class="chap"><div class="chap-k" id="${id}-k">${esc(beat.kicker || "")}</div><div class="chap-t" id="${id}-t">${esc(beat.title || "")}</div></div>`,
    js: info.start === 0 ? "" : popIn(`#${id}-k`, 0.05) + popIn(`#${id}-t`, 0.14), // khung đầu là ảnh xem trước, chữ phải có sẵn
  };
}

const BUILDERS = { play: playBeat, pause: pauseBeat, cutaway: cutawayBeat, chapter: chapterBeat };

// ---------- Chữ và CSS chung ----------
function fontCss() {
  const require = createRequire(path.join(process.cwd(), "package.json"));
  const dir = path.dirname(require.resolve("@fontsource/be-vietnam-pro/package.json"));
  fs.mkdirSync("assets/fonts", { recursive: true });
  let out = "";
  for (const weight of [500, 700, 800]) {
    for (const subset of ["vietnamese", "latin"]) {
      const face = fs.readFileSync(path.join(dir, `${subset}-${weight}.css`), "utf8").match(/@font-face\s*{[^}]*}/)[0];
      const file = `be-vietnam-pro-${subset}-${weight}-normal.woff2`;
      fs.copyFileSync(path.join(dir, "files", file), `assets/fonts/${file}`);
      out += face.replace(/src:[^;]*;/, `src: url("assets/fonts/${file}") format("woff2");`).replace(/font-display:\s*\w+/, "font-display: block").replace(/\s*\n\s*/g, " ") + "\n";
    }
  }
  return out;
}
const FONT_CSS = fontCss();
fs.copyFileSync(path.join(path.dirname(createRequire(path.join(process.cwd(), "package.json")).resolve("gsap/package.json")), "dist/gsap.min.js"), "assets/gsap.min.js");

const SHARED = `
${FONT_CSS}
#root { position: absolute; inset: 0; overflow: hidden; font-family: "Be Vietnam Pro", sans-serif; color: ${THEME.ink}; }
.bg { position: absolute; inset: 0; }
.fill { position: absolute; inset: 0; }
.stage { position: absolute; overflow: hidden; transform-origin: 0 0; background: #000; box-shadow: 0 30px 80px rgba(15,20,36,.28); }
.cam { position: absolute; inset: 0; transform-origin: 0 0; }
.media { position: absolute; inset: 0; width: 100%; height: 100%; object-fit: contain; }
.hl { position: absolute; }
.hl-in { position: absolute; inset: 0; border-style: solid; border-color: ${THEME.accent}; box-shadow: 0 0 0 4000px rgba(10,14,30,.46); }
.hl-label { position: absolute; white-space: nowrap; background: ${THEME.accent}; color: #fff; font-weight: 700; }
.ptr { position: absolute; left: 0; top: 0; pointer-events: none; }
.ov { position: absolute; display: flex; padding: 40px; }
.ov-card { background: #fff; border-radius: 24px; padding: 14px; box-shadow: 0 24px 70px rgba(15,20,36,.32); }
.ov-card img { display: block; width: 100%; border-radius: 14px; }
.ov-cap { padding: 14px 8px 4px; font-size: 28px; font-weight: 700; text-align: center; }
.pres { position: absolute; }
.pres-body { position: absolute; inset: 0; transform-origin: 50% 92%; }
.corner { position: absolute; }
.corner-in { position: absolute; inset: 0; overflow: hidden; border-radius: 50%; border: 7px solid #fff; box-shadow: 0 16px 44px rgba(15,20,36,.34); }
.pill { position: absolute; height: 54px; display: flex; align-items: center; justify-content: center; gap: 7px; border-radius: 27px; background: rgba(15,20,36,.84); color: #fff; font-size: 28px; font-weight: 700; }
.pill i { display: block; width: 7px; height: 22px; border-radius: 2px; background: #fff; }
.pill i + i { margin-right: 8px; }
.cap { position: absolute; left: 0; right: 0; text-align: center; font-size: ${PORTRAIT ? 44 : 38}px; font-weight: 700; line-height: 1.25; }
.cap span { display: inline-block; max-width: ${W - 160}px; padding: 8px 24px; border-radius: 14px; background: rgba(15,20,36,.86); color: #fff; }
.cut { position: absolute; display: flex; flex-direction: column; justify-content: center; gap: 34px; }
.cut-title { font-size: ${PORTRAIT ? 76 : 72}px; line-height: 1.14; font-weight: 800; letter-spacing: -.02em; }
.cut-list { list-style: none; display: grid; gap: 20px; margin: 0; padding: 0; font-size: ${PORTRAIT ? 44 : 40}px; font-weight: 500; line-height: 1.3; }
.cut-list li { padding-left: 34px; border-left: 8px solid ${THEME.accent}; }
.cut-img { display: block; max-width: 100%; max-height: 52%; align-self: flex-start; border-radius: 22px; box-shadow: 0 24px 70px rgba(15,20,36,.24); }
.flow { display: grid; grid-template-columns: repeat(${PORTRAIT ? 2 : 3}, 1fr); gap: 18px; }
.node { display: flex; align-items: center; gap: 14px; min-height: 104px; padding: 16px 20px; border-radius: 18px; background: #fff; box-shadow: 0 10px 30px rgba(15,20,36,.08); font-size: 32px; font-weight: 700; line-height: 1.2; }
.node b { flex: none; display: flex; align-items: center; justify-content: center; width: 44px; height: 44px; border-radius: 50%; background: ${THEME.accent}; color: #fff; font-size: 28px; }
.big { display: flex; flex-wrap: wrap; align-items: center; gap: 22px; font-size: ${PORTRAIT ? 60 : 68}px; font-weight: 800; letter-spacing: -.02em; }
.big div:last-child { width: 100%; color: ${THEME.accent}; font-size: ${PORTRAIT ? 80 : 92}px; }
.cmp { display: grid; grid-template-columns: repeat(${PORTRAIT ? 1 : 2}, 1fr); gap: 22px; }
.cmp-card { padding: 28px 30px; border-radius: 22px; background: #fff; box-shadow: 0 10px 30px rgba(15,20,36,.08); }
.cmp-card:last-child { background: ${THEME.accent}; color: #fff; }
.cmp-card b { display: block; margin-bottom: 14px; font-size: 40px; font-weight: 800; }
.cmp-card ul { list-style: none; display: grid; gap: 12px; margin: 0; padding: 0; font-size: 32px; font-weight: 500; line-height: 1.3; }
.cut-note { font-size: 30px; font-weight: 500; opacity: .72; }
.sample { position: absolute; left: 22px; bottom: 22px; padding: 8px 18px; border-radius: 12px; background: rgba(15,20,36,.84); color: #fff; font-size: 28px; font-weight: 700; }
.chap { position: absolute; inset: 0; display: flex; flex-direction: column; align-items: center; justify-content: center; gap: 18px; padding: 0 120px; text-align: center; color: #fff; }
.chap-k { font-size: 34px; font-weight: 700; letter-spacing: .08em; opacity: .85; }
.chap-t { font-size: ${PORTRAIT ? 88 : 96}px; line-height: 1.12; font-weight: 800; letter-spacing: -.02em; }
`;

// ---------- Ghi file ----------
fs.rmSync("compositions", { recursive: true, force: true });
fs.mkdirSync("compositions", { recursive: true });
const beatsById = new Map(plan.beats.map((b) => [b.id, b]));
let hosts = "", audio = "";

for (const info of timeline.beats) {
  const beat = beatsById.get(info.id);
  if (!beat) throw new Error(`timeline.json lệch plan.json ở ${info.id}, chạy lại raw.py cut`);
  const { body, js, bg } = BUILDERS[info.type](beat, info);
  fs.writeFileSync(`compositions/${info.id}.html`, `<template>
  <style>${SHARED}</style>
  <div id="root" data-composition-id="${info.id}" data-width="${W}" data-height="${H}">
    <div class="bg" id="${info.id}-bg" style="background:${bg || THEME.bg}"></div>
    ${body}
  </div>
  <script>
    const tl = gsap.timeline({ paused: true });
    ${js}
    window.__timelines["${info.id}"] = tl;
  </script>
</template>
`);
  hosts += `      <div id="${info.id}" data-composition-id="${info.id}" data-composition-src="compositions/${info.id}.html" data-start="${info.start}" data-duration="${info.duration}" data-track-index="1" data-track-kind="graphics" data-width="${W}" data-height="${H}"></div>\n`;
  if (info.voice) audio += `      <audio id="vo-${info.id}" class="clip" src="${info.voice}" data-start="${n(info.start + info.vo_start)}" data-duration="${info.voice_len}" data-volume="1" data-track-index="3"></audio>\n`;
  if (info.raw_audio) audio += `      <audio id="raw-${info.id}" class="clip" src="${info.raw_audio}" data-start="${info.start}" data-duration="${info.duration}" data-volume="${info.raw_volume}" data-track-index="4"></audio>\n`;
}

const SFX_LEN = { whoosh: 0.42, pop: 0.11, tick: 0.035, chime: 0.5 };
sfxEvents.sort((a, b) => a.t - b.t).forEach((e, i) => {
  audio += `      <audio id="sfx-${i}" class="clip" src="assets/sfx/${e.k}.wav" data-start="${n(e.t)}" data-duration="${SFX_LEN[e.k]}" data-volume="${e.v}" data-track-index="5"></audio>\n`;
});
if (plan.music) audio += `      <audio id="music" class="clip" src="assets/audio/music.wav" data-start="0" data-duration="${timeline.duration}" data-volume="${plan.music.volume ?? 0.08}" data-track-index="6"></audio>\n`;

fs.writeFileSync("index.html", `<!doctype html>
<html lang="vi">
  <head>
    <meta charset="UTF-8" />
    <meta name="viewport" content="width=${W}, height=${H}" />
    <script src="assets/gsap.min.js"></script>
    <style>
      * { margin: 0; padding: 0; box-sizing: border-box; }
      html, body { width: ${W}px; height: ${H}px; overflow: hidden; background: ${THEME.bg}; }
      #root { position: relative; width: 100%; height: 100%; }
    </style>
  </head>
  <body>
    <div id="root" data-composition-id="main" data-start="0" data-duration="${timeline.duration}" data-width="${W}" data-height="${H}">
${hosts}${audio}    </div>
    <script>
      window.__timelines = window.__timelines || {};
      window.__timelines["main"] = gsap.timeline({ paused: true });
    </script>
  </body>
</html>
`);
console.log(JSON.stringify({ beats: timeline.beats.length, duration: timeline.duration, sfx: sfxEvents.length }));
