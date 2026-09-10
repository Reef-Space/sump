// All API calls use relative paths (no leading slash) so this works
// correctly whether served at "/" (dev) or under HA's ingress subpath.

const $ = (sel) => document.querySelector(sel);
const $$ = (sel) => document.querySelectorAll(sel);

// ---------- tabs ----------

$$(".tab-btn").forEach((btn) => {
  btn.addEventListener("click", () => {
    $$(".tab-btn").forEach((b) => b.classList.remove("active"));
    $$(".tab").forEach((t) => t.classList.remove("active"));
    btn.classList.add("active");
    $(`#tab-${btn.dataset.tab}`).classList.add("active");
    if (btn.dataset.tab === "log") loadEntries();
    if (btn.dataset.tab === "targets") loadTargets();
  });
});

// ---------- shared state ----------

let allParameters = [];
let currentTargets = {};

async function api(path, opts) {
  const res = await fetch(`api/${path}`, opts);
  if (!res.ok) throw new Error(`API ${path} failed: ${res.status}`);
  const ct = res.headers.get("content-type") || "";
  return ct.includes("application/json") ? res.json() : res.text();
}

async function loadParameters() {
  allParameters = await api("parameters");
  const select = $("#param-select");
  const datalist = $("#parameter-list");
  select.innerHTML = "";
  datalist.innerHTML = "";
  allParameters.forEach((p) => {
    const opt = document.createElement("option");
    opt.value = p;
    opt.textContent = p;
    select.appendChild(opt);
    const dl = document.createElement("option");
    dl.value = p;
    datalist.appendChild(dl);
  });
  if (allParameters.length) {
    select.value = allParameters[0];
    refreshDashboard();
  }
}

$("#param-select").addEventListener("change", refreshDashboard);
$("#range-select").addEventListener("change", refreshDashboard);

// ---------- dashboard ----------

async function refreshDashboard() {
  const parameter = $("#param-select").value;
  const days = parseInt($("#range-select").value, 10);
  if (!parameter) return;

  const [entries, stats, targets] = await Promise.all([
    api(`entries?parameter=${encodeURIComponent(parameter)}&days=${days}`),
    api(`stats?parameter=${encodeURIComponent(parameter)}&days=${days}`),
    api("targets"),
  ]);

  const target = targets.find((t) => t.parameter === parameter);
  renderStats(stats, target);
  drawChart(entries, target);
}

function renderStats(stats, target) {
  const row = $("#stats-row");
  row.innerHTML = "";
  const boxes = [
    ["Latest", stats.latest],
    ["Average", stats.average],
    ["Min", stats.min],
    ["Max", stats.max],
    ["Days out of range", stats.days_out_of_range],
  ];
  if (target) {
    boxes.splice(4, 0, ["Target", `${target.target_low ?? "–"} – ${target.target_high ?? "–"}`]);
  }
  boxes.forEach(([label, value]) => {
    const box = document.createElement("div");
    box.className = "stat-box" + (label === "Days out of range" && value > 0 ? " warn" : "");
    box.innerHTML = `<div class="label">${label}</div><div class="value">${value ?? "–"}</div>`;
    row.appendChild(box);
  });
}

function drawChart(entries, target) {
  const canvas = $("#chart");
  const ctx = canvas.getContext("2d");
  const w = canvas.width, h = canvas.height;
  const padL = 50, padR = 20, padT = 20, padB = 30;

  ctx.clearRect(0, 0, w, h);

  if (!entries.length) {
    ctx.fillStyle = "#8ea0b3";
    ctx.font = "14px sans-serif";
    ctx.fillText("No data for this parameter yet", padL, h / 2);
    return;
  }

  const values = entries.map((e) => e.value);
  let minV = Math.min(...values);
  let maxV = Math.max(...values);
  if (target) {
    if (target.target_low !== null && target.target_low !== undefined) minV = Math.min(minV, target.target_low);
    if (target.target_high !== null && target.target_high !== undefined) maxV = Math.max(maxV, target.target_high);
  }
  if (minV === maxV) { minV -= 1; maxV += 1; }
  const pad = (maxV - minV) * 0.1;
  minV -= pad; maxV += pad;

  const x = (i) => padL + (i / Math.max(1, entries.length - 1)) * (w - padL - padR);
  const y = (v) => padT + (1 - (v - minV) / (maxV - minV)) * (h - padT - padB);

  // target band
  if (target && target.target_low !== null && target.target_high !== null &&
      target.target_low !== undefined && target.target_high !== undefined) {
    ctx.fillStyle = "rgba(53, 196, 113, 0.12)";
    ctx.fillRect(padL, y(target.target_high), w - padL - padR, y(target.target_low) - y(target.target_high));
  }

  // gridlines + y labels
  ctx.strokeStyle = "#263341";
  ctx.fillStyle = "#8ea0b3";
  ctx.font = "11px sans-serif";
  const ySteps = 4;
  for (let i = 0; i <= ySteps; i++) {
    const v = minV + (i / ySteps) * (maxV - minV);
    const yy = y(v);
    ctx.beginPath();
    ctx.moveTo(padL, yy);
    ctx.lineTo(w - padR, yy);
    ctx.stroke();
    ctx.fillText(v.toFixed(2), 4, yy + 4);
  }

  // x labels (first, middle, last date)
  [0, Math.floor(entries.length / 2), entries.length - 1].forEach((i) => {
    const label = new Date(entries[i].timestamp).toLocaleDateString();
    ctx.fillText(label, x(i) - 20, h - 8);
  });

  // line
  ctx.strokeStyle = "#3ea6ff";
  ctx.lineWidth = 2;
  ctx.beginPath();
  entries.forEach((e, i) => {
    const px = x(i), py = y(e.value);
    if (i === 0) ctx.moveTo(px, py); else ctx.lineTo(px, py);
  });
  ctx.stroke();

  // points, colored red if out of range
  entries.forEach((e, i) => {
    const outOfRange = target && (
      (target.target_low !== null && target.target_low !== undefined && e.value < target.target_low) ||
      (target.target_high !== null && target.target_high !== undefined && e.value > target.target_high)
    );
    ctx.fillStyle = outOfRange ? "#ef5350" : "#3ea6ff";
    ctx.beginPath();
    ctx.arc(x(i), y(e.value), 3, 0, Math.PI * 2);
    ctx.fill();
  });
}

