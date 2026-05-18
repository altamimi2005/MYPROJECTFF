import re

with open('frontend/index.html', 'r', encoding='utf-8') as f:
    html = f.read()

# Find the '// Global mock data' line to replace the mockup code
js_index = html.find('// Global mock data')
if js_index == -1:
    # If not found, let's look for standard script tag
    js_index = html.find('<script>') + 8

new_js = """
// Global state
let uploadedFiles = [];
let globalResults = [];
let selectedFnames = new Set();
let currentResultsFilter = 'all';

// Handle File Drop & Select
function handleFileSelect(event) {
  const files = event.target.files;
  if (!files || files.length === 0) return;
  
  uploadedFiles = Array.from(files);
  
  // Show recent upload thumbnails or file count
  const thumbsContainer = document.querySelector('.recent-thumbs');
  if (thumbsContainer) {
    thumbsContainer.innerHTML = '';
    const previewCount = Math.min(uploadedFiles.length, 3);
    for (let i = 0; i < previewCount; i++) {
      thumbsContainer.innerHTML += `<div class="recent-thumb" style="background: linear-gradient(135deg,#1a2a1a,#0d1a0d); display: flex; align-items: center; justify-content: center; color: var(--sage); font-size: 10px; font-weight: bold; overflow: hidden; text-overflow: ellipsis; white-space: nowrap; padding: 2px;">Img ${i+1}</div>`;
    }
  }
  
  // Update progress bar to 100% since files are ready
  const progressFill = document.querySelector('.progress-fill');
  const progressLabel = document.querySelector('.progress-bar-label span');
  if (progressFill && progressLabel) {
    progressFill.style.width = '100%';
    progressLabel.textContent = '100%';
  }
  
  const note = document.getElementById('analyzeNote');
  if (note) {
    note.textContent = `${uploadedFiles.length} images loaded & ready for analysis.`;
  }
}

// Drag & Drop event wire up
document.addEventListener('DOMContentLoaded', () => {
  const fileZone = document.getElementById('fileDropZone');
  const folderZone = document.getElementById('folderDropZone');
  
  [fileZone, folderZone].forEach(zone => {
    if (!zone) return;
    zone.addEventListener('dragover', (e) => {
      e.preventDefault();
      zone.style.borderColor = 'var(--leaf)';
      zone.style.background = '#EDF5EE';
    });
    zone.addEventListener('dragleave', () => {
      zone.style.borderColor = 'var(--chalk)';
      zone.style.background = 'var(--dusk)';
    });
    zone.addEventListener('drop', (e) => {
      e.preventDefault();
      zone.style.borderColor = 'var(--chalk)';
      zone.style.background = 'var(--dusk)';
      if (e.dataTransfer.files.length > 0) {
        uploadedFiles = Array.from(e.dataTransfer.files);
        handleFileSelect({ target: { files: e.dataTransfer.files } });
      }
    });
    
    // Also trigger file input on click
    zone.addEventListener('click', () => {
      if (zone.id === 'fileDropZone') {
        document.getElementById('fileInput').click();
      } else {
        document.getElementById('folderInput').click();
      }
    });
  });
});

// Real API Upload & Analysis
async function startAnalysis() {
  if (uploadedFiles.length === 0) {
    alert("Please select or drop some EL scan images first!");
    return;
  }
  
  showScreen('processing');
  
  const formData = new FormData();
  uploadedFiles.forEach(file => {
    formData.append('files', file);
  });
  formData.append('auto_crop', document.getElementById('cropToggle').checked ? 'true' : 'false');
  
  try {
    const res = await fetch('/api/upload', {
      method: 'POST',
      body: formData
    });
    
    if (!res.ok) {
      throw new Error(`Upload failed with status code ${res.status}`);
    }
    
    const data = await res.json();
    
    if (data.results) {
      // Map API results
      globalResults = data.results.map(r => ({
        fname: r.filename,
        result: r.result,
        badge: r.result === 'Damaged' ? 'badge-damaged-full' : (r.result === 'Not Damaged' ? 'badge-not-damaged' : 'badge-uncertain-full'),
        conf: r.confidence === "Overwritten" ? "Overwritten" : parseFloat(r.confidence),
        crop_status: r.crop_status
      }));
      
      // Update statistics
      updateStatistics();
      
      // Clear selection
      selectedFnames.clear();
      updateBulkActionBar();
      
      // Render the 3 views
      renderViews();
      
      // Switch screen to results
      showScreen('results');
    } else {
      alert("Error analyzing images: " + (data.message || "Unknown error"));
      showScreen('landing');
    }
  } catch (e) {
    alert("Failed to connect to backend server: " + e.message);
    showScreen('landing');
  }
}

// Update Statistics dynamically
function updateStatistics() {
  const total = globalResults.length;
  const damaged = globalResults.filter(r => r.result === 'Damaged').length;
  const uncertain = globalResults.filter(r => r.result === 'Uncertain').length;
  const good = globalResults.filter(r => r.result === 'Not Damaged').length;
  
  let validConfs = globalResults.filter(r => typeof r.conf === 'number');
  let avgConf = validConfs.length > 0 ? (validConfs.reduce((sum, r) => sum + r.conf, 0) / validConfs.length) : 0;
  
  // Find stat cards in DOM and update values
  const totalCard = document.querySelector('.stat-card.total .stat-value');
  const damagedCard = document.querySelector('.stat-card.damaged .stat-value');
  const uncertainCard = document.querySelector('.stat-card.uncertain .stat-value');
  const goodCard = document.querySelector('.stat-card.good .stat-value');
  const confCard = document.querySelector('.stat-card.conf .stat-value');
  
  if (totalCard) totalCard.textContent = total;
  if (damagedCard) damagedCard.textContent = damaged;
  if (uncertainCard) uncertainCard.textContent = uncertain;
  if (goodCard) goodCard.textContent = good;
  if (confCard) confCard.textContent = avgConf > 0 ? `${avgConf.toFixed(1)}%` : 'N/A';
  
  // Update subtitle counts
  const totalCardSub = document.querySelector('.stat-card.damaged .stat-sub');
  if (totalCardSub && total > 0) {
    totalCardSub.textContent = `${((damaged / total) * 100).toFixed(1)}% of total site`;
  }
  const uncertainCardSub = document.querySelector('.stat-card.uncertain .stat-sub');
  if (uncertainCardSub && total > 0) {
    uncertainCardSub.textContent = `${((uncertain / total) * 100).toFixed(1)}% require review`;
  }
}

// Set active results filter pill
function setResultsFilter(filterName) {
  currentResultsFilter = filterName;
  
  // Visual state for filter pills
  document.querySelectorAll('.filter-pills .filter-pill').forEach(p => p.classList.remove('active'));
  
  let activePillId = 'pill-all';
  if (filterName === 'damaged') activePillId = 'pill-damaged';
  else if (filterName === 'not_damaged') activePillId = 'pill-good';
  else if (filterName === 'uncertain') activePillId = 'pill-uncertain';
  
  const activePill = document.getElementById(activePillId);
  if (activePill) activePill.classList.add('active');
  
  renderViews();
}

// Get filtered items
function getFilteredResults() {
  if (currentResultsFilter === 'all') return globalResults;
  if (currentResultsFilter === 'damaged') return globalResults.filter(r => r.result === 'Damaged');
  if (currentResultsFilter === 'not_damaged') return globalResults.filter(r => r.result === 'Not Damaged');
  if (currentResultsFilter === 'uncertain') return globalResults.filter(r => r.result === 'Uncertain');
  return globalResults;
}

// Render dynamic results inside the 3 views
function renderViews() {
  const listTbody = document.getElementById('list-tbody');
  const gridContainer = document.getElementById('grid-container');
  const compactTbody = document.getElementById('compact-tbody');
  
  if (!listTbody) return; // Safeguard if not on correct page
  
  listTbody.innerHTML = '';
  gridContainer.innerHTML = '';
  compactTbody.innerHTML = '';
  
  const filtered = getFilteredResults();
  
  if (filtered.length === 0) {
    const emptyRow = `<tr><td colspan="6" style="text-align:center; padding: 40px; color: var(--stone);">No panels found matching this filter</td></tr>`;
    listTbody.innerHTML = emptyRow;
    gridContainer.innerHTML = `<div style="grid-column: 1/-1; text-align:center; padding: 40px; color: var(--stone);">No panels found matching this filter</div>`;
    compactTbody.innerHTML = `<tr><td colspan="3" style="text-align:center; padding: 40px; color: var(--stone);">No panels found matching this filter</td></tr>`;
    return;
  }
  
  filtered.forEach((item, idx) => {
    // Confidence styling
    let confColor = 'high';
    let confText = 'N/A';
    
    if (item.conf === "Overwritten") {
      confColor = 'high';
      confText = 'Overwritten';
    } else if (typeof item.conf === 'number') {
      confColor = item.conf > 90 ? 'high' : (item.conf > 65 ? 'mid' : 'low');
      confText = `${item.conf.toFixed(1)}%`;
    }
    
    const isChecked = selectedFnames.has(item.fname) ? 'checked' : '';
    
    // 1. LIST VIEW ROW
    listTbody.innerHTML += `
      <tr>
        <td style="padding: 12px 16px;"><input type="checkbox" class="row-checkbox" data-fname="${item.fname}" ${isChecked} onchange="toggleRowSelection('${item.fname}', this.checked)" style="scale: 1.2; accent-color: var(--leaf);"></td>
        <td class="td-idx">${idx + 1}</td>
        <td class="td-name" onclick="openModal('${item.fname}')">${item.fname}</td>
        <td onclick="openModal('${item.fname}')"><div style="width:40px;height:30px;border-radius:4px;background:url('assets/hero2.png') center/cover"></div></td>
        <td onclick="openModal('${item.fname}')"><span class="badge ${item.badge}">✓ ${item.result.toUpperCase()}</span></td>
        <td onclick="openModal('${item.fname}')">
          <div class="conf-wrap">
            <div class="conf-bar"><div class="conf-fill ${confColor}" style="width: ${item.conf === 'Overwritten' ? 100 : item.conf}%"></div></div>
            <span class="conf-pct">${confText}</span>
          </div>
        </td>
      </tr>
    `;
    
    // 2. GRID VIEW CARD
    gridContainer.innerHTML += `
      <div class="grid-card">
        <div class="grid-card-img-wrap">
          <input type="checkbox" class="grid-checkbox" data-fname="${item.fname}" ${isChecked} onchange="toggleRowSelection('${item.fname}', this.checked)" style="position:absolute; top:12px; right:12px; z-index:10; scale:1.3; accent-color: var(--leaf); cursor:pointer;">
          <img src="assets/hero2.png" class="grid-card-img" onclick="openModal('${item.fname}')">
          <span class="badge ${item.badge} grid-card-badge" onclick="openModal('${item.fname}')">✓ ${item.result.toUpperCase()}</span>
        </div>
        <div class="grid-card-info" onclick="openModal('${item.fname}')">
          <div class="grid-card-name">${item.fname}</div>
          <div class="grid-card-conf-row">
            <span style="font-size:10px;color:var(--stone)">Confidence</span>
            <div class="conf-wrap" style="flex:1">
              <div class="conf-bar"><div class="conf-fill ${confColor}" style="width: ${item.conf === 'Overwritten' ? 100 : item.conf}%"></div></div>
              <span class="conf-pct">${confText}</span>
            </div>
          </div>
        </div>
      </div>
    `;
    
    // 3. COMPACT VIEW ROW (MASTER)
    compactTbody.innerHTML += `
      <tr class="compact-row ${idx === 0 ? 'active' : ''}" id="compact-row-${idx}">
        <td style="padding: 12px 16px;"><input type="checkbox" class="compact-checkbox" data-fname="${item.fname}" ${isChecked} onchange="toggleRowSelection('${item.fname}', this.checked)" style="scale: 1.2; accent-color: var(--leaf);"></td>
        <td onclick="selectCompact(${idx})">
          <div style="display:flex;align-items:center;gap:12px">
            <img src="assets/hero2.png" class="compact-item-thumb" style="width:40px;height:40px;object-fit:cover;border-radius:4px">
            <span class="compact-item-name" style="font-family:'JetBrains Mono',monospace;font-size:11px">${item.fname}</span>
          </div>
        </td>
        <td onclick="selectCompact(${idx})"><span class="badge ${item.badge}">✓ ${item.result.toUpperCase()}</span></td>
      </tr>
    `;
  });
  
  // Sync the Select All Checkbox state
  const allCheckbox = document.getElementById('selectAllCheckbox');
  if (allCheckbox) {
    const visibleCount = filtered.length;
    const selectedVisible = filtered.filter(item => selectedFnames.has(item.fname)).length;
    allCheckbox.checked = visibleCount > 0 && selectedVisible === visibleCount;
  }
  
  selectCompact(0);
}

// Render Compact Detail View (Detail Pane)
function selectCompact(idx) {
  const filtered = getFilteredResults();
  if (filtered.length === 0) return;
  
  document.querySelectorAll('.compact-row').forEach(r => r.classList.remove('active'));
  const rowEl = document.getElementById(`compact-row-${idx}`);
  if (rowEl) rowEl.classList.add('active');
  
  const item = filtered[idx];
  
  let confColor = 'high';
  let confText = 'N/A';
  
  if (item.conf === "Overwritten") {
    confColor = 'high';
    confText = 'Overwritten';
  } else if (typeof item.conf === 'number') {
    confColor = item.conf > 90 ? 'high' : (item.conf > 65 ? 'mid' : 'low');
    confText = `${item.conf.toFixed(1)}%`;
  }
  
  const detail = document.getElementById('compact-detail');
  if (!detail) return;
  
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
        <div class="compact-detail-conf-title"><span style="font-size:12px;font-weight:600">Model Confidence</span><span style="font-family:'JetBrains Mono',monospace">${confText}</span></div>
        <div class="conf-bar" style="height:6px;background:var(--chalk)"><div class="conf-fill ${confColor}" style="width: ${item.conf === 'Overwritten' ? 100 : item.conf}%"></div></div>
      </div>
      <div class="compact-buttons">
        <button class="btn-compact" onclick="triggerManualOverride('${item.fname}')">Override Label</button>
        <button class="btn-compact" onclick="openModal('${item.fname}')">View Raw Data</button>
      </div>
    </div>
  `;
}

// Toggle Row selection state
function toggleRowSelection(fname, isChecked) {
  if (isChecked) {
    selectedFnames.add(fname);
  } else {
    selectedFnames.delete(fname);
  }
  
  // Keep checkboxes in sync across different views
  document.querySelectorAll(`input[data-fname="${fname}"]`).forEach(cb => {
    cb.checked = isChecked;
  });
  
  updateBulkActionBar();
}

// Toggle Select All Visible Checkbox
function toggleSelectAll(isChecked) {
  const filtered = getFilteredResults();
  filtered.forEach(item => {
    toggleRowSelection(item.fname, isChecked);
  });
}

// Handle Bulk Dropdown Actions
function handleBulkSelect(selectEl) {
  const action = selectEl.value;
  if (!action) return;
  
  if (action === 'all') {
    globalResults.forEach(item => selectedFnames.add(item.fname));
  } else if (action === 'damaged') {
    selectedFnames.clear();
    globalResults.filter(r => r.result === 'Damaged').forEach(item => selectedFnames.add(item.fname));
  } else if (action === 'not_damaged') {
    selectedFnames.clear();
    globalResults.filter(r => r.result === 'Not Damaged').forEach(item => selectedFnames.add(item.fname));
  } else if (action === 'uncertain') {
    selectedFnames.clear();
    globalResults.filter(r => r.result === 'Uncertain').forEach(item => selectedFnames.add(item.fname));
  } else if (action === 'none') {
    selectedFnames.clear();
  }
  
  renderViews();
  updateBulkActionBar();
  
  // reset dropdown select visual
  selectEl.value = '';
}

// Update the bulk action bar count and display status
function updateBulkActionBar() {
  const bar = document.getElementById('bulkActionBar');
  const text = document.getElementById('bulkActionText');
  if (!bar || !text) return;
  
  const count = selectedFnames.size;
  if (count > 0) {
    text.textContent = `${count} panel(s) selected`;
    bar.classList.add('visible');
  } else {
    bar.classList.remove('visible');
  }
}

// Send Manual Override API Request to backend
async function overrideResult(fname, newLabel) {
  try {
    const res = await fetch('/api/override', {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json'
      },
      body: JSON.stringify({ filename: fname, new_result: newLabel })
    });
    
    const data = await res.json();
    if (data.status === 'success') {
      // Update local item
      const item = globalResults.find(r => r.fname === fname);
      if (item) {
        item.result = newLabel;
        item.conf = 'Overwritten';
        item.badge = newLabel === 'Damaged' ? 'badge-damaged-full' : (newLabel === 'Not Damaged' ? 'badge-not-damaged' : 'badge-uncertain-full');
      }
      
      updateStatistics();
      renderViews();
    } else {
      alert("Override failed: " + data.message);
    }
  } catch (e) {
    alert("Connection error during override: " + e.message);
  }
}

// Prompt for manual override
function triggerManualOverride(fname) {
  const choice = prompt(`Override classification for ${fname}. Enter:\\n1 for 'Not Damaged'\\n2 for 'Damaged'\\n3 for 'Uncertain'`);
  if (!choice) return;
  
  let label = '';
  if (choice === '1') label = 'Not Damaged';
  else if (choice === '2') label = 'Damaged';
  else if (choice === '3') label = 'Uncertain';
  else {
    alert("Invalid choice");
    return;
  }
  
  overrideResult(fname, label);
}

// Bulk override all selected items
async function bulkOverride(newLabel) {
  if (selectedFnames.size === 0) return;
  
  const promises = Array.from(selectedFnames).map(fname => overrideResult(fname, newLabel));
  await Promise.all(promises);
  
  selectedFnames.clear();
  updateBulkActionBar();
  renderViews();
  alert(`Manually overrode classification of selected items to ${newLabel}.`);
}

// Main download and export controls (all if none selected, selected if checked)
function triggerMainExport(type) {
  if (selectedFnames.size > 0) {
    exportSelected(type);
  } else {
    // Export All
    const endpoint = type === 'excel' ? '/api/download-report' : '/api/download-results';
    window.location.href = endpoint;
  }
}

// Export selected items only
function exportSelected(type) {
  if (selectedFnames.size === 0) {
    alert("No panels selected for export!");
    return;
  }
  
  const fnamesString = Array.from(selectedFnames).join(',');
  const endpoint = type === 'excel' ? '/api/download-report' : '/api/download-results';
  window.location.href = `${endpoint}?filenames=${encodeURIComponent(fnamesString)}`;
}
"""

html = html[:js_index] + new_js + '\n</script>\n</body>\n</html>'

with open('frontend/index.html', 'w', encoding='utf-8') as f:
    f.write(html)

print("Frontend JS successfully injected")
