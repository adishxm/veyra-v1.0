const API_BASE = "https://veyra-v1-0.onrender.com";

// 1. Initialize Interactive Leaflet Map
const map = L.map('map').setView([22.5726, 88.3639], 5);
L.tileLayer('https://{s}.basemaps.cartocdn.com/dark_all/{z}/{x}/{y}{r}.png', {
  attribution: '&copy; OpenStreetMap &copy; CARTO',
  maxZoom: 18
}).addTo(map);

// 2. Spatial Grid Heatmap Contours for Regional Analysis
const regionalZones = [
  { name: "Eastern Indo-Gangetic (Kolkata Sector)", bounds: [[21.5, 86.5], [23.5, 89.5]], risk: "MEDIUM", color: "#f59e0b" },
  { name: "Northern Plains (Delhi NCR)", bounds: [[27.5, 76.0], [29.5, 78.5]], risk: "LOW", color: "#10b981" },
  { name: "Western Ghats (Mumbai Sector)", bounds: [[18.0, 71.5], [20.0, 74.0]], risk: "HIGH", color: "#ef4444" }
];

regionalZones.forEach(zone => {
  L.rectangle(zone.bounds, {
    color: zone.color,
    weight: 1.5,
    fillOpacity: 0.12
  }).addTo(map).bindPopup(`<b>${zone.name}</b><br>Regional Baseline Risk: ${zone.risk}`);
});

let currentMarker = L.circleMarker([22.5726, 88.3639], {
  color: '#f59e0b',
  fillColor: '#f59e0b',
  fillOpacity: 0.8,
  radius: 10
}).addTo(map).bindPopup("<b>Kolkata</b><br>Risk: MEDIUM<br>Provider: ncmrwf-regional-canonical").openPopup();

map.on('click', (e) => {
  document.getElementById("latitude").value = e.latlng.lat.toFixed(4);
  document.getElementById("longitude").value = e.latlng.lng.toFixed(4);
  document.getElementById("location").value = `Target (${e.latlng.lat.toFixed(2)}, ${e.latlng.lng.toFixed(2)})`;
});

// 3. Form Submission Handling
document.getElementById("prediction-form").addEventListener("submit", async (e) => {
  e.preventDefault();
  const btn = document.getElementById("submit-btn");
  btn.disabled = true;
  btn.innerText = "Evaluating...";

  const lat = parseFloat(document.getElementById("latitude").value);
  const lon = parseFloat(document.getElementById("longitude").value);
  const loc = document.getElementById("location").value;

  const payload = {
    location: loc,
    latitude: lat,
    longitude: lon,
    variable: document.getElementById("variable").value,
    lead_hours: parseInt(document.getElementById("lead_hours").value, 10),
  };

  try {
    const res = await fetch(`${API_BASE}/v1/predict`, {
      method: "POST",
      headers: {
        "Content-Type": "application/json",
        "X-API-Key": "veyra-live-key-prod-001"
      },
      body: JSON.stringify(payload),
    });

    const data = await res.json();
    if (!res.ok) throw new Error(data.detail || "Inference failed");

    document.getElementById("res-location").innerText = data.location;
    document.getElementById("res-prob").innerText = `${(data.bust_probability * 100).toFixed(1)}%`;
    
    const riskEl = document.getElementById("res-risk");
    riskEl.innerText = data.risk_level;
    const color = data.risk_level === "LOW" ? "#10b981" : data.risk_level === "MEDIUM" ? "#f59e0b" : "#ef4444";
    riskEl.className = `text-2xl font-bold mono ${
      data.risk_level === "LOW" ? "text-emerald-400" :
      data.risk_level === "MEDIUM" ? "text-amber-400" : "text-rose-500"
    }`;

    document.getElementById("res-conformal").innerText = `[${data.conformal_lower}°C , ${data.conformal_upper}°C]`;

    // Reposition Marker
    map.setView([lat, lon], 6);
    if (currentMarker) map.removeLayer(currentMarker);
    currentMarker = L.circleMarker([lat, lon], {
      color: color,
      fillColor: color,
      fillOpacity: 0.8,
      radius: 12
    }).addTo(map).bindPopup(`<b>${data.location}</b><br>Risk: ${data.risk_level}<br>Provider: ${data.provider_provenance}`).openPopup();

  } catch (err) {
    alert("Inference Error: " + err.message);
  } finally {
    btn.disabled = false;
    btn.innerText = "Evaluate Reliability";
  }
});