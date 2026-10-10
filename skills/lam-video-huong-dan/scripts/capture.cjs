#!/usr/bin/env node
/*
 * Record a real browser session for a tutorial video.
 *
 *   node capture.cjs --steps demo.steps.json --out captures --format long
 *   node capture.cjs --login --profile .profiles/site --url https://example.com
 *
 * Writes <name>.mp4 (or .webm when ffmpeg is missing), <name>.log.json with the
 * time and cursor position of every step, and any stills requested with "shot".
 * Needs the `playwright` package; set PLAYWRIGHT_MODULE to its folder if it is
 * not resolvable from the current directory.
 */
const fs = require("fs");
const path = require("path");
const { spawnSync } = require("child_process");

const FORMATS = { long: { width: 1920, height: 1080 }, short: { width: 1080, height: 1920 } };

function parseArgs(argv) {
  const args = {};
  for (let i = 0; i < argv.length; i++) {
    if (!argv[i].startsWith("--")) continue;
    const key = argv[i].slice(2);
    const next = argv[i + 1];
    if (next === undefined || next.startsWith("--")) args[key] = true;
    else { args[key] = next; i++; }
  }
  return args;
}

function fail(message) {
  console.error(`LỖI: ${message}`);
  process.exit(1);
}

function loadPlaywright() {
  const candidates = [process.env.PLAYWRIGHT_MODULE, "playwright", path.join(process.cwd(), "node_modules", "playwright")];
  for (const candidate of candidates.filter(Boolean)) {
    try { return require(candidate); } catch { /* try the next location */ }
  }
  fail("Không tìm thấy gói 'playwright'. Chạy `npm i -D playwright && npx playwright install chromium` trong dự án, hoặc đặt PLAYWRIGHT_MODULE.");
}

// A large pointer that follows the mouse, because the system cursor is not
// part of a Playwright recording. Drawn by the page, removed with the page.
const CURSOR_SCRIPT = `(() => {
  if (window.__captureCursor) return;
  const el = document.createElement("div");
  el.id = "__capture-cursor";
  el.innerHTML = '<svg width="44" height="44" viewBox="0 0 24 24"><path d="M5 3l14 8.2-6.1 1.6L16.4 20l-2.9 1.3-3.4-7.1L5 18.5z" fill="#fff" stroke="#111" stroke-width="1.3" stroke-linejoin="round"/></svg>';
  Object.assign(el.style, { position: "fixed", left: "0", top: "0", zIndex: "2147483647", pointerEvents: "none",
    transform: "translate(-200px,-200px)", filter: "drop-shadow(0 2px 4px rgba(0,0,0,.45))", willChange: "transform" });
  const ring = document.createElement("div");
  Object.assign(ring.style, { position: "fixed", left: "0", top: "0", width: "56px", height: "56px", margin: "-28px 0 0 -28px",
    borderRadius: "50%", border: "3px solid rgba(255,255,255,.9)", boxShadow: "0 0 0 1px rgba(0,0,0,.35)", zIndex: "2147483646",
    pointerEvents: "none", opacity: "0", transform: "translate(-200px,-200px) scale(.4)" });
  const mount = () => { document.documentElement.appendChild(ring); document.documentElement.appendChild(el); };
  if (document.documentElement) mount(); else document.addEventListener("DOMContentLoaded", mount);
  let x = -200, y = -200;
  window.addEventListener("mousemove", (e) => { x = e.clientX; y = e.clientY; el.style.transform = "translate(" + (x - 9) + "px," + (y - 5) + "px)"; }, true);
  window.addEventListener("mousedown", () => {
    ring.style.transition = "none"; ring.style.opacity = "1"; ring.style.transform = "translate(" + x + "px," + y + "px) scale(.4)";
    requestAnimationFrame(() => { ring.style.transition = "transform .45s ease-out, opacity .45s ease-out"; ring.style.opacity = "0"; ring.style.transform = "translate(" + x + "px," + y + "px) scale(1.25)"; });
  }, true);
  window.__captureCursor = true;
})();`;

