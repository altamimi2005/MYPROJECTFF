import re

with open('c:/Users/qafms/OneDrive/Desktop/MYPROJECT/frontend/index.html', 'r', encoding='utf-8') as f:
    html = f.read()

# 1. Add CSS
css_to_add = '''
/* ─── RESULT VIEWS ─── */
.view-container { display: none; animation: fadeIn 0.3s ease; }
.view-container.active { display: block; }

/* Grid View */
.grid-view { display: grid; grid-template-columns: repeat(4, 1fr); gap: 20px; margin-bottom: 24px; }
.grid-card { background: var(--panel); border: 1px solid var(--chalk); border-radius: 8px; overflow: hidden; box-shadow: var(--shadow-sm); cursor: pointer; transition: transform 0.15s; }
.grid-card:hover { transform: translateY(-2px); box-shadow: var(--shadow-md); }
.grid-card-img-wrap { height: 160px; background: #1a1a1a; position: relative; }
.grid-card-img { width: 100%; height: 100%; object-fit: cover; opacity: 0.85; }
.grid-card-badge { position: absolute; top: 12px; left: 12px; z-index: 2; }
.grid-card-info { padding: 16px; }
.grid-card-name { font-family: 'JetBrains Mono', monospace; font-size: 11px; color: var(--graphite); margin-bottom: 12px; white-space: nowrap; overflow: hidden; text-overflow: ellipsis; }

/* Compact View (Master-Detail) */
.compact-view { display: flex; gap: 24px; align-items: flex-start; margin-bottom: 24px; }
.compact-left { flex: 1; background: var(--panel); border: 1px solid var(--chalk); border-radius: 10px; overflow: hidden; box-shadow: var(--shadow-sm); }
.compact-right { width: 440px; background: var(--panel); border: 1px solid var(--chalk); border-radius: 10px; overflow: hidden; box-shadow: var(--shadow-sm); position: sticky; top: 80px; }
.compact-detail-top { padding: 14px 20px; display: flex; justify-content: space-between; align-items: center; border-bottom: 1px solid var(--chalk); }
.compact-detail-name { font-family: 'JetBrains Mono', monospace; font-size: 13px; color: var(--graphite); }
.compact-detail-expand { color: var(--stone); cursor: pointer; }
.compact-detail-img-wrap { height: 280px; background: #111; display: flex; align-items: center; justify-content: center; position: relative; }
.compact-detail-img { max-width: 100%; max-height: 100%; object-fit: contain; }
.compact-detail-info { padding: 20px; }
.compact-detail-row { display: flex; justify-content: space-between; align-items: center; margin-bottom: 16px; }
.compact-detail-size { font-size: 11px; color: var(--stone); font-family: 'JetBrains Mono', monospace; }
.compact-detail-conf-title { font-size: 12px; font-weight: 600; color: var(--graphite); margin-bottom: 8px; display: flex; justify-content: space-between; }
.compact-buttons { display: flex; gap: 12px; margin-top: 24px; }
.btn-compact { flex: 1; padding: 10px; background: transparent; border: 1px solid var(--chalk); border-radius: 6px; font-family: 'DM Sans', sans-serif; font-size: 12px; font-weight: 600; color: var(--graphite); cursor: pointer; transition: all 0.15s; }
.btn-compact:hover { background: var(--dusk); }

.compact-table th, .compact-table td { padding: 12px 16px; border-bottom: 1px solid rgba(216,212,203,.5); }
.compact-row { cursor: pointer; transition: background 0.15s; }
.compact-row:hover { background: #EDF5EE; }
.compact-row.active { background: #EDF5EE; border-left: 3px solid var(--leaf); }
'''
html = html.replace('/* ─── RESPONSIVE ─── */', css_to_add + '\n/* ─── RESPONSIVE ─── */')

# 2. Modify View buttons
btn_replace = '''<div class="view-toggle">
          <button class="view-btn active" id="btn-view-list" title="List view" onclick="setView('list')">
            <svg viewBox="0 0 14 14" fill="none" stroke="currentColor" stroke-width="1.5"><path d="M1 3h12M1 7h12M1 11h12"/></svg>
          </button>
          <button class="view-btn" id="btn-view-grid" title="Grid view" onclick="setView('grid')">
            <svg viewBox="0 0 14 14" fill="none" stroke="currentColor" stroke-width="1.5"><rect x="1" y="1" width="5" height="5" rx="1"/><rect x="8" y="1" width="5" height="5" rx="1"/><rect x="1" y="8" width="5" height="5" rx="1"/><rect x="8" y="8" width="5" height="5" rx="1"/></svg>
          </button>
          <button class="view-btn" id="btn-view-compact" title="Compact view" onclick="setView('compact')">
            <svg viewBox="0 0 14 14" fill="none" stroke="currentColor" stroke-width="1.5"><path d="M1 2.5h12M1 5.5h12M1 8.5h12M1 11.5h12"/></svg>
          </button>
        </div>'''
