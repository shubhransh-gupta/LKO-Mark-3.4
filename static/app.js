// LKO MARK 3.4 // NEURAL TACTICAL CONTROLLER

let lkoVoiceEnabled = true;

document.addEventListener("DOMContentLoaded", () => {
  initClock();
  initKeyValidation();
  initTelemetryPolling();
  initChatController();
  initScreenMonitor();
  initSettingsModal();
  initLkoAudio();
});

// 1. Digital Telemetry Clock
function initClock() {
  const clockEl = document.getElementById("live-clock");
  function updateTime() {
    const now = new Date();
    const hrs = String(now.getHours()).padStart(2, "0");
    const mins = String(now.getMinutes()).padStart(2, "0");
    const secs = String(now.getSeconds()).padStart(2, "0");
    if (clockEl) clockEl.textContent = `${hrs}:${mins}:${secs}`;
  }
  updateTime();
  setInterval(updateTime, 1000);
}

// 2. Key Validation & Neural Status
async function initKeyValidation() {
  const badgeText = document.getElementById("system-security-text");
  const modelText = document.getElementById("engine-model-display");
  const footerEngine = document.getElementById("footer-engine");

  try {
    const res = await fetch("/api/validate-key");
    const data = await res.json();
    if (data.valid) {
      if (badgeText) badgeText.textContent = `LKO ONLINE // ${data.model.toUpperCase()}`;
      if (modelText) modelText.textContent = `NEURAL ENGINE: ${data.model.toUpperCase()}`;
      if (footerEngine) footerEngine.textContent = data.model.toUpperCase();
      addLog(`[LKO_CORE] Neural link established with ${data.model}`, "success");
    } else {
      if (badgeText) badgeText.textContent = "KEY CALIBRATION REQUIRED";
      addLog(`[WARNING] ${data.error || "Key validation failed"}`, "warning");
    }
  } catch (err) {
    console.warn("Key validation check error:", err);
  }
}

// 3. Telemetry & Mac Diagnostics
function initTelemetryPolling() {
  const activeAppEl = document.getElementById("active-app-val");
  const volumeValEl = document.getElementById("volume-val");
  const volumeSlider = document.getElementById("volume-slider");
  const batteryValEl = document.getElementById("battery-val");
  const batteryBar = document.getElementById("battery-bar-fill");
  const clipboardEl = document.getElementById("clipboard-preview");
  const copyBtn = document.getElementById("copy-clipboard-btn");
  const copyPublicBtn = document.getElementById("btn-copy-public-url");

  async function fetchTelemetry() {
    try {
      const res = await fetch("/api/system-status");
      if (!res.ok) return;
      const data = await res.json();
      
      if (activeAppEl) activeAppEl.textContent = data.active_application || "Finder";
      
      if (volumeValEl && data.volume_percent !== undefined) {
        volumeValEl.textContent = `${data.volume_percent}%`;
        if (volumeSlider && document.activeElement !== volumeSlider) {
          volumeSlider.value = parseInt(data.volume_percent) || 50;
        }
      }

      if (batteryValEl && data.battery_info) {
        const match = data.battery_info.match(/(\d+)%/);
        const percent = match ? match[1] : "--";
        batteryValEl.textContent = `${percent}%`;
        if (batteryBar && percent !== "--") {
          batteryBar.style.width = `${percent}%`;
        }
      }

      if (clipboardEl && data.clipboard) {
        clipboardEl.textContent = data.clipboard || "Empty clipboard";
      }
    } catch (err) {
      console.warn("Telemetry fetch error:", err);
    }
  }

  fetchTelemetry();
  setInterval(fetchTelemetry, 3500);

  if (volumeSlider) {
    volumeSlider.addEventListener("change", async (e) => {
      const val = e.target.value;
      if (volumeValEl) volumeValEl.textContent = `${val}%`;
      addLog(`[ACOUSTIC] Adjusting output level to ${val}%`, "info");
      try {
        await fetch("/api/set-volume", {
          method: "POST",
          headers: { "Content-Type": "application/json" },
          body: JSON.stringify({ level: parseInt(val) })
        });
      } catch (err) {
        console.error("Volume set error:", err);
      }
    });
  }

  if (copyBtn && clipboardEl) {
    copyBtn.addEventListener("click", () => {
      navigator.clipboard.writeText(clipboardEl.textContent);
      copyBtn.textContent = "COPIED, SIR!";
      setTimeout(() => { copyBtn.textContent = "COPY TO CLIPBOARD"; }, 1500);
    });
  }

  if (copyPublicBtn) {
    copyPublicBtn.addEventListener("click", () => {
      const url = window.location.href;
      navigator.clipboard.writeText(url);
      copyPublicBtn.textContent = "COPIED!";
      setTimeout(() => { copyPublicBtn.textContent = "COPY LINK"; }, 1500);
    });
  }
}

