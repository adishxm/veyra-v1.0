const API_BASE = "https://veyra-v1-0.onrender.com";

async function fetchRegistryAndMetrics() {
  try {
    // 1. Fetch Models
    const modRes = await fetch(`${API_BASE}/v1/models`);
    if (modRes.ok) {
      const data = await modRes.json();
      const listEl = document.getElementById("models-list");
      listEl.innerHTML = data.models.map(m => `
        <div class="p-3 bg-slate-950 border border-slate-800 rounded-lg flex justify-between items-center">
          <div>
            <span class="font-bold text-slate-200">${m.version}</span>
            <span class="text-[10px] text-slate-500 block">${m.algorithm}</span>
          </div>
          <div class="text-right">
            <span class="px-2 py-0.5 rounded text-[10px] font-semibold ${m.stage === 'active' ? 'bg-indigo-500/20 text-indigo-400 border border-indigo-500/30' : 'bg-slate-800 text-slate-400'}">${m.stage.toUpperCase()}</span>
            <span class="text-[10px] text-slate-500 block mt-1">Brier: ${m.metrics.brier_score}</span>
          </div>
        </div>
      `).join("");
    }

    // 2. Fetch Metrics
    const metRes = await fetch(`${API_BASE}/v1/metrics`);
    if (metRes.ok) {
      const met = await metRes.json();
      const metEl = document.getElementById("metrics-summary");
      if (met.status === "insufficient_data") {
        metEl.innerHTML = `<div class="text-slate-500">${met.message}</div>`;
      } else {
        metEl.innerHTML = `
          <div class="grid grid-cols-3 gap-2 text-center">
            <div class="bg-slate-950 p-2.5 rounded border border-slate-800"><span class="text-slate-400 block text-[10px]">VERIFIED</span><span class="font-bold text-slate-200 text-sm">${met.verified_count}</span></div>
            <div class="bg-slate-950 p-2.5 rounded border border-slate-800"><span class="text-slate-400 block text-[10px]">BRIER</span><span class="font-bold text-indigo-400 text-sm">${met.brier_score}</span></div>
            <div class="bg-slate-950 p-2.5 rounded border border-slate-800"><span class="text-slate-400 block text-[10px]">MAE</span><span class="font-bold text-slate-200 text-sm">${met.mean_absolute_error}°C</span></div>
          </div>
        `;
      }
    }
  } catch (err) {
    console.error("Failed to load metadata:", err);
  }
}

document.getElementById("prediction-form").addEventListener("submit", async (e) => {
  e.preventDefault();
  const btn = document.getElementById("submit-btn");
  btn.disabled = true;
  btn.innerText = "Evaluating...";

  const payload = {
    location: document.getElementById("location").value,
    latitude: parseFloat(document.getElementById("latitude").value),
    longitude: parseFloat(document.getElementById("longitude").value),
    variable: document.getElementById("variable").value,
    lead_hours: parseInt(document.getElementById("lead_hours").value, 10),
  };

  try {
    const res = await fetch(`${API_BASE}/v1/predict`, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify(payload),
    });

    const data = await res.json();
    if (!res.ok) throw new Error(data.detail || "Prediction request failed");

    document.getElementById("res-location").innerText = data.location;
    document.getElementById("res-prob").innerText = data.bust_probability !== null ? `${(data.bust_probability * 100).toFixed(1)}%` : "ABSTAINED";
    
    const riskEl = document.getElementById("res-risk");
    riskEl.innerText = data.risk_level || "N/A";
    riskEl.className = `text-2xl font-bold mono ${
      data.risk_level === "LOW" ? "text-emerald-400" :
      data.risk_level === "MEDIUM" ? "text-amber-400" :
      data.risk_level === "HIGH" ? "text-orange-400" : "text-rose-500"
    }`;

    document.getElementById("res-conformal").innerText = (data.conformal_lower !== null && data.conformal_upper !== null) 
      ? `[${data.conformal_lower}°C , ${data.conformal_upper}°C]`
      : "N/A";

    const badge = document.getElementById("res-trust-badge");
    badge.innerText = data.trust_state;
    badge.className = `px-3 py-1 rounded-full text-xs mono font-semibold ${
      data.trust_state === "SUPPORTED" ? "bg-emerald-500/10 text-emerald-400 border border-emerald-500/20" :
      data.trust_state === "DEGRADED" ? "bg-amber-500/10 text-amber-400 border border-amber-500/20" :
      "bg-rose-500/10 text-rose-400 border border-rose-500/20"
    }`;

    document.getElementById("res-novelty").innerText = data.novelty_score ?? "--";
    document.getElementById("res-model").innerText = data.model_version ?? "--";
    document.getElementById("res-evidence").innerText = data.evidence?.join(", ") || "None";
    document.getElementById("res-schema").innerText = `Schema: ${data.feature_schema_version || 'N/A'}`;
    document.getElementById("res-data").innerText = `Data: ${data.data_version || 'N/A'}`;

  } catch (err) {
    alert("Inference Error: " + err.message);
  } finally {
    btn.disabled = false;
    btn.innerText = "Evaluate Reliability";
  }
});

// Initial load
fetchRegistryAndMetrics();