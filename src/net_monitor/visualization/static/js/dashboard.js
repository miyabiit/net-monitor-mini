let selectedTargetId = null;
let refreshTimerId = null;

const GRAPH_LOOKBACK_DAYS = 7;
const GRAPH_LIMIT = 10000;
const TABLE_LIMIT = 100;
const GRAPH_WINDOW_HOURS = 96;
const GRAPH_WINDOW_BACK_HOURS = 72;
const GRAPH_TICK_HOURS = 2;

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
    <div><strong>グラフ範囲:</strong> 最新時刻基準の ${GRAPH_WINDOW_HOURS / 24} 日</div>
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
  const scrollContainer = document.getElementById("chart-scroll");
  const context = canvas.getContext("2d");
  const availableWidth = Math.max(Math.floor(scrollContainer.clientWidth), 300);
  const height = 300;
  const padding = { top: 24, right: 24, bottom: 86, left: 68 };
  const latestTime = results.length
    ? Math.max(...results.map((item) => new Date(item.measured_at).getTime()))
    : null;
  const chartWidth = latestTime === null
    ? availableWidth
    : calculateChartWidth(latestTime, availableWidth, padding);
  const width = Math.max(chartWidth, 300);

  canvas.width = width;
  canvas.height = height;

  context.clearRect(0, 0, width, height);
  context.fillStyle = "#ffffff";
  context.fillRect(0, 0, width, height);

  if (!results.length) {
    context.fillStyle = "#5d728a";
    context.font = "14px sans-serif";
    context.fillText("表示できるデータがありません。", padding.left, height / 2);
    return;
  }

  const timestamps = results.map((item) => new Date(item.measured_at).getTime());
  const xAxisStart = getWindowStartTime(latestTime);
  const xAxisEnd = getWindowEndTime(xAxisStart);
  const visibleResults = results.filter((item) => {
    const time = new Date(item.measured_at).getTime();
    return time >= xAxisStart && time <= xAxisEnd;
  });
  const visibleTimestamps = visibleResults.map((item) => new Date(item.measured_at).getTime());
  const values = visibleResults.map((item) => item.latency_ms).filter((item) => item !== null);
  const maxValue = Math.max(...values, 1);
  const cycleSummaries = buildCycleSummaries(visibleResults);
  const plotWidth = width - padding.left - padding.right;
  const plotHeight = height - padding.top - padding.bottom;

  context.strokeStyle = "#d7e0ea";
  context.lineWidth = 1;

  drawChartAxes(context, width, height, padding);
  drawYAxis(context, width, height, padding, maxValue, plotHeight);
  drawXAxis(context, width, height, padding, xAxisStart, xAxisEnd, plotWidth);
  drawAxisTitles(context, width, height, padding);

  drawAverageLine(context, cycleSummaries, xAxisStart, xAxisEnd, padding.left, plotWidth, maxValue, height, padding.bottom, plotHeight);

  visibleResults.forEach((result, index) => {
    const x = getXPosition(visibleTimestamps[index], xAxisStart, xAxisEnd, padding.left, plotWidth);
    const y = result.latency_ms === null
      ? height - padding.bottom
      : getYPosition(result.latency_ms, maxValue, height, padding.bottom, plotHeight);
    context.fillStyle = result.success ? "#0f7bff" : "#d64545";
    context.beginPath();
    context.arc(x, y, 4, 0, Math.PI * 2);
    context.fill();
  });

  context.fillStyle = "#5d728a";
  context.font = "12px sans-serif";
  context.textAlign = "left";
  context.fillText(`max ${maxValue.toFixed(1)} ms`, padding.left, padding.top - 8);

  scrollChartToLatest(scrollContainer);
}

function drawChartAxes(context, width, height, padding) {
  context.beginPath();
  context.moveTo(padding.left, padding.top);
  context.lineTo(padding.left, height - padding.bottom);
  context.lineTo(width - padding.right, height - padding.bottom);
  context.stroke();
}

function drawYAxis(context, width, height, padding, maxValue, plotHeight) {
  const tickCount = 4;
  context.font = "11px sans-serif";
  context.fillStyle = "#5d728a";
  context.textAlign = "right";
  context.textBaseline = "middle";

  for (let index = 0; index <= tickCount; index += 1) {
    const ratio = index / tickCount;
    const value = maxValue * (1 - ratio);
    const y = padding.top + plotHeight * ratio;

    context.strokeStyle = "#eef3f7";
    context.beginPath();
    context.moveTo(padding.left, y);
    context.lineTo(width - padding.right, y);
    context.stroke();

    context.fillText(value.toFixed(0), padding.left - 8, y);
  }
}

function drawXAxis(context, width, height, padding, minTime, maxTime, plotWidth) {
  context.font = "11px sans-serif";
  context.fillStyle = "#5d728a";
  context.textAlign = "center";
  context.textBaseline = "top";
  const ticks = buildHourlyTicks(minTime, maxTime);

  ticks.forEach((time) => {
    const x = getXPosition(time, minTime, maxTime, padding.left, plotWidth);

    context.strokeStyle = isMidnightTick(time) ? "#d7e0ea" : "#eef3f7";
    context.beginPath();
    context.moveTo(x, padding.top);
    context.lineTo(x, height - padding.bottom);
    context.stroke();

    if (isMidnightTick(time)) {
      drawMidnightXAxisLabel(context, x, height - padding.bottom + 8, time);
    }
  });
}

