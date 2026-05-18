// ── STATE ──
let files = [];
let results = [];
let selected = new Set();
let activeFilter = 'all';
let activeView = 'list';
let overrideFname = null;
let overrideChoice = null;
let compactIdx = 0;

// ── SCREEN MANAGEMENT ──
function showScreen(id) {
  document.querySelectorAll('.screen').forEach(s => s.classList.remove('active'));
  document.getElementById(id).classList.add('active');
}

function goBack() {
  selected.clear();
  updateBulkBar();
  showScreen('landing');
}

// ── FILE SELECTION ──
function filesChosen(fl) {
  files = Array.from(fl).filter(f => f.type.startsWith('image/') || /\.(jpg|jpeg|png|bmp|tiff|tif)$/i.test(f.name));
  updateFileCount();
}

function updateFileCount() {
  const fc = document.getElementById('fileCount');
  const btn = document.getElementById('analyzeBtn');
  if (files.length > 0) {
    fc.textContent = `${files.length} image${files.length > 1 ? 's' : ''} ready`;
    btn.disabled = false;
  } else {
    fc.textContent = '';
    btn.disabled = true;
  }
}

// Drop zone
const dz = document.getElementById('dropZone');
dz.addEventListener('dragover', e => { e.preventDefault(); dz.classList.add('drag'); });
dz.addEventListener('dragleave', () => dz.classList.remove('drag'));
dz.addEventListener('drop', e => {
  e.preventDefault(); dz.classList.remove('drag');
  const fl = e.dataTransfer.files;
  if (fl.length) { filesChosen(fl); }
});
dz.addEventListener('click', () => document.getElementById('fileIn').click());

// ── ANALYSIS ──
async function startAnalysis() {
  if (!files.length) return;
  showScreen('processing');

  // Reset bar animation
  const bar = document.getElementById('procBar');
  bar.style.animation = 'none'; bar.offsetHeight; bar.style.animation = '';

  const msgs = ['Sending images to AI model…','Running defect detection…','Classifying panels…','Calculating confidence scores…','Finalizing results…'];
  let mi = 0;
  const msgEl = document.getElementById('procMsg');
  const interval = setInterval(() => { msgEl.textContent = msgs[Math.min(++mi, msgs.length-1)]; }, 900);

  try {
    const fd = new FormData();
    files.forEach(f => fd.append('files', f));
    fd.append('auto_crop', document.getElementById('cropToggle').checked ? 'true' : 'false');

    const res = await fetch('/api/upload', { method: 'POST', body: fd });
    if (!res.ok) throw new Error(`Server error ${res.status}`);
    const data = await res.json();
    clearInterval(interval);

    if (data.results) {
      results = data.results.map(r => ({
        fname: r.filename,
        result: r.result,
        conf: r.confidence === 'Overwritten' ? 'Overwritten' : parseFloat(r.confidence),
        crop: r.crop_status,
        imgUrl: r.image_url || null
      }));
      selected.clear();
      renderAll();
      updateStats();
      showScreen('results');
    } else {
      throw new Error(data.message || 'Unknown error');
    }
  } catch (e) {
    clearInterval(interval);
    alert('Error: ' + e.message);
    showScreen('landing');
  }
}

// ── FILTER ──
function setFilter(f, el) {
  activeFilter = f;
  document.querySelectorAll('#filterPills .pill').forEach(p => p.classList.remove('active'));
  el.classList.add('active');
  renderAll();
}

function filtered() {
  if (activeFilter === 'all') return results;
  if (activeFilter === 'damaged') return results.filter(r => r.result === 'Damaged');
  if (activeFilter === 'safe') return results.filter(r => r.result === 'Not Damaged');
  if (activeFilter === 'uncertain') return results.filter(r => r.result === 'Uncertain');
  return results;
}

// ── STATS ──
function updateStats() {
  const t = results.length;
  const d = results.filter(r => r.result === 'Damaged').length;
  const u = results.filter(r => r.result === 'Uncertain').length;
  const s = results.filter(r => r.result === 'Not Damaged').length;
  const confs = results.filter(r => typeof r.conf === 'number');
  const avg = confs.length ? (confs.reduce((a,r)=>a+r.conf,0)/confs.length).toFixed(1)+'%' : '—';
  document.getElementById('s-total').textContent = t;
  document.getElementById('s-damaged').textContent = d;
  document.getElementById('s-uncertain').textContent = u;
  document.getElementById('s-safe').textContent = s;
  document.getElementById('s-conf').textContent = avg;
}

