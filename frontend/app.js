const API_BASE = "https://veyra-v1-0.onrender.com";
const CLIENT_TOKEN = "veyra-public-client-token";

function escapeHtml(str) {
  const div = document.createElement("div");
  div.textContent = str;
  return div.innerHTML;
}

const map = L.map("map").setView([20.0, 0.0], 2);

L.tileLayer("https://{s}.basemaps.cartocdn.com/dark_all/{z}/{x}/{y}{r}.png", {
  attribution: "&copy; OpenStreetMap &copy; CARTO",
  maxZoom: 18,
}).addTo(map);

const globalZones = [
  { name: "Indo-Gangetic Basin", bounds: [[20.0, 75.0], [30.0, 90.0]], risk: "MEDIUM", color: "#f59e0b" },
  { name: "Western European Corridor", bounds: [[45.0, -5.0], [58.0, 15.0]], risk: "LOW", color: "#10b981" },
  { name: "North American Great Plains", bounds: [[32.0, -105.0], [48.0, -85.0]], risk: "HIGH", color: "#ef4444" },
  { name: "East Asian Monsoonal Belt", bounds: [[22.0, 110.0], [38.0, 130.0]], risk: "MEDIUM", color: "#f59e0b" },
  { name: "Austral Basin", bounds: [[-38.0, 140.0], [-28.0, 155.0]], risk: "LOW", color: "#10b981" },
];

globalZones.forEach((zone) => {
  L.rectangle(zone.bounds, {
    color: zone.color,
    weight: 1.2,
    fillOpacity: 0.1,
  })
    .addTo(map)
    .bindPopup(`<b>${escapeHtml(zone.name)}</b><br>Regional Baseline Risk: ${escapeHtml(zone.risk)}`);
});

let currentMarker = null;

map.on("click", async (e) => {
  const lat = parseFloat(e.latlng.lat.toFixed(4));
  const lon = parseFloat(e.latlng.lng.toFixed(4));
  document.getElementById("latitude").value = lat;
  document.getElementById("longitude").value = lon;
  document.getElementById("location").value = `Coordinates (${lat}, ${lon})`;
  updateMarker(lat, lon, `Target (${lat}, ${lon})`, "MEDIUM", "#38bdf8");
});

async function resolveLocationCoordinates(query) {
  if (!query || query.trim().length === 0) return null;
  try {
    const geoUrl = `https://geocoding-api.open-meteo.com/v1/search?name=${encodeURIComponent(
      query.trim()
    )}&count=1&language=en&format=json`;
    const res = await fetch(geoUrl);
    const data = await res.json();
    if (data.results && data.results.length > 0) {
      const top = data.results[0];
      return {
        lat: parseFloat(top.latitude.toFixed(4)),
        lon: parseFloat(top.longitude.toFixed(4)),
        name: `${top.name}${top.admin1 ? ", " + top.admin1 : ""}, ${top.country_code || ""}`,
      };
    }
  } catch (err) {
    console.warn("Geocoding lookup failed:", err);
  }
  return null;
}

const locationInput = document.getElementById("location");
let debounceTimer;

locationInput.addEventListener("input", () => {
  clearTimeout(debounceTimer);
  debounceTimer = setTimeout(async () => {
    const query = locationInput.value;
    if (query.length >= 3 && !query.startsWith("Coordinates")) {
      const match = await resolveLocationCoordinates(query);
      if (match) {
        document.getElementById("latitude").value = match.lat;
        document.getElementById("longitude").value = match.lon;
        updateMarker(match.lat, match.lon, match.name, "LOOKUP", "#38bdf8");
        map.flyTo([match.lat, match.lon], 7, { duration: 1.2 });
      }
    }
  }, 400);
});

function updateMarker(lat, lon, label, risk, color) {
  if (currentMarker) map.removeLayer(currentMarker);
  currentMarker = L.circleMarker([lat, lon], {
    color: color,
    fillColor: color,
    fillOpacity: 0.85,
    radius: 10,
  })
    .addTo(map)
    .bindPopup(`<b>${escapeHtml(label)}</b><br>State: ${escapeHtml(risk)}`)
    .openPopup();
}

document.getElementById("prediction-form").addEventListener("submit", async (e) => {
  e.preventDefault();
  const btn = document.getElementById("submit-btn");
  btn.disabled = true;
  btn.innerText = "Evaluating...";

  let loc = document.getElementById("location").value.trim();
  let lat = parseFloat(document.getElementById("latitude").value);
  let lon = parseFloat(document.getElementById("longitude").value);
  const variable = document.getElementById("variable").value;
  const leadHours = parseInt(document.getElementById("lead_hours").value, 10);

  if (isNaN(lat) || isNaN(lon) || !loc.startsWith("Coordinates")) {
    const resolved = await resolveLocationCoordinates(loc);
    if (resolved) {
      lat = resolved.lat;
      lon = resolved.lon;
      loc = resolved.name;
      document.getElementById("latitude").value = lat;
      document.getElementById("longitude").value = lon;
      document.getElementById("location").value = loc;
    }
  }

  if (isNaN(lat) || isNaN(lon)) {
    alert("Could not locate the requested area. Please select a spot on the map or enter coordinates.");
    btn.disabled = false;
    btn.innerText = "Evaluate Reliability";
    return;
  }

  const payload = {
    location: loc,
    latitude: lat,
    longitude: lon,
    variable: variable,
    lead_hours: leadHours,
  };

  try {
    const res = await fetch(`${API_BASE}/v1/predict`, {
      method: "POST",
      headers: {
        "Content-Type": "application/json",
        "X-API-Key": CLIENT_TOKEN,
      },
      body: JSON.stringify(payload),
    });

    const data = await res.json();
    if (!res.ok) {
      throw new Error(data.detail || "Inference evaluation failed");
    }

    document.getElementById("res-location").innerText = data.location;
    document.getElementById("res-prob").innerText = `${(data.bust_probability * 100).toFixed(1)}%`;

    const riskEl = document.getElementById("res-risk");
    riskEl.innerText = data.risk_level;

    let color = "#10b981";
    let colorClass = "text-emerald-400";

    if (data.risk_level === "MEDIUM") {
      color = "#f59e0b";
      colorClass = "text-amber-400";
    } else if (data.risk_level === "HIGH" || data.risk_level === "CRITICAL") {
      color = "#ef4444";
      colorClass = "text-rose-500";
    }

    riskEl.className = `text-2xl font-bold mono ${colorClass}`;

    const trustBadge = document.getElementById("res-trust-badge");
    if (trustBadge) {
      trustBadge.innerText = data.trust_state;
      trustBadge.className = `px-3 py-1 rounded-full text-xs mono font-semibold border ${
        data.trust_state === "SUPPORTED"
          ? "bg-emerald-500/10 text-emerald-400 border-emerald-500/20"
          : "bg-amber-500/10 text-amber-400 border-amber-500/20"
      }`;
    }

    document.getElementById("res-conformal").innerText = `[${data.conformal_lower}°C , ${data.conformal_upper}°C]`;

    map.flyTo([lat, lon], 6, { duration: 1.0 });
    updateMarker(
      lat,
      lon,
      `${data.location} | Risk: ${data.risk_level} | Bust: ${(data.bust_probability * 100).toFixed(1)}%`,
      data.risk_level,
      color
    );
  } catch (err) {
    alert("Inference Error: " + err.message);
  } finally {
    btn.disabled = false;
    btn.innerText = "Evaluate Reliability";
  }
});