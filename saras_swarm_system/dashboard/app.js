// SARAS Mission Control Dashboard Application Logic
let map;
let droneMarkers = {};
let droneFootprints = {};
let droneTrails = {};
let droneHistories = {};
let sectorLayers = {};
let victimMarkers = {};
let hazardLayers = {};
let wsTelemetry;
let currentPolicy = "AUCTION";
let currentSystemMode = "pure_sim";
let isPaused = false;
let missionSeconds = 0;
let hasAutoFitted = false;
let isConnected = false;

// Dynamic URL resolver: supports http://localhost:8000, 127.0.0.1, or direct file:// openings
function getBackendUrls() {
    const isFile = window.location.protocol === "file:";
    const host = (isFile || !window.location.host || window.location.port !== "8000")
        ? "127.0.0.1:8000"
        : window.location.host;
    const httpProto = window.location.protocol === "https:" ? "https:" : "http:";
    const wsProto = window.location.protocol === "https:" ? "wss:" : "ws:";
    return {
        httpBase: `${httpProto}//${host}`,
        wsTelemetry: `${wsProto}//${host}/ws/telemetry`,
        wsAlerts: `${wsProto}//${host}/ws/alerts`
    };
}

document.addEventListener("DOMContentLoaded", () => {
    initMap();
    initTelemetryWebSocket();
    initMissionClock();
    initContinuousGpsAnalysis();   // Always-on background GPS spatial analysis
    fetchSwarmStatus();
    setInterval(fetchSwarmStatus, 1500); // Polling backup (1.5s interval)
});

function initMissionClock() {
    setInterval(() => {
        if (!isPaused) {
            missionSeconds++;
            const mins = String(Math.floor(missionSeconds / 60)).padStart(2, '0');
            const secs = String(missionSeconds % 60).padStart(2, '0');
            const clockEl = document.getElementById("mission-clock");
            if (clockEl) clockEl.textContent = `${mins}:${secs}`;
        }
    }, 1000);
}

// =============================================================================
// CONTINUOUS REAL-TIME GPS SPATIAL ANALYSIS ENGINE
// Starts a watchPosition on page load, never stops, analyses operator position
// against disaster coordinates, hazard zones, and incident perimeter.
// =============================================================================

const INCIDENT_CENTER = { lat: 11.5360, lon: 76.1390, name: "Chooralmala Incident HQ" };
const WAYANAD_HAZARDS_GPS = [
    { id: "HAZ-01", name: "Chooralmala Mudflow", lat: 11.5375, lon: 76.1385, radius: 140, type: "landslide_debris" },
    { id: "HAZ-02", name: "Meppadi Smoke Plume", lat: 11.5340, lon: 76.1415, radius: 95, type: "smoke_plume" },
    { id: "HAZ-03", name: "Transformer Fire",    lat: 11.5388, lon: 76.1420, radius: 60, type: "fire_hotspot" },
    { id: "HAZ-04", name: "Vellarimala Wind Shear", lat: 11.5320, lon: 76.1360, radius: 180, type: "wind_shear" },
];

let gpsWatchId = null;
let lastGpsCoords = null;
let gpsRetryTimer = null;

function haversineGps(lat1, lon1, lat2, lon2) {
    const R = 6371000; // metres
    const phi1 = lat1 * Math.PI / 180;
    const phi2 = lat2 * Math.PI / 180;
    const dphi = (lat2 - lat1) * Math.PI / 180;
    const dlam = (lon2 - lon1) * Math.PI / 180;
    const a = Math.sin(dphi / 2) ** 2 + Math.cos(phi1) * Math.cos(phi2) * Math.sin(dlam / 2) ** 2;
    return R * 2 * Math.atan2(Math.sqrt(a), Math.sqrt(1 - a));
}

function fmtDist(m) {
    if (m >= 1000) return `${(m / 1000).toFixed(2)} km`;
    return `${Math.round(m)} m`;
}

function analyseGpsPosition(lat, lon, accuracy) {
    lastGpsCoords = { lat, lon, accuracy };

    // ── Element refs ───────────────────────────────────────────────────────────
    const el = (id) => document.getElementById(id);

    // ── Update raw coordinate readouts ────────────────────────────────────────
    if (el("gps-val-lat"))      el("gps-val-lat").textContent      = `${lat.toFixed(5)}°N`;
    if (el("gps-val-lon"))      el("gps-val-lon").textContent      = `${lon.toFixed(5)}°E`;
    if (el("gps-val-accuracy")) el("gps-val-accuracy").textContent = `±${Math.round(accuracy)} m`;
    if (el("gps-val-status")) {
        el("gps-val-status").textContent = "LIVE LOCK";
        el("gps-val-status").className   = "highlight-safe";
    }

    // ── Status dot → green ─────────────────────────────────────────────────────
    const dot  = el("gps-status-dot");
    const ring = el("gps-ping-ring");
    if (dot)  dot.style.background  = "var(--status-success)";
    if (ring) ring.style.borderColor = "var(--status-success)";

    // ── Distance from incident HQ ──────────────────────────────────────────────
    const distIncident = haversineGps(lat, lon, INCIDENT_CENTER.lat, INCIDENT_CENTER.lon);
    if (el("gps-val-dist-incident")) {
        el("gps-val-dist-incident").textContent = fmtDist(distIncident);
        el("gps-val-dist-incident").className =
            distIncident < 500  ? "highlight-danger" :
            distIncident < 2000 ? "highlight-warn"   : "highlight-safe";
    }

    // ── Nearest hazard analysis ────────────────────────────────────────────────
    let nearestHaz = null, nearestDist = Infinity;
    WAYANAD_HAZARDS_GPS.forEach(h => {
        const d = haversineGps(lat, lon, h.lat, h.lon);
        if (d < nearestDist) { nearestDist = d; nearestHaz = h; }
    });

    const hazardEl = el("gps-val-nearest-hazard");
    if (hazardEl && nearestHaz) {
        const insideHazard = nearestDist <= nearestHaz.radius;
        hazardEl.innerHTML = insideHazard
            ? `<span class="highlight-danger">⚠ INSIDE ${nearestHaz.name.toUpperCase()} (${fmtDist(nearestDist)})</span>`
            : `${nearestHaz.name}<br><small style="color:var(--muted-foreground)">${fmtDist(nearestDist)} away</small>`;
    }

    // ── Spatial context string ─────────────────────────────────────────────────
    let context = "";
    if (nearestHaz && nearestDist <= nearestHaz.radius) {
        context = `⚠ DANGER: Operator is INSIDE ${nearestHaz.name}. Evacuate immediately.`;
    } else if (distIncident < 500) {
        context = `⚡ CRITICAL ZONE: ${fmtDist(distIncident)} from incident HQ. Maintain safety protocols.`;
    } else if (distIncident < 2000) {
        context = `Operator in outer perimeter, ${fmtDist(distIncident)} from Chooralmala incident centre.`;
    } else if (distIncident < 50000) {
        context = `Operator in Wayanad District, ${fmtDist(distIncident)} from incident HQ. Approaching disaster zone.`;
    } else {
        context = `Remote operator — ${fmtDist(distIncident)} from Wayanad Chooralmala incident zone.`;
    }

    const ctxEl = el("gps-val-context");
    if (ctxEl) {
        ctxEl.textContent = context;
        ctxEl.style.color = nearestHaz && nearestDist <= nearestHaz.radius
            ? "var(--destructive)"
            : distIncident < 500 ? "var(--status-warning)" : "var(--foreground)";
    }

    // ── Update GCS marker on map ───────────────────────────────────────────────
    if (map) {
        const gcsIconHtml = `
            <div class="gcs-marker-beacon">
                <div class="gcs-pulse-ring"></div>
                <div class="gcs-center-pin">📡</div>
            </div>`;
        const gcsIcon = L.divIcon({
            className: "gcs-map-marker",
            html: gcsIconHtml,
            iconSize: [28, 28],
            iconAnchor: [14, 14]
        });
        if (userGpsMarker) {
            userGpsMarker.setLatLng([lat, lon]);
            if (userGpsCircle) { userGpsCircle.setLatLng([lat, lon]); userGpsCircle.setRadius(accuracy); }
        } else {
            userGpsMarker = L.marker([lat, lon], { icon: gcsIcon, zIndexOffset: 2000 }).addTo(map);
            userGpsCircle = L.circle([lat, lon], {
                radius: accuracy, color: "#38bdf8", fillColor: "#38bdf8",
                fillOpacity: 0.10, weight: 1.5, dashArray: "4, 4"
            }).addTo(map);
        }
        userGpsMarker.bindTooltip(
            `<b>📡 OPERATOR GCS</b><br>${lat.toFixed(5)}°N, ${lon.toFixed(5)}°E<br>±${Math.round(accuracy)}m accuracy`,
            { sticky: true }
        );
    }

    // ── Show GPS banner once ───────────────────────────────────────────────────
    showGpsBanner(lat, lon, accuracy);
}

function initContinuousGpsAnalysis() {
    if (!navigator.geolocation) {
        setGpsDockError("Geolocation API not supported in this browser.");
        return;
    }

    // watchPosition keeps firing every time position changes (or improves accuracy)
    gpsWatchId = navigator.geolocation.watchPosition(
        (position) => {
            if (gpsRetryTimer) { clearTimeout(gpsRetryTimer); gpsRetryTimer = null; }
            analyseGpsPosition(
                position.coords.latitude,
                position.coords.longitude,
                position.coords.accuracy || 15
            );
        },
        (error) => {
            console.warn("[GPS] watchPosition error:", error.message);
            setGpsDockError(error.code === 1 ? "Permission denied — allow location access." :
                            error.code === 2 ? "Position unavailable — check device GPS." :
                            "GPS timeout — retrying...");
            // Retry watchPosition silently every 10 seconds after failure
            gpsRetryTimer = setTimeout(initContinuousGpsAnalysis, 10000);
        },
        { enableHighAccuracy: true, timeout: 15000, maximumAge: 5000 }
    );
}

function setGpsDockError(msg) {
    const dot = document.getElementById("gps-status-dot");
    const ring = document.getElementById("gps-ping-ring");
    const status = document.getElementById("gps-val-status");
    const ctx = document.getElementById("gps-val-context");
    if (dot)    dot.style.background   = "var(--destructive)";
    if (ring)   ring.style.borderColor  = "var(--destructive)";
    if (status) { status.textContent = "ERROR"; status.className = "highlight-danger"; }
    if (ctx)    { ctx.textContent = msg; ctx.style.color = "var(--destructive)"; }
}

function triggerManualGpsRefresh() {
    // Stop old watch and restart fresh
    if (gpsWatchId !== null) { navigator.geolocation.clearWatch(gpsWatchId); gpsWatchId = null; }
    const status = document.getElementById("gps-val-status");
    const ctx = document.getElementById("gps-val-context");
    if (status) { status.textContent = "REACQUIRING..."; status.className = ""; }
    if (ctx) ctx.textContent = "Re-acquiring GPS fix...";
    initContinuousGpsAnalysis();
}

function flyMapToGps() {
    if (!lastGpsCoords || !map) return;
    map.flyTo([lastGpsCoords.lat, lastGpsCoords.lon], 17, { duration: 1.5 });
}

async function switchSystemMode(mode) {
    try {
        const urls = getBackendUrls();
        const res = await fetch(`${urls.httpBase}/api/mode`, {
            method: "POST",
            headers: { "Content-Type": "application/json" },
            body: JSON.stringify({ mode: mode })
        });
        const data = await res.json();
        if (data.status === "ok") {
            currentSystemMode = data.mode;
            updateModeButtons(currentSystemMode);
        }
    } catch (e) {
        console.error("Failed to switch mode:", e);
    }
}

function updateModeButtons(mode) {
    const btnSim = document.getElementById("mode-pure-sim");
    const btnHybrid = document.getElementById("mode-hybrid-real");
    if (btnSim && btnHybrid) {
        if (mode === "hybrid_real") {
            btnHybrid.classList.add("active");
            btnSim.classList.remove("active");
        } else {
            btnSim.classList.add("active");
            btnHybrid.classList.remove("active");
        }
    }
}

