"use strict";

const $ = (id) => document.getElementById(id);
const state = { config: null, busy: false, history: [], completed: 0, started: 0,
  pendingSince: null, healthSamples: [], healthErrors: 0, timer: null };
const sleep = (ms) => new Promise((resolve) => setTimeout(resolve, ms));
const seconds = (ms) => (ms / 1000).toFixed(2);

function settings() {
  return {
    mode: document.querySelector('input[name="mode"]:checked').value,
    visitors: Number(document.querySelector('input[name="visitors"]:checked').value),
    scale: Number($("scale").value),
  };
}

async function fetchJSON(url) {
  const controller = new AbortController();
  const timeout = setTimeout(() => controller.abort(), 45000);
  try {
    const response = await fetch(url, { cache: "no-store", signal: controller.signal });
    if (!response.ok) throw new Error(`HTTP ${response.status}`);
    return await response.json();
  } finally {
    clearTimeout(timeout);
  }
}

function setNotice(message, error = false) {
  $("notice").textContent = message;
  $("notice").classList.toggle("error", error);
}

function updateMode() {
  if (!state.config) return;
  const { mode, visitors, scale } = settings();
  const info = state.config.modes.find((item) => item.id === mode);
  $("mode-code").textContent = info.code;
  $("mode-note").textContent = info.note;
  $("code-tag").textContent = info.tag;
  const delays = state.config.services.map((service) => service.seconds * scale);
  const total = delays.reduce((a, b) => a + b, 0);
  const expected = mode === "blocking" ? total * visitors
    : mode === "async-sequential" ? total : Math.max(...delays);
  $("expected").textContent = `이론상 전체 조회 약 ${expected.toFixed(1)}초 · 방문자 ${visitors}명 기준`;
  $("visitor-total").textContent = `/ ${visitors}명`;
  state.config.services.forEach((service) => {
    $(`${service.key}-delay`).textContent = `${(service.seconds * scale).toFixed(2)}s`;
  });
}

function setBusy(busy) {
  state.busy = busy;
  document.querySelectorAll('.controls input, .controls select, .controls button').forEach((el) => {
    el.disabled = busy;
  });
  $("clear-history").disabled = busy || !state.history.length;
  $("run").innerHTML = busy ? '<span aria-hidden="true">◌</span> 요청을 처리하고 있어요'
    : '<span aria-hidden="true">↻</span> 상품 정보 불러오기';
}

function renderHealth() {
  const measured = state.healthSamples.length ? Math.max(...state.healthSamples) : 0;
  const pending = state.pendingSince === null ? 0 : performance.now() - state.pendingSince;
  const max = Math.max(measured, pending);
  $("health-latency").textContent = max ? `${state.pendingSince !== null && pending > measured ? "≥ " : ""}${Math.round(max).toLocaleString("ko-KR")}` : "—";
  $("health-dot").className = `status-dot ${state.pendingSince !== null ? "pending" : max > 500 ? "slow" : max ? "good" : ""}`;
  document.querySelector(".health-metric").classList.toggle("warn", max > 500);
  $("health-note").textContent = state.pendingSince !== null
    ? "/health 응답을 기다리는 중…"
    : state.healthSamples.length
      ? `실제 HTTP 측정 ${state.healthSamples.length}회${state.healthErrors ? ` · 실패 ${state.healthErrors}회` : ""}`
      : state.healthErrors ? "/health 측정 실패 · 서버 연결 확인" : "/health 응답을 함께 측정합니다";
}

async function monitorHealth(control) {
  // 상품 요청보다 뒤에 보내, 서버가 대기 중일 때 가벼운 요청도 처리하는지 확인합니다.
  await sleep(120);
  while (control.active) {
    state.pendingSince = performance.now();
    renderHealth();
    try {
      const health = await fetchJSON("/health");
      if (health.status !== "ok") throw new Error("비정상 health 응답");
      state.healthSamples.push(performance.now() - state.pendingSince);
    } catch {
      state.healthErrors += 1;
    } finally {
      state.pendingSince = null;
      renderHealth();
    }
    if (control.active) await sleep(300);
  }
}