async function login(playwright, args) {
  if (!args.profile || !args.url) fail("Chế độ --login cần --profile <thư mục> và --url <trang>.");
  const context = await playwright.chromium.launchPersistentContext(path.resolve(args.profile), { headless: false, viewport: null });
  const page = context.pages()[0] || (await context.newPage());
  await page.goto(args.url);
  console.log("Trình duyệt đã mở. Người dùng tự đăng nhập, xong thì đóng cửa sổ.");
  await new Promise((resolve) => context.on("close", resolve));
  console.log(JSON.stringify({ profile: path.resolve(args.profile), ready: true }));
}

async function record(playwright, args) {
  if (!args.steps) fail("Cần --steps <file.steps.json>.");
  const plan = JSON.parse(fs.readFileSync(args.steps, "utf8"));
  const format = FORMATS[args.format || plan.format || "long"];
  if (!format) fail("--format phải là long hoặc short.");
  const name = plan.name || path.basename(args.steps).replace(/\.steps\.json$|\.json$/, "");
  const outDir = path.resolve(args.out || path.dirname(args.steps));
  const rawDir = path.join(outDir, `.raw-${name}`);
  fs.mkdirSync(rawDir, { recursive: true });

  const contextOptions = {
    viewport: format,
    deviceScaleFactor: 1,
    recordVideo: { dir: rawDir, size: format },
    colorScheme: plan.colorScheme || "light",
    locale: plan.locale || "vi-VN",
    ...(args.format === "short" || plan.format === "short" ? { isMobile: true, hasTouch: false } : {}),
  };
  let browser = null;
  let context;
  if (args.profile) {
    context = await playwright.chromium.launchPersistentContext(path.resolve(args.profile), { headless: !args.headed, ...contextOptions });
  } else {
    browser = await playwright.chromium.launch({ headless: !args.headed });
    context = await browser.newContext(contextOptions);
  }
  await context.addInitScript(CURSOR_SCRIPT);
  const page = context.pages()[0] || (await context.newPage());
  const started = Date.now();
  const now = () => Math.round((Date.now() - started) / 10) / 100;
  const log = { name, format: args.format || plan.format || "long", ...format, steps: [], marks: [], shots: [] };
  let mouse = { x: format.width / 2, y: format.height / 2 };
  await page.mouse.move(mouse.x, mouse.y);
  // A new document starts with the pointer overlay parked off-screen; nudge it back into place.
  page.on("load", () => {
    page.mouse.move(mouse.x + 1, mouse.y).then(() => page.mouse.move(mouse.x, mouse.y)).catch(() => {});
  });

  const centerOf = async (selector) => {
    const locator = page.locator(selector).first();
    await locator.waitFor({ state: "visible", timeout: 20000 });
    await locator.scrollIntoViewIfNeeded();
    const box = await locator.boundingBox();
    if (!box) throw new Error(`Không thấy phần tử: ${selector}`);
    return { locator, box, x: box.x + box.width / 2, y: box.y + box.height / 2 };
  };
  const glide = async (x, y, ms = 650) => {
    const frames = Math.max(8, Math.round(ms / 16));
    await page.mouse.move(x, y, { steps: frames });
    mouse = { x, y };
  };

  try {
    if (plan.url) await page.goto(plan.url, { waitUntil: "domcontentloaded", timeout: 60000 });
    for (const [index, step] of (plan.steps || []).entries()) {
      const entry = { index, do: step.do, t: now() };
      switch (step.do) {
        case "goto":
          await page.goto(step.url, { waitUntil: "domcontentloaded", timeout: 60000 });
          entry.url = step.url;
          break;
        case "wait":
          if (step.selector) await page.locator(step.selector).first().waitFor({ state: "visible", timeout: step.timeout || 30000 });
          else await page.waitForTimeout(step.ms || 1000);
          break;
        case "move": {
          const target = step.selector ? await centerOf(step.selector) : step;
          await glide(target.x, target.y, step.ms);
          if (target.box) entry.box = target.box;
          break;
        }
        case "click": {
          const target = await centerOf(step.selector);
          await glide(target.x, target.y, step.ms);
          await page.waitForTimeout(180);
          entry.box = target.box;
          entry.clickAt = now();
          await page.mouse.click(target.x, target.y);
          break;
        }
        case "type": {
          const target = await centerOf(step.selector);
          const type = await target.locator.getAttribute("type");
          if ((type || "").toLowerCase() === "password") {
            throw new Error("Script không gõ vào ô mật khẩu. Dùng --login --profile để người dùng tự đăng nhập.");
          }
          await glide(target.x, target.y, step.ms);
          await page.mouse.click(target.x, target.y);
          entry.box = target.box;
          await page.keyboard.type(step.text, { delay: step.delay || 55 });
          break;
        }
        case "key":
          await page.keyboard.press(step.key);
          break;
        case "scroll": {
          const total = step.y || 0;
          const frames = Math.max(1, Math.round((step.ms || 800) / 16));
          for (let i = 0; i < frames; i++) {
            await page.mouse.wheel(0, total / frames);
            await page.waitForTimeout(16);
          }
          break;
        }
        case "mark":
          log.marks.push({ label: step.label, t: now(), x: mouse.x, y: mouse.y });
          break;
        case "shot": {
          const file = path.join(outDir, `${name}-${step.name || index}.png`);
          await page.screenshot({ path: file });
          log.shots.push({ file: path.basename(file), t: now() });
          break;
        }
        default:
          throw new Error(`Lệnh không hỗ trợ: ${step.do}`);
      }
      entry.end = now();
      entry.mouse = { ...mouse };
      log.steps.push(entry);
    }
    await page.waitForTimeout(plan.tail ?? 800);
    log.duration = now();
    log.finalUrl = page.url();
  } catch (error) {
    log.error = String(error.message || error);
  }

  const video = page.video();
  await context.close();
  if (browser) await browser.close();
  const rawPath = video ? await video.path() : null;

  let output = null;
  if (rawPath && fs.existsSync(rawPath)) {
    const mp4 = path.join(outDir, `${name}.mp4`);
    const ffmpeg = spawnSync("ffmpeg", ["-y", "-loglevel", "error", "-i", rawPath, "-r", "30", "-c:v", "libx264", "-preset", "medium",
      "-crf", "16", "-pix_fmt", "yuv420p", "-movflags", "+faststart", "-an", mp4], { encoding: "utf8" });
    if (ffmpeg.status === 0) {
      output = mp4;
    } else {
      output = path.join(outDir, `${name}.webm`);
      fs.copyFileSync(rawPath, output);
      log.warning = "ffmpeg không chạy được nên giữ file .webm; cài ffmpeg rồi chuyển sang mp4 trước khi dựng.";
    }
    fs.rmSync(rawDir, { recursive: true, force: true });
  }
  log.file = output ? path.basename(output) : null;
  // Step times are measured from script start; the recording starts a little later.
  // videoOffset is what to subtract from a step's `t` to get its time in the video file.
  if (output && log.duration) {
    const probe = spawnSync("ffprobe", ["-v", "error", "-show_entries", "format=duration", "-of", "csv=p=0", output], { encoding: "utf8" });
    const videoDuration = parseFloat(probe.stdout);
    if (Number.isFinite(videoDuration)) {
      log.videoDuration = Math.round(videoDuration * 100) / 100;
      log.videoOffset = Math.round((log.duration - videoDuration) * 100) / 100;
    }
  }
  fs.writeFileSync(path.join(outDir, `${name}.log.json`), JSON.stringify(log, null, 2));

  // Record where the footage came from next to the other project assets.
  const ledgerPath = [path.join(outDir, "..", "assets", "ledger.json"), path.join(outDir, "ledger.json")].find((p) => fs.existsSync(p));
  if (ledgerPath && output) {
    const ledger = JSON.parse(fs.readFileSync(ledgerPath, "utf8")).filter((e) => e.file !== `captures/${log.file}`);
    ledger.push({ file: `captures/${log.file}`, kind: "screen-recording", source: plan.url || log.finalUrl, fetched: new Date().toISOString().slice(0, 19) });
    fs.writeFileSync(ledgerPath, JSON.stringify(ledger, null, 2) + "\n");
  }

  console.log(JSON.stringify({ file: output, log: path.join(outDir, `${name}.log.json`), duration: log.duration, steps: log.steps.length,
    shots: log.shots.map((s) => s.file), error: log.error || null }, null, 2));
  if (log.error) process.exit(1);
}

(async () => {
  const args = parseArgs(process.argv.slice(2));
  const playwright = loadPlaywright();
  if (args.login) await login(playwright, args);
  else await record(playwright, args);
})().catch((error) => fail(error.message || String(error)));
