/**
 * SARAS TACTICAL COMMAND CONSOLE CONTROLLER
 * Real-time WebSocket Client, Geospatial Leaflet Map,
 * MAVLink Status Tracker, and Dual-Mode Swarm Dispatcher.
 */

const state = {
  report: null,
  map: null,
  layers: {
    hazards: null,
    sectors: null,
    drones: null,
    victims: null,
    base: null,
  },
  ws: null,
  isPaused: false,
  mode: "pure_sim",
  droneCount: 4,
  reconnectTimer: null,
  baseLat: 11.5360,
  baseLon: 76.1390,
};

const $ = (selector) => document.querySelector(selector);
const $$ = (selector) => document.querySelectorAll(selector);

// -----------------------------------------------------------------------------
// INITIALIZATION
// -----------------------------------------------------------------------------
function init() {
  initTacticalMap();
  setupEventListeners();
  connectWebSocket();
}

// -----------------------------------------------------------------------------
// LEAFLET GEOSPATIAL MAP INITIALIZATION
// -----------------------------------------------------------------------------
function initTacticalMap() {
  const mapCenter = [state.baseLat, state.baseLon];
  
  state.map = L.map("tactical-map", {
    zoomControl: true,
    attributionControl: false,
    minZoom: 13,
    maxZoom: 18,
  }).setView(mapCenter, 15);

  // CartoDB Dark Matter / Aerospace Dark Tiles
  L.tileLayer("https://{s}.basemaps.cartocdn.com/dark_all/{z}/{x}/{y}{r}.png", {
    maxZoom: 19,
    subdomains: "abcd",
  }).addTo(state.map);

  // Initialize Layer Groups
  state.layers.hazards = L.layerGroup().addTo(state.map);
  state.layers.sectors = L.layerGroup().addTo(state.map);
  state.layers.drones = L.layerGroup().addTo(state.map);
  state.layers.victims = L.layerGroup().addTo(state.map);
  state.layers.base = L.layerGroup().addTo(state.map);

  // Add Rescue HQ Base Marker
  const baseIcon = L.divIcon({
    className: "saras-marker-wrap",
    html: `<div class="base-marker-pin"><span>⌖</span></div>`,
    iconSize: [26, 26],
    iconAnchor: [13, 13],
  });
  
  // Rescue Base Camp at south edge of arena
  const baseLat = state.baseLat - (450.0 / 111000.0);
  const baseLon = state.baseLon - (450.0 / 108750.0);
  L.marker([baseLat, baseLon], { icon: baseIcon })
    .bindTooltip("<b>R-POINT 01 // CHOORALMALA DISASTER HQ</b><br>Triage Center & Mobile Command Post", { direction: "top" })
    .addTo(state.layers.base);
}

// -----------------------------------------------------------------------------
// WEBSOCKET TELEMETRY CLIENT WITH HTTP FALLBACK
// -----------------------------------------------------------------------------
function connectWebSocket() {
  const loc = window.location;
  const proto = loc.protocol === "https:" ? "wss:" : "ws:";
  const host = loc.host || "localhost:8000";
  const wsUrl = `${proto}//${host}/ws/telemetry`;

  try {
    state.ws = new WebSocket(wsUrl);

    state.ws.onopen = () => {
      console.log("[SARAS] WebSocket telemetry link active:", wsUrl);
      $("#stream-rate").textContent = "WEBSOCKET LIVE (8.3 Hz)";
      $(".pulse-indicator").style.background = "var(--phosphor-green)";
    };

    state.ws.onmessage = (event) => {
      try {
        const data = JSON.parse(event.data);
        handleTelemetryUpdate(data);
      } catch (err) {
        console.error("[SARAS] JSON decode error:", err);
      }
    };

    state.ws.onerror = (err) => {
      console.warn("[SARAS] WebSocket error, trying fallback...", err);
      fallbackHttpPoll();
    };

    state.ws.onclose = () => {
      console.warn("[SARAS] WebSocket closed. Retrying in 2 seconds...");
      $("#stream-rate").textContent = "RECONNECTING...";
      $(".pulse-indicator").style.background = "var(--amber-warning)";
      clearTimeout(state.reconnectTimer);
      state.reconnectTimer = setTimeout(connectWebSocket, 2000);
    };
  } catch (e) {
    fallbackHttpPoll();
  }
}

async function fallbackHttpPoll() {
  try {
    const res = await fetch("/api/status");
    if (res.ok) {
      const data = await res.json();
      handleTelemetryUpdate(data);
      $("#stream-rate").textContent = "HTTP REST POLL (1.0 Hz)";
    }
  } catch (err) {
    // Try simulation_report.json directly
    try {
      const res2 = await fetch("../simulation_report.json?t=" + Date.now());
      if (res2.ok) {
        const data2 = await res2.json();
        handleTelemetryUpdate(data2);
      }
    } catch (e) {
      // offline
    }
  }
}