async function toggleMissionPause() {
    const urls = getBackendUrls();
    const cmd = isPaused ? "resume" : "pause";
    try {
        const res = await fetch(`${urls.httpBase}/api/command`, {
            method: "POST",
            headers: { "Content-Type": "application/json" },
            body: JSON.stringify({ command: cmd })
        });
        const data = await res.json();
        isPaused = data.is_paused !== undefined ? data.is_paused : !isPaused;
        updatePauseButton(isPaused);
    } catch (e) {
        console.error("Pause/resume command error:", e);
    }
}

function updatePauseButton(paused) {
    const btn = document.getElementById("pause-btn");
    const txt = document.getElementById("pause-btn-text");
    if (txt) txt.textContent = paused ? "RESUME" : "PAUSE";
    if (btn) {
        if (paused) {
            btn.classList.add("active");
        } else {
            btn.classList.remove("active");
        }
    }
}

async function triggerSwarmRebid() {
    const urls = getBackendUrls();
    try {
        await fetch(`${urls.httpBase}/api/command`, {
            method: "POST",
            headers: { "Content-Type": "application/json" },
            body: JSON.stringify({ command: "rebid" })
        });
    } catch (e) {
        console.error("Rebid error:", e);
    }
}

const DEFAULT_MAPBOX_TOKEN = localStorage.getItem("saras_mapbox_token") || "";

let allMapLayers = {};
let currentMapLayerKey = "google-hybrid";
let userGpsMarker = null;
let userGpsCircle = null;
let userGpsCoords = null;

function initMap() {
    // Default Staging center (Wayanad Chooralmala disaster search area)
    const center = [11.5360, 76.1390];
    map = L.map("map", {
        center: center,
        zoom: 15,
        zoomControl: true,
        attributionControl: false
    });

    const mapboxToken = localStorage.getItem("saras_mapbox_token") || DEFAULT_MAPBOX_TOKEN;

    // 1. Google Maps Hybrid HD (Photorealistic satellite imagery + street and locality overlays)
    allMapLayers["google-hybrid"] = L.tileLayer(
        "https://mt1.google.com/vt/lyrs=y&x={x}&y={y}&z={z}",
        { maxZoom: 22, subdomains: ["mt0", "mt1", "mt2", "mt3"], attribution: "© Google Maps" }
    );

    // 2. Google Maps Pure Satellite
    allMapLayers["google-satellite"] = L.tileLayer(
        "https://mt1.google.com/vt/lyrs=s&x={x}&y={y}&z={z}",
        { maxZoom: 22, subdomains: ["mt0", "mt1", "mt2", "mt3"], attribution: "© Google Maps" }
    );

    // 3. Google Maps Standard Roadmap
    allMapLayers["google-roadmap"] = L.tileLayer(
        "https://mt1.google.com/vt/lyrs=m&x={x}&y={y}&z={z}",
        { maxZoom: 22, subdomains: ["mt0", "mt1", "mt2", "mt3"], attribution: "© Google Maps" }
    );

    // 4. Google Maps Topographic Terrain
    allMapLayers["google-terrain"] = L.tileLayer(
        "https://mt1.google.com/vt/lyrs=p&x={x}&y={y}&z={z}",
        { maxZoom: 22, subdomains: ["mt0", "mt1", "mt2", "mt3"], attribution: "© Google Maps" }
    );

    // 5. Mapbox Satellite Streets HD
    allMapLayers["mapbox-satellite"] = L.tileLayer(
        `https://api.mapbox.com/styles/v1/mapbox/satellite-streets-v12/tiles/{z}/{x}/{y}?access_token=${mapboxToken}`,
        { maxZoom: 22, tileSize: 512, zoomOffset: -1, attribution: "© Mapbox © Maxar" }
    );

    // 6. Mapbox Dark Tactical
    allMapLayers["mapbox-dark"] = L.tileLayer(
        `https://api.mapbox.com/styles/v1/mapbox/dark-v11/tiles/{z}/{x}/{y}?access_token=${mapboxToken}`,
        { maxZoom: 22, tileSize: 512, zoomOffset: -1, attribution: "© Mapbox" }
    );

    // 7. ESRI Satellite Fallback
    allMapLayers["esri-satellite"] = L.tileLayer(
        "https://server.arcgisonline.com/ArcGIS/rest/services/World_Imagery/MapServer/tile/{z}/{y}/{x}",
        { maxZoom: 19, attribution: "ESRI Satellite" }
    );

    // Add Google Maps Hybrid HD as default active layer
    currentMapLayerKey = localStorage.getItem("saras_map_provider") || "google-hybrid";
    if (allMapLayers[currentMapLayerKey]) {
        allMapLayers[currentMapLayerKey].addTo(map);
    } else {
        allMapLayers["google-hybrid"].addTo(map);
        currentMapLayerKey = "google-hybrid";
    }

    // Sync layer selector dropdown
    const layerSelect = document.getElementById("map-layer-select");
    if (layerSelect) layerSelect.value = currentMapLayerKey;

    const baseLayers = {
        "🗺️ Google Maps (Hybrid HD)": allMapLayers["google-hybrid"],
        "🛰️ Google Maps (Satellite)": allMapLayers["google-satellite"],
        "🚗 Google Maps (Roadmap)": allMapLayers["google-roadmap"],
        "⛰️ Google Maps (Terrain)": allMapLayers["google-terrain"],
        "📡 Mapbox Satellite HD": allMapLayers["mapbox-satellite"],
        "🌑 Mapbox Dark Tactical": allMapLayers["mapbox-dark"],
        "🛰️ ESRI Satellite": allMapLayers["esri-satellite"]
    };

    L.control.layers(baseLayers, null, { position: "topright" }).addTo(map);

    // Ensure Leaflet calculates container geometry properly
    setTimeout(() => { if (map) map.invalidateSize(); }, 250);
    setTimeout(() => { if (map) map.invalidateSize(); }, 1000);
    window.addEventListener("resize", () => { if (map) map.invalidateSize(); });

    // Initialize tactical region drawing interaction
    initMapDrawingEvents();
}

function switchMapLayer(key) {
    if (!allMapLayers[key] || !map) return;
    Object.keys(allMapLayers).forEach(k => {
        if (map.hasLayer(allMapLayers[k])) {
            map.removeLayer(allMapLayers[k]);
        }
    });
    allMapLayers[key].addTo(map);
    currentMapLayerKey = key;
    localStorage.setItem("saras_map_provider", key);
    const select = document.getElementById("map-layer-select");
    if (select && select.value !== key) select.value = key;
}

function locateUserLiveGps() {
    if (!navigator.geolocation) {
        alert("Geolocation is not supported by your browser or environment. Enter coordinates manually.");
        promptManualCoordinates();
        return;
    }

    const gpsBtn = document.getElementById("btn-user-gps");
    if (gpsBtn) {
        gpsBtn.classList.add("loading");
        gpsBtn.innerHTML = `
            <svg class="spin-icon" width="13" height="13" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><circle cx="12" cy="12" r="10" stroke-dasharray="32" stroke-dashoffset="10"/></svg>
            <span>Acquiring GPS...</span>
        `;
    }

    navigator.geolocation.getCurrentPosition(
        (position) => {
            const lat = position.coords.latitude;
            const lon = position.coords.longitude;
            const accuracy = position.coords.accuracy || 12;
            userGpsCoords = { lat, lon, accuracy };

            if (gpsBtn) {
                gpsBtn.classList.remove("loading");
                gpsBtn.classList.add("active");
                gpsBtn.innerHTML = `
                    <svg width="13" height="13" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><circle cx="12" cy="12" r="10"/><circle cx="12" cy="12" r="3"/><line x1="12" y1="2" x2="12" y2="22"/><line x1="2" y1="12" x2="22" y2="12"/></svg>
                    <span>GPS Locked</span>
                `;
            }

            // Smoothly fly map to user's real location
            map.flyTo([lat, lon], 17, { duration: 1.5 });

            // Create or update GCS marker
            const gcsIconHtml = `
                <div class="gcs-marker-beacon">
                    <div class="gcs-pulse-ring"></div>
                    <div class="gcs-center-pin">📍</div>
                </div>
            `;
            const gcsIcon = L.divIcon({
                className: "gcs-map-marker",
                html: gcsIconHtml,
                iconSize: [28, 28],
                iconAnchor: [14, 14]
            });

            if (userGpsMarker) {
                userGpsMarker.setLatLng([lat, lon]);
                userGpsCircle.setLatLng([lat, lon]);
                userGpsCircle.setRadius(accuracy);
            } else {
                userGpsMarker = L.marker([lat, lon], { icon: gcsIcon, zIndexOffset: 2000 }).addTo(map);
                userGpsCircle = L.circle([lat, lon], {
                    radius: accuracy,
                    color: "#38bdf8",
                    fillColor: "#38bdf8",
                    fillOpacity: 0.12,
                    weight: 1.5,
                    dashArray: "4, 4"
                }).addTo(map);
            }

            const popupHtml = `
                <div style="font-family:-apple-system,BlinkMacSystemFont,sans-serif; min-width:210px; padding:4px;">
                    <div style="display:flex; align-items:center; gap:6px; margin-bottom:6px;">
                        <span style="font-size:14px;">📡</span>
                        <div>
                            <b style="color:#38bdf8; font-size:12px;">OPERATOR GCS (LIVE GPS)</b>
                            <div style="font-size:10px; color:#94a3b8;">Accuracy: ±${accuracy.toFixed(1)}m</div>
                        </div>
                    </div>
                    <div style="font-family:'JetBrains Mono',monospace; font-size:11px; background:rgba(0,0,0,0.4); padding:4px 8px; border-radius:6px; margin-bottom:8px; color:#fff;">
                        LAT: ${lat.toFixed(5)}°<br/>
                        LON: ${lon.toFixed(5)}°
                    </div>
                    <button onclick="relocateSwarmToBase(${lat}, ${lon})" style="width:100%; padding:6px 10px; border-radius:12px; background:#0a84ff; color:#fff; border:none; font-weight:700; font-size:11px; cursor:pointer; margin-bottom:4px;">
                        ⚡ Relocate Swarm Base Here
                    </button>
                </div>
            `;
            userGpsMarker.bindPopup(popupHtml).openPopup();

            showGpsBanner(lat, lon, accuracy);
        },
        (error) => {
            console.warn("Geolocation warning:", error.message);
            if (gpsBtn) {
                gpsBtn.classList.remove("loading");
                gpsBtn.innerHTML = `
                    <svg width="13" height="13" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><circle cx="12" cy="12" r="10"/><circle cx="12" cy="12" r="3"/><line x1="12" y1="2" x2="12" y2="22"/><line x1="2" y1="12" x2="22" y2="12"/></svg>
                    <span>Live GPS</span>
                `;
            }
            promptManualCoordinates();
        },
        { enableHighAccuracy: true, timeout: 10000, maximumAge: 0 }
    );
}

function showGpsBanner(lat, lon, accuracy) {
    const banner = document.getElementById("gps-location-banner");
    const textEl = document.getElementById("gps-banner-text");
    if (banner && textEl) {
        textEl.textContent = `Live GPS Locked: ${lat.toFixed(5)}° N, ${lon.toFixed(5)}° E (±${Math.round(accuracy)}m)`;
        banner.classList.remove("hidden");
    }
}

function hideGpsBanner() {
    const banner = document.getElementById("gps-location-banner");
    if (banner) banner.classList.add("hidden");
}

async function relocateSwarmToBase(lat, lon) {
    const urls = getBackendUrls();
    try {
        const res = await fetch(`${urls.httpBase}/api/swarm/relocate`, {
            method: "POST",
            headers: { "Content-Type": "application/json" },
            body: JSON.stringify({ lat: lat, lon: lon })
        });
        if (res.ok) {
            const data = await res.json();
            hideGpsBanner();
            fetchSwarmStatus();
            alert(`Swarm launch pad successfully relocated to GPS coordinates [${lat.toFixed(5)}, ${lon.toFixed(5)}]!\n\nAll staged UAVs are now aligned at your physical launch pad.`);
        }
    } catch (e) {
        console.error("Relocate error:", e);
    }
}

