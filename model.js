/**
 * DAU Model İdarəetmə - AI Modelləri siyahısı, seçim, əlavə, silmə
 */

const ModelManager = {
    models: [],
    activeModel: null,

    // Modelləri yüklə
    loadModels: function() {
        fetch('/api/model/list')
            .then(res => res.json())
            .then(data => {
                if (data.success && data.models) {
                    this.models = data.models;
                    this.activeModel = data.models.find(m => m.is_active) || data.models[0];
                    this.renderModels();
                }
            })
            .catch(err => {
                console.error('Model yükləmə xətası:', err);
                // Fallback modellər
                this.models = [
                    { id: 'model-qwen3-8b', name: 'Qwen3 8B', provider: 'ollama', is_active: 1 }
                ];
                this.renderModels();
            });
    },

    // Modelləri HTML-ə çevir
    renderModels: function() {
        const container = document.getElementById('model-list');
        if (!container) return;

        let html = '';
        for (const model of this.models) {
            const active = model.is_active ? 'active' : '';
            const provider = model.provider || 'ollama';
            html += `
                <div class="model-item ${active}" data-model-id="${model.id}">
                    <div class="model-info">
                        <span class="model-name">${model.name}</span>
                        <span class="model-provider">${provider}</span>
                    </div>
                    <div class="model-actions">
                        <button class="btn-select-model" onclick="ModelManager.selectModel('${model.id}')">Seç</button>
                        <button class="btn-delete-model" onclick="ModelManager.deleteModel('${model.id}')">✕</button>
                    </div>
                </div>
            `;
        }
        container.innerHTML = html;
    },

    // Model seç
    selectModel: function(modelId) {
        fetch('/api/model/switch', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ model_id: modelId })
        })
        .then(res => res.json())
        .then(data => {
            if (data.success) {
                // Aktiv modeli yenilə
                this.models.forEach(m => m.is_active = m.id === modelId ? 1 : 0);
                this.activeModel = this.models.find(m => m.id === modelId);
                this.renderModels();

                if (typeof showToast === 'function') {
                    showToast(`Model dəyişdirildi: ${this.activeModel.name}`, 'success');
                }
            }
        })
        .catch(err => {
            console.error('Model seçmə xətası:', err);
        });
    },

    // Yeni model əlavə et
    addModel: function(modelData) {
        fetch('/api/model/add', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify(modelData)
        })
        .then(res => res.json())
        .then(data => {
            if (data.success) {
                this.loadModels();
                if (typeof showToast === 'function') {
                    showToast('Model əlavə edildi', 'success');
                }
            }
        })
        .catch(err => {
            console.error('Model əlavə xətası:', err);
        });
    },

    // Model sil
    deleteModel: function(modelId) {
        if (!confirm('Bu modeli silmək istəyirsiniz?')) return;

        fetch(`/api/model/delete/${modelId}`, {
            method: 'DELETE'
        })
        .then(res => res.json())
        .then(data => {
            if (data.success) {
                this.loadModels();
                if (typeof showToast === 'function') {
                    showToast('Model silindi', 'info');
                }
            }
        })
        .catch(err => {
            console.error('Model silmə xətası:', err);
        });
    },

    // Aktiv modelin adını qaytar
    getActiveModelName: function() {
        return this.activeModel ? this.activeModel.name : 'Qwen3 8B';
    }
};

// Səhifə yüklənəndə modelləri yüklə
document.addEventListener('DOMContentLoaded', function() {
    ModelManager.loadModels();
});