// ── HELPERS ──
function badgeClass(result) {
  if (result === 'Damaged') return 'damaged';
  if (result === 'Not Damaged') return 'safe';
  if (result === 'Uncertain') return 'uncertain';
  return 'safe';
}

function confHTML(item) {
  if (item.conf === 'Overwritten') return '<span class="badge overwritten" style="font-size:10px">Overwritten</span>';
  const pct = typeof item.conf === 'number' ? item.conf : 0;
  const cls = pct > 90 ? '' : pct > 65 ? 'mid' : 'low';
  return `<div class="conf-cell"><div class="conf-bar"><div class="conf-fill ${cls}" style="width:${pct}%"></div></div><span class="conf-pct">${pct.toFixed(1)}%</span></div>`;
}

function thumbEl(item, w, h) {
  if (item.imgUrl) {
    return `<img src="${item.imgUrl}" style="width:${w}px;height:${h}px;border-radius:4px;object-fit:cover;display:block">`;
  }
  return `<div style="width:${w}px;height:${h}px;border-radius:4px;background:#1a2a1a"></div>`;
}

// ── RENDER ALL VIEWS ──
function renderAll() {
  renderList();
  renderGrid();
  renderCompact();
}

function renderList() {
  const data = filtered();
  const tb = document.getElementById('listBody');
  if (!data.length) { tb.innerHTML = `<tr><td colspan="6"><div class="empty"><p>No panels match this filter.</p></div></td></tr>`; return; }
  tb.innerHTML = data.map((item, i) => `
    <tr>
      <td><input type="checkbox" class="row-cb" data-f="${item.fname}" ${selected.has(item.fname)?'checked':''} onchange="toggleSel('${item.fname}',this.checked)" style="accent-color:var(--green)"></td>
      <td style="color:var(--text3);font-size:12px">${i+1}</td>
      <td class="fname-cell img-trigger" data-url="${item.imgUrl||''}" data-caption="${item.fname}" style="cursor:pointer;color:var(--green)">${item.fname}</td>
      <td class="img-trigger" data-url="${item.imgUrl||''}" data-caption="${item.fname}" style="cursor:pointer">${thumbEl(item, 52, 38)}</td>
      <td><span class="badge ${badgeClass(item.result)}">${item.result}</span></td>
      <td>${confHTML(item)}</td>
    </tr>`).join('');
}

function renderGrid() {
  const data = filtered();
  const gc = document.getElementById('gridBody');
  if (!data.length) { gc.innerHTML = `<div class="empty" style="grid-column:1/-1"><p>No panels match this filter.</p></div>`; return; }
  gc.innerHTML = data.map(item => `
    <div class="grid-card">
      <div class="grid-img-wrap img-trigger" data-url="${item.imgUrl||''}" data-caption="${item.fname}" style="cursor:${item.imgUrl?'zoom-in':'default'}">
        <input type="checkbox" class="grid-check row-cb" data-f="${item.fname}" ${selected.has(item.fname)?'checked':''} onchange="event.stopPropagation();toggleSel('${item.fname}',this.checked)" onclick="event.stopPropagation()">
        <div class="grid-badge"><span class="badge ${badgeClass(item.result)}">${item.result}</span></div>
        ${item.imgUrl
          ? `<img src="${item.imgUrl}" style="width:100%;height:100%;object-fit:cover;display:block;opacity:.9" onerror="this.outerHTML='<div style=\'width:100%;height:100%;background:linear-gradient(135deg,#1a2a1a,#0d150d)\'></div>'">`
          : `<div style="width:100%;height:100%;background:linear-gradient(135deg,#1a2a1a,#0d150d)"></div>`
        }
      </div>
      <div class="grid-info">
        <div class="grid-name">${item.fname}</div>
        ${confHTML(item)}
      </div>
    </div>`).join('');
}