function relocateSwarmToGps() {
    const coords = lastGpsCoords || userGpsCoords;
    if (coords) {
        relocateSwarmToBase(coords.lat, coords.lon);
    }
}

function promptManualCoordinates() {
    const cur = userGpsCoords ? `${userGpsCoords.lat.toFixed(5)}, ${userGpsCoords.lon.toFixed(5)}` : "12.9750, 77.5970";
    const input = prompt(
        "Browser Geolocation unavailable or denied.\nEnter custom GPS Latitude & Longitude to position GCS Base (e.g. 12.9750, 77.5970):",
        cur
    );
    if (input) {
        const parts = input.split(",").map(p => parseFloat(p.trim()));
        if (parts.length === 2 && !isNaN(parts[0]) && !isNaN(parts[1])) {
            const lat = parts[0];
            const lon = parts[1];
            userGpsCoords = { lat, lon, accuracy: 10 };
            map.flyTo([lat, lon], 17);
            relocateSwarmToBase(lat, lon);
        } else {
            alert("Invalid coordinates. Please enter in format: Latitude, Longitude");
        }
    }
}

function promptMapboxToken() {
    const existing = localStorage.getItem("saras_mapbox_token") || DEFAULT_MAPBOX_TOKEN;
    const token = prompt(
        "Mapbox Access Token is currently configured and active.\n\nEnter new Mapbox Access Token to change, or clear to restore default:",
        existing
    );
    if (token !== null) {
        const trimmed = token.trim();
        if (trimmed && trimmed !== DEFAULT_MAPBOX_TOKEN) {
            localStorage.setItem("saras_mapbox_token", trimmed);
            alert("Custom Mapbox API Token saved! Reloading dashboard...");
        } else {
            localStorage.removeItem("saras_mapbox_token");
            alert("Default Mapbox token restored.");
        }
        location.reload();
    }
}

function initTelemetryWebSocket() {
    const urls = getBackendUrls();
    try {
        wsTelemetry = new WebSocket(urls.wsTelemetry);

        wsTelemetry.onopen = () => {
            console.log("[SARAS WS] Telemetry stream connected:", urls.wsTelemetry);
            setConnectionStatus(true, "WEBSOCKET LIVE (10 Hz)");
        };

        wsTelemetry.onmessage = (event) => {
            try {
                const data = JSON.parse(event.data);
                updateDashboard(data);
                setConnectionStatus(true, "WEBSOCKET LIVE (10 Hz)");
            } catch (e) {
                console.error("[SARAS WS] Error parsing telemetry:", e);
            }
        };

        wsTelemetry.onclose = () => {
            setConnectionStatus(false, "RECONNECTING...");
            setTimeout(initTelemetryWebSocket, 2000);
        };

        wsTelemetry.onerror = () => {
            setConnectionStatus(false, "HTTP FALLBACK");
        };
    } catch (e) {
        setConnectionStatus(false, "HTTP FALLBACK");
    }
}

function setConnectionStatus(connected, text) {
    isConnected = connected;
    const pulse = document.querySelector(".logo-pulse");
    if (pulse) {
        pulse.style.background = connected ? "var(--color-cyan)" : "var(--color-amber)";
        pulse.style.boxShadow = connected ? "0 0 12px var(--color-cyan)" : "0 0 12px var(--color-amber)";
    }
    const healthEl = document.getElementById("stat-health");
    if (healthEl && !connected) {
        healthEl.textContent = text;
        healthEl.className = "m-val status-degraded";
    }
}

async function fetchSwarmStatus() {
    const urls = getBackendUrls();
    try {
        const res = await fetch(`${urls.httpBase}/api/swarm/status`);
        if (res.ok) {
            const data = await res.json();
            updateDashboard(data);
            if (!isConnected) {
                setConnectionStatus(true, "HTTP LIVE (1 Hz)");
            }
        }
    } catch (e) {
        // Fallback check to /api/status
        try {
            const res2 = await fetch(`${urls.httpBase}/api/status`);
            if (res2.ok) {
                const data2 = await res2.json();
                updateDashboard(data2);
                if (!isConnected) {
                    setConnectionStatus(true, "HTTP LIVE (1 Hz)");
                }
            }
        } catch (err) {
            setConnectionStatus(false, "OFFLINE");
        }
    }
}

function updateDashboard(state) {
    if (!state) return;

    try {
        // 1. Update Header Metrics
        const healthEl = document.getElementById("stat-health");
        if (healthEl) {
            healthEl.textContent = state.system_health || "HEALTHY";
            healthEl.className = `m-val status-${(state.system_health || "HEALTHY").toLowerCase()}`;
        }

        // Normalize drones dictionary / list
        let drones = {};
        const rawDrones = state.active_drones || state.drones || {};
        if (Array.isArray(rawDrones)) {
            rawDrones.forEach(d => { if (d && d.drone_id) drones[d.drone_id] = d; });
        } else if (typeof rawDrones === "object" && rawDrones !== null) {
            drones = rawDrones;
        }

        const droneCount = Object.keys(drones).length;
        const activeCount = Object.values(drones).filter(d => d.status === "SEARCHING" || d.status === "IDLE").length;
        const stagedCount = Object.values(drones).filter(d => d.status === "IDLE" && !d.current_sector_id).length;
        if (droneCount > 0 && droneCount !== currentFleetSize) {
            currentFleetSize = droneCount;
            syncFleetSizeUI(droneCount);
        }

        const dronesStat = document.getElementById("stat-drones");
        if (dronesStat) {
            if (stagedCount === droneCount && droneCount > 0) {
                dronesStat.textContent = `${droneCount} STAGED`;
            } else {
                dronesStat.textContent = `${activeCount} / ${droneCount || currentFleetSize}`;
            }
        }

        const covEl = document.getElementById("stat-coverage");
        if (covEl) covEl.textContent = `${(state.total_coverage_pct || 0).toFixed(1)}%`;
        const covFill = document.getElementById("stat-coverage-fill");
        if (covFill) covFill.style.width = `${Math.min(100, state.total_coverage_pct || 0)}%`;

        const detections = state.active_detections || state.victims || [];
        const victimsStat = document.getElementById("stat-victims");
        if (victimsStat) victimsStat.textContent = detections.length;

        currentPolicy = state.allocation_policy || "AUCTION";
        const policyEl = document.getElementById("stat-policy");
        if (policyEl) policyEl.textContent = currentPolicy;
        updatePolicyButtons();

        // MAVLink / Hardware Bridge Status
        const mavDot = document.getElementById("mavlink-dot");
        const mavTxt = document.getElementById("mavlink-status");
        const isMavConnected = state.mavlink_connected || state.mavlink_status?.connected || false;
        if (mavDot && mavTxt) {
            if (isMavConnected) {
                mavDot.classList.add("connected");
                mavTxt.textContent = "ONLINE (14550)";
                mavTxt.style.color = "var(--status-success)";
            } else {
                mavDot.classList.remove("connected");
                mavTxt.textContent = "STANDBY";
                mavTxt.style.color = "var(--muted-foreground)";
            }
        }

        // Operating Mode Sync
        if (state.mode && state.mode !== currentSystemMode) {
            currentSystemMode = state.mode;
            updateModeButtons(currentSystemMode);
        }

        // Pause/Resume State Sync
        if (state.is_paused !== undefined) {
            isPaused = state.is_paused;
            updatePauseButton(isPaused);
        }

        // Video HUD Quick Telemetry Sync
        const dList = Object.values(drones);
        if (dList.length > 0) {
            const d1 = dList[0];
            const hudFlight = document.getElementById("hud-flight-data");
            if (hudFlight) hudFlight.textContent = `ALT: ${(d1.alt || 35.0).toFixed(1)}M | SPD: ${(d1.speed_mps || 10.0).toFixed(1)}M/S | BATT: ${Math.round(d1.battery || 100)}%`;
            const hudGps = document.getElementById("hud-target-gps");
            if (hudGps) hudGps.textContent = `${(d1.lat || 11.5360).toFixed(4)}°N, ${(d1.lon || 76.1390).toFixed(4)}°E`;
            const hudCam = document.getElementById("hud-cam-source");
            if (hudCam) {
                hudCam.textContent = "AERIAL EO/IR OPTICAL HUD (TEST FEED)";
            }
            const hudTarget = document.getElementById("hud-target-count");
            if (hudTarget) {
                hudTarget.textContent = `${detections.length} VICTIMS ACQUIRED`;
            }
        }

        // 2. Render Hazards (Leaflet map circles & sidebar card)
        if (state.hazards && Array.isArray(state.hazards)) {
            renderHazards(state.hazards);
        }

        // Normalize sectors dictionary / list
        let sectors = {};
        const rawSectors = state.sectors || {};
        if (Array.isArray(rawSectors)) {
            rawSectors.forEach(s => { if (s && s.sector_id) sectors[s.sector_id] = s; });
        } else if (typeof rawSectors === "object" && rawSectors !== null) {
            sectors = rawSectors;
        }

        // Update mission staging banner visibility
        const stagingBanner = document.getElementById("mission-staging-banner");
        if (stagingBanner) {
            if (Object.keys(sectors).length === 0) {
                stagingBanner.classList.remove("hidden");
            } else {
                stagingBanner.classList.add("hidden");
            }
        }

        // Auto-fit map to sectors once on startup
        if (!hasAutoFitted && Object.keys(sectors).length > 0 && map) {
            const allCoords = [];
            Object.values(sectors).forEach(sec => {
                if (sec.bounds) {
                    sec.bounds.forEach(pt => {
                        if (Array.isArray(pt) && pt.length >= 2) allCoords.push(pt);
                        else if (typeof pt === "string") {
                            const p = pt.trim().split(/\s+/).map(Number);
                            if (p.length >= 2 && !isNaN(p[0]) && !isNaN(p[1])) allCoords.push([p[0], p[1]]);
                        }
                    });
                }
            });
            if (allCoords.length > 0) {
                map.fitBounds(allCoords, { padding: [25, 25], maxZoom: 16 });
                hasAutoFitted = true;
            }
        }

        // 2. Update Sectors on Leaflet
        renderSectors(sectors);

        // 3. Update Drones on Leaflet & Sidebar
        renderDrones(drones);

        // 4. Update Victims & Triage
        renderVictims(detections, state.recommendations || []);

        // 5. Update Alerts
        renderAlerts(state.alerts || []);
    } catch (err) {
        console.error("Dashboard update error:", err);
    }
}

function renderHazards(hazards) {
    if (!hazards || !Array.isArray(hazards)) return;

    // 1. Render hazard cards in sidebar roster
    const container = document.getElementById("hazard-roster");
    const countBadge = document.getElementById("hazard-count-badge");
    const bannerCount = document.getElementById("stat-hazards-count");
    if (countBadge) countBadge.textContent = `${hazards.length} ACTIVE`;
    if (bannerCount) bannerCount.textContent = `${hazards.length} ACTIVE`;

    if (container) {
        container.innerHTML = hazards.map(h => {
            let iconClass = "h-debris";
            let glyph = "▲";
            if (h.hazard_type === "smoke_plume") { iconClass = "h-smoke"; glyph = "☁"; }
            else if (h.hazard_type === "wind_shear") { iconClass = "h-wind"; glyph = "⇄"; }
            else if (h.hazard_type === "fire_hotspot") { iconClass = "h-thermal"; glyph = "♨"; }

            return `
            <div class="hazard-card" title="${h.description}">
                <div class="hazard-icon-box ${iconClass}">${glyph}</div>
                <div class="hazard-desc">
                    <strong>${h.name || h.hazard_id}</strong>
                    <small>${h.description} · RAD: ${h.radius}M</small>
                </div>
                <div class="hazard-severity">
                    ${Math.round((h.severity || 0.8) * 100)}% RISK
                </div>
            </div>
            `;
        }).join("");
    }

    // 2. Render hazard circles on Leaflet map
    if (!map) return;
    hazards.forEach(h => {
        const hid = h.hazard_id;
        let color = "#ef4444";
        let fillColor = "#ef4444";
        let fillOpacity = 0.22;

        if (h.hazard_type === "landslide_debris") {
            color = "#f97316";
            fillColor = "#ea580c";
            fillOpacity = 0.26;
        } else if (h.hazard_type === "smoke_plume") {
            color = "#94a3b8";
            fillColor = "#64748b";
            fillOpacity = 0.28;
        } else if (h.hazard_type === "wind_shear") {
            color = "#38bdf8";
            fillColor = "#0284c7";
            fillOpacity = 0.20;
        }

        if (!hazardLayers[hid]) {
            hazardLayers[hid] = L.circle([h.lat, h.lon], {
                radius: h.radius || 100,
                color: color,
                weight: 1.5,
                dashArray: "4, 4",
                fillColor: fillColor,
                fillOpacity: fillOpacity
            }).addTo(map);

            hazardLayers[hid].bindTooltip(`
                <div style="font-family:var(--font-sans); padding:2px;">
                    <strong style="color:${color}; font-size:12px;">${h.name || hid}</strong><br>
                    <span style="font-size:11px; color:var(--foreground);">${h.description}</span><br>
                    <small style="color:var(--muted-foreground);">Radius: ${h.radius}m | Risk: ${Math.round((h.severity || 0.8)*100)}%</small>
                </div>
            `, { sticky: true });
        }
    });
}

