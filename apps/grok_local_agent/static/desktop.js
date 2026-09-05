(function () {
  const panel = document.getElementById("panel");
  const tokenEl = document.getElementById("token");
  const statusEl = document.getElementById("status");
  const lineEl = document.getElementById("line");
  const ptt = document.getElementById("ptt");
  const flag = document.getElementById("listen-flag");
  tokenEl.value = sessionStorage.getItem("grok_agent_token") || "";
  tokenEl.onchange = function () {
    sessionStorage.setItem("grok_agent_token", tokenEl.value.trim());
  };

  const headers = function () {
    return { "Content-Type": "application/json", Authorization: "Bearer " + tokenEl.value.trim() };
  };

  function applyState(mode, detail) {
    panel.className = mode || "idle";
    if (panel.classList.contains("minimized")) panel.classList.add("minimized");
    const labels = {
      idle: "Ready",
      listening: "Listening...",
      thinking: "Thinking...",
      speaking: "Speaking...",
      working: "Working...",
      success: "Done.",
      warning: "Permission needed",
      error: "Something failed",
    };
    statusEl.textContent = labels[mode] || "FARNAZ";
    if (detail) lineEl.textContent = detail;
    flag.hidden = mode !== "listening";
    mouthFromState(mode);
  }

  function svgDoc() {
    return document.getElementById("face").contentDocument;
  }

  function mouthFromState(mode) {
    const doc = svgDoc();
    if (!doc) return;
    const root = doc.getElementById("farnaz-face") || doc.documentElement;
    root.setAttribute("data-state", mode || "idle");
    if (mode !== "speaking") setMouth(doc, "rest");
  }

  function setMouth(doc, kind) {
    const names = ["rest", "a", "o", "e", "m", "f"];
    names.forEach(function (n) {
      doc.querySelectorAll(".m-" + n).forEach(function (el) {
        el.setAttribute("opacity", n === kind ? "1" : "0");
      });
    });
  }

  function playVisemes(frames) {
    const doc = svgDoc();
    if (!doc || !frames || !frames.length) return;
    const t0 = performance.now();
    function tick(now) {
      const t = now - t0;
      let cur = frames[0];
      for (let i = 0; i < frames.length; i++) {
        if (frames[i].t <= t) cur = frames[i];
      }
      setMouth(doc, cur.mouth || "rest");
      if (t <= frames[frames.length - 1].t) requestAnimationFrame(tick);
      else {
        setMouth(doc, "rest");
        applyState("idle");
      }
    }
    requestAnimationFrame(tick);
  }

  async function api(path, body) {
    const r = await fetch(path, {
      method: body ? "POST" : "GET",
      headers: headers(),
      body: body ? JSON.stringify(body) : undefined,
    });
    const t = await r.text();
    try { return JSON.parse(t); } catch { return { detail: t }; }
  }

  async function speakText(text) {
    applyState("speaking", text);
    const data = await api("/avatar/speak", { text: text });
    if (window.speechSynthesis && (!data.wav || data.backend === "viseme" || data.backend === "muted")) {
      if (data.backend !== "muted") {
        const u = new SpeechSynthesisUtterance(text.slice(0, 400));
        u.lang = /[\u0600-\u06FF]/.test(text) ? "fa-IR" : "en-US";
        speechSynthesis.cancel();
        speechSynthesis.speak(u);
      }
    }
    playVisemes(data.visemes || []);
  }

  async function ask(message) {
    applyState("thinking", message);
    const r = await fetch("/grok/chat", {
      method: "POST",
      headers: headers(),
      body: JSON.stringify({ message: message }),
    });
    const d = await r.json();
    const content = String(d.content || d.detail || "");
    lineEl.textContent = content.slice(0, 400);
    await speakText(content);
  }

  document.getElementById("chat").onsubmit = function (e) {
    e.preventDefault();
    const msg = document.getElementById("msg").value.trim();
    if (!msg) return;
    document.getElementById("msg").value = "";
    ask(msg);
  };

  document.getElementById("stop").onclick = function () {
    if (window.speechSynthesis) speechSynthesis.cancel();
    api("/avatar/stop", {});
    applyState("idle", "Stopped.");
  };
  document.getElementById("kill").onclick = async function () {
    if (window.speechSynthesis) speechSynthesis.cancel();
    await api("/operator/stop", {});
    applyState("warning", "EMERGENCY STOP. Automation frozen.");
  };
  document.getElementById("mute").onclick = async function () {
    const cur = await api("/avatar/config");
    const muted = !cur.muted;
    await api("/avatar/config", { muted: muted });
    document.getElementById("mute").textContent = muted ? "UNMUTE" : "MUTE";
  };
  document.getElementById("min").onclick = function () {
    panel.classList.toggle("minimized");
  };
  document.getElementById("hide").onclick = function () {
    api("/avatar/config", { hidden: true });
    panel.style.display = "none";
  };

  const SR = window.SpeechRecognition || window.webkitSpeechRecognition;
  let rec = null;
  ptt.addEventListener("pointerdown", function () {
    ptt.classList.add("live");
    api("/avatar/ptt/start", { backend: "client" });
    applyState("listening");
    if (!SR) {
      lineEl.textContent = "No speech recognizer in this browser. Type instead.";
      return;
    }
    rec = new SR();
    rec.lang = "fa-IR";
    rec.onresult = function (e) {
      ask(e.results[0][0].transcript);
    };
    rec.start();
  });
  function endPtt() {
    ptt.classList.remove("live");
    rec && rec.stop();
    rec = null;
    api("/avatar/ptt/stop", {});
  }
  ptt.addEventListener("pointerup", endPtt);
  ptt.addEventListener("pointerleave", endPtt);

  (function drag() {
    const bar = document.getElementById("drag");
    let x = 0, y = 0, down = false;
    bar.addEventListener("pointerdown", function (e) {
      down = true; x = e.clientX; y = e.clientY; bar.setPointerCapture(e.pointerId);
    });
    bar.addEventListener("pointermove", function (e) {
      if (!down) return;
      const dx = e.clientX - x, dy = e.clientY - y;
      x = e.clientX; y = e.clientY;
      panel.style.position = "fixed";
      panel.style.left = (panel.offsetLeft + dx) + "px";
      panel.style.top = (panel.offsetTop + dy) + "px";
    });
    bar.addEventListener("pointerup", function () { down = false; });
  })();

  applyState("idle", "فرناز اینجاست. نگه دارید و حرف بزنید.");
  api("/operator").then(function (d) {
    if (d && d.job) {
      document.getElementById("task").textContent = (d.job.title || "JOB") + " · " + (d.job.stage || "start");
    }
    if (d && d.halted) applyState("warning", "EMERGENCY STOP");
  }).catch(function () {});
})();