function renderCompact() {
  const data = filtered();
  const cl = document.getElementById('compactList');
  if (!data.length) { cl.innerHTML = `<div class="empty"><p>No panels match this filter.</p></div>`; return; }
  cl.innerHTML = data.map((item, i) => `
    <div class="compact-row ${i===compactIdx?'active':''}" onclick="selectCompact(${i})">
      ${item.imgUrl
        ? `<img src="${item.imgUrl}" style="width:36px;height:28px;border-radius:3px;object-fit:cover;flex-shrink:0" onerror="this.style.display='none'">`
        : `<div style="width:36px;height:28px;border-radius:3px;background:linear-gradient(135deg,#1a2a1a,#0d150d);flex-shrink:0"></div>`
      }
      <span class="c-name">${item.fname}</span>
      <span class="badge ${badgeClass(item.result)}" style="flex-shrink:0;font-size:10px">${item.result}</span>
    </div>`).join('');
  showCompactDetail(data[Math.min(compactIdx, data.length-1)], Math.min(compactIdx, data.length-1));
}

function selectCompact(i) {
  compactIdx = i;
  const data = filtered();
  document.querySelectorAll('.compact-row').forEach((r,idx) => r.classList.toggle('active', idx===i));
  if (data[i]) showCompactDetail(data[i], i);
}

function showCompactDetail(item, i) {
  const det = document.getElementById('compactDetail');
  if (!item) { det.innerHTML = ''; return; }
  const pct = typeof item.conf === 'number' ? item.conf : 0;
  const confDisplay = item.conf === 'Overwritten' ? '<span class="badge overwritten">Overwritten</span>' : `${pct.toFixed(1)}%`;
  const confBar = item.conf !== 'Overwritten' ? `<div class="conf-bar" style="height:6px;background:var(--border)"><div class="conf-fill ${pct>90?'':pct>65?'mid':'low'}" style="width:${pct}%"></div></div>` : '';
  const imgBlock = item.imgUrl
    ? `<img src="${item.imgUrl}" style="width:100%;height:200px;border-radius:6px;object-fit:cover;display:block" onerror="this.outerHTML='<div style=\'width:100%;height:200px;border-radius:6px;background:linear-gradient(135deg,#1a2a1a,#0d150d)\'></div>'">`
    : `<div style="width:100%;height:200px;border-radius:6px;background:linear-gradient(135deg,#1a2a1a,#0d150d);display:flex;align-items:center;justify-content:center"><svg width=40 height=40 viewBox='0 0 24 24' fill=none stroke='#3A7D44' stroke-width=1><circle cx=12 cy=12 r=4/><line x1=12 y1=2 x2=12 y2=6/><line x1=12 y1=18 x2=12 y2=22/><line x1=2 y1=12 x2=6 y2=12/><line x1=18 y1=12 x2=22 y2=12/></svg></div>`;
  det.innerHTML = `
    ${imgBlock}
    <div class="detail-section">
      <div class="detail-row"><span class="detail-lbl">Filename</span><span class="detail-val" style="font-family:monospace;font-size:12px">${item.fname}</span></div>
      <div class="detail-row"><span class="detail-lbl">Classification</span><span class="badge ${badgeClass(item.result)}">${item.result}</span></div>
      <div class="detail-row"><span class="detail-lbl">Confidence</span><span class="detail-val">${confDisplay}</span></div>
      ${confBar}
      ${item.crop ? `<div class="detail-row"><span class="detail-lbl">Crop Status</span><span class="detail-val" style="font-size:12px">${item.crop}</span></div>` : ''}
    </div>
    <div class="detail-btns">
      <button class="detail-btn" onclick="openOverride('${item.fname}')">Override Label</button>
      <button class="detail-btn img-trigger" data-url="${item.imgUrl||''}" data-caption="${item.fname}" ${!item.imgUrl?'disabled':''}>View Full Image</button>
    </div>`;
}

// ── VIEW SWITCHING ──
function setView(v) {
  activeView = v;
  ['list','grid','compact'].forEach(id => {
    document.getElementById(`vp-${id}`).classList.toggle('active', id===v);
    document.getElementById(`vb-${id}`).classList.toggle('active', id===v);
  });
  if (v === 'compact') renderCompact();
}

// ── SELECTION ──
function toggleSel(fname, checked) {
  if (checked) selected.add(fname);
  else selected.delete(fname);
  syncCheckboxes(fname, checked);
  updateBulkBar();
  updateSelectAll();
}

function syncCheckboxes(fname, checked) {
  document.querySelectorAll(`.row-cb[data-f="${fname}"]`).forEach(cb => cb.checked = checked);
}

function toggleAll(checked) {
  filtered().forEach(item => { if (checked) selected.add(item.fname); else selected.delete(item.fname); });
  document.querySelectorAll('.row-cb').forEach(cb => cb.checked = checked);
  updateBulkBar();
}