function updatePolicyButtons() {
    const btnAuction = document.getElementById("btn-policy-auction");
    const btnGreedy = document.getElementById("btn-policy-greedy");
    if (btnAuction && btnGreedy) {
        if (currentPolicy === "AUCTION") {
            btnAuction.classList.add("active");
            btnGreedy.classList.remove("active");
        } else {
            btnGreedy.classList.add("active");
            btnAuction.classList.remove("active");
        }
    }
}

function renderSectors(sectors) {
    if (!map) return;

    // 1. Remove layers for sectors that were deleted on the backend
    Object.keys(sectorLayers).forEach(layerId => {
        if (!sectors[layerId]) {
            map.removeLayer(sectorLayers[layerId]);
            delete sectorLayers[layerId];
        }
    });

    // 2. Render / Update each active sector
    Object.values(sectors).forEach(sec => {
        if (!sec || !sec.sector_id) return;
        const id = sec.sector_id;
        const isCustom = id.startsWith("CUST");

        // Inherit dynamic color assigned to this specific sector/region
        const baseColor = sec.color || (isCustom ? "#00f0ff" : "#64748b");
        let color = baseColor;
        let dashArray = "4, 4";
        let fillOpacity = 0.12;

        if (sec.status === "SEARCHING") {
            color = baseColor;
            dashArray = null;
            fillOpacity = 0.35;
        } else if (sec.status === "COVERED") {
            color = baseColor;
            dashArray = null;
            fillOpacity = 0.42;
        } else if (sec.status === "NO_FLY") {
            color = "#ff453a";
            dashArray = "6, 4";
            fillOpacity = 0.28;
        } else if (sec.status === "HAZARD") {
            color = "#ff9f0a";
            dashArray = "6, 4";
            fillOpacity = 0.28;
        } else {
            // UNSEARCHED
            color = baseColor;
            dashArray = isCustom ? "6, 4" : "4, 4";
            fillOpacity = 0.18;
        }

        // Ensure latlngs are properly parsed numbers
        const latlngs = (sec.bounds || []).map(pt => {
            if (Array.isArray(pt) && pt.length >= 2) return [Number(pt[0]), Number(pt[1])];
            if (typeof pt === "string") {
                const parts = pt.trim().split(/\s+/).map(Number);
                return [parts[0], parts[1]];
            }
            return pt;
        }).filter(pt => Array.isArray(pt) && !isNaN(pt[0]) && !isNaN(pt[1]));

        if (latlngs.length < 3) return;

        const parentRegionId = id.split("-").length >= 3 ? id.split("-").slice(0, 2).join("-") : id;

        const tooltipHtml = `
            <div style="font-family:-apple-system,BlinkMacSystemFont,sans-serif;">
                <b style="color:${baseColor};">${sec.name || id}</b>${isCustom ? " <span style='font-size:9px; color:" + baseColor + "; font-weight:800;'>[CUSTOM]</span>" : ""}<br/>
                Status: <span style="font-weight:700;">${sec.status}</span> | Coverage: <span style="color:#10b981; font-weight:700;">${(sec.coverage_pct || 0).toFixed(0)}%</span>
                ${sec.assigned_drone_id ? `<br/>Assigned UAV: <b>${sec.assigned_drone_id}</b>` : ""}
                ${isCustom ? `<br/>Priority Weight: <b>${sec.priority || 1.0}x</b>` : ""}
            </div>
        `;

        const popupHtml = `
            <div style="font-family:-apple-system,BlinkMacSystemFont,sans-serif; min-width:160px; padding:2px;">
                <div style="display:flex; align-items:center; gap:6px; margin-bottom:4px;">
                    <span style="display:inline-block; width:8px; height:8px; border-radius:50%; background:${baseColor}; box-shadow:0 0 6px ${baseColor};"></span>
                    <b style="color:${baseColor}; font-size:12px;">${sec.name || id}</b>
                </div>
                <div style="font-size:11px; color:#cbd5e1; margin:6px 0; line-height:1.4;">
                    Status: <span style="color:#fff; font-weight:700;">${sec.status}</span><br/>
                    Coverage: <span style="color:#10b981; font-weight:700;">${(sec.coverage_pct || 0).toFixed(0)}%</span><br/>
                    ${sec.assigned_drone_id ? `Assigned UAV: <b style="color:#38bdf8;">${sec.assigned_drone_id}</b><br/>` : ""}
                    ${isCustom ? `Priority: <b>${sec.priority || 1.0}x</b><br/>` : ""}
                </div>
                ${isCustom ? `
                    <button class="popup-delete-btn" onclick="deleteCustomSector('${parentRegionId}')" title="Delete this entire marked region">
                        <svg width="11" height="11" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.5"><path d="M3 6h18"/><path d="M19 6v14c0 1-1 2-2 2H7c-1 0-2-1-2-2V6"/><path d="M8 6V4c0-1 1-2 2-2h4c1 0 2 1 2 2v2"/></svg>
                        <span>Delete Region (${parentRegionId})</span>
                    </button>
                ` : ""}
            </div>
        `;

        if (sectorLayers[id]) {
            sectorLayers[id].setStyle({
                color: color,
                weight: isCustom ? 2 : 1.5,
                dashArray: dashArray,
                fillColor: color,
                fillOpacity: fillOpacity
            });
            sectorLayers[id].setTooltipContent(tooltipHtml);
            sectorLayers[id].setPopupContent(popupHtml);
        } else {
            const polygon = L.polygon(latlngs, {
                color: color,
                weight: isCustom ? 2 : 1.5,
                dashArray: dashArray,
                fillColor: color,
                fillOpacity: fillOpacity
            }).addTo(map);

            polygon.bindTooltip(tooltipHtml, { sticky: true, className: "sector-tooltip" });
            polygon.bindPopup(popupHtml);

            sectorLayers[id] = polygon;
        }
    });

    // 3. Update the floating Marked Tactical Regions Manager dock
    updateMarkedRegionsDock(sectors);
}

function updateMarkedRegionsDock(sectors) {
    const dock = document.getElementById("marked-regions-dock");
    const list = document.getElementById("marked-regions-list");
    const badge = document.getElementById("marked-regions-badge");
    if (!dock || !list) return;

    // Filter all custom sectors
    const customSectors = Object.values(sectors).filter(s => s && s.sector_id && s.sector_id.startsWith("CUST"));
    if (customSectors.length === 0) {
        dock.classList.add("hidden");
        return;
    }

    // Group sub-sectors under parent region (e.g. CUST-01)
    const regionsMap = {};
    customSectors.forEach(sec => {
        const parts = sec.sector_id.split("-");
        const parentId = parts.length >= 3 ? `${parts[0]}-${parts[1]}` : sec.sector_id;
        if (!regionsMap[parentId]) {
            regionsMap[parentId] = {
                id: parentId,
                name: (sec.name || parentId).replace(/\s*\(Sec\s+[A-Z]\)/i, "").replace(/\s*\(Sector\s+[A-Z]\)/i, ""),
                color: sec.color || "#00f0ff",
                status: sec.status,
                priority: sec.priority || 1.0,
                subSectors: [],
                assignedDrones: new Set()
            };
        }
        regionsMap[parentId].subSectors.push(sec);
        if (sec.assigned_drone_id) {
            regionsMap[parentId].assignedDrones.add(sec.assigned_drone_id);
        }
    });

    const regionEntries = Object.values(regionsMap);
    if (badge) badge.textContent = regionEntries.length;

    let itemsHtml = "";
    regionEntries.forEach(reg => {
        const droneInfo = reg.assignedDrones.size > 0 ? Array.from(reg.assignedDrones).join(", ") : "Pending";
        const subCount = reg.subSectors.length > 1 ? ` (${reg.subSectors.length} subs)` : "";
        itemsHtml += `
            <div class="marked-region-item">
                <div class="region-color-indicator-bar" style="background:${reg.color}; box-shadow:0 0 8px ${reg.color};"></div>
                <div class="region-info-main">
                    <div class="region-name-row">
                        <span class="region-title-text" title="${reg.name}">${reg.name}</span>
                    </div>
                    <div class="region-sub-meta">
                        <span style="color:${reg.color}; font-weight:800;">${reg.id}${subCount}</span>
                        <span>•</span>
                        <span>${droneInfo}</span>
                        <span>•</span>
                        <span>${reg.priority}x</span>
                    </div>
                </div>
                <div class="region-item-actions">
                    <button class="btn-region-fly" onclick="flyToSector('${reg.subSectors[0].sector_id}')" title="Zoom to region">
                        <svg width="11" height="11" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.5"><circle cx="11" cy="11" r="8"/><path d="m21 21-4.3-4.3"/></svg>
                    </button>
                    <button class="btn-region-del" onclick="deleteCustomSector('${reg.id}')" title="Delete marked region">
                        <svg width="11" height="11" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.5"><path d="M3 6h18"/><path d="M19 6v14c0 1-1 2-2 2H7c-1 0-2-1-2-2V6"/><path d="M8 6V4c0-1 1-2 2-2h4c1 0 2 1 2 2v2"/></svg>
                    </button>
                </div>
            </div>
        `;
    });

    list.innerHTML = itemsHtml;
    dock.classList.remove("hidden");
}

function flyToSector(sectorId) {
    if (sectorLayers[sectorId] && map) {
        map.fitBounds(sectorLayers[sectorId].getBounds(), { padding: [60, 60], maxZoom: 17 });
        sectorLayers[sectorId].openPopup();
    }
}