// -----------------------------------------------------------------------------
// TELEMETRY STATE HANDLER
// -----------------------------------------------------------------------------
function handleTelemetryUpdate(report) {
  state.report = report;
  state.mode = report.mode || state.mode;
  state.isPaused = report.is_paused || false;

  const drones = report.drones || [];
  const sectors = report.sectors || [];
  const victims = report.victims || [];
  const hazards = report.hazards || [];
  const metrics = report.metrics || {};

  state.droneCount = drones.length;

  // Update Topbar Readouts
  $("#mission-clock").textContent = `00:${String(metrics.total_steps || 0).padStart(2, "0")}`;
  $("#drone-count-display").textContent = `${drones.length} DRONES`;
  $("#coverage-val").textContent = `${Math.round((report.coverage_ratio || 0) * 100)}%`;
  $("#coverage-fill").style.width = `${Math.round((report.coverage_ratio || 0) * 100)}%`;
  
  const detectedCount = victims.filter(v => v.detected).length;
  $("#detected-val").textContent = `${detectedCount} / ${victims.length}`;
  $("#hazards-val").textContent = `${hazards.length} ACTIVE`;
  $("#reassignments-val").textContent = metrics.reassigned_sectors || 0;
  
  $("#grid-status").textContent = `${report.sectors?.length || 9} SECTORS`;
  $("#roster-active-badge").textContent = `${drones.filter(d => d.health === 'active').length}/${drones.length} ONLINE`;
  $("#hazard-count-badge").textContent = `${hazards.length} IDENTIFIED`;
  $("#triage-count-badge").textContent = `${detectedCount} LOCATED`;

  // MAVLink / Hardware Status
  const mavlinkConnected = report.mavlink_connected || report.mavlink_status?.connected || false;
  const mavDot = $("#mavlink-dot");
  const mavTxt = $("#mavlink-status");
  if (mavlinkConnected) {
    mavDot.classList.add("connected");
    mavTxt.textContent = "ONLINE (LIVE)";
    mavTxt.style.color = "var(--phosphor-green)";
  } else {
    mavDot.classList.remove("connected");
    mavTxt.textContent = "STANDBY";
    mavTxt.style.color = "var(--text-muted)";
  }

  // Update Mode Switcher Visual State
  updateModeUI(state.mode);

  // Update Pause Button Text
  $("#pause-btn").textContent = state.isPaused ? "RESUME" : "PAUSE";
  $("#pause-btn").style.background = state.isPaused ? "var(--amber-warning)" : "var(--phosphor-green)";

  // Update Drone-01 Video Feed Overlay Telemetry
  if (drones.length > 0) {
    const d1 = drones[0];
    $("#hud-flight-data").textContent = `ALT: ${d1.altitude}M | SPD: ${d1.speed}M/S | BATT: ${Math.round(d1.battery)}%`;
    $("#hud-target-gps").textContent = `${d1.lat}°N, ${d1.lon}°E`;
    if (state.mode === "hybrid_real") {
      $("#video-node-badge").textContent = "NODE D1 [PHYSICAL]";
      $("#video-node-badge").className = "badge cyan-badge";
      $("#hud-cam-source").textContent = d1.telemetry_source === "mavlink" ? "MAVLINK MISSION PLANNER EO/IR" : "AERIAL SAR TEST FEED (480P)";
    } else {
      $("#video-node-badge").textContent = "NODE D1 [SIMULATED]";
      $("#video-node-badge").className = "badge slate-badge";
      $("#hud-cam-source").textContent = "VIRTUAL SENSOR EMULATION";
    }
  }

  // Render Map & Roster Panels
  renderMap(report);
  renderDroneRoster(drones);
  renderHazards(hazards);
  renderVictims(report.rescue_recommendations || [], victims);

  // Update AI Recommendation Text
  const topRec = report.rescue_recommendations?.[0];
  if (topRec) {
    $("#ai-recommendation").textContent = 
      `Dispatch ${topRec.drone_id} to ${topRec.victim_id} immediately; ${topRec.rationale}. Estimated distance: ${topRec.estimated_distance}m.`;
  } else {
    $("#ai-recommendation").textContent = 
      `Swarm executing auction sector sweep across Chooralmala debris perimeter. All airframes maintaining altitude.`;
  }
}

