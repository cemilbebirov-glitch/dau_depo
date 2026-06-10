"""
DAU Dashboard - Yaddaş Sistemi API Routes
"""

from flask import Blueprint, request, jsonify
from modules.memory_system import MemorySystem

memory_bp = Blueprint('memory', __name__, url_prefix='/api/memory')
memory = MemorySystem()


@memory_bp.route('/save', methods=['POST'])
def save_memory():
    """Yaddaş saxlayır"""
    data = request.get_json()

    if not data:
        return jsonify({'error': 'Məlumat göndərilməyib'}), 400

    user_id = data.get('user_id', 'default_user')
    category = data.get('category', 'general')
    key = data.get('key', '')
    value = data.get('value', '')
    metadata = data.get('metadata', {})
    expires_at = data.get('expires_at')

    if not key or not value:
        return jsonify({'error': 'key və value tələb olunur'}), 400

    result = memory.save(
        user_id=user_id,
        category=category,
        key=key,
        value=value,
        metadata=metadata,
        expires_at=expires_at,
    )

    if 'error' in result:
        return jsonify(result), 400

    return jsonify(result), 200


@memory_bp.route('/get/<category>/<key>', methods=['GET'])
def get_memory(category, key):
    """Yaddaş oxuyur"""
    user_id = request.args.get('user_id', 'default_user')
    result = memory.get(user_id=user_id, category=category, key=key)

    if result is None:
        return jsonify({'error': 'Yaddaş tapılmadı'}), 404

    return jsonify(result), 200


@memory_bp.route('/search', methods=['POST'])
def search_memory():
    """Yaddaş axtarır"""
    data = request.get_json()

    if not data:
        return jsonify({'error': 'Məlumat göndərilməyib'}), 400

    user_id = data.get('user_id', 'default_user')
    query = data.get('query', '')
    category = data.get('category')
    limit = data.get('limit', 20)

    if not query:
        return jsonify({'error': 'query tələb olunur'}), 400

    results = memory.search(
        user_id=user_id,
        query=query,
        category=category,
        limit=limit,
    )

    return jsonify({'results': results, 'count': len(results)}), 200


@memory_bp.route('/delete/<memory_id>', methods=['DELETE'])
def delete_memory(memory_id):
    """Yaddaş silir"""
    user_id = request.args.get('user_id', 'default_user')
    result = memory.delete(memory_id=memory_id, user_id=user_id)

    if 'error' in result:
        return jsonify(result), 400

    return jsonify(result), 200


@memory_bp.route('/stats', methods=['GET'])
def get_stats():
    """Yaddaş statistikası"""
    user_id = request.args.get('user_id', 'default_user')
    result = memory.get_stats(user_id=user_id)

    return jsonify(result), 200


@memory_bp.route('/user-profile', methods=['POST'])
def save_user_profile():
    """İstifadəçi profilini saxlayır"""
    data = request.get_json()

    if not data:
        return jsonify({'error': 'Məlumat göndərilməyib'}), 400

    user_id = data.get('user_id', 'default_user')
    profile_data = data.get('profile', {})

    result = memory.save_user_profile(user_id=user_id, profile_data=profile_data)

    if 'error' in result:
        return jsonify(result), 400

    return jsonify(result), 200


@memory_bp.route('/conversation', methods=['POST'])
def save_conversation():
    """Söhbət yaddaşını saxlayır"""
    data = request.get_json()

    if not data:
        return jsonify({'error': 'Məlumat göndərilməyib'}), 400

    user_id = data.get('user_id', 'default_user')
    role = data.get('role', 'user')
    content = data.get('content', '')
    conversation_id = data.get('conversation_id')

    if not content:
        return jsonify({'error': 'content tələb olunur'}), 400

    result = memory.save_conversation_memory(
        user_id=user_id,
        role=role,
        content=content,
        conversation_id=conversation_id,
    )

    if 'error' in result:
        return jsonify(result), 400

    return jsonify(result), 200


@memory_bp.route('/long-term', methods=['POST'])
def save_long_term():
    """Uzunmüddətli yaddaş saxlayır"""
    data = request.get_json()

    if not data:
        return jsonify({'error': 'Məlumat göndərilməyib'}), 400

    user_id = data.get('user_id', 'default_user')
    key = data.get('key', '')
    value = data.get('value', '')
    importance = data.get('importance', 5)

    if not key or not value:
        return jsonify({'error': 'key və value tələb olunur'}), 400

    result = memory.save_long_term(
        user_id=user_id,
        key=key,
        value=value,
        importance=importance,
    )

    if 'error' in result:
        return jsonify(result), 400

    return jsonify(result), 200