function renderDrones(drones) {
    if (!map) return;
    const listContainer = document.getElementById("drone-list");
    let listHtml = "";

    const droneList = Array.isArray(drones) ? drones : Object.values(drones);

    droneList.forEach(drone => {
        if (!drone || typeof drone.lat !== "number" || typeof drone.lon !== "number") return;
        const id = drone.drone_id;
        const lat = drone.lat;
        const lon = drone.lon;
        const isStaged = (drone.status === "IDLE" && !drone.current_sector_id);
        const displayStatus = isStaged ? "STAGED" : drone.status;
        const statusClass = (displayStatus || "SEARCHING").toLowerCase();
        const bat = Math.round(drone.battery || 0);
        let batClass = "";
        if (bat < 25) batClass = "crit";
        else if (bat < 50) batClass = "low";

        // Sidebar card HTML with click to focus on map
        const isSelected = (drone.drone_id.toLowerCase() === activeVideoDroneId.toLowerCase()) ? "active-selected" : "";
        listHtml += `
            <div class="drone-card ${isSelected} ${statusClass}" onclick="focusDroneOnMap('${drone.drone_id}')" title="Click to center UAV on map & view optical HUD">
                <div class="drone-header">
                    <div class="drone-id-wrap">
                        <span class="drone-indicator ${statusClass}"></span>
                        <span class="drone-title">${drone.drone_id}</span>
                    </div>
                    <span class="drone-status-tag ${statusClass}">${displayStatus}</span>
                </div>
                <div class="battery-track">
                    <div class="battery-fill ${batClass}" style="width: ${bat}%"></div>
                </div>
                <div class="telemetry-row">
                    <span>BAT: <strong>${bat}%</strong></span>
                    <span>ALT: <strong>${drone.alt}m</strong></span>
                    <span>SPD: <strong>${(drone.speed || 0).toFixed(1)}m/s</strong></span>
                </div>
                <div class="telemetry-row">
                    <span>SEC: <strong>${drone.status === "RETURNING" ? "RTH Base" : (drone.current_sector_id || "None")}</strong></span>
                    <span>VIC: <strong>${drone.victims_detected || 0}</strong></span>
                    <span>HDG: <strong>${(drone.heading || 0).toFixed(0)}°</strong></span>
                </div>
            </div>
        `;

        // Update coordinate history for flight trails
        if (!droneHistories[id]) {
            droneHistories[id] = [];
        }
        droneHistories[id].push([lat, lon]);
        if (droneHistories[id].length > 40) {
            droneHistories[id].shift();
        }

        // Draw or update flight trail polyline
        let trailColor = "#0ea5e9";
        if (statusClass === "returning") trailColor = "#f59e0b";
        else if (statusClass === "lost") trailColor = "#ef4444";

        if (droneTrails[id]) {
            droneTrails[id].setLatLngs(droneHistories[id]);
            droneTrails[id].setStyle({ color: trailColor });
        } else if (map) {
            droneTrails[id] = L.polyline(droneHistories[id], {
                color: trailColor,
                weight: 2.5,
                opacity: 0.7,
                dashArray: "4, 6"
            }).addTo(map);
        }

        // Draw or update 38-meter sensor detection footprint circle
        if (droneFootprints[id]) {
            droneFootprints[id].setLatLng([lat, lon]);
            droneFootprints[id].setStyle({
                color: trailColor,
                fillColor: trailColor,
                fillOpacity: (statusClass === "searching") ? 0.12 : 0.05
            });
        } else if (map) {
            droneFootprints[id] = L.circle([lat, lon], {
                radius: 38,
                color: trailColor,
                weight: 1.5,
                dashArray: "3, 3",
                fillColor: trailColor,
                fillOpacity: 0.12
            }).addTo(map);
        }

        // Highlighted Map Marker with Quadrotor SVG, radar ping, and callout badge
        const headingDeg = Math.round(drone.heading || 0);
        const iconHtml = `
            <div class="drone-highlight-container ${statusClass}">
                <div class="drone-radar-ping"></div>
                <div class="drone-heading-wrapper" style="transform: rotate(${headingDeg}deg);">
                    <svg class="drone-quad-svg" viewBox="0 0 40 40" width="34" height="34">
                        <line x1="8" y1="8" x2="32" y2="32" stroke="currentColor" stroke-width="2.5" stroke-linecap="round"/>
                        <line x1="8" y1="32" x2="32" y2="8" stroke="currentColor" stroke-width="2.5" stroke-linecap="round"/>
                        <circle cx="8" cy="8" r="3.5" class="rotor"/>
                        <circle cx="32" cy="8" r="3.5" class="rotor"/>
                        <circle cx="8" cy="32" r="3.5" class="rotor"/>
                        <circle cx="32" cy="32" r="3.5" class="rotor"/>
                        <polygon points="20,5 27,23 20,19 13,23" class="drone-core-arrow"/>
                        <circle cx="20" cy="20" r="4.5" class="drone-core-dot"/>
                    </svg>
                </div>
                <div class="drone-callout-pill">
                    <span class="callout-id">${drone.drone_id}</span>
                    <span class="callout-bat ${batClass}">${bat}%</span>
                </div>
            </div>
        `;
        const icon = L.divIcon({
            className: "drone-map-icon",
            html: iconHtml,
            iconSize: [50, 50],
            iconAnchor: [25, 25]
        });

        const popupContent = `
            <div style="min-width: 140px; padding: 2px;">
                <div style="display:flex; justify-content:space-between; align-items:center; margin-bottom:4px;">
                    <strong style="font-size:13px; color:var(--foreground);">${drone.drone_id}</strong>
                    <span style="font-size:10px; padding:2px 6px; border-radius:4px; font-weight:700; background:var(--secondary); color:var(--secondary-foreground);">${drone.status}</span>
                </div>
                <div style="font-size:11px; line-height:1.5; color:var(--muted-foreground);">
                    <div>Battery: <b style="color:var(--foreground);">${bat}%</b></div>
                    <div>Altitude: <b style="color:var(--foreground);">${drone.alt}m</b></div>
                    <div>Speed: <b style="color:var(--foreground);">${(drone.speed || 0).toFixed(1)} m/s</b></div>
                    <div>Sector: <b style="color:var(--foreground);">${drone.status === "RETURNING" ? "Returning to Pad" : (drone.current_sector_id || "Staged at Base")}</b></div>
                </div>
                <button onclick="selectDroneForVideo('${drone.drone_id}')" style="margin-top:8px; width:100%; padding:5px 10px; border-radius:6px; background:var(--primary); color:var(--primary-foreground); border:none; cursor:pointer; font-size:11px; font-weight:600;">
                    View Optical HUD
                </button>
            </div>
        `;

        if (droneMarkers[id]) {
            droneMarkers[id].setLatLng([lat, lon]);
            droneMarkers[id].setIcon(icon);
            droneMarkers[id].setPopupContent(popupContent);
        } else {
            const marker = L.marker([lat, lon], { icon: icon }).addTo(map);
            marker.bindPopup(popupContent);
            marker.on("click", () => {
                selectDroneForVideo(drone.drone_id);
            });
            droneMarkers[id] = marker;
        }
    });

    // Clean up markers, footprints, and trails for decommissioned drones
    const currentDroneIds = new Set(droneList.map(d => d.drone_id));
    Object.keys(droneMarkers).forEach(mId => {
        if (!currentDroneIds.has(mId)) {
            map.removeLayer(droneMarkers[mId]);
            delete droneMarkers[mId];
            if (droneFootprints[mId]) {
                map.removeLayer(droneFootprints[mId]);
                delete droneFootprints[mId];
            }
            if (droneTrails[mId]) {
                map.removeLayer(droneTrails[mId]);
                delete droneTrails[mId];
            }
            delete droneHistories[mId];
        }
    });

    // Update fleet display elements if fleet size changed
    if (droneList.length > 0 && droneList.length !== currentFleetSize) {
        currentFleetSize = droneList.length;
        syncFleetSizeUI(currentFleetSize);
    }

    if (listContainer) listContainer.innerHTML = listHtml;
}

function focusDroneOnMap(droneId) {
    selectDroneForVideo(droneId);
    if (droneMarkers[droneId]) {
        const latLng = droneMarkers[droneId].getLatLng();
        map.setView(latLng, Math.max(map.getZoom(), 16), { animate: true, duration: 0.8 });
        droneMarkers[droneId].openPopup();
    }
}

function renderVictims(detections, recommendations) {
    if (!map) return;
    const recMap = {};
    (recommendations || []).forEach(r => {
        if (r && r.victim_id) recMap[r.victim_id] = r;
    });

    const triageContainer = document.getElementById("triage-list");
    const triageCountEl = document.getElementById("triage-count");
    if (triageCountEl) triageCountEl.textContent = detections.length;

    if (detections.length === 0) {
        if (triageContainer) {
            triageContainer.innerHTML = '<div class="empty-state">No victims detected yet. Swarm is conducting search sweeps...</div>';
        }
        return;
    }

    let triageHtml = "";

    detections.forEach(det => {
        if (!det || typeof det.lat !== "number" || typeof det.lon !== "number") return;
        const id = det.detection_id;
        const rec = recMap[id];
        const category = rec ? rec.triage_category : "URGENT";
        const score = rec ? rec.urgency_score : 50.0;
        const action = rec ? rec.recommended_action : "Awaiting triage assessment...";
        const notes = rec ? rec.notes : (det.notes || "");
        const catClass = (category || "urgent").toLowerCase();

        triageHtml += `
            <div class="triage-item ${catClass}">
                <div class="triage-top">
                    <span>${det.detection_id} (${det.drone_id || "UAV"})</span>
                    <span class="triage-score">URGENCY: ${score} [${category}]</span>
                </div>
                <div class="triage-action">${action}</div>
                <div class="triage-meta">
                    Tags: ${(det.environment_tags || []).join(", ") || "none"} • Temp: ${det.thermal_signature ? det.thermal_signature + "°C" : "N/A"}<br/>
                    ${notes}
                </div>
            </div>
        `;

        // Map pin for victim
        let pinColor = "#ef4444";
        if (category === "URGENT") pinColor = "#f59e0b";
        if (category === "STABLE") pinColor = "#10b981";

        const pinHtml = `<div class="victim-marker-icon" style="background: ${pinColor};"></div>`;
        const icon = L.divIcon({
            className: "victim-map-pin",
            html: pinHtml,
            iconSize: [16, 16],
            iconAnchor: [8, 8]
        });

        const popupContent = `
            <div style="font-family: sans-serif; font-size: 12px; min-width: 180px;">
                <b style="color: ${pinColor}; font-size: 13px;">${id} [${category}]</b><br/>
                <b>Reported by:</b> ${det.drone_id || "UAV"}<br/>
                <b>Thermal Signature:</b> ${det.thermal_signature ? det.thermal_signature + "°C" : "Unknown"}<br/>
                <b>Action:</b> ${action}<br/>
                <b>SOP Ref:</b> ${(rec ? rec.sop_references : []).join(", ") || "Standard"}
            </div>
        `;

        if (victimMarkers[id]) {
            victimMarkers[id].setLatLng([det.lat, det.lon]);
            victimMarkers[id].setIcon(icon);
            victimMarkers[id].setPopupContent(popupContent);
        } else {
            const marker = L.marker([det.lat, det.lon], { icon: icon }).addTo(map);
            marker.bindPopup(popupContent);
            victimMarkers[id] = marker;
        }
    });

    if (triageContainer) triageContainer.innerHTML = triageHtml;
}

function renderAlerts(alerts) {
    const alertBox = document.getElementById("alert-list");
    const alertCountEl = document.getElementById("alert-counter");
    if (alertCountEl) alertCountEl.textContent = alerts.length;
    if (!alertBox) return;

    let html = "";

    alerts.slice().reverse().forEach(a => {
        const timeStr = new Date((a.timestamp || Date.now()/1000) * 1000).toLocaleTimeString();
        html += `
            <div class="alert-entry ${a.level || 'INFO'}">
                <span class="alert-time">[${timeStr}]</span>
                <span><b>${a.drone_id || "SWARM"}:</b> ${a.message || ""}</span>
            </div>
        `;
    });

    alertBox.innerHTML = html;
}

// Tactical Controls & Actions
async function setPolicy(policy) {
    const urls = getBackendUrls();
    try {
        const res = await fetch(`${urls.httpBase}/api/swarm/policy`, {
            method: "POST",
            headers: { "Content-Type": "application/json" },
            body: JSON.stringify({ policy: policy })
        });
        if (res.ok) {
            currentPolicy = policy;
            updatePolicyButtons();
        }
    } catch (e) {
        console.error("Set policy error:", e);
    }
}

async function injectFault(droneId, faultType, val = null) {
    const urls = getBackendUrls();
    try {
        await fetch(`${urls.httpBase}/api/swarm/fault`, {
            method: "POST",
            headers: { "Content-Type": "application/json" },
            body: JSON.stringify({
                drone_id: droneId,
                fault_type: faultType,
                value: val
            })
        });
    } catch (e) {
        console.error("Fault injection error:", e);
    }
}

// Swarm Fleet Size Controller
let currentFleetSize = 4;