html = re.sub(r'<div class="view-toggle">.*?</div>\s*</div>\s*</div>', btn_replace + '\n      </div>\n    </div>', html, flags=re.DOTALL)

# 3. Modify Table wrapper to include views container
table_wrap_start = html.find('<div class="table-wrap">')
table_wrap_end = html.find('<!-- Export section -->')

views_html = '''
    <div id="views-container">
      <!-- List View -->
      <div class="view-container active" id="view-list">
        <div class="table-wrap">
          <table id="list-table">
            <thead>
              <tr>
                <th class="td-idx">#</th>
                <th class="td-thumb">Image Name</th>
                <th>Preview</th>
                <th>Result</th>
                <th>Confidence</th>
              </tr>
            </thead>
            <tbody id="list-tbody">
            </tbody>
          </table>
        </div>
      </div>
      
      <!-- Grid View -->
      <div class="view-container" id="view-grid">
        <div class="grid-view" id="grid-container"></div>
      </div>
      
      <!-- Compact View -->
      <div class="view-container" id="view-compact">
        <div class="compact-view">
          <div class="compact-left">
            <table style="width:100%; border-collapse:collapse;" class="compact-table">
              <thead>
                <tr>
                  <th class="td-idx">#</th>
                  <th>Image</th>
                  <th>Result</th>
                </tr>
              </thead>
              <tbody id="compact-tbody">
              </tbody>
            </table>
          </div>
          <div class="compact-right" id="compact-detail">
            <!-- Detail pane populated by JS -->
          </div>
        </div>
      </div>
    </div>
'''
html = html[:table_wrap_start] + views_html + '\n    ' + html[table_wrap_end:]

