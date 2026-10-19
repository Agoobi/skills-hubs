/* Khung chat website cho chatbot Hermes. Nhung bang: <script src="https://<bot>/widget.js" defer></script> */
(function () {
  if (window.__hermesWebchat) return;
  window.__hermesWebchat = true;
  var CONF = __WEBCHAT_CONFIG__;
  var me = document.currentScript || document.querySelector('script[src*="widget.js"]');
  var API = new URL(me.src).origin;
  var KEY = "hermes_webchat_v1";

  function load() { try { return JSON.parse(localStorage.getItem(KEY)) || {}; } catch (e) { return {}; } }
  function save() { try { localStorage.setItem(KEY, JSON.stringify(state)); } catch (e) {} }
  function rid() {
    var a = new Uint8Array(12);
    (window.crypto || window.msCrypto).getRandomValues(a);
    return Array.prototype.map.call(a, function (b) { return ("0" + b.toString(16)).slice(-2); }).join("");
  }
  var state = load();
  if (!state.vid) { state.vid = rid(); state.last = 0; state.log = []; save(); }

  function esc(s) { return s.replace(/[&<>"']/g, function (c) { return "&#" + c.charCodeAt(0) + ";"; }); }
  function fmt(s) {
    return esc(s)
      .replace(/\*\*(.+?)\*\*/g, "<b>$1</b>")
      .replace(/(https?:\/\/[^\s<]+)/g, '<a href="$1" target="_blank" rel="noopener">$1</a>')
      .replace(/\n/g, "<br>");
  }

  var css = "#hwc-btn{position:fixed;right:20px;bottom:20px;width:56px;height:56px;border-radius:50%;border:0;cursor:pointer;" +
    "background:" + CONF.color + ";color:#fff;font-size:26px;box-shadow:0 4px 14px rgba(0,0,0,.25);z-index:2147483000}" +
    "#hwc-box{position:fixed;right:20px;bottom:88px;width:340px;max-width:calc(100vw - 32px);height:480px;max-height:calc(100vh - 120px);" +
    "background:#fff;border-radius:12px;box-shadow:0 8px 30px rgba(0,0,0,.25);display:none;flex-direction:column;overflow:hidden;" +
    "font:14px/1.45 -apple-system,Segoe UI,Roboto,sans-serif;color:#1b2430;z-index:2147483000}" +
    "#hwc-box.open{display:flex}#hwc-head{background:" + CONF.color + ";color:#fff;padding:12px 14px;font-weight:600}" +
    "#hwc-log{flex:1;overflow-y:auto;padding:12px;background:#f5f7fa}" +
    ".hwc-m{max-width:85%;padding:8px 11px;border-radius:12px;margin:4px 0;word-wrap:break-word}" +
    ".hwc-bot{background:#fff;border:1px solid #e3e8ee}.hwc-user{background:" + CONF.color + ";color:#fff;margin-left:auto}" +
    ".hwc-m a{color:inherit;text-decoration:underline}#hwc-typing{display:none;color:#6b7684;font-size:12px;padding:0 12px 6px;background:#f5f7fa}" +
    "#hwc-form{display:flex;border-top:1px solid #e3e8ee}#hwc-in{flex:1;border:0;padding:12px;font:inherit;outline:none}" +
    "#hwc-send{border:0;background:none;color:" + CONF.color + ";font-weight:600;padding:0 14px;cursor:pointer}";
  var st = document.createElement("style"); st.textContent = css; document.head.appendChild(st);

  var box = document.createElement("div"); box.id = "hwc-box";
  box.innerHTML = '<div id="hwc-head"></div><div id="hwc-log" aria-live="polite"></div><div id="hwc-typing">Đang trả lời…</div>' +
    '<form id="hwc-form"><input id="hwc-in" maxlength="1000" autocomplete="off" placeholder="Nhập câu hỏi…"><button id="hwc-send">Gửi</button></form>';
  var btn = document.createElement("button"); btn.id = "hwc-btn"; btn.setAttribute("aria-label", CONF.title); btn.textContent = "💬";
  document.body.appendChild(box); document.body.appendChild(btn);
  box.querySelector("#hwc-head").textContent = CONF.title;
  var logEl = box.querySelector("#hwc-log"), typingEl = box.querySelector("#hwc-typing"), input = box.querySelector("#hwc-in");

  function add(role, text, keep) {
    var d = document.createElement("div");
    d.className = "hwc-m " + (role === "user" ? "hwc-user" : "hwc-bot");
    d.innerHTML = fmt(text);
    logEl.appendChild(d); logEl.scrollTop = logEl.scrollHeight;
    if (keep) { state.log.push({ r: role, t: text }); state.log = state.log.slice(-60); save(); }
  }
  add("bot", CONF.greeting, false);
  state.log.forEach(function (m) { add(m.r, m.t, false); });

  var polling = false, typing = false;
  function poll() {
    if (polling) return; polling = true;
    fetch(API + "/api/messages?vid=" + state.vid + "&after=" + state.last + "&typing=" + (typing ? 1 : 0))
      .then(function (r) { return r.json(); })
      .then(function (j) {
        polling = false;
        (j.messages || []).forEach(function (m) { add("bot", m.text, true); state.last = Math.max(state.last, m.seq); });
        save();
        typing = !!j.typing; typingEl.style.display = typing ? "block" : "none";
        if (box.classList.contains("open") || typing) poll();
      })
      .catch(function () { polling = false; setTimeout(poll, 5000); });
  }

  btn.onclick = function () {
    box.classList.toggle("open");
    if (box.classList.contains("open")) { input.focus(); poll(); }
  };
  box.querySelector("#hwc-form").onsubmit = function (e) {
    e.preventDefault();
    var text = input.value.trim(); if (!text) return;
    input.value = ""; add("user", text, true);
    fetch(API + "/api/chat", { method: "POST", headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ vid: state.vid, text: text, page: location.href }) })
      .then(function (r) {
        if (r.status === 429) add("bot", "Anh/chị gửi hơi nhanh, vui lòng thử lại sau ít phút ạ.", false);
        else if (!r.ok) add("bot", "Xin lỗi, hệ thống đang bận. Anh/chị thử lại giúp em ạ.", false);
        else { typing = true; typingEl.style.display = "block"; poll(); }
      })
      .catch(function () { add("bot", "Không kết nối được. Anh/chị kiểm tra mạng giúp em ạ.", false); });
  };
})();
