let selectedTargetId = null;
let refreshTimerId = null;

async function fetchJson(url) {
  const response = await fetch(url);
  if (!response.ok) {
    throw new Error(`request failed: ${response.status}`);
  }
  return response.json();
}

function renderTargets(targets) {
  const list = document.getElementById("target-list");
  list.innerHTML = "";
  targets.forEach((target) => {
    const button = document.createElement("button");
    button.className = "target-item";
    button.innerHTML = `
      <strong>${target.name}</strong><br>
      <span class="muted">${target.address}</span>
    `;
    button.onclick = () => selectTarget(target.id);
    if (target.id === selectedTargetId) {
      button.classList.add("active");
    }
    list.appendChild(button);
  });
}

function renderSummary(target, summary) {
  document.getElementById("target-name").textContent = target.name;
  document.getElementById("target-address").textContent = target.address;

  const latest = summary.latest_result;
  const latestText = latest
    ? `${latest.success ? "成功" : "失敗"} / ${latest.status_code}`
    : "結果なし";

  document.getElementById("summary").innerHTML = `
    <div><strong>最新結果:</strong> ${latestText}</div>
    <div><strong>成功率:</strong> ${summary.success_rate === null ? "-" : summary.success_rate.toFixed(1) + "%"}</div>
    <div><strong>平均応答:</strong> ${summary.average_latency_ms === null ? "-" : summary.average_latency_ms.toFixed(1) + " ms"}</div>
    <div><strong>保存件数:</strong> ${summary.total_count}</div>
  `;
}

function renderTable(results) {
  const body = document.getElementById("results-body");
  body.innerHTML = "";
  results.forEach((result) => {
    const row = document.createElement("tr");
    row.innerHTML = `
      <td>${new Date(result.measured_at).toLocaleString()}</td>
      <td>${result.attempt_no}</td>
      <td class="${result.success ? "status-success" : "status-failed"}">${result.success ? "成功" : "失敗"}</td>
      <td>${result.latency_ms === null ? "-" : result.latency_ms}</td>
      <td>${result.status_code}</td>
    `;
    body.appendChild(row);
  });
}

function renderChart(results) {
  const canvas = document.getElementById("latency-chart");
  const context = canvas.getContext("2d");
  const rect = canvas.getBoundingClientRect();
  const width = Math.max(Math.floor(rect.width), 300);
  const height = Math.max(Math.floor(rect.height), 240);
  const padding = 28;

  canvas.width = width;
  canvas.height = height;

  context.clearRect(0, 0, width, height);
  context.fillStyle = "#ffffff";
  context.fillRect(0, 0, width, height);

  if (!results.length) {
    context.fillStyle = "#5d728a";
    context.font = "14px sans-serif";
    context.fillText("表示できるデータがありません。", padding, height / 2);
    return;
  }

  const values = results.map((item) => item.latency_ms).filter((item) => item !== null);
  const maxValue = Math.max(...values, 1);
  const plotWidth = width - padding * 2;
  const plotHeight = height - padding * 2;

  context.strokeStyle = "#d7e0ea";
  context.lineWidth = 1;
  context.beginPath();
  context.moveTo(padding, padding);
  context.lineTo(padding, height - padding);
  context.lineTo(width - padding, height - padding);
  context.stroke();

  context.strokeStyle = "#0f7bff";
  context.lineWidth = 2;
  context.beginPath();

  results.forEach((result, index) => {
    if (result.latency_ms === null) {
      return;
    }
    const x = padding + (plotWidth * index) / Math.max(results.length - 1, 1);
    const y = height - padding - (result.latency_ms / maxValue) * plotHeight;
    if (index === 0 || results[index - 1].latency_ms === null) {
      context.moveTo(x, y);
    } else {
      context.lineTo(x, y);
    }
  });
  context.stroke();

  results.forEach((result, index) => {
    const x = padding + (plotWidth * index) / Math.max(results.length - 1, 1);
    const y = result.latency_ms === null
      ? height - padding
      : height - padding - (result.latency_ms / maxValue) * plotHeight;
    context.fillStyle = result.success ? "#0f7bff" : "#d64545";
    context.beginPath();
    context.arc(x, y, 4, 0, Math.PI * 2);
    context.fill();
  });

  context.fillStyle = "#5d728a";
  context.font = "12px sans-serif";
  context.fillText(`max ${maxValue.toFixed(1)} ms`, padding, padding - 8);
}

async function selectTarget(targetId) {
  selectedTargetId = targetId;
  const targets = await fetchJson("/api/targets");
  renderTargets(targets);

  const target = targets.find((item) => item.id === targetId);
  const [resultsPayload, summary] = await Promise.all([
    fetchJson(`/api/targets/${targetId}/results?limit=50`),
    fetchJson(`/api/targets/${targetId}/summary`)
  ]);

  renderSummary(target, summary);
  renderTable(resultsPayload.results);
  renderChart(resultsPayload.results);
}

async function initializeDashboard() {
  const targets = await fetchJson("/api/targets");
  if (!targets.length) {
    document.getElementById("target-list").innerHTML = "<p>監視対象がありません。</p>";
    return;
  }
  selectedTargetId = targets[0].id;
  renderTargets(targets);
  await selectTarget(selectedTargetId);

  if (refreshTimerId === null) {
    refreshTimerId = window.setInterval(async () => {
      if (selectedTargetId !== null) {
        await selectTarget(selectedTargetId);
      }
    }, 30000);
  }
}

initializeDashboard().catch((error) => {
  console.error(error);
  document.getElementById("target-list").innerHTML = "<p>読み込みに失敗しました。</p>";
});
