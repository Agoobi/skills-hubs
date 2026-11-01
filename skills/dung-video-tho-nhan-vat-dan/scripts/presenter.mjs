// Ráp nhân vật Open Peeps (CC0, Pablo Stanley; gói npm @opeepsfun/open-peeps MIT) thành SVG lúc build.
// Gói nằm trong node_modules của dự án video, nên phải chạy với cwd là thư mục dự án.
import fs from "node:fs";
import path from "node:path";
import { createRequire } from "node:module";
import { pathToFileURL } from "node:url";

const require = createRequire(path.join(process.cwd(), "package.json"));
const load = (name) => import(pathToFileURL(require.resolve(name)).href);
const React = (await load("react")).default;
const { renderToStaticMarkup } = (await load("react-dom/server")).default;
const ROOT = path.dirname(require.resolve("@opeepsfun/open-peeps/package.json"));
const BUILD = path.join(ROOT, "build");
const OUT = "#121826";

const MODS = new Map();
for (const dir of ["head", "face", "beard", "accessory", "body/standing", "body/effigy"]) {
  for (const f of fs.readdirSync(path.join(BUILD, dir)).filter((x) => x.endsWith(".js") && x !== "index.js")) {
    MODS.set(`${dir}/${f.slice(0, -3)}`, await import(pathToFileURL(path.join(BUILD, dir, f)).href));
  }
}
const part = (rel, props = {}) => {
  const m = MODS.get(rel);
  if (!m) throw new Error(`Không có phần nhân vật ${rel}`);
  return renderToStaticMarkup(React.createElement(m.default, props));
};

// Độ lệch kiểu tóc lấy thẳng từ Effigy.js của gói, để tóc ôm đúng đầu.
const HAIR_ADJ = {};
const effigy = fs.readFileSync(path.join(BUILD, "Effigy.js"), "utf8");
for (const m of effigy.matchAll(/head\.type === "(\w+)"\)\s*{\s*return React\.createElement\("g", { transform: 'translate\(([-\d.]+) ([-\d.]+)\)' }/g)) HAIR_ADJ[m[1]] = [+m[2], +m[3]];

const NECK_EFFIGY = { x: 579, y: 757 };
const NECKS = JSON.parse(fs.readFileSync(new URL("./peeps-necks.json", import.meta.url), "utf8"));

// Miệng ngậm, miệng mở, chớp mắt. Ba nét này có mắt gần giống nhau nên đổi qua lại không bị giật.
export const FACES = { closed: "Smile", open: "Explaining", blink: "Calm" };

function head({ hair, skin, hairColor, beard, accessory }, cls) {
  const adj = HAIR_ADJ[hair] || [0, 0];
  let g = `<g transform="translate(${342 + adj[0]} ${190 + adj[1]})">${part("head/" + hair, { skinColor: skin, hairColor, outlineColor: OUT })}</g>`;
  Object.values(FACES).forEach((f, i) => {
    g += `<g class="${cls}-f-${f}"${i ? ' opacity="0"' : ""}><g transform="translate(531 366)">${part("face/" + f, { outlineColor: OUT })}</g></g>`;
  });
  if (beard) g += `<g transform="translate(495 518)">${part("beard/" + beard, { hairColor, outlineColor: OUT })}</g>`;
  if (accessory) g += `<g transform="translate(419 421)">${part("accessory/" + accessory, { outlineColor: OUT })}</g>`;
  return g;
}

// Tư thế đứng: cùng một khung để chân luôn chạm đất ở cùng chỗ.
export const STAND = { x: 0, y: -720, w: 1645, h: 3250 };
// Dùng họ ColorPants vì tư thế chỉ tay không có bản đổi màu áo: áo cố định theo nét, quần theo màu nhân vật.
export const POSES = { explain: "ShirtColorPants", point: "PointingFingerColorPants", calm: "RestingColorPants", think: "CrossArmColorPants" };

export function standing(pose, who, cls) {
  const name = POSES[pose] || POSES.explain;
  const body = part("body/standing/" + name, {
    skinColor: who.skin, outlineColor: OUT, pantsColor: who.pants, shoesColor: "#FFFFFF",
  });
  const k = 1.2;
  const nk = NECKS[name];
  if (!nk) throw new Error(`Chưa dò cổ cho tư thế ${name}`);
  const tx = nk.x - NECK_EFFIGY.x * k, ty = nk.y + 120 - NECK_EFFIGY.y * k;
  return `${body}<g transform="translate(${tx.toFixed(1)} ${ty.toFixed(1)}) scale(${k})">${head(who, cls)}</g>`;
}

export const BUST = { x: 285, y: 175, w: 600, h: 600 };

export function bust(who, cls) {
  const b = part("body/effigy/Explaining", { skinColor: who.skin, outlineColor: OUT, topColor: who.top });
  return `<g transform="translate(147 639)">${b}</g><g transform="translate(0 30)">${head(who, cls)}</g>`;
}