function syncFleetSizeUI(count) {
    const valEl = document.getElementById("fleet-size-val");
    if (valEl) valEl.textContent = `${count} UAVs`;

    // Update preset pills active state
    document.querySelectorAll("#fleet-presets-bar .preset-pill").forEach(pill => {
        const n = parseInt(pill.getAttribute("data-n") || "0", 10);
        if (n === count) pill.classList.add("active");
        else pill.classList.remove("active");
    });

    // Update staging banner count
    const stagingCountEl = document.getElementById("staging-drone-count");
    if (stagingCountEl) stagingCountEl.textContent = count;

    // Update region modal deploy button count
    const deployCountEl = document.getElementById("deploy-swarm-count");
    if (deployCountEl) deployCountEl.textContent = count;

    // Update video drone tabs
    updateVideoDroneTabs(count);
}

async function setFleetCount(count, resetMission = false) {
    const target = Math.max(1, Math.min(16, parseInt(count, 10)));
    const urls = getBackendUrls();
    try {
        const res = await fetch(`${urls.httpBase}/api/swarm/fleet-size`, {
            method: "POST",
            headers: { "Content-Type": "application/json" },
            body: JSON.stringify({ count: target, reset_mission: resetMission })
        });
        if (res.ok) {
            const data = await res.json();
            currentFleetSize = data.drone_count || target;
            syncFleetSizeUI(currentFleetSize);
            fetchSwarmStatus();
        }
    } catch (e) {
        console.error("Failed to set fleet size:", e);
    }
}

function stepFleetSize(delta) {
    const target = Math.max(1, Math.min(16, currentFleetSize + delta));
    setFleetCount(target);
}

function promptFleetSize() {
    const input = prompt(`Enter desired UAV swarm fleet size (1 - 16):\nCurrent fleet: ${currentFleetSize} UAVs`, currentFleetSize);
    if (input !== null) {
        const parsed = parseInt(input.trim(), 10);
        if (!isNaN(parsed) && parsed >= 1 && parsed <= 16) {
            setFleetCount(parsed);
        } else if (input.trim()) {
            alert("Please enter a valid fleet size between 1 and 16.");
        }
    }
}

async function resetSim() {
    const urls = getBackendUrls();
    try {
        await fetch(`${urls.httpBase}/api/swarm/reset`, {
            method: "POST",
            headers: { "Content-Type": "application/json" },
            body: JSON.stringify({ num_drones: currentFleetSize })
        });
        // Clear pins
        Object.values(victimMarkers).forEach(m => map.removeLayer(m));
        victimMarkers = {};
        fetchSwarmStatus();
    } catch (e) {
        console.error("Reset error:", e);
    }
}

// RAG Assistant Queries
async function sendRagQuery() {
    const input = document.getElementById("rag-input");
    if (!input) return;
    const query = input.value.trim();
    if (!query) return;

    const box = document.getElementById("rag-response-box");
    if (box) box.innerHTML = `<p style="color: #94a3b8;">Consulting Disaster SOP Knowledge Base for: <i>"${query}"</i>...</p>`;

    const urls = getBackendUrls();
    try {
        const res = await fetch(`${urls.httpBase}/api/query`, {
            method: "POST",
            headers: { "Content-Type": "application/json" },
            body: JSON.stringify({ query: query })
        });

        if (res.ok && box) {
            const data = await res.json();
            box.innerHTML = `
                <div class="rag-guidance">${data.synthesized_guidance}</div>
                <div class="rag-action-highlight">⚡ Tactical Action: ${data.recommended_action}</div>
                <div class="rag-citations">📚 SOP References: ${(data.sop_references || []).join(", ")} (Confidence: ${((data.confidence || 0.8) * 100).toFixed(0)}%)</div>
            `;
            input.value = "";
        }
    } catch (e) {
        if (box) box.innerHTML = `<p style="color: #ef4444;">Error retrieving SOP response.</p>`;
    }
}

function handleRagKey(e) {
    if (e.key === "Enter") {
        sendRagQuery();
    }
}

function quickQuery(q) {
    const input = document.getElementById("rag-input");
    if (input) input.value = q;
    sendRagQuery();
}

// Benchmark Modal (IEEE Evaluation)
async function runAblationBenchmark() {
    const modal = document.getElementById("benchmark-modal");
    const content = document.getElementById("benchmark-content");
    if (modal) modal.classList.remove("hidden");
    if (content) content.innerHTML = "<p>Running comparative simulation across allocation policies...</p>";

    const urls = getBackendUrls();
    try {
        const res = await fetch(`${urls.httpBase}/api/benchmark`);
        if (res.ok && content) {
            const data = await res.json();
            const metrics = data.metrics;
            const greedy = metrics.GreedyDistanceBaseline;
            const auction = metrics.MarketAuctionProposed;

            const travelDiff = ((greedy.total_travel_meters - auction.total_travel_meters) / greedy.total_travel_meters * 100).toFixed(1);
            const varDiff = ((greedy.workload_variance - auction.workload_variance) / greedy.workload_variance * 100).toFixed(1);

            content.innerHTML = `
                <h4>Comparative Evaluation: Market-Based Auction vs. Greedy Distance Baseline</h4>
                <p style="color: #94a3b8; font-size: 0.72rem; margin-bottom: 8px;">
                    Simulated under identical heterogeneous battery initializations and variable sector priorities (rows=3, cols=4, drones=4).
                </p>
                <table class="benchmark-table">
                    <thead>
                        <tr>
                            <th>Evaluation Metric</th>
                            <th>Greedy Baseline</th>
                            <th>Market Auction (Proposed)</th>
                            <th>Improvement (%)</th>
                        </tr>
                    </thead>
                    <tbody>
                        <tr>
                            <td>Total Swarm Travel (m)</td>
                            <td>${greedy.total_travel_meters} m</td>
                            <td style="color: #10b981; font-weight: bold;">${auction.total_travel_meters} m</td>
                            <td style="color: #10b981;">+${travelDiff}%</td>
                        </tr>
                        <tr>
                            <td>Workload/Battery Variance</td>
                            <td>${greedy.workload_variance}</td>
                            <td style="color: #10b981; font-weight: bold;">${auction.workload_variance}</td>
                            <td style="color: #10b981;">+${varDiff}% balance</td>
                        </tr>
                        <tr>
                            <td>Avg Priority Weight Served</td>
                            <td>${greedy.avg_priority_weight}</td>
                            <td style="color: #10b981; font-weight: bold;">${auction.avg_priority_weight}</td>
                            <td>+${((auction.avg_priority_weight - greedy.avg_priority_weight)/greedy.avg_priority_weight*100).toFixed(1)}%</td>
                        </tr>
                        <tr>
                            <td>Energy Efficiency Composite Score</td>
                            <td>${greedy.energy_efficiency_score}</td>
                            <td style="color: #06b6d4; font-weight: bold;">${auction.energy_efficiency_score}</td>
                            <td style="color: #06b6d4;">+${(auction.energy_efficiency_score - greedy.energy_efficiency_score).toFixed(1)} pts</td>
                        </tr>
                    </tbody>
                </table>
                <div style="margin-top: 12px; padding: 10px; background: rgba(16, 185, 129, 0.1); border-left: 3px solid #10b981; font-size: 0.75rem;">
                    <b>IEEE Conclusion:</b> The Market-Based Auction mechanism avoids over-committing depleted UAVs to distant sectors, resulting in superior energy distribution and significantly reduced battery workload variance across the swarm.
                </div>
            `;
        }
    } catch (e) {
        if (content) content.innerHTML = `<p style="color: #ef4444;">Error executing benchmark.</p>`;
    }
}

function closeModal() {
    const modal = document.getElementById("benchmark-modal");
    if (modal) modal.classList.add("hidden");
}

// ==============================================================================
// APPLE VISION-OS DRONE VIDEO STREAMING CONTROLLER
// ==============================================================================
let activeVideoDroneId = "Drone-1";
let isVideoMinimized = false;
let isVideoEnlarged = false;

function updateVideoDroneTabs(count) {
    const tabsContainer = document.getElementById("video-drone-tabs");
    if (!tabsContainer) return;

    // Check if active drone is beyond current fleet size
    const match = activeVideoDroneId.match(/Drone-(\d+)/i);
    if (match) {
        const currentIdx = parseInt(match[1], 10);
        if (currentIdx > count) {
            switchVideoDrone("Drone-1");
            return;
        }
    }

    let html = "";
    for (let i = 1; i <= count; i++) {
        const dId = `Drone-${i}`;
        const isActive = (dId.toLowerCase() === activeVideoDroneId.toLowerCase()) ? "active" : "";
        html += `<button class="drone-tab ${isActive}" id="tab-drone-${i}" onclick="switchVideoDrone('${dId}')">UAV-${i}</button>`;
    }
    tabsContainer.innerHTML = html;
}

function switchVideoDrone(droneId) {
    if (!droneId) return;
    activeVideoDroneId = droneId;

    // Update active video window title
    const titleEl = document.getElementById("active-video-title");
    if (titleEl) {
        titleEl.textContent = `${droneId.toUpperCase()} OPTICAL HUD`;
    }

    // Update segmented tab pills dynamically across all tabs
    document.querySelectorAll(".drone-switcher-bar .drone-tab").forEach(tab => {
        const onclickAttr = tab.getAttribute("onclick") || "";
        if (onclickAttr.toLowerCase().includes(droneId.toLowerCase())) {
            tab.classList.add("active");
        } else {
            tab.classList.remove("active");
        }
    });

    // Refresh image stream URL with timestamp to burst cache
    const imgEl = document.getElementById("drone-video-feed");
    if (imgEl) {
        const urls = getBackendUrls();
        imgEl.src = `${urls.httpBase}/api/video/feed?drone_id=${droneId}&_t=${Date.now()}`;
    }

    // Update telemetry badge
    const badgeEl = document.getElementById("video-stream-status");
    if (badgeEl) {
        badgeEl.textContent = `1080p • 15 FPS • ${droneId.toUpperCase()} LOCK`;
    }

    // Highlight selected drone card in sidebar
    document.querySelectorAll(".drone-card").forEach(card => {
        const title = card.querySelector(".drone-title");
        if (title && title.textContent.trim().toLowerCase() === droneId.toLowerCase()) {
            card.classList.add("active-selected");
        } else {
            card.classList.remove("active-selected");
        }
    });
}

function selectDroneForVideo(droneId) {
    const windowEl = document.getElementById("uav-video-window");
    if (windowEl) {
        if (windowEl.classList.contains("hidden")) {
            windowEl.classList.remove("hidden");
        }
        if (windowEl.classList.contains("minimized")) {
            windowEl.classList.remove("minimized");
            isVideoMinimized = false;
        }
    }
    switchVideoDrone(droneId);
}

function toggleVideoFeed() {
    const windowEl = document.getElementById("uav-video-window");
    if (windowEl) {
        windowEl.classList.toggle("hidden");
    }
}

function minimizeVideoFeed() {
    const windowEl = document.getElementById("uav-video-window");
    if (windowEl) {
        isVideoMinimized = !isVideoMinimized;
        if (isVideoMinimized) {
            windowEl.classList.add("minimized");
        } else {
            windowEl.classList.remove("minimized");
        }
    }
}

function toggleVideoSize() {
    const windowEl = document.getElementById("uav-video-window");
    const wrapperEl = document.getElementById("video-feed-wrapper");
    if (windowEl) {
        isVideoEnlarged = !isVideoEnlarged;
        if (isVideoEnlarged) {
            windowEl.style.width = "540px";
            if (wrapperEl) wrapperEl.style.height = "320px";
        } else {
            windowEl.style.width = "380px";
            if (wrapperEl) wrapperEl.style.height = "215px";
        }
    }
}

function handleVideoError(img) {
    console.warn("[SARAS Video] Video stream reconnecting for drone:", activeVideoDroneId);
    setTimeout(() => {
        if (img) {
            const urls = getBackendUrls();
            img.src = `${urls.httpBase}/api/video/feed?drone_id=${activeVideoDroneId}&_retry=${Date.now()}`;
        }
    }, 2000);
}