function drawAxisTitles(context, width, height, padding) {
  context.fillStyle = "#5d728a";
  context.font = "12px sans-serif";

  context.textAlign = "center";
  context.textBaseline = "top";
  context.fillText("日時", (padding.left + width - padding.right) / 2, height - 20);

  context.save();
  context.translate(18, (padding.top + height - padding.bottom) / 2);
  context.rotate(-Math.PI / 2);
  context.textAlign = "center";
  context.textBaseline = "top";
  context.fillText("応答時間 (ms)", 0, 0);
  context.restore();
}

function getXPosition(timestamp, minTime, maxTime, left, plotWidth) {
  if (maxTime === minTime) {
    return left + plotWidth / 2;
  }
  return left + ((timestamp - minTime) / (maxTime - minTime)) * plotWidth;
}

function getYPosition(value, maxValue, height, bottom, plotHeight) {
  return height - bottom - (value / maxValue) * plotHeight;
}

function formatAxisDate(timestamp) {
  const date = new Date(timestamp);
  const day = String(date.getDate()).padStart(2, "0");
  return {
    day
  };
}

function drawMidnightXAxisLabel(context, x, y, timestamp) {
  const label = formatAxisDate(timestamp);
  context.font = "12px sans-serif";
  context.fillText(label.day, x, y);
  context.font = "11px sans-serif";
}

function buildHourlyTicks(minTime, maxTime) {
  const ticks = [];
  let current = minTime;
  while (current <= maxTime) {
    ticks.push(current);
    current += GRAPH_TICK_HOURS * 60 * 60 * 1000;
  }
  if (ticks[ticks.length - 1] !== maxTime) {
    ticks.push(maxTime);
  }
  return ticks;
}

function calculateChartWidth(latestTime, availableWidth, padding) {
  return availableWidth;
}

function buildCycleSummaries(results) {
  const cycles = new Map();

  results.forEach((result) => {
    if (!cycles.has(result.cycle_id)) {
      cycles.set(result.cycle_id, {
        timestamp: new Date(result.measured_at).getTime(),
        values: []
      });
    }
    if (result.latency_ms !== null) {
      cycles.get(result.cycle_id).values.push(result.latency_ms);
    }
  });

  return [...cycles.values()]
    .map((cycle) => ({
      timestamp: cycle.timestamp,
      averageLatency: cycle.values.length
        ? cycle.values.reduce((sum, value) => sum + value, 0) / cycle.values.length
        : null
    }))
    .sort((left, right) => left.timestamp - right.timestamp);
}

function drawAverageLine(context, cycleSummaries, minTime, maxTime, left, plotWidth, maxValue, height, bottom, plotHeight) {
  context.strokeStyle = "#5b7cff";
  context.lineWidth = 2;
  context.beginPath();

  let started = false;
  cycleSummaries.forEach((cycle) => {
    if (cycle.averageLatency === null) {
      started = false;
      return;
    }

    const x = getXPosition(cycle.timestamp, minTime, maxTime, left, plotWidth);
    const y = getYPosition(cycle.averageLatency, maxValue, height, bottom, plotHeight);
    if (!started) {
      context.moveTo(x, y);
      started = true;
    } else {
      context.lineTo(x, y);
    }
  });

  context.stroke();
}

function getWindowStartTime(timestamp) {
  const date = new Date(timestamp);
  date.setMinutes(0, 0, 0);
  date.setHours(date.getHours() - GRAPH_WINDOW_BACK_HOURS);
  return date.getTime();
}

function getWindowEndTime(startTime) {
  return startTime + GRAPH_WINDOW_HOURS * 60 * 60 * 1000;
}

function isMidnightTick(timestamp) {
  const date = new Date(timestamp);
  return date.getHours() === 0;
}

function scrollChartToLatest(scrollContainer) {
  const maxScrollLeft = scrollContainer.scrollWidth - scrollContainer.clientWidth;
  if (maxScrollLeft > 0) {
    scrollContainer.scrollLeft = maxScrollLeft;
  }
}

async function selectTarget(targetId) {
  selectedTargetId = targetId;
  const targets = await fetchJson("/api/targets");
  renderTargets(targets);

  const target = targets.find((item) => item.id === targetId);
  const [graphPayload, tablePayload, summary] = await Promise.all([
    fetchJson(`/api/targets/${targetId}/results?days=${GRAPH_LOOKBACK_DAYS}&limit=${GRAPH_LIMIT}`),
    fetchJson(`/api/targets/${targetId}/results?limit=${TABLE_LIMIT}`),
    fetchJson(`/api/targets/${targetId}/summary`)
  ]);

  renderSummary(target, summary);
  renderTable(tablePayload.results);
  renderChart(graphPayload.results);
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