// 4. Tactical Command Center
function initChatController() {
  const inputEl = document.getElementById("command-input");
  const sendBtn = document.getElementById("send-btn");
  const messagesContainer = document.getElementById("chat-messages");
  const coreIndicator = document.getElementById("core-state-indicator");
  const clearBtn = document.getElementById("clear-chat-btn");
  const quickSlackBtn = document.getElementById("quick-slack-btn");
  const quickScreenBtn = document.getElementById("quick-screen-btn");
  const micBtn = document.getElementById("mic-btn");

  async function handleSend() {
    const text = inputEl.value.trim();
    if (!text) return;

    appendMessage("user", "OPERATOR", text);
    inputEl.value = "";
    playStarkChime("engage");

    setCoreState("PROCESSING PROTOCOL", "yellow");
    addLog(`[TACTICAL_IN] Order: "${text.substring(0, 45)}..."`, "info");

    try {
      const res = await fetch("/api/chat", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ message: text })
      });

      const data = await res.json();
      setCoreState("STANDBY", "green");
      playStarkChime("complete");

      if (data.success) {
        appendMessage("ai", "LKO MARK 3.4", data.response, data.media);
        addLog(`[EXECUTED] Protocol complete, sir.`, "success");
        speakLko(data.response);
      } else {
        appendMessage("ai", "LKO WARNING", data.error || "Protocol failed.");
        addLog(`[ERROR] ${data.error}`, "error");
        speakLko("I encountered an anomaly executing that protocol, sir.");
      }

      refreshScreen();
    } catch (err) {
      setCoreState("ERROR", "red");
      appendMessage("ai", "LKO ERROR", `Network anomaly: ${err.message}`);
      addLog(`[ERROR] Network link interrupted: ${err.message}`, "error");
    }
  }

  function setCoreState(stateText, color) {
    if (coreIndicator) {
      coreIndicator.textContent = `SYSTEM STATE: ${stateText}`;
      if (color === "yellow") {
        coreIndicator.style.color = "var(--stark-gold)";
        coreIndicator.style.borderColor = "var(--stark-gold)";
        coreIndicator.style.background = "rgba(255, 170, 0, 0.18)";
      } else if (color === "red") {
        coreIndicator.style.color = "var(--armor-red)";
        coreIndicator.style.borderColor = "var(--armor-red)";
        coreIndicator.style.background = "rgba(255, 26, 64, 0.18)";
      } else {
        coreIndicator.style.color = "var(--armor-green)";
        coreIndicator.style.borderColor = "var(--armor-green)";
        coreIndicator.style.background = "rgba(0, 255, 170, 0.12)";
      }
    }
  }

  function appendMessage(type, sender, text, media = []) {
    const msgDiv = document.createElement("div");
    msgDiv.className = `jarvis-bubble ${type}`;

    const avatar = type === "user" ? "⚡" : "LKO";
    const now = new Date().toLocaleTimeString();

    let mediaHtml = "";
    if (media && media.length > 0) {
      media.forEach(src => {
        mediaHtml += `<div style="margin-top: 10px; border-radius: 6px; overflow: hidden; border: 1px solid var(--arc-cyan);"><img src="/api/screenshot?t=${Date.now()}" style="width: 100%; display: block;" alt="Optical Scan"></div>`;
      });
    }

    msgDiv.innerHTML = `
      <div class="bubble-avatar">
        <div class="mini-arc"></div>
      </div>
      <div class="bubble-content">
        <div class="bubble-sender">${sender}</div>
        <div class="bubble-text">${escapeHtml(text)}${mediaHtml}</div>
        <div class="bubble-time">${now}</div>
      </div>
    `;

    messagesContainer.appendChild(msgDiv);
    messagesContainer.scrollTop = messagesContainer.scrollHeight;
  }

  sendBtn.addEventListener("click", handleSend);
  inputEl.addEventListener("keydown", (e) => {
    if (e.key === "Enter") handleSend();
  });

  if (clearBtn) {
    clearBtn.addEventListener("click", async () => {
      messagesContainer.innerHTML = "";
      addLog("[LKO_CORE] Neural buffer purged, sir.", "info");
      speakLko("Neural memory cleared, sir.");
      await fetch("/api/reset", { method: "POST" });
    });
  }

  if (quickSlackBtn) {
    quickSlackBtn.addEventListener("click", () => {
      inputEl.value = 'Send a message "Hello Team" to general on Slack';
      inputEl.focus();
    });
  }

  if (quickScreenBtn) {
    quickScreenBtn.addEventListener("click", () => {
      inputEl.value = 'Take a screenshot of my Mac and tell me what is open';
      inputEl.focus();
    });
  }

  // Voice Input (Web Speech)
  if (micBtn && ('webkitSpeechRecognition' in window || 'SpeechRecognition' in window)) {
    const SpeechRecognition = window.SpeechRecognition || window.webkitSpeechRecognition;
    const recognition = new SpeechRecognition();
    recognition.continuous = false;
    recognition.interimResults = false;

    micBtn.addEventListener("click", () => {
      micBtn.style.color = "var(--stark-gold)";
      addLog("[VOICE_RECOGNITION] Listening for operator...", "info");
      recognition.start();
    });

    recognition.onresult = (event) => {
      const transcript = event.results[0][0].transcript;
      inputEl.value = transcript;
      micBtn.style.color = "";
      addLog(`[VOICE_IN] "${transcript}"`, "success");
      handleSend();
    };

    recognition.onerror = () => { micBtn.style.color = ""; };
    recognition.onend = () => { micBtn.style.color = ""; };
  }
}

