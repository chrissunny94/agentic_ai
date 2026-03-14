let chartInstance = null;
let animationId = null;

// Populate model selector on load
window.addEventListener('DOMContentLoaded', async () => {
  try {
    const res = await fetch('/models');
    const models = await res.json();
    const sel = document.getElementById('modelSelect');
    sel.innerHTML = models.map(m =>
      `<option value="${m}">${m.charAt(0).toUpperCase() + m.slice(1)}</option>`
    ).join('');
    sel.addEventListener('change', onModelChange);
    onModelChange(); // run once on load
  } catch (e) {
    console.warn('Could not load model list:', e);
  }
});

async function onModelChange() {
  const provider = document.getElementById('modelSelect').value;
  const wrap = document.getElementById('ollamaModelWrap');
  if (provider !== 'ollama') { wrap.style.display = 'none'; return; }

  wrap.style.display = 'block';
  const ollamaSel = document.getElementById('ollamaModelSelect');
  ollamaSel.innerHTML = '<option>loading...</option>';
  try {
    const res  = await fetch('/ollama-models');
    const data = await res.json();
    if (data.available.length === 0) {
      ollamaSel.innerHTML = '<option value="">no models found</option>';
    } else {
      ollamaSel.innerHTML = data.available.map(m =>
        `<option value="${m}" ${m === data.current ? 'selected' : ''}>${m}</option>`
      ).join('');
    }
  } catch (e) {
    ollamaSel.innerHTML = '<option value="llama3.1">llama3.1</option>';
  }
}

function setStatus(state, text) {
  document.getElementById('statusDot').className = 'status-dot ' + state;
  document.getElementById('statusText').textContent = text;
}

async function generateCode() {
  const prompt      = document.getElementById('promptInput').value.trim();
  const provider    = document.getElementById('modelSelect').value;
  const ollamaSel   = document.getElementById('ollamaModelSelect');
  const ollamaModel = (provider === 'ollama' && ollamaSel.value) ? ollamaSel.value : null;
  const btn         = document.getElementById('generateBtn');
  if (!prompt) return;

  btn.disabled = true;
  btn.innerHTML = 'Working<br>...';
  cancelAnimationFrame(animationId);
  const displayName = ollamaModel ? `ollama/${ollamaModel}` : provider;
  setStatus('active', `${displayName} — compiling simulation...`);

  // Reset UI
  document.getElementById('animationCanvas').style.display = 'none';
  document.getElementById('animEmpty').style.display = 'flex';
  document.getElementById('plotCanvas').style.display = 'none';
  document.getElementById('plotEmpty').style.display = 'flex';
  document.getElementById('codeOutput').textContent = '// generating...';
  document.getElementById('simOutput').textContent = '// awaiting output...';

  try {
    const response = await fetch('/generate', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ prompt, model: provider, ollama_model: ollamaModel })
    });

    const data = await response.json();
    document.getElementById('codeOutput').textContent = data.code || '// no code returned';

    if (response.ok) {
      setStatus('success', `${data.model || displayName} — compiled in ${data.attempts} attempt${data.attempts > 1 ? 's' : ''}`);
      const parsed = typeof data.output === 'object' ? data.output : null;
      const rawOutput = parsed ? parsed.text : data.output;

      const badge = `[✓ ${data.attempts} attempt${data.attempts > 1 ? 's' : ''}]\n\n`;
      document.getElementById('simOutput').textContent = badge + (rawOutput || '');

      if (parsed) {
        if (parsed.animation?.length) renderAnimation(parsed.animation);
        if (parsed.plot && Object.keys(parsed.plot).length) renderChart(parsed.plot);
      } else {
        parseAndRender(data.output);
      }
    } else {
      setStatus('error', `failed — ${data.error}`);
      document.getElementById('simOutput').textContent =
        `[✗ FAILED]\n${data.error || ''}\n\n${data.last_log || ''}`;
    }
  } catch (err) {
    setStatus('error', 'network error');
    console.error(err);
  } finally {
    btn.disabled = false;
    btn.innerHTML = 'Run<br>Agent';
  }
}

function parseAndRender(text) {
  const plotMatch = text.match(/---PLOT_DATA---\n([\s\S]*?)\n---END_PLOT---/);
  if (plotMatch) {
    try { renderChart(JSON.parse(plotMatch[1])); } catch (e) {}
  }
  const animMatch = text.match(/---ANIMATION_DATA---\n([\s\S]*?)\n---END_ANIMATION---/);
  if (animMatch) {
    try { renderAnimation(JSON.parse(animMatch[1])); } catch (e) {}
  }
}