function updateSelectAll() {
  const all = document.getElementById('selectAll');
  if (!all) return;
  const f = filtered();
  all.checked = f.length > 0 && f.every(item => selected.has(item.fname));
  all.indeterminate = !all.checked && f.some(item => selected.has(item.fname));
}

function clearSel() {
  selected.clear();
  document.querySelectorAll('.row-cb').forEach(cb => cb.checked = false);
  updateBulkBar();
  updateSelectAll();
}

function updateBulkBar() {
  const bar = document.getElementById('bulkBar');
  const cnt = document.getElementById('bulkCount');
  const n = selected.size;
  cnt.textContent = `${n} panel${n!==1?'s':''} selected`;
  bar.classList.toggle('visible', n > 0);
}

// ── BULK SELECT ──
function bulkAction(sel) {
  const v = sel.value; sel.value = '';
  if (!v) return;
  selected.clear();
  if (v === 'all') results.forEach(r => selected.add(r.fname));
  else if (v === 'damaged') results.filter(r => r.result==='Damaged').forEach(r => selected.add(r.fname));
  else if (v === 'safe') results.filter(r => r.result==='Not Damaged').forEach(r => selected.add(r.fname));
  else if (v === 'uncertain') results.filter(r => r.result==='Uncertain').forEach(r => selected.add(r.fname));
  renderAll();
  updateBulkBar();
}

// ── BULK OVERRIDE ──
async function bulkOverride(label) {
  if (!selected.size) return;
  const targets = Array.from(selected);
  for (const fname of targets) { await doOverride(fname, label); }
  selected.clear();
  renderAll();
  updateStats();
  updateBulkBar();
}

// ── SINGLE OVERRIDE ──
function openOverride(fname) {
  overrideFname = fname;
  overrideChoice = null;
  document.querySelectorAll('.modal-opt').forEach(o => o.classList.remove('selected'));
  document.getElementById('overrideFname').textContent = `File: ${fname}`;
  document.getElementById('overrideModal').classList.add('open');
}

function selectOpt(el) {
  document.querySelectorAll('.modal-opt').forEach(o => o.classList.remove('selected'));
  el.classList.add('selected');
  overrideChoice = el.dataset.val;
}

function closeModal() {
  document.getElementById('overrideModal').classList.remove('open');
  overrideFname = null; overrideChoice = null;
}

async function confirmOverride() {
  if (!overrideFname || !overrideChoice) { alert('Please select a classification.'); return; }
  await doOverride(overrideFname, overrideChoice);
  closeModal();
  renderAll();
  updateStats();
}

async function doOverride(fname, label) {
  try {
    const res = await fetch('/api/override', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ filename: fname, new_result: label })
    });
    const data = await res.json();
    if (data.status === 'success') {
      const item = results.find(r => r.fname === fname);
      if (item) { item.result = label; item.conf = 'Overwritten'; }
    }
  } catch(e) {
    const item = results.find(r => r.fname === fname);
    if (item) { item.result = label; item.conf = 'Overwritten'; }
  }
}

// ── EXPORT ──
function doExport(type, selOnly = false) {
  const endpoint = type === 'excel' ? '/api/download-report' : '/api/download-results';
  if (selOnly && selected.size > 0) {
    window.location.href = `${endpoint}?filenames=${encodeURIComponent(Array.from(selected).join(','))}`;
  } else {
    window.location.href = endpoint;
  }
}

// ── KEYBOARD ──
document.addEventListener('keydown', e => {
  if (e.key === 'Escape') { closeModal(); closeImgModal(); }
});

// ── IMAGE MODAL ──
function openImgModal(url, caption) {
  if (!url) return;
  document.getElementById('imgModalImg').src = url;
  document.getElementById('imgModalCaption').textContent = caption || '';
  document.getElementById('imgModal').classList.add('open');
}

function closeImgModal() {
  document.getElementById('imgModal').classList.remove('open');
  document.getElementById('imgModalImg').src = '';
}

// Event delegation for img-trigger clicks (avoids escaping issues with inline onclick)
document.addEventListener('click', e => {
  const trigger = e.target.closest('.img-trigger');
  if (trigger) {
    const url = trigger.dataset.url;
    const caption = trigger.dataset.caption;
    if (url) openImgModal(url, caption);
  }
});

document.getElementById('overrideModal').addEventListener('click', e => {
  if (e.target === document.getElementById('overrideModal')) closeModal();
});