function renderTimeline(responses) {
  const container = $("timeline");
  container.replaceChildren();
  if (!responses.length) return;
  const origin = Math.min(...responses.map((r) => r.server_started_ms));
  const duration = Math.max(...responses.map((r) => r.server_started_ms - origin + r.elapsed_ms));
  const axis = document.createElement("div");
  axis.className = "timeline-axis";
  for (let i = 0; i <= 4; i++) {
    const tick = document.createElement("span");
    tick.textContent = `${seconds(duration * i / 4)}s`;
    axis.append(tick);
  }
  container.append(axis);
  responses.sort((a, b) => a.visitor - b.visitor).forEach((response) => {
    const row = document.createElement("div");
    row.className = "visitor-row";
    const label = document.createElement("span");
    label.className = "visitor-label";
    label.textContent = `방문자 ${response.visitor}`;
    const lanes = document.createElement("div");
    lanes.className = "visitor-lanes";
    response.services.forEach((service) => {
      const start = response.server_started_ms - origin + service.start_ms;
      const bar = document.createElement("div");
      bar.className = `service-bar ${service.key}`;
      bar.style.left = `${start / duration * 100}%`;
      bar.style.width = `${(service.end_ms - service.start_ms) / duration * 100}%`;
      bar.textContent = service.label.split(" ")[0];
      const explanation = `${service.label}: ${seconds(start)}~${seconds(start + service.end_ms - service.start_ms)}초, 소요 ${seconds(service.end_ms - service.start_ms)}초`;
      bar.title = explanation;
      bar.setAttribute("aria-label", explanation);
      lanes.append(bar);
    });
    row.append(label, lanes);
    container.append(row);
  });
}

function renderServices(response, loading = true) {
  const container = $("service-results");
  container.replaceChildren();
  state.config.services.forEach((spec) => {
    const result = response?.services.find((service) => service.key === spec.key);
    const article = document.createElement("article");
    for (const [tag, text] of [["span", spec.label.split(" ")[0]],
      ["strong", result ? result.value : loading ? "조회 중…" : "아직 조회 전"],
      ["small", result ? result.detail : loading ? "외부 서비스 응답을 기다립니다" : "실행 후 정보를 표시합니다"]]) {
      const el = document.createElement(tag);
      el.textContent = text;
      article.append(el);
    }
    container.append(article);
  });
}

function resetDisplay() {
  state.healthSamples = [];
  state.healthErrors = 0;
  state.pendingSince = null;
  $("elapsed").textContent = "—";
  $("completed").textContent = "0";
  $("elapsed-note").textContent = "실행 버튼을 눌러 시작하세요";
  $("completion-note").textContent = "같은 상품 페이지를 동시에 요청";
  $("run-status").className = "status-pill";
  $("run-status").textContent = "실행 대기";
  $("timeline").innerHTML = '<div class="timeline-empty"><span aria-hidden="true">≋</span><p>기다림의 모양을 확인해 보세요.</p><small>실행이 끝나면 방문자별 조회 구간이 표시됩니다.</small></div>';
  renderServices(null, false);
  renderHealth();
  setNotice("실제 요청을 보내고 응답 시간을 측정합니다. 브라우저의 애니메이션은 서버가 멈춰도 계속 움직입니다.");
}

function renderHistory() {
  const body = $("history-body");
  body.replaceChildren();
  if (!state.history.length) {
    body.innerHTML = '<tr class="empty-row"><td colspan="4">여러 방식을 실행하면 결과를 나란히 비교할 수 있어요.</td></tr>';
  }
  state.history.forEach((result) => {
    const row = document.createElement("tr");
    const info = state.config.modes.find((mode) => mode.id === result.mode);
    const cells = [info.name, `${result.visitors}명 · ${result.scale}배`,
      `${seconds(result.elapsed)}초`, result.healthPeak === null ? "측정 실패"
        : `${Math.round(result.healthPeak).toLocaleString("ko-KR")} ms${result.healthErrors ? " (일부 실패)" : ""}`];
    cells.forEach((text, i) => {
      const cell = document.createElement("td");
      cell.textContent = text;
      if (i === 3 && result.healthPeak > 500) cell.className = "slow";
      row.append(cell);
    });
    body.append(row);
  });
  $("clear-history").disabled = state.busy || !state.history.length;
}

