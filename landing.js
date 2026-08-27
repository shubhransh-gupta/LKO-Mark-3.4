/* LKO MARK 3.4 // MARKETING & LANDING INTERACTION SCRIPT */

document.addEventListener("DOMContentLoaded", () => {
  initParticleCanvas();
  init3DReactorTilt();
  initLiveTelemetry();
  initSimulatorTerminal();
  initAudioSFX();
  initWaitlistForm();
});

/* ----------------------------------------------------
   1. PARTICLE CANVAS ANIMATION (Holographic Atmosphere)
   ---------------------------------------------------- */
function initParticleCanvas() {
  const canvas = document.getElementById("particle-canvas");
  if (!canvas) return;
  const ctx = canvas.getContext("2d");

  let width = (canvas.width = window.innerWidth);
  let height = (canvas.height = window.innerHeight);

  window.addEventListener("resize", () => {
    width = canvas.width = window.innerWidth;
    height = canvas.height = window.innerHeight;
  });

  const particles = [];
  const count = 45;

  for (let i = 0; i < count; i++) {
    particles.push({
      x: Math.random() * width,
      y: Math.random() * height,
      size: Math.random() * 2 + 0.5,
      speedX: (Math.random() - 0.5) * 0.4,
      speedY: (Math.random() - 0.5) * 0.4,
      alpha: Math.random() * 0.5 + 0.2,
      color: Math.random() > 0.3 ? "#00d2ff" : "#ffaa00",
    });
  }

  function draw() {
    ctx.clearRect(0, 0, width, height);

    particles.forEach((p) => {
      p.x += p.speedX;
      p.y += p.speedY;

      if (p.x < 0) p.x = width;
      if (p.x > width) p.x = 0;
      if (p.y < 0) p.y = height;
      if (p.y > height) p.y = 0;

      ctx.beginPath();
      ctx.arc(p.x, p.y, p.size, 0, Math.PI * 2);
      ctx.fillStyle = p.color;
      ctx.globalAlpha = p.alpha;
      ctx.shadowBlur = 8;
      ctx.shadowColor = p.color;
      ctx.fill();
    });

    requestAnimationFrame(draw);
  }
  draw();
}

/* ----------------------------------------------------
   2. 3D INTERACTIVE TILT ON ARC REACTOR
   ---------------------------------------------------- */
function init3DReactorTilt() {
  const orb = document.getElementById("reactor-interactive-orb");
  if (!orb) return;

  const stage = orb.closest(".hologram-stage-frame");
  if (!stage) return;

  stage.addEventListener("mousemove", (e) => {
    const rect = stage.getBoundingClientRect();
    const x = e.clientX - rect.left - rect.width / 2;
    const y = e.clientY - rect.top - rect.height / 2;

    const tiltX = (y / rect.height) * -25;
    const tiltY = (x / rect.width) * 25;

    orb.style.transform = `rotateX(${tiltX}deg) rotateY(${tiltY}deg)`;
  });

  stage.addEventListener("mouseleave", () => {
    orb.style.transform = "rotateX(0deg) rotateY(0deg)";
  });
}

/* ----------------------------------------------------
   3. LIVE TELEMETRY OSCILLATION
   ---------------------------------------------------- */
function initLiveTelemetry() {
  const powerEl = document.getElementById("live-power-val");
  if (!powerEl) return;

  setInterval(() => {
    const base = 3.4;
    const jitter = (Math.random() * 0.04 - 0.02);
    const current = (base + jitter).toFixed(2);
    powerEl.textContent = current;
  }, 1800);
}

/* ----------------------------------------------------
   4. WEB AUDIO API SCI-FI SFX SYNTHESIZER
   ---------------------------------------------------- */
let audioCtx = null;
let sfxEnabled = true;

function initAudioSFX() {
  const toggleBtn = document.getElementById("sfx-toggle");
  if (!toggleBtn) return;

  toggleBtn.addEventListener("click", () => {
    sfxEnabled = !sfxEnabled;
    const dot = toggleBtn.querySelector(".sfx-dot");
    const label = toggleBtn.querySelector(".sfx-label");

    if (sfxEnabled) {
      dot.style.background = "#00ffaa";
      dot.style.boxShadow = "0 0 6px #00ffaa";
      label.textContent = "JARVIS AUDIO: ON";
      playSciFiBeep(880, 0.08);
    } else {
      dot.style.background = "#ff2255";
      dot.style.boxShadow = "0 0 6px #ff2255";
      label.textContent = "JARVIS AUDIO: MUTED";
    }
  });

  // Attach hover sounds to preset buttons and CTA
  document.querySelectorAll(".preset-btn, .hud-btn").forEach((el) => {
    el.addEventListener("mouseenter", () => {
      if (sfxEnabled) playSciFiBeep(1200, 0.02, "triangle");
    });
  });
}

function playSciFiBeep(freq = 600, duration = 0.05, type = "sine") {
  try {
    if (!audioCtx) {
      audioCtx = new (window.AudioContext || window.webkitAudioContext)();
    }
    if (audioCtx.state === "suspended") {
      audioCtx.resume();
    }
    const osc = audioCtx.createOscillator();
    const gain = audioCtx.createGain();
    osc.type = type;
    osc.frequency.setValueAtTime(freq, audioCtx.currentTime);
    gain.gain.setValueAtTime(0.04, audioCtx.currentTime);
    gain.gain.exponentialRampToValueAtTime(0.0001, audioCtx.currentTime + duration);

    osc.connect(gain);
    gain.connect(audioCtx.destination);
    osc.start();
    osc.stop(audioCtx.currentTime + duration);
  } catch (e) {
    // AudioContext blocked or unsupported
  }
}

