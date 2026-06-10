/* ============================================
   DAU JARVIS DASHBOARD - MEMORY MODULE
   ============================================ */

// ---- MEMORY: SHOW ADD FORM ----
function memoryShowAdd() {
    const form = document.getElementById('memoryAddForm');
    if (form) form.style.display = 'block';
}

function memoryHideAdd() {
    const form = document.getElementById('memoryAddForm');
    if (form) form.style.display = 'none';
    document.getElementById('memoryContent').value = '';
    document.getElementById('memoryCategory').selectedIndex = 0;
    document.getElementById('memoryImportance').selectedIndex = 0;
}

// ---- MEMORY: SAVE ----
async function memorySave() {
    const content = document.getElementById('memoryContent').value.trim();
    const category = document.getElementById('memoryCategory').value;
    const importance = document.getElementById('memoryImportance').value;

    if (!content) {
        showToast('Məzmun boş ola bilməz', 'error');
        return;
    }

    try {
        await apiCall('/api/memory/save', {
            method: 'POST',
            body: JSON.stringify({ content, category, importance })
        });
        showToast('Yaddaş yadda saxlanıldı', 'success');
        memoryHideAdd();
        memoryRefresh();
    } catch (err) {
        // Error already shown by apiCall
    }
}

// ---- MEMORY: REFRESH LIST ----
async function memoryRefresh() {
    try {
        const data = await apiCall('/api/memory/list');
        const memories = data.memories || data || [];
        renderMemoryList(memories);
    } catch (err) {
        document.getElementById('memoryList').innerHTML = '<div class="hud-empty">Yaddaş məlumatları yüklənə bilmədi</div>';
    }
}

// ---- MEMORY: RENDER LIST ----
function renderMemoryList(memories) {
    const container = document.getElementById('memoryList');

    if (!memories || memories.length === 0) {
        container.innerHTML = '<div class="hud-empty">Yaddaş məlumatı yoxdur</div>';
        return;
    }

    container.innerHTML = memories.map(mem => `
        <div class="memory-card" data-id="${mem.id}">
            <div class="memory-card-header">
                <span class="memory-category">${escapeHtml(mem.category || 'general').toUpperCase()}</span>
                <span class="memory-importance ${mem.importance || 'low'}">${escapeHtml(mem.importance || 'low').toUpperCase()}</span>
            </div>
            <div class="memory-content">${escapeHtml(mem.content || '')}</div>
            <div class="memory-footer">
                <span class="memory-time">${formatDateTime(mem.created_at)}</span>
                <div class="memory-actions">
                    <button class="btn-icon delete" onclick="memoryDelete(${mem.id})" title="Sil">
                        <svg viewBox="0 0 24 24" width="12" height="12" fill="none" stroke="currentColor" stroke-width="2"><path d="M6 19c0 1.1.9 2 2 2h8c1.1 0 2-.9 2-2V7H6v12zM19 4h-3.5l-1-1h-5l-1 1H5v2h14V4z"/></svg>
                    </button>
                </div>
            </div>
        </div>
    `).join('');
}

// ---- MEMORY: SEARCH ----
function memorySearchHandler() {
    const query = document.getElementById('memorySearch').value.trim();
    if (!query) {
        memoryRefresh();
        return;
    }
    memorySearch(query);
}

async function memorySearch(query) {
    try {
        const data = await apiCall(`/api/memory/search?q=${encodeURIComponent(query)}`);
        const memories = data.memories || data.results || data || [];
        renderMemoryList(memories);
    } catch (err) {
        showToast('Axtarış xətası', 'error');
    }
}

// ---- MEMORY: DELETE ----
async function memoryDelete(id) {
    if (!confirm('Bu yaddaş məlumatını silmək istəyirsiniz?')) return;

    try {
        await apiCall(`/api/memory/delete/${id}`, { method: 'DELETE' });
        showToast('Yaddaş məlumatı silindi', 'success');
        memoryRefresh();
    } catch (err) {
        // Error already shown
    }
}