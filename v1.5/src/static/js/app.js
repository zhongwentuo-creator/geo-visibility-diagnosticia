const TOTAL_STAGES = 9;
const API_BASE = window.location.protocol === 'file:' ? 'http://127.0.0.1:8000' : '';

const stageNames = {
  1: '用户画像构建', 2: '基建评估', 3: '竞品分析', 4: 'AI 搜索测试', 5: 'GEO 效果汇总',
  6: '舆情扫描', 7: '综合总览', 8: 'AIVO 评分', 9: '建议系统',
};

const sampleStages = {
  1: '识别 3 类核心用户及其搜索意图', 2: '基建完善度 55/100', 3: '识别竞品：小度、阿尔法蛋',
  4: '完成 6 个搜索查询测试', 5: '跨平台表现已汇总', 6: '舆情风险等级：中等',
  7: '亮点 2 个，风险 3 个', 8: 'AIVO 总分 74/100（中等）', 9: '生成 5 条优化建议',
};

const sampleDimensions = [
  { name: 'AI 搜索可见度', score: 58 }, { name: '基建完善度', score: 55 },
  { name: '竞品对比优势', score: 60 }, { name: '舆情健康度', score: 56 },
];

let isRunning = false;
let eventSource = null;
let activeTaskId = null;
let recoveryTimer = null;
let recoveryInFlight = false;
let completedStages = new Set();

function getEl(id) { return document.getElementById(id); }

function setConnection(label, state = '') {
  const el = getEl('connection-state');
  el.className = `connection-state ${state}`;
  el.innerHTML = `<span class="status-dot"></span>${escapeHtml(label)}`;
}

function setMessage(message = '', isError = false) {
  const el = getEl('form-message');
  el.textContent = message;
  el.classList.toggle('is-error', isError);
}

function focusComposer() { getEl('diagnostic-request').focus(); }

function selectRailNav(link) {
  document.querySelectorAll('.rail-link').forEach((item) => {
    const isActive = item === link;
    item.classList.toggle('is-active', isActive);
    if (isActive) item.setAttribute('aria-current', 'page');
    else item.removeAttribute('aria-current');
    const icon = item.querySelector('.rail-icon');
    if (!icon) return;
    icon.className = `rail-icon ${isActive ? icon.dataset.solid : icon.dataset.regular}`;
    icon.setAttribute('aria-hidden', 'true');
  });
}

function loadRecent(button) {
  getEl('diagnostic-request').value = `帮我诊断${button.dataset.brand}，产品类型是${button.dataset.category}，重点关注 AI 搜索中的 GEO 可见度。`;
  syncIntentFromRequest();
  focusComposer();
}

