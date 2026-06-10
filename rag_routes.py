"""
DAU Dashboard - RAG Sistemi API Routes
"""

import os
from flask import Blueprint, request, jsonify
from modules.rag_system import RAGSystem

rag_bp = Blueprint('rag', __name__, url_prefix='/api/rag')
rag = RAGSystem()


@rag_bp.route('/upload', methods=['POST'])
def upload_document():
    """Sənəd yükləyir"""
    user_id = request.form.get('user_id', 'default_user')
    project_id = request.form.get('project_id')

    if 'file' not in request.files:
        return jsonify({'error': 'Fayl göndərilməyib'}), 400

    file = request.files['file']

    if file.filename == '':
        return jsonify({'error': 'Fayl seçilməyib'}), 400

    # Fayl növünü müəyyən et
    filename = file.filename
    extension = os.path.splitext(filename)[1].lower().lstrip('.')

    supported_types = ['pdf', 'docx', 'txt', 'csv', 'xlsx']
    if extension not in supported_types:
        return jsonify({'error': f'Dəstəklənməyən fayl növü: {extension}. Dəstəklənən: {supported_types}'}), 400

    # Fayl məzmununu oxu
    file_data = file.read()

    if len(file_data) == 0:
        return jsonify({'error': 'Fayl boşdur'}), 400

    # Maksimum fayl ölçüsü: 50MB
    max_size = 50 * 1024 * 1024
    if len(file_data) > max_size:
        return jsonify({'error': f'Fayl çox böyükdür. Maksimum: 50MB'}), 400

    result = rag.upload_document(
        user_id=user_id,
        file_data=file_data,
        original_name=filename,
        mime_type=extension,
        project_id=project_id,
    )

    if 'error' in result:
        return jsonify(result), 400

    return jsonify(result), 200


@rag_bp.route('/documents', methods=['GET'])
def get_documents():
    """Sənəd siyahısı"""
    user_id = request.args.get('user_id', 'default_user')
    mime_type = request.args.get('mime_type')
    project_id = request.args.get('project_id')

    result = rag.get_documents(
        user_id=user_id,
        mime_type=mime_type,
        project_id=project_id,
    )

    return jsonify({'documents': result, 'count': len(result)}), 200


@rag_bp.route('/document/<document_id>', methods=['GET'])
def get_document(document_id):
    """Bir sənədin məlumatları"""
    user_id = request.args.get('user_id', 'default_user')

    result = rag.get_document(document_id=document_id, user_id=user_id)

    if result is None:
        return jsonify({'error': 'Sənəd tapılmadı'}), 404

    return jsonify(result), 200


@rag_bp.route('/document/<document_id>', methods=['DELETE'])
def delete_document(document_id):
    """Sənədi silir"""
    user_id = request.args.get('user_id', 'default_user')

    result = rag.delete_document(document_id=document_id, user_id=user_id)

    if 'error' in result:
        return jsonify(result), 400

    return jsonify(result), 200


@rag_bp.route('/search', methods=['POST'])
def search_documents():
    """Semantik axtarış"""
    data = request.get_json()

    if not data:
        return jsonify({'error': 'Məlumat göndərilməyib'}), 400

    user_id = data.get('user_id', 'default_user')
    query = data.get('query', '')
    top_k = data.get('top_k', 5)
    threshold = data.get('threshold', 0.1)
    document_ids = data.get('document_ids')

    if not query:
        return jsonify({'error': 'query tələb olunur'}), 400

    results = rag.search(
        user_id=user_id,
        query=query,
        top_k=top_k,
        threshold=threshold,
        document_ids=document_ids,
    )

    return jsonify({'results': results, 'count': len(results)}), 200


@rag_bp.route('/stats', methods=['GET'])
def get_stats():
    """Sənəd statistikası"""
    user_id = request.args.get('user_id', 'default_user')

    result = rag.get_stats(user_id=user_id)

    return jsonify(result), 200


@rag_bp.route('/chromadb/status', methods=['GET'])
def chromadb_status():
    """ChromaDB inteqrasiya statusu"""
    result = rag.get_chromadb_status()
    return jsonify(result), 200


@rag_bp.route('/chromadb/migrate', methods=['POST'])
def migrate_to_chromadb():
    """Sənədləri ChromaDB-ə köçürür"""
    data = request.get_json() or {}
    user_id = data.get('user_id', 'default_user')

    result = rag.migrate_to_chromadb(user_id=user_id)

    if 'error' in result:
        return jsonify(result), 400

    return jsonify(result), 200