// 5. Optical Sensors Monitor
function initScreenMonitor() {
  const screenImg = document.getElementById("live-screen-img");
  const refreshBtn = document.getElementById("refresh-screen-btn");
  const coordsHud = document.getElementById("screen-coords");
  const container = document.querySelector(".vision-stage");

  window.refreshScreen = function() {
    if (screenImg) {
      screenImg.src = `/api/screenshot?t=${Date.now()}`;
      const timeTag = document.getElementById("screen-time-tag");
      if (timeTag) timeTag.textContent = `FEED: ${new Date().toLocaleTimeString()}`;
    }
  };

  if (refreshBtn) {
    refreshBtn.addEventListener("click", () => {
      addLog("[OPTICAL] Scanning visual frame...", "info");
      window.refreshScreen();
    });
  }

  if (container && coordsHud) {
    container.addEventListener("mousemove", (e) => {
      const rect = container.getBoundingClientRect();
      const x = Math.round(((e.clientX - rect.left) / rect.width) * 1920);
      const y = Math.round(((e.clientY - rect.top) / rect.height) * 1080);
      coordsHud.textContent = `HUD // X: ${String(x).padStart(4, "0")} | Y: ${String(y).padStart(4, "0")}`;
    });
  }
}

// 6. Settings Modal
function initSettingsModal() {
  const modal = document.getElementById("settings-modal");
  const openBtn = document.getElementById("settings-open-btn");
  const closeBtn = document.getElementById("close-modal-btn");
  const backdrop = document.getElementById("modal-backdrop");
  const saveBtn = document.getElementById("save-config-btn");

  if (openBtn && modal) openBtn.addEventListener("click", () => modal.classList.remove("hidden"));
  if (closeBtn && modal) closeBtn.addEventListener("click", () => modal.classList.add("hidden"));
  if (backdrop && modal) backdrop.addEventListener("click", () => modal.classList.add("hidden"));

  if (saveBtn) {
    saveBtn.addEventListener("click", async () => {
      const geminiKey = document.getElementById("cfg-gemini-key").value;
      const model = document.getElementById("cfg-gemini-model").value;
      const tgToken = document.getElementById("cfg-tg-token").value;
      const tgUsers = document.getElementById("cfg-tg-users").value;

      try {
        await fetch("/api/config", {
          method: "POST",
          headers: { "Content-Type": "application/json" },
          body: JSON.stringify({
            GEMINI_API_KEY: geminiKey,
            GEMINI_MODEL: model,
            TELEGRAM_BOT_TOKEN: tgToken,
            ALLOWED_TELEGRAM_USER_IDS: tgUsers
          })
        });
        addLog("[LKO_CONFIG] Parameters updated and recalibrated.", "success");
        modal.classList.add("hidden");
        initKeyValidation();
      } catch (err) {
        alert("Calibration Error: " + err.message);
      }
    });
  }
}