function parseDiagnosticIntent(request) {
  const text = request.trim();
  const website = text.match(/https?:\/\/[^\s，。！？；）】]+/i)?.[0] || '';
  const quotedBrand = text.match(/[「“"']([^」”"']{2,24})[」”"']/)?.[1] || '';
  const actionBrand = text.match(/(?:诊断|分析|评估|检查)(?:一下|下)?(?:品牌)?\s*[「“"']?([A-Za-z0-9\u4e00-\u9fff·_-]{2,24})/)?.[1] || '';
  const namedBrand = text.match(/(?:品牌(?:是|为|叫|名为)|针对)\s*[「“"']?([A-Za-z0-9\u4e00-\u9fff·_-]{2,24})/)?.[1] || '';
  const brand = cleanBrand(quotedBrand || actionBrand || namedBrand);
  const explicitCategory = text.match(/(?:产品类型|品类|产品(?:是|为|属于))\s*[:：]?\s*([^，。；！？]+)/)?.[1] || text.match(/(?:它|这(?:是|款产品)?)(?:是|为)一?款?([^，。；！？]+)/)?.[1] || '';
  const category = cleanCategory(explicitCategory) || inferCategory(text);
  return { brand, category, website };
}

function cleanBrand(value) {
  return value.replace(/(?:在(?:AI|人工智能|搜索)|的(?:GEO|可见度)|(?:GEO|可见度|品牌)).*$/i, '').trim();
}

function cleanCategory(value) {
  return value.replace(/^(?:是|为|属于)\s*/, '').replace(/^(?:一款|一个)/, '').trim();
}

function inferCategory(text) {
  if (/智能音箱|语音助手/.test(text)) return '智能音箱与 AI 助手';
  if (/学习机|学习设备/.test(text)) return '儿童智能学习设备';
  if (/儿童/.test(text) && /(AI|陪伴|对话|智能体)/i.test(text)) return '儿童 AI 对话智能体';
  return '';
}

function syncIntentFromRequest() {
  const parsed = parseDiagnosticIntent(getEl('diagnostic-request').value);
  if (parsed.brand) getEl('brand-input').value = parsed.brand;
  if (parsed.category) getEl('category-input').value = parsed.category;
  if (parsed.website) getEl('website-input').value = parsed.website;
}

function resetWorkspace() {
  closeStream();
  isRunning = false;
  activeTaskId = null;
  completedStages = new Set();
  getEl('conversation').replaceChildren();
  getEl('welcome-panel').classList.remove('hidden');
  getEl('app-shell').classList.remove('is-conversation-active');
  getEl('diagnosis-form').reset();
  getEl('intent-details').open = false;
  setMessage('');
  setConnection('准备就绪');
  setStartButton(false);
  getEl('scroll-region').scrollTo({ top: 0, behavior: 'smooth' });
  focusComposer();
}

function setStartButton(running) {
  const button = getEl('btn-start');
  button.disabled = running;
  button.innerHTML = running
    ? '<span>诊断中</span><i class="fa-solid fa-spinner fa-spin" aria-hidden="true"></i>'
    : '<span>开始诊断</span><i class="fa-solid fa-arrow-up" aria-hidden="true"></i>';
}

function readFormData() {
  return {
    brand: getEl('brand-input').value.trim(),
    category: getEl('category-input').value.trim(),
    website: getEl('website-input').value.trim() || null,
    platform: getEl('platform-select').value,
    request: getEl('diagnostic-request').value.trim(),
  };
}

async function startDiagnosis(event) {
  event.preventDefault();
  if (isRunning) return;
  const form = readFormData();
  if (!form.brand || !form.category) {
    getEl('intent-details').open = true;
    setMessage('未能从描述中识别完整信息，请补充品牌名称和产品类型。', true);
    (!form.brand ? getEl('brand-input') : getEl('category-input')).focus();
    return;
  }

  prepareRun(form);
  try {
    const response = await fetch(`${API_BASE}/api/diagnose`, {
      method: 'POST', headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ brand: form.brand, category: form.category, website: form.website, platform: form.platform }),
    });
    if (!response.ok) throw new Error(`服务返回 ${response.status}`);
    const task = await response.json();
    activeTaskId = task.task_id;
    connectStream(task.task_id);
  } catch (error) {
    finishWithError('无法连接本地诊断服务。请启动 FastAPI 后重试；也可以使用“预览流程”查看界面。', error);
  }
}

function prepareRun(form) {
  closeStream();
  isRunning = true;
  completedStages = new Set();
  getEl('welcome-panel').classList.add('hidden');
  getEl('conversation').replaceChildren();
  getEl('app-shell').classList.add('is-conversation-active');
  setStartButton(true);
  setMessage('已提交诊断请求，正在连接实时进度…');
  setConnection('诊断进行中', 'is-running');
  appendUserMessage(form.request || `帮我诊断${form.brand}，产品类型是${form.category}。`);
  appendIntro(form.brand, form.category);
  appendProgress();
  getEl('diagnostic-request').value = '';
  scrollConversation();
}

function connectStream(taskId) {
  eventSource = new EventSource(`${API_BASE}/api/diagnose/${encodeURIComponent(taskId)}/stream`);
  eventSource.onopen = () => {
    clearRecoveryTimer();
    if (isRunning) setConnection('实时连接正常', 'is-running');
  };
  eventSource.addEventListener('start', (event) => {
    const data = JSON.parse(event.data);
    setMessage(`已连接，正在诊断「${data.brand}」。`);
  });
  eventSource.addEventListener('stage_start', (event) => onStageStart(JSON.parse(event.data)));
  eventSource.addEventListener('stage_complete', (event) => onStageComplete(JSON.parse(event.data)));
  eventSource.addEventListener('search_progress', (event) => onSearchProgress(JSON.parse(event.data)));
  eventSource.addEventListener('heartbeat', (event) => onHeartbeat(JSON.parse(event.data)));
  eventSource.addEventListener('complete', (event) => onComplete(JSON.parse(event.data)));
  eventSource.addEventListener('error', (event) => {
    if (event.data) {
      onStreamError(JSON.parse(event.data));
    } else if (isRunning) {
      recoverTaskStatus();
    }
  });
}

function startDemo() {
  if (isRunning) return;
  activeTaskId = null;
  const form = readFormData();
  const demoForm = { brand: form.brand || '示例品牌', category: form.category || '儿童 AI 对话智能体', request: form.request };
  if (!form.brand) getEl('brand-input').value = demoForm.brand;
  if (!form.category) getEl('category-input').value = demoForm.category;
  prepareRun(demoForm);
  setMessage('正在预览 9 阶段工作流（演示数据）。');
  let index = 1;
  const runStage = () => {
    if (!isRunning) return;
    if (index > TOTAL_STAGES) {
      onComplete({ aivo_score: 74, grade: '中等', demo: true });
      return;
    }
    onStageStart({ stage: index, name: stageNames[index] });
    window.setTimeout(() => {
      onStageComplete({ stage: index, name: stageNames[index], summary: sampleStages[index], elapsed_ms: 680 + index * 120 });
      index += 1;
      window.setTimeout(runStage, 220);
    }, 360);
  };
  window.setTimeout(runStage, 300);
}

function getAssistantTurn() { return getEl('assistant-turn') || getEl('conversation'); }

function appendUserMessage(request) {
  const message = document.createElement('article');
  message.className = 'user-message fade-in';
  message.innerHTML = `<p><span class="sr-only">用户问题：</span>${escapeHtml(request)}</p>`;
  getEl('conversation').appendChild(message);
}

function appendIntro(brand, category) {
  const intro = document.createElement('article');
  intro.id = 'assistant-turn';
  intro.className = 'assistant-turn fade-in';
  intro.innerHTML = `
    <div class="assistant-turn-heading">
      <span class="trace-symbol"><i class="fa-solid fa-magnifying-glass" aria-hidden="true"></i></span>
      <div><p class="assistant-label">AI 诊断师</p><h3>正在规划「${escapeHtml(brand)}」的 GEO 诊断</h3><p class="assistant-context">${escapeHtml(category)} · 共 ${TOTAL_STAGES} 个诊断阶段</p></div>
    </div>`;
  getEl('conversation').appendChild(intro);
}

function appendProgress() {
  const progress = document.createElement('div');
  progress.className = 'progress-summary fade-in';
  progress.id = 'progress-summary';
  progress.innerHTML = '<span id="progress-label">准备 9 个诊断阶段</span><div class="progress-track"><div class="progress-fill" id="progress-fill"></div></div><span id="progress-value">0%</span>';
  getAssistantTurn().appendChild(progress);
}

function onStageStart(data) {
  const id = `stage-${data.stage}`;
  let trace = getEl(id);
  if (!trace) {
    trace = document.createElement('article');
    trace.id = id;
    trace.className = 'stage-trace is-running fade-in';
    trace.innerHTML = `<span class="trace-symbol"><i class="fa-solid fa-spinner fa-spin" aria-hidden="true"></i></span><div><h3>阶段 ${data.stage}/${TOTAL_STAGES} · ${escapeHtml(data.name)}</h3><p class="stage-summary">正在执行诊断…</p></div><span class="stage-meta">运行中</span>`;
    getAssistantTurn().appendChild(trace);
  }
  updateProgress(completedStages.size);
  scrollConversation();
}

function onStageComplete(data) {
  if (!getEl(`stage-${data.stage}`)) onStageStart(data);
  const trace = getEl(`stage-${data.stage}`);
  trace.classList.remove('is-running');
  trace.classList.add('is-complete');
  trace.querySelector('.trace-symbol').innerHTML = '<i class="fa-solid fa-check" aria-hidden="true"></i>';
  trace.querySelector('.stage-summary').textContent = data.summary || '阶段已完成';
  trace.querySelector('.stage-meta').textContent = data.elapsed_ms ? `${Math.round(data.elapsed_ms / 100) / 10}s` : '完成';
  completedStages.add(data.stage);
  updateProgress(completedStages.size);
  scrollConversation();
}

function onSearchProgress(data) {
  const trace = getEl('stage-4');
  if (!trace) return;
  const summary = `已完成 ${data.completed}/${data.total} 条 AI 搜索查询`;
  trace.querySelector('.stage-summary').textContent = summary;
  trace.querySelector('.stage-meta').textContent = `${data.completed}/${data.total}`;
  setMessage(`正在执行 AI 搜索测试：${summary}。`);
  scrollConversation();
}

function onHeartbeat(data) {
  if (!isRunning) return;
  const search = data.search_progress;
  const summary = search
    ? `AI 搜索仍在运行：已完成 ${search.completed}/${search.total} 条查询。`
    : data.message || '诊断仍在运行，连接保持正常。';
  setConnection('实时连接正常', 'is-running');
  setMessage(summary);
}

function updateProgress(completed) {
  const percent = Math.round((completed / TOTAL_STAGES) * 100);
  const fill = getEl('progress-fill');
  if (fill) fill.style.width = `${percent}%`;
  const label = getEl('progress-label');
  if (label) label.textContent = completed === TOTAL_STAGES ? '9 个诊断阶段已完成' : `已完成 ${completed}/${TOTAL_STAGES} 个诊断阶段`;
  const value = getEl('progress-value');
  if (value) value.textContent = `${percent}%`;
}

async function onComplete(data) {
  closeStream();
  isRunning = false;
  setStartButton(false);
  setConnection('诊断完成');
  setMessage('诊断已完成。你可以查看报告或重新发起一次诊断。');
  updateProgress(TOTAL_STAGES);
  let report = null;
  if (!data.demo && activeTaskId) {
    try {
      const response = await fetch(`${API_BASE}/api/diagnose/${encodeURIComponent(activeTaskId)}/report`);
      if (response.ok) report = await response.json();
    } catch (_) { /* 摘要事件仍可展示，报告数据稍后可重取 */ }
  }
  appendReport(data, report);
  scrollConversation();
}

function appendReport(data, report) {
  const aivo = report?.aivoScore || report?.aivo_score || {};
  const score = data.aivo_score ?? aivo.total ?? 74;
  const grade = data.grade ?? aivo.grade ?? '已完成';
  const dimensions = normalizeDimensions(aivo);
  const card = document.createElement('article');
  card.className = 'report-card fade-in';
  card.innerHTML = `
    <div class="report-topline"><div><h3>可见度诊断摘要</h3><p class="report-caption">AIVO 评分已生成，可据此继续查看优化方向。</p></div><div class="score-display"><strong>${escapeHtml(String(score))}</strong><span>/ 100 · ${escapeHtml(grade)}</span></div></div>
    <div class="dimension-list">${dimensions.map((item) => `<div class="dimension"><span class="dimension-label">${escapeHtml(item.name)}</span><div class="dimension-track"><span style="--score:${item.score}%"></span></div><strong class="dimension-value">${item.score}</strong></div>`).join('')}</div>
    <div class="report-actions"><button class="secondary-button" type="button" onclick="openReport('json')"><i class="fa-regular fa-file-lines" aria-hidden="true"></i>查看 JSON 报告</button><button class="secondary-button" type="button" onclick="openReport('html')"><i class="fa-solid fa-arrow-down" aria-hidden="true"></i>下载 HTML 报告</button><button class="secondary-button" type="button" onclick="resetWorkspace()"><i class="fa-solid fa-rotate-right" aria-hidden="true"></i>新建诊断</button></div>`;
  getAssistantTurn().appendChild(card);
  window.setTimeout(() => card.querySelectorAll('.dimension-track span').forEach((bar) => { bar.style.width = bar.style.getPropertyValue('--score'); }), 80);
}

async function recoverTaskStatus() {
  if (!activeTaskId || !isRunning || recoveryInFlight) return;
  recoveryInFlight = true;
  setConnection('正在恢复连接', 'is-running');
  setMessage('实时连接短暂中断，诊断仍在后台继续，正在恢复状态…');
  try {
    const response = await fetch(`${API_BASE}/api/diagnose/${encodeURIComponent(activeTaskId)}`);
    if (!response.ok) throw new Error(`服务返回 ${response.status}`);
    const task = await response.json();
    (task.stages || []).forEach((stage) => onStageComplete(stage));
    if (task.search_progress) onSearchProgress(task.search_progress);
    if (task.status === 'success') {
      await onComplete({ aivo_score: task.aivo_score, grade: '已完成' });
      return;
    }
    if (task.status === 'error') {
      onStreamError({ message: '后台诊断未完成。', error: task.error });
      return;
    }
    scheduleStatusRecovery();
  } catch (_) {
    scheduleStatusRecovery();
  } finally {
    recoveryInFlight = false;
  }
}

function scheduleStatusRecovery() {
  if (recoveryTimer || !isRunning) return;
  recoveryTimer = window.setTimeout(() => {
    recoveryTimer = null;
    recoverTaskStatus();
  }, 5000);
}

function clearRecoveryTimer() {
  if (recoveryTimer) window.clearTimeout(recoveryTimer);
  recoveryTimer = null;
}

function normalizeDimensions(aivo) {
  const raw = aivo?.dimensions || aivo?.dimensionScores;
  if (Array.isArray(raw)) return raw.slice(0, 4).map((item, index) => ({ name: item.name || item.label || sampleDimensions[index]?.name || '诊断维度', score: Number(item.score ?? item.value ?? 0) }));
  if (raw && typeof raw === 'object') return Object.entries(raw).slice(0, 4).map(([name, score]) => ({ name, score: Number(score) }));
  return sampleDimensions;
}

function onStreamError(data) { finishWithError(data.message || '诊断过程中发生错误，请稍后重试。', data.error); }

function finishWithError(message, detail = '') {
  closeStream();
  isRunning = false;
  setStartButton(false);
  setConnection('连接异常', 'is-error');
  setMessage(message, true);
  const card = document.createElement('article');
  card.className = 'error-card fade-in';
  card.innerHTML = `<h3><i class="fa-solid fa-triangle-exclamation" aria-hidden="true"></i> 暂时无法完成诊断</h3><p>${escapeHtml(message)}${detail ? `（${escapeHtml(String(detail))}）` : ''}</p>`;
  getAssistantTurn().appendChild(card);
  scrollConversation();
}

function openReport(type) {
  if (!activeTaskId) { setMessage('当前为流程预览，没有可下载的真实报告。', true); return; }
  const suffix = type === 'html' ? '/report/html' : '/report';
  window.open(`${API_BASE}/api/diagnose/${encodeURIComponent(activeTaskId)}${suffix}`, '_blank', 'noopener');
}

function closeStream() {
  clearRecoveryTimer();
  if (eventSource) { eventSource.close(); eventSource = null; }
}
function scrollConversation() { window.setTimeout(() => getEl('scroll-region').scrollTo({ top: getEl('scroll-region').scrollHeight, behavior: 'smooth' }), 0); }
function showHelp() { getEl('help-modal').showModal(); }
function closeHelp() { getEl('help-modal').close(); }
function escapeHtml(value) { const div = document.createElement('div'); div.textContent = value; return div.innerHTML; }

document.addEventListener('keydown', (event) => {
  if ((event.metaKey || event.ctrlKey) && event.key === 'Enter') getEl('diagnosis-form').requestSubmit();
});

getEl('diagnostic-request').addEventListener('input', syncIntentFromRequest);
