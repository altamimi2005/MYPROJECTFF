import re

with open('frontend/index.html', 'r', encoding='utf-8') as f:
    html = f.read()

# 1. Inject hidden file inputs right after the body tag
hidden_inputs = """<body>
<!-- Hidden inputs for actual uploads -->
<input type="file" id="fileInput" multiple style="display:none" onchange="handleFileSelect(event)">
<input type="file" id="folderInput" webkitdirectory directory multiple style="display:none" onchange="handleFileSelect(event)">"""
html = html.replace('<body>', hidden_inputs)

# 2. Wire the buttons in the upload cards to click the hidden file inputs
html = html.replace('<button class="btn-primary">Choose File</button>', 
                    '<button class="btn-primary" onclick="document.getElementById(\'fileInput\').click()">Choose Files</button>')
html = html.replace('<button class="btn-primary">Select Folder</button>', 
                    '<button class="btn-primary" onclick="document.getElementById(\'folderInput\').click()">Select Folder</button>')

# 3. Add drag and drop visual and triggers to drop zones
html = html.replace('<div class="drop-zone">', '<div class="drop-zone" id="fileDropZone">', 1)
html = html.replace('<div class="drop-zone">', '<div class="drop-zone" id="folderDropZone">', 1)

# 4. Wire the main Analyze button to call the real upload function
html = html.replace('onclick="startProcessing()"', 'onclick="startAnalysis()"')

# 5. Inject bulk select dropdown in the header controls row
old_controls = """    <div class="controls-row">
      <div class="controls-left">
        <span class="section-label">Detailed Findings</span>
        <div class="filter-pills">
          <span class="filter-pill active" onclick="setFilter(this)">All</span>
          <span class="filter-pill" onclick="setFilter(this)">Damaged</span>
          <span class="filter-pill" onclick="setFilter(this)">Not Damaged</span>
          <span class="filter-pill" onclick="setFilter(this)">Uncertain</span>
        </div>
      </div>"""

new_controls = """    <div class="controls-row">
      <div class="controls-left">
        <span class="section-label">Detailed Findings</span>
        <div class="filter-pills">
          <span class="filter-pill active" id="pill-all" onclick="setResultsFilter('all')">All</span>
          <span class="filter-pill" id="pill-damaged" onclick="setResultsFilter('damaged')">Damaged</span>
          <span class="filter-pill" id="pill-good" onclick="setResultsFilter('not_damaged')">Not Damaged</span>
          <span class="filter-pill" id="pill-uncertain" onclick="setResultsFilter('uncertain')">Uncertain</span>
        </div>
        <select id="bulkSelectDropdown" onchange="handleBulkSelect(this)" class="filter-pill" style="border: 1.5px solid var(--chalk); padding: 5px 12px; font-family:'DM Sans'; font-size:11px; color: var(--stone); background: var(--panel); outline:none; border-radius:20px; cursor:pointer;">
          <option value="">Bulk Actions...</option>
          <option value="all">Select All</option>
          <option value="damaged">Select All Damaged</option>
          <option value="not_damaged">Select All Not Damaged</option>
          <option value="uncertain">Select All Uncertain</option>
          <option value="none">Clear Selection</option>
        </select>
      </div>"""
html = html.replace(old_controls, new_controls)

# 6. Inject the checkboxes column in the list table
old_table_headers = """            <thead>
              <tr>
                <th class="td-idx">#</th>
                <th class="td-thumb">Image Name</th>
                <th>Preview</th>
                <th>Result</th>
                <th>Confidence</th>
              </tr>
            </thead>"""

new_table_headers = """            <thead>
              <tr>
                <th style="width: 40px; padding: 12px 16px;"><input type="checkbox" id="selectAllCheckbox" onchange="toggleSelectAll(this.checked)" style="scale: 1.2; accent-color: var(--leaf);"></th>
                <th class="td-idx">#</th>
                <th>Image Name</th>
                <th>Preview</th>
                <th>Result</th>
                <th>Confidence</th>
              </tr>
            </thead>"""