// -----------------------------------------------------------------------------
// MAP RENDERING (HAZARDS, SECTORS, DRONES, VICTIMS)
// -----------------------------------------------------------------------------
function renderMap(report) {
  if (!state.map) return;

  // 1. Render Hazards
  state.layers.hazards.clearLayers();
  (report.hazards || []).forEach((h) => {
    let color = "#f59e0b";
    let fillColor = "#f59e0b";
    let fillOpacity = 0.15;
    let dashArray = null;

    if (h.hazard_type === "landslide_debris") {
      color = "#d97706";
      fillColor = "#b45309";
      fillOpacity = 0.22;
      dashArray = "6, 6";
    } else if (h.hazard_type === "smoke_plume") {
      color = "#94a3b8";
      fillColor = "#64748b";
      fillOpacity = 0.35;
    } else if (h.hazard_type === "wind_shear") {
      color = "#38bdf8";
      fillColor = "#0284c7";
      fillOpacity = 0.15;
    } else if (h.hazard_type === "fire_hotspot") {
      color = "#ef4444";
      fillColor = "#dc2626";
      fillOpacity = 0.30;
    }

    const circle = L.circle([h.lat, h.lon], {
      radius: h.radius,
      color: color,
      weight: 1.5,
      dashArray: dashArray,
      fillColor: fillColor,
      fillOpacity: fillOpacity,
    }).bindTooltip(`<b>${h.hazard_id}</b><br>${h.description}<br>Severity: ${Math.round(h.severity * 100)}%`, { sticky: true });
    
    circle.addTo(state.layers.hazards);
  });

  // 2. Render Sectors
  state.layers.sectors.clearLayers();
  (report.sectors || []).forEach((sec) => {
    const halfLat = (sec.height / 2.0) / 111000.0;
    const halfLon = (sec.width / 2.0) / 108750.0;
    const bounds = [
      [sec.lat - halfLat, sec.lon - halfLon],
      [sec.lat + halfLat, sec.lon + halfLon]
    ];

    let borderColor = "#334155";
    let fill = "#00e599";
    let fillOp = 0.04;

    if (sec.status === "covered") {
      borderColor = "#00e599";
      fill = "#00e599";
      fillOp = 0.18;
    } else if (sec.status === "locked") {
      borderColor = "#ef4444";
      fill = "#ef4444";
      fillOp = 0.22;
    } else if (sec.status === "assigned") {
      borderColor = "#38bdf8";
      fill = "#38bdf8";
      fillOp = 0.10;
    }

    L.rectangle(bounds, {
      color: borderColor,
      weight: 1,
      fillColor: fill,
      fillOpacity: fillOp,
    }).bindTooltip(`<b>SECTOR ${sec.sector_id}</b><br>Assigned: ${sec.assigned_to || 'None'}<br>Sweep: ${Math.round(sec.completion * 100)}%<br>Status: ${sec.status.toUpperCase()}`, { sticky: true })
      .addTo(state.layers.sectors);

    // Sector Label Marker
    L.marker([sec.lat, sec.lon], {
      icon: L.divIcon({
        className: "saras-marker-wrap",
        html: `<div class="sector-tag">${sec.sector_id}</div>`,
        iconSize: [32, 16],
        iconAnchor: [16, 8],
      }),
    }).addTo(state.layers.sectors);
  });

  // 3. Render Drones
  state.layers.drones.clearLayers();
  (report.drones || []).forEach((d) => {
    const isPhys = d.is_physical || false;
    const pinClass = `saras-drone-pin ${isPhys ? 'physical' : ''} ${d.health}`;
    const glyph = isPhys ? "◈" : d.drone_id.replace("D", "");

    const droneIcon = L.divIcon({
      className: "saras-marker-wrap",
      html: `<div class="${pinClass}"><span>${glyph}</span></div>`,
      iconSize: [28, 28],
      iconAnchor: [14, 14],
    });

    const marker = L.marker([d.lat, d.lon], { icon: droneIcon })
      .bindPopup(`
        <div style="font-family:'JetBrains Mono',monospace;font-size:11px;color:#f1f5f9;background:#0d121a;padding:4px;">
          <b style="color:${isPhys ? 'var(--cyan-telemetry)' : 'var(--phosphor-green)'}">${d.drone_id} [${isPhys ? 'PHYSICAL NODE' : 'VIRTUAL SWARM'}]</b><br>
          Status: <strong>${d.health.toUpperCase()}</strong><br>
          Battery: <strong>${Math.round(d.battery)}%</strong><br>
          Altitude: <strong>${d.altitude}m AGL</strong><br>
          Speed: <strong>${d.speed} m/s</strong><br>
          Heading: <strong>${d.heading}°</strong><br>
          Sector: <strong>${d.sector_id || 'UNASSIGNED'}</strong><br>
          Telemetry: <strong>${d.telemetry_source.toUpperCase()}</strong>
        </div>
      `)
      .addTo(state.layers.drones);
  });

  // 4. Render Victims
  state.layers.victims.clearLayers();
  (report.victims || []).forEach((v) => {
    if (!v.detected) return;
    const vIcon = L.divIcon({
      className: "saras-marker-wrap",
      html: `<div class="victim-marker-pin">!</div>`,
      iconSize: [22, 22],
      iconAnchor: [11, 11],
    });

    L.marker([v.lat, v.lon], { icon: vIcon })
      .bindPopup(`
        <div style="font-family:'JetBrains Mono',monospace;font-size:11px;color:#f1f5f9;background:#0d121a;padding:4px;">
          <b style="color:var(--alert-red)">VICTIM ${v.victim_id}</b><br>
          Severity: <strong style="color:var(--alert-red)">${v.severity.toUpperCase()}</strong><br>
          Rescue Priority: <strong>P${v.rescue_priority}</strong><br>
          Coordinates: <strong>${v.lat}°N, ${v.lon}°E</strong>
        </div>
      `)
      .addTo(state.layers.victims);
  });
}

