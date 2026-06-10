"""
DAU Dashboard - İş Sahəsi API Routes
"""

from flask import Blueprint, request, jsonify
from modules.workspace_module import WorkspaceModule

workspace_bp = Blueprint('workspace', __name__, url_prefix='/api/workspace')
ws = WorkspaceModule()


@workspace_bp.route('/directory', methods=['GET'])
def list_directory():
    """Kataloq məzmunu"""
    path = request.args.get('path')
    result = ws.list_directory(path=path)

    if 'error' in result:
        return jsonify(result), 400

    return jsonify(result), 200


@workspace_bp.route('/file', methods=['GET'])
def read_file():
    """Fayl oxu"""
    path = request.args.get('path')

    if not path:
        return jsonify({'error': 'path tələb olunur'}), 400

    result = ws.read_file(path=path)

    if 'error' in result:
        return jsonify(result), 400

    return jsonify(result), 200


@workspace_bp.route('/file', methods=['POST'])
def write_file():
    """Fayl yaz"""
    data = request.get_json()

    if not data:
        return jsonify({'error': 'Məlumat göndərilməyib'}), 400

    path = data.get('path', '')
    content = data.get('content', '')

    if not path:
        return jsonify({'error': 'path tələb olunur'}), 400

    result = ws.write_file(path=path, content=content)

    if 'error' in result:
        return jsonify(result), 400

    return jsonify(result), 200


@workspace_bp.route('/directory', methods=['POST'])
def create_directory():
    """Yeni kataloq yarat"""
    data = request.get_json()

    if not data:
        return jsonify({'error': 'Məlumat göndərilməyib'}), 400

    path = data.get('path', '')

    if not path:
        return jsonify({'error': 'path tələb olunur'}), 400

    result = ws.create_directory(path=path)

    if 'error' in result:
        return jsonify(result), 400

    return jsonify(result), 200


@workspace_bp.route('/delete', methods=['DELETE'])
def delete_item():
    """Fayl/kataloq sil"""
    path = request.args.get('path')

    if not path:
        return jsonify({'error': 'path tələb olunur'}), 400

    result = ws.delete_item(path=path)

    if 'error' in result:
        return jsonify(result), 400

    return jsonify(result), 200


@workspace_bp.route('/rename', methods=['POST'])
def rename_item():
    """Yenidən adlandır"""
    data = request.get_json()

    if not data:
        return jsonify({'error': 'Məlumat göndərilməyib'}), 400

    old_path = data.get('old_path', '')
    new_name = data.get('new_name', '')

    if not old_path or not new_name:
        return jsonify({'error': 'old_path və new_name tələb olunur'}), 400

    result = ws.rename_item(old_path=old_path, new_name=new_name)

    if 'error' in result:
        return jsonify(result), 400

    return jsonify(result), 200


@workspace_bp.route('/search', methods=['POST'])
def search_files():
    """Fayl axtarışı"""
    data = request.get_json()

    if not data:
        return jsonify({'error': 'Məlumat göndərilməyib'}), 400

    query = data.get('query', '')
    path = data.get('path')
    search_content = data.get('search_content', False)

    if not query:
        return jsonify({'error': 'query tələb olunur'}), 400

    result = ws.search_files(
        query=query,
        path=path,
        search_content=search_content,
    )

    return jsonify(result), 200


# ============================================
# LAYİHƏ ROUTE-LARI
# ============================================

@workspace_bp.route('/projects', methods=['GET'])
def get_projects():
    """Layihə siyahısı"""
    user_id = request.args.get('user_id', 'default_user')

    result = ws.get_projects(user_id=user_id)

    return jsonify({'projects': result, 'count': len(result)}), 200


@workspace_bp.route('/project', methods=['POST'])
def create_project():
    """Yeni layihə yarat"""
    data = request.get_json()

    if not data:
        return jsonify({'error': 'Məlumat göndərilməyib'}), 400

    user_id = data.get('user_id', 'default_user')
    name = data.get('name', '')
    description = data.get('description', '')
    project_type = data.get('type', 'general')

    if not name:
        return jsonify({'error': 'name tələb olunur'}), 400

    result = ws.create_project(
        user_id=user_id,
        name=name,
        description=description,
        project_type=project_type,
    )

    if 'error' in result:
        return jsonify(result), 400

    return jsonify(result), 200


@workspace_bp.route('/project/<project_id>', methods=['GET'])
def get_project(project_id):
    """Layihə detalları"""
    user_id = request.args.get('user_id', 'default_user')

    result = ws.get_project(project_id=project_id, user_id=user_id)

    if result is None:
        return jsonify({'error': 'Layihə tapılmadı'}), 404

    return jsonify(result), 200


@workspace_bp.route('/project/<project_id>', methods=['DELETE'])
def delete_project(project_id):
    """Layihəni sil"""
    user_id = request.args.get('user_id', 'default_user')

    result = ws.delete_project(project_id=project_id, user_id=user_id)

    if 'error' in result:
        return jsonify(result), 400

    return jsonify(result), 200


# ============================================
# KOD GENERASİYASI
# ============================================

@workspace_bp.route('/generate-code', methods=['POST'])
def generate_code():
    """AI ilə kod generasiya et"""
    data = request.get_json()

    if not data:
        return jsonify({'error': 'Məlumat göndərilməyib'}), 400

    user_id = data.get('user_id', 'default_user')
    prompt = data.get('prompt', '')
    language = data.get('language', 'python')
    context = data.get('context')

    if not prompt:
        return jsonify({'error': 'prompt tələb olunur'}), 400

    result = ws.generate_code(
        user_id=user_id,
        prompt=prompt,
        language=language,
        context=context,
    )

    if 'error' in result:
        return jsonify(result), 400

    return jsonify(result), 200


# ============================================
# TERMİNAL
# ============================================

@workspace_bp.route('/terminal', methods=['POST'])
def execute_command():
    """Terminal əmri icra et"""
    data = request.get_json()

    if not data:
        return jsonify({'error': 'Məlumat göndərilməyib'}), 400

    command = data.get('command', '')
    working_dir = data.get('working_dir')
    timeout = data.get('timeout', 30)

    if not command:
        return jsonify({'error': 'command tələb olunur'}), 400

    result = ws.execute_command(
        command=command,
        working_dir=working_dir,
        timeout=timeout,
    )

    if 'error' in result:
        return jsonify(result), 400

    return jsonify(result), 200


# ============================================
# STATİSTİKA
# ============================================

@workspace_bp.route('/stats', methods=['GET'])
def get_stats():
    """İş sahəsi statistikası"""
    user_id = request.args.get('user_id')

    result = ws.get_stats(user_id=user_id)

    return jsonify(result), 200