// 7. LKO Voice Output (Text-to-Speech)
function initLkoAudio() {
  const voiceBtn = document.getElementById("voice-reply-toggle");
  if (voiceBtn) {
    voiceBtn.addEventListener("click", () => {
      lkoVoiceEnabled = !lkoVoiceEnabled;
      voiceBtn.innerHTML = lkoVoiceEnabled ? "<span>🔊 VOICE: ON</span>" : "<span>🔇 VOICE: OFF</span>";
      voiceBtn.classList.toggle("active", lkoVoiceEnabled);
    });
  }
}

function speakLko(text) {
  if (!lkoVoiceEnabled || !('speechSynthesis' in window)) return;
  try {
    window.speechSynthesis.cancel();
    const cleanText = text.replace(/[*_#`~]/g, '').substring(0, 200);
    const utterance = new SpeechSynthesisUtterance(cleanText);
    
    const voices = window.speechSynthesis.getVoices();
    const deepVoice = voices.find(v => v.lang.includes("en-GB") || v.name.includes("Daniel") || v.name.includes("Arthur") || v.name.includes("Oliver"));
    if (deepVoice) utterance.voice = deepVoice;
    
    utterance.rate = 1.05;
    utterance.pitch = 0.95;
    window.speechSynthesis.speak(utterance);
  } catch (e) {}
}

function addLog(text, level = "info") {
  const feed = document.getElementById("terminal-feed");
  if (!feed) return;
  const now = new Date().toLocaleTimeString();
  const div = document.createElement("div");
  div.className = `log-entry ${level}`;
  div.textContent = `[${now}] ${text}`;
  feed.appendChild(div);
  feed.scrollTop = feed.scrollHeight;
}

window.sendQuickPrompt = function(promptText) {
  const inputEl = document.getElementById("command-input");
  if (inputEl) {
    inputEl.value = promptText;
    document.getElementById("send-btn").click();
  }
};

function escapeHtml(str) {
  return str.replace(/&/g, "&amp;").replace(/</g, "&lt;").replace(/>/g, "&gt;").replace(/"/g, "&quot;");
}

let audioCtx = null;
function playStarkChime(type) {
  try {
    if (!audioCtx) audioCtx = new (window.AudioContext || window.webkitAudioContext)();
    const osc = audioCtx.createOscillator();
    const gain = audioCtx.createGain();
    osc.connect(gain);
    gain.connect(audioCtx.destination);

    if (type === "engage") {
      osc.type = "sine";
      osc.frequency.setValueAtTime(520, audioCtx.currentTime);
      osc.frequency.exponentialRampToValueAtTime(1040, audioCtx.currentTime + 0.14);
      gain.gain.setValueAtTime(0.06, audioCtx.currentTime);
      gain.gain.exponentialRampToValueAtTime(0.001, audioCtx.currentTime + 0.14);
      osc.start();
      osc.stop(audioCtx.currentTime + 0.14);
    } else if (type === "complete") {
      osc.type = "sine";
      osc.frequency.setValueAtTime(880, audioCtx.currentTime);
      osc.frequency.exponentialRampToValueAtTime(1320, audioCtx.currentTime + 0.2);
      gain.gain.setValueAtTime(0.06, audioCtx.currentTime);
      gain.gain.exponentialRampToValueAtTime(0.001, audioCtx.currentTime + 0.2);
      osc.start();
      osc.stop(audioCtx.currentTime + 0.2);
    }
  } catch (e) {}
}
