"""
DAU Dashboard - Memory API Route-ları
"""

from flask import Blueprint, request, jsonify
from database import Session, MemoryEntry
from modules.memory_system import MemorySystem

memory_bp = Blueprint('memory', __name__)
memory_system = MemorySystem()


@memory_bp.route('/api/memory/list', methods=['GET'])
def memory_list():
    """Bütün yaddaş məlumatlarını siyahıya alır"""
    db = Session()
    try:
        user_id = request.args.get('user_id', 'default-user')
        entries = db.query(MemoryEntry).filter_by(user_id=user_id).order_by(MemoryEntry.created_at.desc()).all()
        result = []
        for e in entries:
            result.append({
                'id': e.id,
                'type': e.type,
                'category': e.category,
                'key': e.key,
                'value': e.value,
                'importance': e.importance,
                'access_count': e.access_count,
                'last_accessed': e.last_accessed,
                'expires_at': e.expires_at,
                'created_at': e.created_at,
                'updated_at': e.updated_at,
            })
        return jsonify({'memories': result})
    except Exception as e:
        return jsonify({'error': str(e)}), 500
    finally:
        db.close()


@memory_bp.route('/api/memory/save', methods=['POST'])
def memory_save():
    """Yeni yaddaş məlumatı saxlayır"""
    data = request.get_json()
    if not data:
        return jsonify({'error': 'Məlumat göndərilməyib'}), 400

    content = data.get('content', '')
    category = data.get('category', 'general')
    importance = data.get('importance', 'medium')

    if not content:
        return jsonify({'error': 'Məzmun boşdur'}), 400

    # Importance-ni float-a çevir
    importance_map = {'low': 0.3, 'medium': 0.5, 'high': 0.8, 'critical': 1.0}
    importance_float = importance_map.get(importance, 0.5)

    db = Session()
    try:
        entry = MemoryEntry(
            user_id='default-user',
            type=category,
            category=category,
            key=category + '_' + str(hash(content))[:8],
            value=content,
            importance=importance_float,
        )
        db.add(entry)
        db.commit()
        return jsonify({'success': True, 'id': entry.id})
    except Exception as e:
        db.rollback()
        return jsonify({'error': str(e)}), 500
    finally:
        db.close()


@memory_bp.route('/api/memory/search', methods=['GET'])
def memory_search():
    """Yaddaşda axtarış edir"""
    query = request.args.get('q', '')
    if not query:
        return jsonify({'memories': []})

    db = Session()
    try:
        entries = db.query(MemoryEntry).filter(
            MemoryEntry.value.contains(query)
        ).order_by(MemoryEntry.importance.desc()).all()
        result = []
        for e in entries:
            result.append({
                'id': e.id,
                'type': e.type,
                'category': e.category,
                'key': e.key,
                'value': e.value,
                'importance': e.importance,
                'created_at': e.created_at,
            })
        return jsonify({'memories': result})
    except Exception as e:
        return jsonify({'error': str(e)}), 500
    finally:
        db.close()


@memory_bp.route('/api/memory/delete/<memory_id>', methods=['DELETE'])
def memory_delete(memory_id):
    """Yaddaş məlumatını silir"""
    db = Session()
    try:
        entry = db.query(MemoryEntry).filter_by(id=memory_id).first()
        if not entry:
            return jsonify({'error': 'Məlumat tapılmadı'}), 404
        db.delete(entry)
        db.commit()
        return jsonify({'success': True})
    except Exception as e:
        db.rollback()
        return jsonify({'error': str(e)}), 500
    finally:
        db.close()


@memory_bp.route('/api/memory/get/<memory_id>', methods=['GET'])
def memory_get(memory_id):
    """Bir yaddaş məlumatını gətirir"""
    db = Session()
    try:
        entry = db.query(MemoryEntry).filter_by(id=memory_id).first()
        if not entry:
            return jsonify({'error': 'Məlumat tapılmadı'}), 404
        # Access count artır
        entry.access_count = (entry.access_count or 0) + 1
        db.commit()
        return jsonify({
            'id': entry.id,
            'type': entry.type,
            'category': entry.category,
            'key': entry.key,
            'value': entry.value,
            'importance': entry.importance,
            'access_count': entry.access_count,
            'created_at': entry.created_at,
        })
    except Exception as e:
        return jsonify({'error': str(e)}), 500
    finally:
        db.close()