// -----------------------------------------------------------------------------
// FLEET ROSTER PANEL RENDERER
// -----------------------------------------------------------------------------
function renderDroneRoster(drones) {
  const container = $("#drone-roster");
  if (!container) return;

  container.innerHTML = drones.map((d) => {
    const isPhys = d.is_physical;
    const nodeBadge = isPhys 
      ? `<span class="node-badge">PHYSICAL EO/IR</span>` 
      : `<span class="node-badge" style="background:rgba(100,116,139,0.2);color:#94a3b8">VIRTUAL</span>`;
    
    const battClass = d.battery < 25 ? "low" : "";
    const cardClass = isPhys ? "physical-node" : d.health;

    return `
      <div class="drone-card ${cardClass}">
        <div class="drone-icon-box">${d.drone_id}</div>
        <div class="drone-info">
          <strong>${d.drone_id} ${nodeBadge}</strong>
          <small>SECTOR: ${d.sector_id || 'STANDBY'} · ALT: ${d.altitude}M · ${d.speed}M/S</small>
        </div>
        <div class="drone-status-col">
          <span class="status-txt ${d.health}">${d.health}</span>
          <div class="batt-gauge" title="Battery: ${Math.round(d.battery)}%">
            <div class="batt-fill ${battClass}" style="width:${Math.round(d.battery)}%"></div>
          </div>
        </div>
      </div>
    `;
  }).join("");
}

// -----------------------------------------------------------------------------
// HAZARD LIST RENDERER
// -----------------------------------------------------------------------------
function renderHazards(hazards) {
  const container = $("#hazard-roster");
  if (!container) return;

  container.innerHTML = hazards.map((h) => {
    let iconClass = "h-debris";
    let glyph = "▲";
    if (h.hazard_type === "smoke_plume") { iconClass = "h-smoke"; glyph = "☁"; }
    else if (h.hazard_type === "wind_shear") { iconClass = "h-wind"; glyph = "⇄"; }
    else if (h.hazard_type === "fire_hotspot") { iconClass = "h-thermal"; glyph = "♨"; }

    return `
      <div class="hazard-card">
        <div class="hazard-icon-box ${iconClass}">${glyph}</div>
        <div class="hazard-desc">
          <strong>${h.hazard_id}</strong>
          <small>${h.description} · RAD: ${h.radius}M</small>
        </div>
        <div class="hazard-severity">
          ${Math.round(h.severity * 100)}% RISK
        </div>
      </div>
    `;
  }).join("");
}

// -----------------------------------------------------------------------------
// VICTIM TRIAGE LIST RENDERER
// -----------------------------------------------------------------------------
function renderVictims(recommendations, allVictims) {
  const container = $("#victim-roster");
  if (!container) return;

  const detected = (allVictims || []).filter(v => v.detected);
  if (detected.length === 0) {
    container.innerHTML = `<p style="padding:14px;font-family:var(--font-mono);font-size:10px;color:var(--text-muted);">No confirmed human detections in active sectors yet.</p>`;
    return;
  }

  container.innerHTML = detected.map((v) => {
    const prioClass = `prio-${v.severity.toLowerCase()}`;
    const rec = recommendations.find(r => r.victim_id === v.victim_id);
    const dist = rec ? `${rec.estimated_distance}m` : "~120m";
    const assigned = rec ? `DISPATCH ${rec.drone_id}` : "QUEUED";

    return `
      <div class="victim-card">
        <div class="victim-prio-badge ${prioClass}">P${v.rescue_priority}</div>
        <div class="victim-details">
          <strong>${v.victim_id} // ${v.severity.toUpperCase()} PRIORITY</strong>
          <small>SECTOR: ${v.sector_id || 'UNKNOWN'} · TARGET DISTANCE: ${dist}</small>
        </div>
        <div class="victim-meta">
          <strong>${assigned}</strong>
        </div>
      </div>
    `;
  }).join("");
}