function renderChart(data) {
  const canvas = document.getElementById('plotCanvas');
  const empty  = document.getElementById('plotEmpty');
  canvas.style.display = 'block';
  empty.style.display  = 'none';

  const ctx = canvas.getContext('2d');
  if (chartInstance) chartInstance.destroy();

  const palette = ['#00ffb3', '#7b61ff', '#ff6b6b', '#ffd166', '#06d6a0'];
  const datasets = Object.keys(data).map((label, i) => ({
    label,
    data: data[label].map(p => ({ x: p[0], y: p[1] })),
    borderColor: palette[i % palette.length],
    backgroundColor: palette[i % palette.length] + '18',
    showLine: true,
    pointRadius: 0,
    borderWidth: 1.5,
    tension: 0.3,
  }));

  chartInstance = new Chart(ctx, {
    type: 'scatter',
    data: { datasets },
    options: {
      responsive: true,
      animation: { duration: 600, easing: 'easeOutQuart' },
      plugins: {
        legend: {
          labels: {
            color: '#6b6b88',
            font: { family: "'Space Mono', monospace", size: 11 },
            boxWidth: 12,
          }
        }
      },
      scales: {
        x: {
          type: 'linear',
          grid: { color: 'rgba(255,255,255,0.04)' },
          ticks: { color: '#6b6b88', font: { family: "'Space Mono', monospace", size: 10 } }
        },
        y: {
          grid: { color: 'rgba(255,255,255,0.04)' },
          ticks: { color: '#6b6b88', font: { family: "'Space Mono', monospace", size: 10 } }
        }
      }
    }
  });
}

function renderAnimation(frames) {
  const canvas = document.getElementById('animationCanvas');
  const empty  = document.getElementById('animEmpty');
  canvas.style.display = 'block';
  empty.style.display  = 'none';

  const ctx = canvas.getContext('2d');
  let frameIdx = 0;
  const trail = [];
  const MAX_TRAIL = 28;

  function draw() {
    const frame = frames[frameIdx];
    const W = canvas.offsetWidth;
    const H = canvas.offsetHeight;
    canvas.width  = W;
    canvas.height = H;

    // Background
    ctx.fillStyle = '#0d0d14';
    ctx.fillRect(0, 0, W, H);

    // Grid
    ctx.strokeStyle = 'rgba(255,255,255,0.04)';
    ctx.lineWidth = 1;
    for (let gx = 0; gx < W; gx += 40) {
      ctx.beginPath(); ctx.moveTo(gx, 0); ctx.lineTo(gx, H); ctx.stroke();
    }
    for (let gy = 0; gy < H; gy += 40) {
      ctx.beginPath(); ctx.moveTo(0, gy); ctx.lineTo(W, gy); ctx.stroke();
    }

    // Axes
    ctx.strokeStyle = 'rgba(0,255,179,0.12)';
    ctx.lineWidth = 1;
    ctx.beginPath(); ctx.moveTo(W / 2, 0); ctx.lineTo(W / 2, H); ctx.stroke();
    ctx.beginPath(); ctx.moveTo(0, H / 2); ctx.lineTo(W, H / 2); ctx.stroke();

    const cx = W / 2 + (frame.x * 50);
    const cy = H / 2 + (frame.y * 50);

    trail.push({ x: cx, y: cy });
    if (trail.length > MAX_TRAIL) trail.shift();

    // Trail
    for (let i = 0; i < trail.length - 1; i++) {
      const alpha = (i / MAX_TRAIL) * 0.5;
      ctx.beginPath();
      ctx.arc(trail[i].x, trail[i].y, (3 + (i / MAX_TRAIL) * 8) * 0.3, 0, Math.PI * 2);
      ctx.fillStyle = `rgba(123,97,255,${alpha})`;
      ctx.fill();
    }

    // Glow ring
    const grad = ctx.createRadialGradient(cx, cy, 0, cx, cy, 32);
    grad.addColorStop(0, 'rgba(0,255,179,0.25)');
    grad.addColorStop(1, 'rgba(0,255,179,0)');
    ctx.beginPath();
    ctx.arc(cx, cy, 32, 0, Math.PI * 2);
    ctx.fillStyle = grad;
    ctx.fill();

    // Particle
    ctx.beginPath();
    ctx.arc(cx, cy, 10, 0, Math.PI * 2);
    ctx.fillStyle = '#00ffb3';
    ctx.fill();

    // Core
    ctx.beginPath();
    ctx.arc(cx, cy, 4, 0, Math.PI * 2);
    ctx.fillStyle = '#ffffff';
    ctx.fill();

    // Time readout
    ctx.fillStyle = 'rgba(107,107,136,0.8)';
    ctx.font = "10px 'Space Mono', monospace";
    ctx.fillText(`t = ${frame.t.toFixed(3)}s`, 12, H - 12);

    frameIdx = (frameIdx + 1) % frames.length;
    animationId = requestAnimationFrame(draw);
  }

  draw();
}
