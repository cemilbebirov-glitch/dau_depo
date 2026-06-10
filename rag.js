/* ============================================
   DAU JARVIS DASHBOARD - RAG MODULE
   ============================================ */

// ---- RAG: SHOW UPLOAD ----
function ragShowUpload() {
    const area = document.getElementById('ragUploadArea');
    if (area) {
        area.style.display = area.style.display === 'none' ? 'block' : 'none';
    }
}

// ---- RAG: DROPZONE INIT ----
document.addEventListener('DOMContentLoaded', () => {
    const dropzone = document.getElementById('ragDropzone');
    const fileInput = document.getElementById('ragFileInput');

    if (dropzone && fileInput) {
        dropzone.addEventListener('click', () => fileInput.click());

        dropzone.addEventListener('dragover', (e) => {
            e.preventDefault();
            dropzone.style.borderColor = '#ff0040';
            dropzone.style.background = 'rgba(255, 0, 64, 0.08)';
        });

        dropzone.addEventListener('dragleave', () => {
            dropzone.style.borderColor = '';
            dropzone.style.background = '';
        });

        dropzone.addEventListener('drop', (e) => {
            e.preventDefault();
            dropzone.style.borderColor = '';
            dropzone.style.background = '';
            const files = e.dataTransfer.files;
            if (files.length > 0) {
                ragUploadFileList(files);
            }
        });
    }
});

// ---- RAG: UPLOAD FILES ----
function ragUploadFiles() {
    const fileInput = document.getElementById('ragFileInput');
    if (fileInput && fileInput.files.length > 0) {
        ragUploadFileList(fileInput.files);
    }
}

async function ragUploadFileList(files) {
    for (const file of files) {
        const formData = new FormData();
        formData.append('file', file);

        try {
            showToast(`${file.name} yüklənir...`, 'info');
            const response = await fetch('/api/rag/upload', {
                method: 'POST',
                body: formData
            });
            const data = await response.json();
            if (response.ok) {
                showToast(`${file.name} uğurla yükləndi`, 'success');
            } else {
                showToast(`Xəta: ${data.error || 'Yükləmə alınmadı'}`, 'error');
            }
        } catch (err) {
            showToast(`${file.name} yüklənə bilmədi`, 'error');
        }
    }

    ragLoadDocs();

    // Reset file input
    const fileInput = document.getElementById('ragFileInput');
    if (fileInput) fileInput.value = '';
}

// ---- RAG: LOAD DOCUMENTS ----
async function ragLoadDocs() {
    try {
        const data = await apiCall('/api/rag/documents');
        const docs = data.documents || data || [];
        renderRagDocs(docs);
    } catch (err) {
        document.getElementById('ragDocList').innerHTML = '<div class="hud-empty">Sənədlər yüklənə bilmədi</div>';
    }
}

function renderRagDocs(docs) {
    const container = document.getElementById('ragDocList');

    if (!docs || docs.length === 0) {
        container.innerHTML = '<div class="hud-empty">Sənəd yoxdur</div>';
        return;
    }

    container.innerHTML = docs.map(doc => `
        <div class="data-list-item">
            <div>
                <div class="doc-name">${escapeHtml(doc.filename || doc.name || 'Naməlum')}</div>
            </div>
            <div class="doc-info">
                <span>${doc.chunks || doc.chunk_count || 0} parça</span>
                <button class="btn-icon delete" onclick="ragDeleteDoc('${doc.id || doc.filename}')" title="Sil">
                    <svg viewBox="0 0 24 24" width="10" height="10" fill="none" stroke="currentColor" stroke-width="2"><path d="M6 19c0 1.1.9 2 2 2h8c1.1 0 2-.9 2-2V7H6v12zM19 4h-3.5l-1-1h-5l-1 1H5v2h14V4z"/></svg>
                </button>
            </div>
        </div>
    `).join('');
}

// ---- RAG: SEARCH ----
async function ragSearch() {
    const query = document.getElementById('ragQuery').value.trim();
    if (!query) {
        showToast('Sual daxil edin', 'error');
        return;
    }

    try {
        const data = await apiCall('/api/rag/query', {
            method: 'POST',
            body: JSON.stringify({ query, top_k: 5 })
        });

        const results = data.results || data.answer || [];
        const section = document.getElementById('ragResultsSection');
        const container = document.getElementById('ragResults');

        if (section) section.style.display = 'block';

        if (typeof results === 'string') {
            container.innerHTML = `<div class="rag-result"><div class="rag-result-content">${escapeHtml(results)}</div></div>`;
        } else if (Array.isArray(results) && results.length > 0) {
            container.innerHTML = results.map(r => `
                <div class="rag-result">
                    <div class="rag-result-header">
                        <span class="rag-result-source">${escapeHtml(r.source || r.filename || 'Sənəd')}</span>
                        <span class="rag-result-score">${r.score ? (r.score * 100).toFixed(1) + '%' : ''}</span>
                    </div>
                    <div class="rag-result-content">${escapeHtml(r.content || r.text || '')}</div>
                </div>
            `).join('');
        } else {
            container.innerHTML = '<div class="hud-empty">Nəticə tapılmadı</div>';
        }
    } catch (err) {
        showToast('RAG axtarış xətası', 'error');
    }
}

// ---- RAG: DELETE DOCUMENT ----
async function ragDeleteDoc(docId) {
    if (!confirm('Bu sənədi silmək istəyirsiniz?')) return;

    try {
        await apiCall(`/api/rag/document/${docId}`, { method: 'DELETE' });
        showToast('Sənəd silindi', 'success');
        ragLoadDocs();
    } catch (err) {
        // Error shown by apiCall
    }
}