# 4. Inject JS
js_logic = '''
// Global mock data
const mockResults = [
  { fname: 'PANEL_14B_SEC2.tiff', result: 'Not Damaged', badge: 'badge-not-damaged', conf: 98.2, ibadge: 'ib-good' },
  { fname: 'PANEL_14C_SEC2.tiff', result: 'Not Damaged', badge: 'badge-not-damaged', conf: 97.5, ibadge: 'ib-good' },
  { fname: 'PANEL_14D_SEC2.tiff', result: 'Damaged', badge: 'badge-damaged-full', conf: 91.0, ibadge: 'ib-damaged' },
  { fname: 'PANEL_15A_SEC1.tiff', result: 'Uncertain', badge: 'badge-uncertain-full', conf: 64.3, ibadge: 'ib-uncertain' },
  { fname: 'PANEL_15B_SEC1.tiff', result: 'Not Damaged', badge: 'badge-not-damaged', conf: 99.1, ibadge: 'ib-good' },
  { fname: 'PANEL_15C_SEC1.tiff', result: 'Damaged', badge: 'badge-damaged-full', conf: 88.7, ibadge: 'ib-damaged' },
  { fname: 'PANEL_16A_SEC4.tiff', result: 'Not Damaged', badge: 'badge-not-damaged', conf: 95.4, ibadge: 'ib-good' },
  { fname: 'PANEL_16B_SEC4.tiff', result: 'Not Damaged', badge: 'badge-not-damaged', conf: 96.0, ibadge: 'ib-good' }
];

function setView(viewName) {
  document.querySelectorAll('.view-btn').forEach(btn => btn.classList.remove('active'));
  document.getElementById('btn-view-' + viewName).classList.add('active');
  
  document.querySelectorAll('.view-container').forEach(c => c.classList.remove('active'));
  document.getElementById('view-' + viewName).classList.add('active');
}

function renderViews() {
  const listTbody = document.getElementById('list-tbody');
  const gridContainer = document.getElementById('grid-container');
  const compactTbody = document.getElementById('compact-tbody');
  
  if (!listTbody) return; // safeguard
  
  listTbody.innerHTML = '';
  gridContainer.innerHTML = '';
  compactTbody.innerHTML = '';
  
  mockResults.forEach((item, idx) => {
    let confColor = item.conf > 95 ? 'high' : (item.conf > 70 ? 'mid' : 'low');
    if(item.result === 'Not Damaged') confColor = 'high';
    if(item.result === 'Uncertain') confColor = 'mid';
    
    // LIST
    listTbody.innerHTML += `
      <tr onclick="openModal('${item.fname}')">
        <td class="td-idx">${idx + 1}</td>
        <td class="td-name">${item.fname}</td>
        <td><div style="width:40px;height:30px;border-radius:4px;background:url('assets/hero2.png') center/cover"></div></td>
        <td><span class="badge ${item.badge}">✓ ${item.result.toUpperCase()}</span></td>
        <td><div class="conf-wrap"><div class="conf-bar"><div class="conf-fill ${confColor}" style="width:${item.conf}%"></div></div><span class="conf-pct">${item.conf.toFixed(1)}%</span></div></td>
      </tr>
    `;
    
    // GRID
    gridContainer.innerHTML += `
      <div class="grid-card" onclick="openModal('${item.fname}')">
        <div class="grid-card-img-wrap">
          <img src="assets/hero2.png" class="grid-card-img">
          <span class="badge ${item.badge} grid-card-badge">✓ ${item.result.toUpperCase()}</span>
        </div>
        <div class="grid-card-info">
          <div class="grid-card-name">${item.fname}</div>
          <div class="grid-card-conf-row">
            <span style="font-size:10px;color:var(--stone)">Confidence</span>
            <div class="conf-wrap" style="flex:1"><div class="conf-bar"><div class="conf-fill ${confColor}" style="width:${item.conf}%"></div></div><span class="conf-pct">${item.conf.toFixed(1)}%</span></div>
          </div>
        </div>
      </div>
    `;
    
    // COMPACT LIST
    compactTbody.innerHTML += `
      <tr class="compact-row ${idx === 0 ? 'active' : ''}" onclick="selectCompact(${idx}, this)">
        <td class="td-idx">${idx + 1}</td>
        <td>
          <div style="display:flex;align-items:center;gap:12px">
            <img src="assets/hero2.png" class="compact-item-thumb" style="width:40px;height:40px;object-fit:cover;border-radius:4px">
            <span class="compact-item-name" style="font-family:'JetBrains Mono',monospace;font-size:11px">${item.fname}</span>
          </div>
        </td>
        <td><span class="badge ${item.badge}">✓ ${item.result.toUpperCase()}</span></td>
      </tr>
    `;
  });
  
  selectCompact(0);
}

function selectCompact(idx, rowEl) {
  if (rowEl) {
    document.querySelectorAll('.compact-row').forEach(r => r.classList.remove('active'));
    rowEl.classList.add('active');
  }
  
  const item = mockResults[idx];
  let confColor = item.conf > 95 ? 'high' : (item.conf > 70 ? 'mid' : 'low');
  if(item.result === 'Not Damaged') confColor = 'high';
  if(item.result === 'Uncertain') confColor = 'mid';
  
  const detail = document.getElementById('compact-detail');
  if(!detail) return;
  
  detail.innerHTML = `
    <div class="compact-detail-top">
      <div class="compact-detail-name">${item.fname}</div>
      <div class="compact-detail-expand" onclick="openModal('${item.fname}')"><svg viewBox="0 0 16 16" fill="none" stroke="currentColor" stroke-width="1.5" style="width:16px;height:16px"><path d="M4 1L1 4M15 12l-3 3M15 1v5M15 1h-5M1 15v-5M1 15h5"/></svg></div>
    </div>
    <div class="compact-detail-img-wrap">
      <img src="assets/hero2.png" class="compact-detail-img">
    </div>
    <div class="compact-detail-info">
      <div class="compact-detail-row">
        <span class="badge ${item.badge}">✓ ${item.result.toUpperCase()}</span>
        <span class="compact-detail-size">Size: 4.2 MB</span>
      </div>
      <div>
        <div class="compact-detail-conf-title"><span style="font-size:12px;font-weight:600">Model Confidence</span><span style="font-family:'JetBrains Mono',monospace">${item.conf.toFixed(1)}%</span></div>
        <div class="conf-bar" style="height:6px;background:var(--chalk)"><div class="conf-fill ${confColor}" style="width:${item.conf}%"></div></div>
      </div>
      <div class="compact-buttons">
        <button class="btn-compact">Override Label</button>
        <button class="btn-compact">View Raw Data</button>
      </div>
    </div>
  `;
}

// Hook into the processing animation to show views when done
if(typeof startProcessingAnim !== 'undefined') {
  const originalStartProcessingAnim = startProcessingAnim;
  window.startProcessingAnim = function() {
    originalStartProcessingAnim();
    setTimeout(renderViews, 5500);
  }
} else {
  // if not defined yet
  document.addEventListener('DOMContentLoaded', () => {
     if(typeof startProcessingAnim !== 'undefined') {
        const originalStartProcessingAnim = startProcessingAnim;
        window.startProcessingAnim = function() {
          originalStartProcessingAnim();
          setTimeout(renderViews, 5500);
        }
     }
  });
}
document.addEventListener('DOMContentLoaded', renderViews);
'''

html = html.replace('</script>', js_logic + '\n</script>')

with open('c:/Users/qafms/OneDrive/Desktop/MYPROJECT/frontend/index.html', 'w', encoding='utf-8') as f:
    f.write(html)
print("Updated successfully")