// ---------- log tab ----------

$("#entry-form").addEventListener("submit", async (e) => {
  e.preventDefault();
  const body = {
    parameter: $("#entry-parameter").value,
    value: parseFloat($("#entry-value").value),
    unit: $("#entry-unit").value || null,
    notes: $("#entry-notes").value || null,
    timestamp: $("#entry-timestamp").value ? new Date($("#entry-timestamp").value).toISOString() : null,
  };
  await api("entries", { method: "POST", headers: { "Content-Type": "application/json" }, body: JSON.stringify(body) });
  e.target.reset();
  await loadParameters();
  await loadEntries();
});

async function loadEntries() {
  const entries = await api("entries");
  const targets = await api("targets");
  const targetMap = Object.fromEntries(targets.map((t) => [t.parameter, t]));
  const tbody = $("#entries-table tbody");
  tbody.innerHTML = "";
  entries.slice().reverse().forEach((e) => {
    const t = targetMap[e.parameter];
    const outOfRange = t && (
      (t.target_low !== null && t.target_low !== undefined && e.value < t.target_low) ||
      (t.target_high !== null && t.target_high !== undefined && e.value > t.target_high)
    );
    const tr = document.createElement("tr");
    if (outOfRange) tr.classList.add("out-of-range");
    tr.innerHTML = `
      <td>${new Date(e.timestamp).toLocaleString()}</td>
      <td>${e.parameter}</td>
      <td>${e.value}</td>
      <td>${e.unit ?? ""}</td>
      <td>${e.source}</td>
      <td>${e.notes ?? ""}</td>
      <td><button class="del-btn" data-id="${e.id}">✕</button></td>
    `;
    tbody.appendChild(tr);
  });
  tbody.querySelectorAll(".del-btn").forEach((btn) => {
    btn.addEventListener("click", async () => {
      await api(`entries/${btn.dataset.id}`, { method: "DELETE" });
      loadEntries();
      refreshDashboard();
    });
  });
}

$("#import-file").addEventListener("change", async (e) => {
  const file = e.target.files[0];
  if (!file) return;
  const formData = new FormData();
  formData.append("file", file);
  const res = await fetch("api/import", { method: "POST", body: formData });
  const result = await res.json();
  alert(`Imported ${result.imported} rows`);
  await loadParameters();
  await loadEntries();
  e.target.value = "";
});

// ---------- targets tab ----------

$("#target-form").addEventListener("submit", async (e) => {
  e.preventDefault();
  const body = {
    parameter: $("#target-parameter").value,
    target_low: $("#target-low").value === "" ? null : parseFloat($("#target-low").value),
    target_high: $("#target-high").value === "" ? null : parseFloat($("#target-high").value),
    unit: $("#target-unit").value || null,
  };
  await api("targets", { method: "POST", headers: { "Content-Type": "application/json" }, body: JSON.stringify(body) });
  e.target.reset();
  await loadTargets();
  await loadParameters();
});

async function loadTargets() {
  const targets = await api("targets");
  const tbody = $("#targets-table tbody");
  tbody.innerHTML = "";
  targets.forEach((t) => {
    const tr = document.createElement("tr");
    tr.innerHTML = `
      <td>${t.parameter}</td>
      <td>${t.target_low ?? "–"}</td>
      <td>${t.target_high ?? "–"}</td>
      <td>${t.unit ?? ""}</td>
      <td><button class="del-btn" data-param="${t.parameter}">✕</button></td>
    `;
    tbody.appendChild(tr);
  });
}

// ---------- boot ----------

loadParameters();