@memory_bp.route('/project', methods=['POST'])
def save_project_memory():
    """Layihə yaddaşı saxlayır"""
    data = request.get_json()

    if not data:
        return jsonify({'error': 'Məlumat göndərilməyib'}), 400

    user_id = data.get('user_id', 'default_user')
    project_id = data.get('project_id', '')
    key = data.get('key', '')
    value = data.get('value', '')

    if not project_id or not key or not value:
        return jsonify({'error': 'project_id, key və value tələb olunur'}), 400

    result = memory.save_project_memory(
        user_id=user_id,
        project_id=project_id,
        key=key,
        value=value,
    )

    if 'error' in result:
        return jsonify(result), 400

    return jsonify(result), 200


@memory_bp.route('/trading', methods=['POST'])
def save_trading_memory():
    """Ticarət yaddaşı saxlayır"""
    data = request.get_json()

    if not data:
        return jsonify({'error': 'Məlumat göndərilməyib'}), 400

    user_id = data.get('user_id', 'default_user')
    key = data.get('key', '')
    value = data.get('value', '')

    if not key or not value:
        return jsonify({'error': 'key və value tələb olunur'}), 400

    result = memory.save_trading_memory(
        user_id=user_id,
        key=key,
        value=value,
    )

    if 'error' in result:
        return jsonify(result), 400

    return jsonify(result), 200

"""
DAU Dashboard - Sistem Monitorinq API Routes
"""

from flask import Blueprint, request, jsonify
from modules.monitor_module import MonitorModule

monitor_bp = Blueprint('monitor', __name__, url_prefix='/api/monitor')
monitor = MonitorModule()


@monitor_bp.route('/overview', methods=['GET'])
def get_overview():
    """Tam sistem icmalı"""
    result = monitor.get_system_overview()
    return jsonify(result), 200


@monitor_bp.route('/cpu', methods=['GET'])
def get_cpu():
    """CPU məlumatları"""
    result = monitor.get_cpu_info()

    if 'error' in result:
        return jsonify(result), 400

    return jsonify(result), 200


@monitor_bp.route('/ram', methods=['GET'])
def get_ram():
    """RAM məlumatları"""
    result = monitor.get_ram_info()

    if 'error' in result:
        return jsonify(result), 400

    return jsonify(result), 200


@monitor_bp.route('/gpu', methods=['GET'])
def get_gpu():
    """GPU məlumatları"""
    result = monitor.get_gpu_info()
    return jsonify(result), 200


@monitor_bp.route('/disk', methods=['GET'])
def get_disk():
    """Disk məlumatları"""
    result = monitor.get_disk_info()

    if 'error' in result:
        return jsonify(result), 400

    return jsonify(result), 200


@monitor_bp.route('/network', methods=['GET'])
def get_network():
    """Şəbəkə məlumatları"""
    result = monitor.get_network_info()

    if 'error' in result:
        return jsonify(result), 400

    return jsonify(result), 200


@monitor_bp.route('/processes', methods=['GET'])
def get_top_processes():
    """Ən çox resurs istifadə edən proseslər"""
    sort_by = request.args.get('sort_by', 'cpu')
    limit = request.args.get('limit', 10, type=int)

    result = monitor.get_top_processes(sort_by=sort_by, limit=limit)

    if 'error' in result:
        return jsonify(result), 400

    return jsonify(result), 200


@monitor_bp.route('/live', methods=['GET'])
def get_live_data():
    """Canlı data (WebSocket üçün)"""
    result = monitor.get_live_data()

    if 'error' in result:
        return jsonify(result), 400

    return jsonify(result), 200


@monitor_bp.route('/history/<metric_type>', methods=['GET'])
def get_metric_history(metric_type):
    """Metrik tarixçəsi"""
    hours = request.args.get('hours', 1, type=int)

    valid_types = ['cpu', 'ram', 'gpu', 'disk']
    if metric_type not in valid_types:
        return jsonify({'error': f'Yanlış metrik növü. Mövcud: {valid_types}'}), 400

    result = monitor.get_metric_history(metric_type=metric_type, hours=hours)

    return jsonify(result), 200


@monitor_bp.route('/stats', methods=['GET'])
def get_stats():
    """Monitorinq statistikası"""
    result = monitor.get_stats()
    return jsonify(result), 200


@monitor_bp.route('/cleanup', methods=['POST'])
def cleanup_old_metrics():
    """Köhnə metrikları təmizlə"""
    data = request.get_json() or {}
    days = data.get('days', 7, type=int)

    result = monitor.cleanup_old_metrics(days=days)

    if 'error' in result:
        return jsonify(result), 400

    return jsonify(result), 200
@memory_bp.route('/cleanup', methods=['POST'])
def cleanup_expired():
    """Müddəti bitmiş yaddaşları təmizləyir"""
    result = memory.cleanup_expired()
    return jsonify(result), 200