async function runScenario(mode, progress = "") {
  document.querySelector(`input[name="mode"][value="${mode}"]`).checked = true;
  updateMode();
  const { visitors, scale } = settings();
  state.completed = 0;
  state.healthSamples = [];
  state.healthErrors = 0;
  state.pendingSince = null;
  $("elapsed").textContent = "0.00";
  $("completed").textContent = "0";
  $("elapsed-note").textContent = "브라우저에서 실제 경과 시간 측정";
  $("completion-note").textContent = "각 방문자의 세 조회가 끝나면 완료";
  $("run-status").className = "status-pill running";
  $("run-status").textContent = `${progress}실행 중`;
  $("timeline").innerHTML = '<div class="timeline-empty running"><span aria-hidden="true">≋</span><p>서버에 실제 상품 조회 요청을 보냈습니다.</p><small>완료 후 서버 측정값으로 타임라인을 그립니다.</small></div>';
  renderServices(null);
  setNotice(mode === "blocking"
    ? "동기 함수가 이벤트 루프를 차지하는 동안, 다른 요청의 대기 시간이 늘어나는지 지켜보세요."
    : "조회 응답을 기다리는 동안에도 /health 요청을 처리하는지 함께 확인하세요.");
  renderHealth();
  state.started = performance.now();
  state.timer = setInterval(() => {
    $("elapsed").textContent = seconds(performance.now() - state.started);
    renderHealth();
  }, 75);

  const control = { active: true };
  const requests = Array.from({ length: visitors }, (_, i) => (async () => {
    const query = new URLSearchParams({ mode, scale, visitor: i + 1 });
    const result = await fetchJSON(`/api/product?${query}`);
    state.completed += 1;
    $("completed").textContent = state.completed;
    return result;
  })());
  const monitor = monitorHealth(control);
  // 다른 요청이 실패해도 이미 보낸 요청을 모두 기다린 뒤 다음 실험으로 넘어갑니다.
  const settled = await Promise.allSettled(requests);
  const elapsed = performance.now() - state.started;
  control.active = false;
  await monitor;
  clearInterval(state.timer);
  state.timer = null;
  $("elapsed").textContent = seconds(elapsed);
  renderHealth();
  const successful = settled.filter((r) => r.status === "fulfilled").map((r) => r.value);
  if (successful.length) {
    renderTimeline(successful);
    renderServices(successful.find((r) => r.visitor === 1) || successful[0]);
  }
  if (successful.length !== visitors) {
    throw new Error(`상품 조회 ${visitors - successful.length}건 실패. 서버 실행 상태와 터미널 로그를 확인해 주세요.`);
  }
  const healthPeak = state.healthSamples.length ? Math.max(...state.healthSamples) : null;
  state.history.unshift({ mode, visitors, scale, elapsed, healthPeak, healthErrors: state.healthErrors });
  state.history = state.history.slice(0, 12);
  renderHistory();
  $("run-status").className = "status-pill";
  $("run-status").textContent = `${progress}조회 완료`;
  $("elapsed-note").textContent = "모든 방문자의 응답 수신까지 측정";
  $("completion-note").textContent = "재고 · 리뷰 · 배송 조회 완료";
  const healthText = healthPeak === null ? "다른 요청은 측정하지 못했습니다."
    : healthPeak > 500 ? `다른 요청도 최대 ${seconds(healthPeak)}초 기다렸습니다.`
      : "다른 요청도 짧은 대기로 응답했습니다.";
  setNotice(`${visitors}명의 상품 조회에 ${seconds(elapsed)}초가 걸렸습니다. ${healthText} 타임라인은 서버 실행 구간이며 네트워크 대기는 제외합니다.`);
}

async function run(compare = false) {
  if (state.busy || !state.config) return;
  const selected = settings().mode;
  setBusy(true);
  try {
    if (compare) {
      for (let i = 0; i < state.config.modes.length; i++) {
        await runScenario(state.config.modes[i].id, `${i + 1}/4 · `);
      }
      setNotice("네 가지 방식의 비교를 마쳤습니다. 실험 기록에서 전체 조회 시간과 다른 요청의 대기 시간을 비교해 보세요.");
    } else {
      await runScenario(selected);
    }
  } catch (error) {
    if (state.timer) clearInterval(state.timer);
    state.timer = null;
    $("run-status").className = "status-pill error";
    $("run-status").textContent = "요청 실패";
    $("elapsed-note").textContent = "연결 상태를 확인한 후 다시 시도하세요";
    setNotice(`${error.message} 서버 실행 후 이 페이지를 새로고침해 주세요.`, true);
  } finally {
    setBusy(false);
  }
}

async function initialize() {
  try {
    state.config = await fetchJSON("/api/config");
    const options = $("mode-options");
    state.config.modes.forEach((mode) => {
      const label = document.createElement("label");
      label.className = "mode-option";
      label.title = mode.description;
      const input = document.createElement("input");
      input.type = "radio";
      input.name = "mode";
      input.value = mode.id;
      input.checked = mode.id === "async-concurrent";
      const copy = document.createElement("span");
      const name = document.createElement("strong");
      name.textContent = mode.name;
      const tag = document.createElement("small");
      tag.textContent = mode.tag;
      copy.append(name, tag);
      label.append(input, copy);
      options.append(label);
    });
    document.querySelectorAll('.controls input, .controls select').forEach((el) => el.addEventListener("change", () => {
      updateMode();
      resetDisplay();
    }));
    $("run").addEventListener("click", () => run());
    $("compare").addEventListener("click", () => run(true));
    $("clear-history").addEventListener("click", () => { state.history = []; renderHistory(); });
    updateMode();
    setBusy(false);
  } catch {
    $("expected").textContent = "서버 연결 실패";
    $("mode-code").textContent = "서버 실행 후 페이지를 새로고침해 주세요.";
    setNotice("설정을 가져오지 못했습니다. 가이드에 따라 FastAPI 서버를 실행하고 http://127.0.0.1:8017 로 접속해 주세요.", true);
  }
}

initialize();
