"""
DAU Dashboard - Model İdarəetmə API Routes
"""

from flask import Blueprint, request, jsonify
from modules.model_management import ModelManagement

model_bp = Blueprint('model', __name__, url_prefix='/api/model')
model_mgmt = ModelManagement()


@model_bp.route('/list', methods=['GET'])
def get_models():
    """Bütün modellərin siyahısı"""
    result = model_mgmt.get_models()
    return jsonify({'models': result, 'count': len(result)}), 200


@model_bp.route('/active', methods=['GET'])
def get_active_model():
    """Aktiv model"""
    result = model_mgmt.get_active_model()

    if result is None:
        return jsonify({'error': 'Aktiv model yoxdur'}), 404

    return jsonify(result), 200


@model_bp.route('/add', methods=['POST'])
def add_model():
    """Yeni model əlavə et"""
    data = request.get_json()

    if not data:
        return jsonify({'error': 'Məlumat göndərilməyib'}), 400

    name = data.get('name', '')
    model_id = data.get('model_id', '')
    provider = data.get('provider', '')
    description = data.get('description', '')
    max_tokens = data.get('max_tokens', 4096)
    temperature = data.get('temperature', 0.7)
    api_endpoint = data.get('api_endpoint')
    api_key = data.get('api_key')

    if not name or not model_id or not provider:
        return jsonify({'error': 'name, model_id və provider tələb olunur'}), 400

    valid_providers = ['ollama', 'openai', 'anthropic']
    if provider not in valid_providers:
        return jsonify({'error': f'Dəstəklənməyən provider. Mövcud: {valid_providers}'}), 400

    result = model_mgmt.add_model(
        name=name,
        model_id=model_id,
        provider=provider,
        description=description,
        max_tokens=max_tokens,
        temperature=temperature,
        api_endpoint=api_endpoint,
        api_key=api_key,
    )

    if 'error' in result:
        return jsonify(result), 400

    return jsonify(result), 200


@model_bp.route('/<model_db_id>/activate', methods=['POST'])
def set_active_model(model_db_id):
    """Modeli aktivləşdir"""
    result = model_mgmt.set_active_model(model_db_id=model_db_id)

    if 'error' in result:
        return jsonify(result), 400

    return jsonify(result), 200


@model_bp.route('/<model_db_id>', methods=['PUT'])
def update_model(model_db_id):
    """Model parametrlərini yenilə"""
    data = request.get_json()

    if not data:
        return jsonify({'error': 'Məlumat göndərilməyib'}), 400

    updatable = {}
    for field in ['name', 'description', 'max_tokens', 'temperature',
                  'api_endpoint', 'api_key', 'model_id']:
        if field in data and data[field] is not None:
            updatable[field] = data[field]

    if not updatable:
        return jsonify({'error': 'Yenilənəcək məlumat yoxdur'}), 400

    result = model_mgmt.update_model(model_db_id=model_db_id, **updatable)

    if 'error' in result:
        return jsonify(result), 400

    return jsonify(result), 200


@model_bp.route('/<model_db_id>', methods=['DELETE'])
def delete_model(model_db_id):
    """Modeli sil"""
    result = model_mgmt.delete_model(model_db_id=model_db_id)

    if 'error' in result:
        return jsonify(result), 400

    return jsonify(result), 200


# ============================================
# OLLAMA ROUTE-LARI
# ============================================

@model_bp.route('/ollama/list', methods=['GET'])
def get_ollama_models():
    """Ollama-da yüklü modellər"""
    result = model_mgmt.get_ollama_models()
    return jsonify(result), 200


@model_bp.route('/ollama/pull', methods=['POST'])
def pull_ollama_model():
    """Ollama-dan model yüklə"""
    data = request.get_json()

    if not data:
        return jsonify({'error': 'Məlumat göndərilməyib'}), 400

    model_id = data.get('model_id', '')

    if not model_id:
        return jsonify({'error': 'model_id tələb olunur'}), 400

    result = model_mgmt.pull_ollama_model(model_id=model_id)

    if 'error' in result:
        return jsonify(result), 400

    return jsonify(result), 200


# ============================================
# API SINAQ ROUTE-LARI
# ============================================

@model_bp.route('/test/openai', methods=['POST'])
def test_openai():
    """OpenAI API sınağı"""
    data = request.get_json()

    if not data:
        return jsonify({'error': 'Məlumat göndərilməyib'}), 400

    api_key = data.get('api_key', '')
    model = data.get('model', 'gpt-3.5-turbo')

    if not api_key:
        return jsonify({'error': 'api_key tələb olunur'}), 400

    result = model_mgmt.test_openai_connection(api_key=api_key, model=model)

    if 'error' in result:
        return jsonify(result), 400

    return jsonify(result), 200


@model_bp.route('/test/anthropic', methods=['POST'])
def test_anthropic():
    """Anthropic API sınağı"""
    data = request.get_json()

    if not data:
        return jsonify({'error': 'Məlumat göndərilməyib'}), 400

    api_key = data.get('api_key', '')
    model = data.get('model', 'claude-3-haiku-20240307')

    if not api_key:
        return jsonify({'error': 'api_key tələb olunur'}), 400

    result = model_mgmt.test_anthropic_connection(api_key=api_key, model=model)

    if 'error' in result:
        return jsonify(result), 400

    return jsonify(result), 200


# ============================================
# UNİVERSAL ÇAĞIRMA
# ============================================

@model_bp.route('/call', methods=['POST'])
def call_model():
    """Aktiv modelə müraciət et"""
    data = request.get_json()

    if not data:
        return jsonify({'error': 'Məlumat göndərilməyib'}), 400

    prompt = data.get('prompt', '')
    system_prompt = data.get('system_prompt')
    history = data.get('history')

    if not prompt:
        return jsonify({'error': 'prompt tələb olunur'}), 400

    result = model_mgmt.call_model(
        prompt=prompt,
        system_prompt=system_prompt,
        history=history,
    )

    if 'error' in result:
        return jsonify(result), 400

    return jsonify(result), 200


# ============================================
# STATİSTİKA VƏ İLKLƏŞDİRMƏ
# ============================================

@model_bp.route('/stats', methods=['GET'])
def get_stats():
    """Model statistikası"""
    result = model_mgmt.get_stats()
    return jsonify(result), 200


@model_bp.route('/init-defaults', methods=['POST'])
def init_defaults():
    """Defolt modelləri yarat"""
    result = model_mgmt.ensure_default_models()

    if 'error' in result:
        return jsonify(result), 400

    return jsonify(result), 200