/* ----------------------------------------------------
   5. LIVE JARVIS TERMINAL SIMULATOR
   ---------------------------------------------------- */
function initSimulatorTerminal() {
  const form = document.getElementById("sim-form");
  const input = document.getElementById("sim-input");
  const output = document.getElementById("sim-output");
  const presetBtns = document.querySelectorAll(".preset-btn");

  if (!form || !input || !output) return;

  presetBtns.forEach((btn) => {
    btn.addEventListener("click", () => {
      const query = btn.dataset.query;
      input.value = query;
      handleSimulation(query);
    });
  });

  form.addEventListener("submit", (e) => {
    e.preventDefault();
    const query = input.value.trim();
    if (!query) return;
    handleSimulation(query);
    input.value = "";
  });

  function handleSimulation(query) {
    appendLine("user", `❯ USER: ${query}`);
    playSciFiBeep(440, 0.05);

    // Simulated Thinking state
    const thinkingId = appendLine("system", "[PROCESSING] JARVIS neural sub-routine executing...");
    scrollTerminal();

    setTimeout(() => {
      const thinkingEl = document.getElementById(thinkingId);
      if (thinkingEl) thinkingEl.remove();

      const response = generateSimulatedReply(query);
      typeBotResponse(response);
    }, 600);
  }

  function appendLine(type, text) {
    const id = "line-" + Date.now() + "-" + Math.random().toString(36).substr(2, 4);
    const div = document.createElement("div");
    div.id = id;
    div.className = `sim-line ${type}`;
    div.textContent = text;
    output.appendChild(div);
    scrollTerminal();
    return id;
  }

  function typeBotResponse(text) {
    const div = document.createElement("div");
    div.className = "sim-line bot";
    const tag = document.createElement("span");
    tag.className = "bot-tag";
    tag.textContent = "> JARVIS: ";
    div.appendChild(tag);
    output.appendChild(div);

    let idx = 0;
    const span = document.createElement("span");
    div.appendChild(span);

    const interval = setInterval(() => {
      if (idx < text.length) {
        span.textContent += text[idx];
        idx++;
        if (idx % 4 === 0 && sfxEnabled) playSciFiBeep(1400 + Math.random() * 400, 0.015, "triangle");
        scrollTerminal();
      } else {
        clearInterval(interval);
        // Optional voice speech synthesis
        speakIfSupported(text);
      }
    }, 18);
  }

  function scrollTerminal() {
    output.scrollTop = output.scrollHeight;
  }

  function speakIfSupported(text) {
    if (!sfxEnabled || !("speechSynthesis" in window)) return;
    try {
      window.speechSynthesis.cancel();
      const cleanText = text.replace(/[*_`]/g, "");
      const utterance = new SpeechSynthesisUtterance(cleanText);
      utterance.rate = 1.05;
      utterance.pitch = 0.95;
      const voices = window.speechSynthesis.getVoices();
      const britishVoice = voices.find(
        (v) => v.lang.includes("en-GB") || v.name.includes("Daniel") || v.name.includes("Oliver")
      );
      if (britishVoice) utterance.voice = britishVoice;
      window.speechSynthesis.speak(utterance);
    } catch (e) {}
  }

  function generateSimulatedReply(q) {
    const lower = q.toLowerCase();

    if (lower.includes("screen") || lower.includes("vision") || lower.includes("window")) {
      return "Optical capture complete, Sir. I've analyzed your Retina viewport: Visual hierarchy grounded, 4 windows detected, active workspace: Terminal & VS Code. No security anomalies observed.";
    } else if (lower.includes("slack") || lower.includes("message")) {
      return "Slack AppleScript dispatcher activated. Target channel selected. Message queued and delivered through macOS GUI automation successfully.";
    } else if (lower.includes("battery") || lower.includes("telemetry") || lower.includes("hardware") || lower.includes("cpu")) {
      return "Suit telemetry query: Battery reserve at 94% [AC connected], M-Series neural engine running at 3.4 GW nominal, audio output set to 48%.";
    } else if (lower.includes("tunnel") || lower.includes("mobile") || lower.includes("cloudflare")) {
      return "Cloudflare Quick Tunnel established. Secure HTTPS endpoint: https://lko-neural-gateway.trycloudflare.com. Encrypted mobile downlink active.";
    } else if (lower.includes("volume")) {
      return "Adjusting macOS CoreAudio volume levels to requested specification immediately, Sir.";
    } else {
      return `Instruction acknowledged: "${q}". Autonomous sub-routine dispatched through Gemini Multimodal Flash engine. Task executed.`;
    }
  }
}

/* ----------------------------------------------------
   6. WAITLIST / EARLY ACCESS TRANSMISSION FORM
   ---------------------------------------------------- */
function initWaitlistForm() {
  const form = document.getElementById("waitlist-form");
  const emailInput = document.getElementById("waitlist-email");
  const feedback = document.getElementById("waitlist-feedback");

  if (!form || !emailInput || !feedback) return;

  form.addEventListener("submit", (e) => {
    e.preventDefault();
    const email = emailInput.value.trim();
    if (!email) return;

    feedback.style.color = "#00ffaa";
    feedback.textContent = `⚡ [TRANSMISSION CONFIRMED] Pilot clearance granted for: ${email}. Welcome to Stark Protocol.`;
    playSciFiBeep(980, 0.2);
    emailInput.value = "";
  });
}