// ==============================================================================
// APPLE TACTICAL MAP REGION DRAWING & MARKING CONTROLLER
// ==============================================================================
const TACTICAL_REGION_PALETTE = [
    { hex: "#00f0ff", name: "Electric Cyan" },
    { hex: "#a855f7", name: "Electric Purple" },
    { hex: "#f97316", name: "Vivid Orange" },
    { hex: "#10b981", name: "Emerald Mint" },
    { hex: "#ec4899", name: "Neon Rose" },
    { hex: "#eab308", name: "Golden Yellow" },
    { hex: "#3b82f6", name: "Royal Blue" },
    { hex: "#ef4444", name: "Crimson Red" },
    { hex: "#14b8a6", name: "Deep Teal" },
    { hex: "#84cc16", name: "Lime Green" }
];
let selectedRegionColor = "#00f0ff";

let currentDrawMode = null; // 'polygon' | 'box' | 'circle'
let drawPoints = [];
let activeDrawLayer = null;
let drawRubberband = null;
let drawVertexMarkers = [];
let pendingRegionData = null;
let selectedRegionType = "SEARCH";
let selectedPriority = 2.5;

function initMapDrawingEvents() {
    if (!map) return;
    map.on("click", handleMapDrawClick);
    map.on("mousemove", handleMapDrawMouseMove);
    map.on("dblclick", handleMapDrawDblClick);
}

function startDrawingMode(mode) {
    if (currentDrawMode === mode) {
        cancelDrawing();
        return;
    }

    cancelDrawing();
    currentDrawMode = mode;
    document.body.classList.add("drawing-mode-active");

    // Automatically pick the next distinct color in the palette for this new region
    const existingRegionsCount = new Set(
        Object.keys(sectorLayers)
            .filter(k => k.startsWith("CUST"))
            .map(k => k.split("-").slice(0, 2).join("-"))
    ).size;
    selectedRegionColor = TACTICAL_REGION_PALETTE[existingRegionsCount % TACTICAL_REGION_PALETTE.length].hex;

    ["polygon", "box", "circle"].forEach(m => {
        const btn = document.getElementById(`btn-draw-${m}`);
        if (btn) btn.classList.toggle("active", m === mode);
    });

    const pill = document.getElementById("drawing-status-pill");
    const inst = document.getElementById("drawing-instructions-text");
    const count = document.getElementById("drawing-points-count");
    if (pill) pill.classList.remove("hidden");
    if (count) count.textContent = "0 pts";

    if (mode === "polygon") {
        if (inst) inst.textContent = "Click map to place polygon vertices (min 3)...";
    } else if (mode === "box") {
        if (inst) inst.textContent = "Click first corner of bounding box on map...";
    } else if (mode === "circle") {
        if (inst) inst.textContent = "Click center point of hazard geofence...";
    }
}

function handleMapDrawClick(e) {
    if (!currentDrawMode) return;

    const lat = e.latlng.lat;
    const lng = e.latlng.lng;

    if (currentDrawMode === "polygon") {
        drawPoints.push([lat, lng]);

        const ptIdx = drawPoints.length;
        const vHtml = `
            <div class="vertex-pin-wrap">
                <div class="drawing-vertex-handle" style="background:${selectedRegionColor}; box-shadow:0 0 10px ${selectedRegionColor};"></div>
                <div class="vertex-label-pill" style="border-color:${selectedRegionColor};">P${ptIdx}: ${lat.toFixed(4)}, ${lng.toFixed(4)}</div>
            </div>
        `;
        const vIcon = L.divIcon({
            className: "custom-drawing-vertex",
            html: vHtml,
            iconSize: [140, 20],
            iconAnchor: [5, 5]
        });
        const vMarker = L.marker([lat, lng], { icon: vIcon }).addTo(map);
        drawVertexMarkers.push(vMarker);

        const count = document.getElementById("drawing-points-count");
        if (count) count.textContent = `${drawPoints.length} pts`;

        const inst = document.getElementById("drawing-instructions-text");
        if (inst) {
            inst.textContent = drawPoints.length >= 3 
                ? "Click 'Confirm Zone' or double-click to finalize." 
                : `Placed vertex ${drawPoints.length}. Add ${3 - drawPoints.length} more...`;
        }

        if (drawPoints.length >= 2) {
            if (!activeDrawLayer) {
                activeDrawLayer = L.polygon(drawPoints, {
                    color: selectedRegionColor,
                    weight: 2,
                    dashArray: "6, 4",
                    fillColor: selectedRegionColor,
                    fillOpacity: 0.22
                }).addTo(map);
            } else {
                activeDrawLayer.setLatLngs(drawPoints);
            }
        }
    } else if (currentDrawMode === "box") {
        if (drawPoints.length === 0) {
            drawPoints.push([lat, lng]);
            const vHtml = `
                <div class="vertex-pin-wrap">
                    <div class="drawing-vertex-handle" style="background:${selectedRegionColor}; box-shadow:0 0 10px ${selectedRegionColor};"></div>
                    <div class="vertex-label-pill" style="border-color:${selectedRegionColor};">Corner 1: ${lat.toFixed(4)}, ${lng.toFixed(4)}</div>
                </div>
            `;
            const vIcon = L.divIcon({
                className: "custom-drawing-vertex",
                html: vHtml,
                iconSize: [160, 20],
                iconAnchor: [5, 5]
            });
            const vMarker = L.marker([lat, lng], { icon: vIcon }).addTo(map);
            drawVertexMarkers.push(vMarker);

            const inst = document.getElementById("drawing-instructions-text");
            if (inst) inst.textContent = "Click opposite corner to complete bounding box...";
            const count = document.getElementById("drawing-points-count");
            if (count) count.textContent = "1 / 2 pts";
        } else if (drawPoints.length === 1) {
            drawPoints.push([lat, lng]);
            const p1 = drawPoints[0];
            const p2 = drawPoints[1];
            const bounds = [
                [p1[0], p1[1]],
                [p1[0], p2[1]],
                [p2[0], p2[1]],
                [p2[0], p1[1]]
            ];
            drawPoints = bounds;
            finishCurrentDrawing();
        }
    } else if (currentDrawMode === "circle") {
        if (drawPoints.length === 0) {
            drawPoints.push([lat, lng]);
            const vHtml = `
                <div class="vertex-pin-wrap">
                    <div class="drawing-vertex-handle" style="background:${selectedRegionColor}; box-shadow:0 0 10px ${selectedRegionColor};"></div>
                    <div class="vertex-label-pill" style="border-color:${selectedRegionColor};">Center: ${lat.toFixed(4)}, ${lng.toFixed(4)}</div>
                </div>
            `;
            const vIcon = L.divIcon({
                className: "custom-drawing-vertex",
                html: vHtml,
                iconSize: [160, 20],
                iconAnchor: [5, 5]
            });
            const vMarker = L.marker([lat, lng], { icon: vIcon }).addTo(map);
            drawVertexMarkers.push(vMarker);

            const inst = document.getElementById("drawing-instructions-text");
            if (inst) inst.textContent = "Click perimeter point to set geofence radius...";
            const count = document.getElementById("drawing-points-count");
            if (count) count.textContent = "Center set";
        } else if (drawPoints.length === 1) {
            const center = drawPoints[0];
            const radiusM = map.distance(center, [lat, lng]);
            drawPoints = generateCircleVertices(center[0], center[1], radiusM, 18);
            finishCurrentDrawing();
        }
    }
}

function handleMapDrawMouseMove(e) {
    if (!map) return;
    const lat = e.latlng.lat;
    const lng = e.latlng.lng;

    // 1. Update Floating Cursor Coordinate HUD
    const badge = document.getElementById("map-cursor-coord-badge");
    const coordText = document.getElementById("cursor-coord-text");
    if (currentDrawMode && badge && coordText) {
        badge.classList.remove("hidden");
        coordText.textContent = `LAT: ${lat.toFixed(5)}° N | LON: ${lng.toFixed(5)}° E`;
        const pt = map.latLngToContainerPoint(e.latlng);
        badge.style.left = `${pt.x}px`;
        badge.style.top = `${pt.y}px`;
    }

    // 2. Update Live Coordinates in Top Status Pill
    const liveCoordsEl = document.getElementById("drawing-live-coords");
    if (currentDrawMode && liveCoordsEl) {
        liveCoordsEl.textContent = `LAT: ${lat.toFixed(5)}° | LON: ${lng.toFixed(5)}°`;
    }

    if (!currentDrawMode || drawPoints.length === 0) return;

    const cur = [lat, lng];

    if (currentDrawMode === "polygon") {
        const last = drawPoints[drawPoints.length - 1];
        if (!drawRubberband) {
            drawRubberband = L.polyline([last, cur], {
                color: selectedRegionColor,
                weight: 1.5,
                dashArray: "4, 4"
            }).addTo(map);
        } else {
            drawRubberband.setLatLngs([last, cur]);
        }
    } else if (currentDrawMode === "box" && drawPoints.length === 1) {
        const p1 = drawPoints[0];
        const previewBounds = [
            [p1[0], p1[1]],
            [p1[0], cur[1]],
            [cur[0], cur[1]],
            [cur[0], p1[1]]
        ];
        if (!activeDrawLayer) {
            activeDrawLayer = L.polygon(previewBounds, {
                color: selectedRegionColor,
                weight: 2,
                dashArray: "5, 5",
                fillColor: selectedRegionColor,
                fillOpacity: 0.20
            }).addTo(map);
        } else {
            activeDrawLayer.setLatLngs(previewBounds);
        }
    } else if (currentDrawMode === "circle" && drawPoints.length === 1) {
        const center = drawPoints[0];
        const radiusM = map.distance(center, cur);
        if (!activeDrawLayer) {
            activeDrawLayer = L.circle(center, {
                radius: radiusM,
                color: selectedRegionColor,
                weight: 2,
                dashArray: "4, 4",
                fillColor: selectedRegionColor,
                fillOpacity: 0.20
            }).addTo(map);
        } else {
            activeDrawLayer.setRadius(radiusM);
        }
    }
}

function handleMapDrawDblClick(e) {
    if (currentDrawMode === "polygon" && drawPoints.length >= 3) {
        L.DomEvent.stop(e);
        finishCurrentDrawing();
    }
}

function generateCircleVertices(lat, lon, radiusM, numPoints = 18) {
    const coords = [];
    const earthRadius = 6378137;
    for (let i = 0; i < numPoints; i++) {
        const angle = (i * 360 / numPoints) * Math.PI / 180;
        const dLat = (radiusM * Math.cos(angle)) / earthRadius;
        const dLon = (radiusM * Math.sin(angle)) / (earthRadius * Math.cos(lat * Math.PI / 180));
        coords.push([lat + (dLat * 180 / Math.PI), lon + (dLon * 180 / Math.PI)]);
    }
    return coords;
}

function computePolygonAreaM2(points) {
    if (points.length < 3) return 0;
    const radius = 6378137;
    let area = 0;
    const len = points.length;
    for (let i = 0; i < len; i++) {
        const p1 = points[i];
        const p2 = points[(i + 1) % len];
        const radLat1 = p1[0] * Math.PI / 180;
        const radLat2 = p2[0] * Math.PI / 180;
        const radLon1 = p1[1] * Math.PI / 180;
        const radLon2 = p2[1] * Math.PI / 180;
        area += (radLon2 - radLon1) * (2 + Math.sin(radLat1) + Math.sin(radLat2));
    }
    area = Math.abs(area * radius * radius / 2.0);
    return area;
}

function computePerimeterM(points) {
    let perimeter = 0;
    const len = points.length;
    for (let i = 0; i < len; i++) {
        const p1 = points[i];
        const p2 = points[(i + 1) % len];
        if (map) {
            perimeter += map.distance(p1, p2);
        }
    }
    return perimeter;
}

function finishCurrentDrawing() {
    if (drawPoints.length < 3) {
        alert("Please place at least 3 points on the map to define a region.");
        return;
    }

    const areaM2 = computePolygonAreaM2(drawPoints);
    const areaHa = areaM2 / 10000;
    const perimeterM = computePerimeterM(drawPoints);
    const lats = drawPoints.map(p => p[0]);
    const lons = drawPoints.map(p => p[1]);
    const centroid = [
        lats.reduce((a, b) => a + b, 0) / lats.length,
        lons.reduce((a, b) => a + b, 0) / lons.length
    ];

    pendingRegionData = {
        bounds: [...drawPoints],
        areaHa: areaHa,
        areaM2: areaM2,
        perimeterM: perimeterM,
        centroid: centroid
    };

    openRegionModal();
    cleanupDrawingInteraction();
}

