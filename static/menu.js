// LKO Aerolite Menu Controller - Native REST Bridge

document.addEventListener("DOMContentLoaded", () => {
  initMenuActions();
  initLiveTelemetry();
});

function showToast(text) {
  const toast = document.getElementById("toast-notify");
  if (!toast) return;
  toast.textContent = text;
  toast.classList.remove("hidden");
  setTimeout(() => {
    toast.classList.add("hidden");
  }, 2200);
}

function initMenuActions() {
  const btnDashboard = document.getElementById("btn-open-dashboard");
  const btnSlack = document.getElementById("btn-slack-dispatch");
  const slackDrawer = document.getElementById("slack-drawer");
  const slackChevron = document.getElementById("slack-chevron");
  const slackInput = document.getElementById("slack-input");
  const slackSubmit = document.getElementById("slack-submit-btn");

  const btnOptical = document.getElementById("btn-optical-scan");
  const badgeOptical = document.getElementById("badge-optical");

  const btnMobile = document.getElementById("btn-copy-mobile");
  const badgeMobile = document.getElementById("badge-mobile-status");

  const btnNeural = document.getElementById("btn-neural-engine");
  const badgeNeural = document.getElementById("badge-neural");

  const btnDaemon = document.getElementById("btn-toggle-daemon");
  const badgeDaemon = document.getElementById("badge-daemon");

  const btnSettings = document.getElementById("btn-open-settings");

  // 1. Open Dashboard in Brave
  if (btnDashboard) {
    btnDashboard.addEventListener("click", async () => {
      showToast("Launching HUD in Brave...");
      try {
        await fetch("/api/open-hud", { method: "POST" });
      } catch (e) {
        window.open("/", "_blank");
      }
    });
  }

  // 2. Slack Protocol & Inline Drawer
  if (btnSlack && slackDrawer) {
    btnSlack.addEventListener("click", () => {
      const isHidden = slackDrawer.classList.contains("hidden");
      slackDrawer.classList.toggle("hidden", !isHidden);
      if (slackChevron) slackChevron.classList.toggle("rotated", isHidden);
      if (isHidden && slackInput) slackInput.focus();
    });
  }

  async function handleSlackSend() {
    const raw = slackInput.value.trim();
    if (!raw) return;
    
    let target = "general";
    let text = raw;
    if (raw.includes(":")) {
      const parts = raw.split(":");
      target = parts[0].trim();
      text = parts.slice(1).join(":").trim();
    }

    showToast(`Dispatching to #${target}...`);
    slackInput.value = "";
    slackDrawer.classList.add("hidden");
    if (slackChevron) slackChevron.classList.remove("rotated");

    try {
      await fetch("/api/chat", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ message: `Send a message "${text}" to ${target} on Slack` })
      });
      showToast("Slack message transmitted!");
    } catch (e) {
      showToast("Transmission anomaly");
    }
  }

  if (slackSubmit) slackSubmit.addEventListener("click", handleSlackSend);
  if (slackInput) {
    slackInput.addEventListener("keydown", (e) => {
      if (e.key === "Enter") handleSlackSend();
    });
  }

  // 3. Optical Screen Vision
  if (btnOptical) {
    btnOptical.addEventListener("click", async () => {
      if (badgeOptical) badgeOptical.textContent = "SCANNING...";
      showToast("Scanning Optical Frame...");
      try {
        await fetch("/api/screenshot");
        showToast("Screen Captured & Analyzed!");
      } catch (e) {
        showToast("Scan Error");
      } finally {
        if (badgeOptical) badgeOptical.textContent = "SCAN";
      }
    });
  }

  // 4. Copy Mobile Uplink
  if (btnMobile) {
    btnMobile.addEventListener("click", async () => {
      try {
        const res = await fetch("/api/copy-tunnel", { method: "POST" });
        const data = await res.json();
        if (badgeMobile) {
          badgeMobile.textContent = "COPIED!";
          setTimeout(() => { badgeMobile.textContent = "ONLINE"; }, 2000);
        }
        showToast("Mobile Link Copied to Clipboard!");
      } catch (e) {
        showToast("Link Copy Error");
      }
    });
  }

  // 5. Neural Engine Info
  if (btnNeural) {
    btnNeural.addEventListener("click", async () => {
      showToast("Validating Neural Engine...");
      try {
        const res = await fetch("/api/validate-key");
        const data = await res.json();
        if (data.valid) {
          showToast(`Engine: ${data.model}`);
        } else {
          showToast("Key Calibration Needed");
        }
      } catch (e) {}
    });
  }

  // 6. 24/7 Autostart Daemon Toggle
  if (btnDaemon) {
    btnDaemon.addEventListener("click", async () => {
      try {
        const res = await fetch("/api/toggle-daemon", { method: "POST" });
        const data = await res.json();
        if (badgeDaemon) {
          badgeDaemon.textContent = data.active ? "ON" : "OFF";
          badgeDaemon.className = data.active ? "nav-badge green" : "nav-badge";
        }
        showToast(data.active ? "24/7 Daemon: Enabled" : "24/7 Daemon: Disabled");
      } catch (e) {
        showToast("Toggle Error");
      }
    });
  }

  // 7. Settings (.env)
  if (btnSettings) {
    btnSettings.addEventListener("click", async () => {
      showToast("Opening System Config (.env)...");
      try {
        await fetch("/api/open-env", { method: "POST" });
      } catch (e) {
        window.open("/", "_blank");
      }
    });
  }
}

// Live Radar & Diagnostics Poller
function initLiveTelemetry() {
  const nodeApp = document.getElementById("radar-app-name");
  const nodeBatt = document.getElementById("radar-battery-val");
  const footApp = document.getElementById("foot-app");
  const footVol = document.getElementById("foot-vol");
  const badgeDaemon = document.getElementById("badge-daemon");

  async function poll() {
    try {
      const res = await fetch("/api/system-status");
      if (!res.ok) return;
      const data = await res.json();

      const app = data.active_application || "Finder";
      const vol = data.volume_percent !== undefined ? data.volume_percent : "50";
      
      let batt = "85%";
      if (data.battery_info) {
        const m = data.battery_info.match(/(\d+)%/);
        if (m) batt = `${m[1]}%`;
      }

      if (nodeApp) nodeApp.textContent = app.substring(0, 9);
      if (nodeBatt) nodeBatt.textContent = batt;
      if (footApp) footApp.textContent = app.substring(0, 11);
      if (footVol) footVol.textContent = `${vol}%`;

      if (badgeDaemon && data.daemon_active !== undefined) {
        badgeDaemon.textContent = data.daemon_active ? "ON" : "OFF";
        badgeDaemon.className = data.daemon_active ? "nav-badge green" : "nav-badge";
      }
    } catch (e) {}
  }

  poll();
  setInterval(poll, 3500);
}