html = html.replace(old_table_headers, new_table_headers)

# 7. Add Floating Bulk Action Bar to HTML body (right before </body>)
bulk_bar_html = """
<!-- Floating Bulk Action Bar -->
<div class="bulk-action-bar" id="bulkActionBar">
  <div class="bulk-action-text" id="bulkActionText">0 items selected</div>
  <div class="bulk-action-btns">
    <button class="btn-bulk secondary" onclick="bulkOverride('Not Damaged')">Override to Safe</button>
    <button class="btn-bulk secondary" onclick="bulkOverride('Damaged')">Override to Damaged</button>
    <button class="btn-bulk primary" onclick="exportSelected('excel')">Export Selected (Excel)</button>
    <button class="btn-bulk primary" onclick="exportSelected('csv')">Export Selected (CSV)</button>
  </div>
</div>
"""

html = html.replace('</body>', bulk_bar_html + '\n</body>')

# 8. Add CSS styles for custom checkboxes, sticky bar
css_styles = """
/* ─── BULK ACTION BAR ─── */
.bulk-action-bar {
  position: fixed;
  bottom: -90px;
  left: 50%;
  transform: translateX(-50%);
  width: 900px;
  max-width: 92%;
  background: rgba(26, 38, 28, 0.96);
  backdrop-filter: blur(16px);
  border: 1.5px solid var(--leaf);
  border-radius: 12px;
  padding: 16px 28px;
  display: flex;
  justify-content: space-between;
  align-items: center;
  z-index: 1000;
  transition: bottom 0.3s cubic-bezier(0.4, 0, 0.2, 1);
  box-shadow: var(--shadow-lg);
}
.bulk-action-bar.visible {
  bottom: 24px;
}
.bulk-action-text {
  color: #fff;
  font-family: 'DM Sans', sans-serif;
  font-size: 13px;
  font-weight: 500;
  letter-spacing: 0.02em;
}
.bulk-action-btns {
  display: flex;
  gap: 12px;
}
.btn-bulk {
  padding: 10px 18px;
  border-radius: 6px;
  font-family: 'DM Sans', sans-serif;
  font-size: 12px;
  font-weight: 600;
  cursor: pointer;
  transition: all 0.15s;
}
.btn-bulk.primary {
  background: var(--leaf);
  color: #fff;
  border: none;
}
.btn-bulk.primary:hover {
  background: var(--forest);
  transform: translateY(-1px);
}
.btn-bulk.secondary {
  background: transparent;
  border: 1.5px solid rgba(255,255,255,0.25);
  color: #fff;
}
.btn-bulk.secondary:hover {
  border-color: #fff;
  background: rgba(255,255,255,0.06);
  transform: translateY(-1px);
}
"""
html = html.replace('/* ─── RESPONSIVE ─── */', css_styles + '\n/* ─── RESPONSIVE ─── */')

# 9. Update the main export section buttons
export_buttons = """      <div class="export-btns">
        <button class="btn-dl btn-pdf" onclick="triggerMainExport('excel')">
          <svg viewBox="0 0 14 14" fill="none" stroke="currentColor" stroke-width="1.5"><rect x="2" y="1" width="10" height="12" rx="1.5"/><path d="M4 5h6M4 7.5h4"/></svg>
          Download Excel Report
        </button>
        <button class="btn-dl btn-csv" onclick="triggerMainExport('csv')">
          <svg viewBox="0 0 14 14" fill="none" stroke="currentColor" stroke-width="1.5"><rect x="2" y="1" width="10" height="12" rx="1.5"/><path d="M4 5h6M4 7.5h6M4 10h4"/></svg>
          Download CSV Data
        </button>
      </div>"""
html = re.sub(r'<div class="export-btns">.*?</div>', export_buttons, html, flags=re.DOTALL)

with open('frontend/index.html', 'w', encoding='utf-8') as f:
    f.write(html)

print("Frontend HTML layout updated successfully")