// -----------------------------------------------------------------------------
// EVENT LISTENERS & OPERATOR CONTROLS
// -----------------------------------------------------------------------------
function setupEventListeners() {
  // Mode Switcher Buttons
  $("#mode-pure-sim").addEventListener("click", () => switchMode("pure_sim"));
  $("#mode-hybrid-real").addEventListener("click", () => switchMode("hybrid_real"));

  // Fleet Size Stepper
  $("#drone-dec").addEventListener("click", () => adjustDroneCount(state.droneCount - 1));
  $("#drone-inc").addEventListener("click", () => adjustDroneCount(state.droneCount + 1));

  // Control Action Buttons
  $("#pause-btn").addEventListener("click", togglePause);
  $("#reassign-btn").addEventListener("click", triggerReassignment);
  $("#reset-btn").addEventListener("click", resetMission);

  // Toggle Video Height
  $("#toggle-video-btn").addEventListener("click", () => {
    const wrap = $("#video-wrap");
    const btn = $("#toggle-video-btn");
    if (wrap.style.display === "none") {
      wrap.style.display = "flex";
      btn.textContent = "COLLAPSE";
    } else {
      wrap.style.display = "none";
      btn.textContent = "EXPAND";
    }
  });

  // Knowledge Agent Form
  $("#agent-form").addEventListener("submit", (e) => {
    e.preventDefault();
    const query = $("#agent-input").value.trim();
    if (query) {
      askAgent(query);
    }
  });

  // Quick Query Chips
  $$(".quick-chip").forEach((chip) => {
    chip.addEventListener("click", () => {
      const q = chip.dataset.q;
      $("#agent-input").value = q;
      askAgent(q);
    });
  });
}

function updateModeUI(mode) {
  if (mode === "hybrid_real") {
    $("#mode-hybrid-real").classList.add("active");
    $("#mode-pure-sim").classList.remove("active");
    $("#video-panel").style.display = "block";
  } else {
    $("#mode-pure-sim").classList.add("active");
    $("#mode-hybrid-real").classList.remove("active");
  }
}

async function switchMode(mode) {
  try {
    const res = await fetch("/api/mode", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ mode: mode }),
    });
    if (res.ok) {
      showToast(`Operating Mode: ${mode === 'hybrid_real' ? 'HYBRID REAL (1 Physical + N Virtual)' : 'PURE SIMULATION'}`);
    }
  } catch (err) {
    console.error(err);
  }
}

async function adjustDroneCount(count) {
  const newCount = Math.max(1, Math.min(10, count));
  try {
    const res = await fetch("/api/drones/count", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ count: newCount }),
    });
    if (res.ok) {
      showToast(`Fleet adjusted to ${newCount} drones`);
    }
  } catch (err) {
    console.error(err);
  }
}

async function togglePause() {
  const cmd = state.isPaused ? "resume" : "pause";
  sendCommand(cmd);
}

async function triggerReassignment() {
  sendCommand("reassign");
  showToast("Swarm auction re-bid triggered");
}

async function resetMission() {
  sendCommand("reset");
  showToast("Mission reset to initial state");
}

async function sendCommand(command) {
  try {
    await fetch("/api/command", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ command: command }),
    });
  } catch (err) {
    console.error(err);
  }
}

async function askAgent(query) {
  const box = $("#agent-response");
  const content = $("#agent-response-text");
  content.textContent = "Retrieving disaster SAR procedure...";
  box.style.display = "block";

  try {
    const res = await fetch("/api/agent/query", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ query: query }),
    });
    if (res.ok) {
      const data = await res.json();
      content.textContent = data.answer;
    } else {
      content.textContent = "Error communicating with knowledge agent.";
    }
  } catch (e) {
    content.textContent = "Agent service currently offline.";
  }
}

function showToast(message) {
  const toast = $("#toast-notice");
  toast.textContent = message;
  toast.classList.add("show");
  setTimeout(() => toast.classList.remove("show"), 2500);
}

// Launch on DOM ready
document.addEventListener("DOMContentLoaded", init);