function cleanupDrawingInteraction() {
    currentDrawMode = null;
    document.body.classList.remove("drawing-mode-active");
    ["polygon", "box", "circle"].forEach(m => {
        const btn = document.getElementById(`btn-draw-${m}`);
        if (btn) btn.classList.remove("active");
    });
    const pill = document.getElementById("drawing-status-pill");
    if (pill) pill.classList.add("hidden");

    const badge = document.getElementById("map-cursor-coord-badge");
    if (badge) badge.classList.add("hidden");

    if (drawRubberband && map) {
        map.removeLayer(drawRubberband);
        drawRubberband = null;
    }
    drawVertexMarkers.forEach(m => { if (map) map.removeLayer(m); });
    drawVertexMarkers = [];
    if (activeDrawLayer && map) {
        map.removeLayer(activeDrawLayer);
        activeDrawLayer = null;
    }
}

function cancelDrawing() {
    cleanupDrawingInteraction();
    drawPoints = [];
    pendingRegionData = null;
}

function openRegionModal() {
    if (!pendingRegionData) return;
    const modal = document.getElementById("region-modal");
    if (!modal) return;

    const areaEl = document.getElementById("region-stat-area");
    const perimEl = document.getElementById("region-stat-perimeter");
    const vertEl = document.getElementById("region-stat-vertices");
    const nameInp = document.getElementById("region-name-input");

    if (areaEl) {
        areaEl.textContent = pendingRegionData.areaHa >= 1
            ? `${pendingRegionData.areaHa.toFixed(2)} ha`
            : `${Math.round(pendingRegionData.areaM2)} m²`;
    }
    if (perimEl) perimEl.textContent = `${Math.round(pendingRegionData.perimeterM)} m`;
    if (vertEl) vertEl.textContent = `${pendingRegionData.bounds.length} vertices`;
    if (nameInp) nameInp.value = `Custom Search Zone ${Object.keys(sectorLayers).filter(k => k.startsWith('CUST')).length + 1}`;

    // Render exact geographic boundary coordinates in preview box
    const box = document.getElementById("region-coords-preview-box");
    if (box && pendingRegionData && pendingRegionData.bounds) {
        let coordsHtml = "";
        pendingRegionData.bounds.forEach((pt, i) => {
            const pLat = Array.isArray(pt) ? pt[0] : pt.lat;
            const pLng = Array.isArray(pt) ? pt[1] : pt.lng;
            coordsHtml += `
                <div class="coord-row">
                    <span class="coord-idx">Point ${i + 1}</span>
                    <span class="coord-latlng">${Number(pLat).toFixed(5)}° N, ${Number(pLng).toFixed(5)}° E</span>
                    <span style="font-size: 0.58rem; color: #10b981; font-weight: 600;">LOCKED</span>
                </div>
            `;
        });
        box.innerHTML = coordsHtml;
    }

    // Render tactical color selection swatches
    const paletteEl = document.getElementById("region-color-palette");
    const colorNameEl = document.getElementById("selected-color-name");
    if (paletteEl) {
        let swatchesHtml = "";
        TACTICAL_REGION_PALETTE.forEach(c => {
            const isAct = c.hex.toLowerCase() === selectedRegionColor.toLowerCase();
            swatchesHtml += `
                <button type="button" class="color-swatch-btn ${isAct ? 'active' : ''}" 
                    data-hex="${c.hex}" data-name="${c.name}"
                    style="background:${c.hex}; color:${c.hex};" 
                    onclick="setRegionColor('${c.hex}', '${c.name}')" 
                    title="${c.name}">
                </button>
            `;
        });
        paletteEl.innerHTML = swatchesHtml;
    }
    const curColorObj = TACTICAL_REGION_PALETTE.find(c => c.hex.toLowerCase() === selectedRegionColor.toLowerCase()) || TACTICAL_REGION_PALETTE[0];
    if (colorNameEl) {
        colorNameEl.textContent = curColorObj.name;
        colorNameEl.style.color = curColorObj.hex;
    }

    // Populate dedicated UAV dropdown with active fleet
    const droneSelect = document.getElementById("target-drone-select");
    if (droneSelect) {
        let dHtml = "";
        for (let i = 1; i <= currentFleetSize; i++) {
            dHtml += `<option value="Drone-${i}">Drone-${i} (Dedicated Single UAV)</option>`;
        }
        droneSelect.innerHTML = dHtml;
    }

    setRegionType("SEARCH");
    setPriorityWeight(2.5);
    setDeployMode("SWARM");

    modal.classList.remove("hidden");
}

function setRegionColor(hex, name) {
    selectedRegionColor = hex;
    const colorNameEl = document.getElementById("selected-color-name");
    if (colorNameEl) {
        colorNameEl.textContent = name;
        colorNameEl.style.color = hex;
    }
    document.querySelectorAll(".color-swatch-btn").forEach(btn => {
        btn.classList.toggle("active", btn.getAttribute("data-hex").toLowerCase() === hex.toLowerCase());
    });
}

function closeRegionModal() {
    const modal = document.getElementById("region-modal");
    if (modal) modal.classList.add("hidden");
}

let selectedDeployMode = "SWARM";

function setDeployMode(mode) {
    selectedDeployMode = mode;
    const btnSwarm = document.getElementById("deploy-swarm");
    const btnSingle = document.getElementById("deploy-single");
    if (btnSwarm) btnSwarm.classList.toggle("active", mode === "SWARM");
    if (btnSingle) btnSingle.classList.toggle("active", mode === "SINGLE");

    const singleGroup = document.getElementById("single-drone-select-group");
    if (singleGroup) {
        if (mode === "SINGLE") singleGroup.classList.remove("hidden");
        else singleGroup.classList.add("hidden");
    }
}

function setRegionType(type) {
    selectedRegionType = type;
    ["SEARCH", "NO_FLY", "HAZARD"].forEach(t => {
        const btn = document.getElementById(`type-${t.toLowerCase().replace('_', '')}`);
        if (btn) btn.classList.toggle("active", t === type);
    });

    const dispatchBtn = document.getElementById("btn-dispatch-region");
    const pGroup = document.getElementById("priority-selector-group");
    const deployGroup = document.getElementById("deployment-mode-group");
    const singleGroup = document.getElementById("single-drone-select-group");

    if (type === "SEARCH") {
        if (dispatchBtn) dispatchBtn.innerHTML = "⚡ Dispatch Swarm to Region";
        if (pGroup) pGroup.style.display = "flex";
        if (deployGroup) deployGroup.style.display = "flex";
        if (singleGroup && selectedDeployMode === "SINGLE") singleGroup.classList.remove("hidden");
    } else if (type === "NO_FLY") {
        if (dispatchBtn) dispatchBtn.innerHTML = "🚫 Register No-Fly Geofence";
        if (pGroup) pGroup.style.display = "none";
        if (deployGroup) deployGroup.style.display = "none";
        if (singleGroup) singleGroup.classList.add("hidden");
    } else {
        if (dispatchBtn) dispatchBtn.innerHTML = "⚠️ Mark Debris Hazard Zone";
        if (pGroup) pGroup.style.display = "none";
        if (deployGroup) deployGroup.style.display = "none";
        if (singleGroup) singleGroup.classList.add("hidden");
    }
}

function setPriorityWeight(p) {
    selectedPriority = p;
    document.querySelectorAll(".priority-pill").forEach(el => {
        el.classList.toggle("active", parseFloat(el.getAttribute("data-p")) === p);
    });
}

function discardMarkedRegion() {
    closeRegionModal();
    pendingRegionData = null;
    drawPoints = [];
}

async function dispatchMarkedRegion() {
    if (!pendingRegionData) return;
    const nameInp = document.getElementById("region-name-input");
    const regionName = nameInp ? nameInp.value.trim() : "Custom Search Zone";

    let targetDroneId = null;
    if (selectedDeployMode === "SINGLE") {
        const droneSelect = document.getElementById("target-drone-select");
        if (droneSelect) targetDroneId = droneSelect.value;
    }

    const urls = getBackendUrls();
    try {
        const payload = {
            name: regionName,
            bounds: pendingRegionData.bounds,
            priority: selectedPriority,
            zone_type: selectedRegionType,
            dispatch_mode: selectedDeployMode,
            target_drone_id: targetDroneId,
            color: selectedRegionColor
        };

        const res = await fetch(`${urls.httpBase}/api/sectors/custom`, {
            method: "POST",
            headers: { "Content-Type": "application/json" },
            body: JSON.stringify(payload)
        });

        if (res.ok) {
            const data = await res.json();
            console.log("[SARAS] Custom sector dispatched:", data);

            // Add non-search geofences directly to map
            if (selectedRegionType !== "SEARCH" && map) {
                const geoColor = selectedRegionColor || (selectedRegionType === "NO_FLY" ? "#ff453a" : "#ff9f0a");
                const geofence = L.polygon(pendingRegionData.bounds, {
                    color: geoColor,
                    weight: 2,
                    dashArray: "6, 4",
                    fillColor: geoColor,
                    fillOpacity: 0.28
                }).addTo(map);

                geofence.bindTooltip(`<b>${selectedRegionType}: ${regionName}</b><br/>Area: ${(pendingRegionData.areaHa).toFixed(2)} ha`, {
                    sticky: true
                });
            }

            closeRegionModal();
            pendingRegionData = null;
            drawPoints = [];

            // Refresh status immediately
            fetchSwarmStatus();
        } else {
            alert("Error registering custom region with backend.");
        }
    } catch (e) {
        console.error("Error creating custom sector:", e);
        alert("Failed to communicate with SARAS backend.");
    }
}

async function deleteCustomSector(sectorId) {
    if (!confirm(`Delete marked region ${sectorId} from the swarm mission?`)) return;
    const urls = getBackendUrls();
    try {
        const res = await fetch(`${urls.httpBase}/api/sectors/${sectorId}`, { method: "DELETE" });
        if (res.ok) {
            const data = await res.json();
            console.log("[SARAS] Sector deleted:", data);
            // Remove layers matching sectorId or its sub-sectors
            Object.keys(sectorLayers).forEach(id => {
                if (id === sectorId || id.startsWith(`${sectorId}-`)) {
                    if (map && sectorLayers[id]) {
                        map.removeLayer(sectorLayers[id]);
                    }
                    delete sectorLayers[id];
                }
            });
            fetchSwarmStatus();
        } else {
            alert(`Failed to delete sector ${sectorId}.`);
        }
    } catch (e) {
        console.error("Error deleting sector:", e);
    }
}

async function clearCustomRegions() {
    if (!confirm("Delete all marked custom regions from the mission grid?")) return;
    cancelDrawing();
    const urls = getBackendUrls();
    try {
        const res = await fetch(`${urls.httpBase}/api/sectors/custom/all`, { method: "DELETE" });
        if (res.ok) {
            Object.keys(sectorLayers).forEach(secId => {
                if (secId.startsWith("CUST")) {
                    if (map && sectorLayers[secId]) {
                        map.removeLayer(sectorLayers[secId]);
                    }
                    delete sectorLayers[secId];
                }
            });
            fetchSwarmStatus();
        }
    } catch (e) {
        console.error("Error clearing custom sectors:", e);
    }
}

// ==============================================================================
// SHADCN/UI THEME MANAGER (DARK / LIGHT DYNAMIC TOGGLE)
// ==============================================================================
function toggleShadcnTheme() {
    const isDark = document.documentElement.classList.toggle("dark");
    try {
        localStorage.setItem("saras-shadcn-theme", isDark ? "dark" : "light");
    } catch (e) {}

    const themeLabel = document.getElementById("theme-label");
    if (themeLabel) {
        themeLabel.textContent = isDark ? "DARK" : "LIGHT";
    }
    console.log(`[SARAS UI] Switched theme to: ${isDark ? "dark" : "light"}`);
}



