"""
DAU Dashboard - Yaddaş Sistemi
User Profile, Conversation, Long-Term, Project, Trading Memory
SQLAlchemy ilə database əməliyyatları
"""

import json
from datetime import datetime
from database import Session, generate_id, MemoryEntry, User


class MemorySystem:
    """Yaddaş Sistemi - 5 növ yaddaşın idarəetməsi"""

    MEMORY_TYPES = ['user_profile', 'conversation', 'long_term', 'project', 'trading']

    # ============================================
    # YADDAS YARAT / YENILƏ
    # ============================================

    def save(self, user_id, memory_type, key, value, category=None, importance=0.5, expires_at=None):
        """
        Yaddaş qeydi yaradır və ya yeniləyir
        Əgər eyni user_id + type + key varsa, yeniləyir
        """
        if memory_type not in self.MEMORY_TYPES:
            return {'error': f'Yanlış yaddaş növü. Mümkün növlər: {self.MEMORY_TYPES}'}

        db = Session()
        try:
            existing = db.query(MemoryEntry).filter_by(
                user_id=user_id, type=memory_type, key=key
            ).first()

            now = datetime.now().isoformat()

            if existing:
                existing.value = value
                existing.category = category
                existing.importance = importance
                existing.access_count += 1
                existing.last_accessed = now
                existing.expires_at = expires_at
                existing.updated_at = now
                memory_id = existing.id
            else:
                entry = MemoryEntry(
                    user_id=user_id,
                    type=memory_type,
                    category=category,
                    key=key,
                    value=value,
                    importance=importance,
                    access_count=0,
                    last_accessed=now,
                    expires_at=expires_at,
                    created_at=now,
                    updated_at=now,
                )
                db.add(entry)
                memory_id = entry.id

            db.commit()
            return {'success': True, 'id': memory_id}

        except Exception as e:
            db.rollback()
            return {'error': str(e)}
        finally:
            db.close()

    # ============================================
    # YADDAS OXU
    # ============================================

    def get(self, user_id, memory_type=None, key=None, memory_id=None):
        """Yaddaş qeydini oxuyur"""
        db = Session()
        try:
            query = db.query(MemoryEntry).filter_by(user_id=user_id)

            if memory_id:
                entry = query.filter_by(id=memory_id).first()
                return self._to_dict(entry) if entry else None

            if memory_type:
                query = query.filter_by(type=memory_type)

            if key:
                query = query.filter_by(key=key)

            entries = query.order_by(
                MemoryEntry.importance.desc(),
                MemoryEntry.updated_at.desc()
            ).all()

            return [self._to_dict(e) for e in entries]

        finally:
            db.close()

    # ============================================
    # YADDAS AXTAR
    # ============================================

    def search(self, user_id, query_text, memory_type=None, limit=50):
        """Açar sözü ilə yaddaş axtarır"""
        db = Session()
        try:
            q = db.query(MemoryEntry).filter_by(user_id=user_id)

            if memory_type:
                q = q.filter_by(type=memory_type)

            search_pattern = f'%{query_text}%'
            from sqlalchemy import or_
            q = q.filter(
                or_(
                    MemoryEntry.key.like(search_pattern),
                    MemoryEntry.value.like(search_pattern)
                )
            )

            entries = q.order_by(
                MemoryEntry.importance.desc(),
                MemoryEntry.updated_at.desc()
            ).limit(limit).all()

            return [self._to_dict(e) for e in entries]

        finally:
            db.close()

    # ============================================
    # YADDAS SİL
    # ============================================

    def delete(self, user_id, memory_id):
        """Yaddaş qeydini silir"""
        db = Session()
        try:
            entry = db.query(MemoryEntry).filter_by(id=memory_id, user_id=user_id).first()
            if not entry:
                return {'error': 'Yaddaş qeydi tapılmadı'}

            db.delete(entry)
            db.commit()
            return {'success': True, 'message': 'Yaddaş qeydi silindi'}

        except Exception as e:
            db.rollback()
            return {'error': str(e)}
        finally:
            db.close()

    # ============================================
    # STATİSTİKA
    # ============================================

    def get_stats(self, user_id):
        """Yaddaş statistikasını qaytarır"""
        db = Session()
        try:
            from sqlalchemy import func, case

            # Ümumi say
            total = db.query(MemoryEntry).filter_by(user_id=user_id).count()

            # Növə görə say
            type_rows = db.query(
                MemoryEntry.type,
                func.count(MemoryEntry.id).label('count')
            ).filter_by(user_id=user_id).group_by(MemoryEntry.type).all()

            by_type = {row.type: row.count for row in type_rows}

            # Əhəmiyyət bölgüsü
            high = db.query(MemoryEntry).filter(
                MemoryEntry.user_id == user_id,
                MemoryEntry.importance > 0.7
            ).count()

            medium = db.query(MemoryEntry).filter(
                MemoryEntry.user_id == user_id,
                MemoryEntry.importance >= 0.4,
                MemoryEntry.importance <= 0.7
            ).count()

            low = db.query(MemoryEntry).filter(
                MemoryEntry.user_id == user_id,
                MemoryEntry.importance < 0.4
            ).count()

            # Ən çox istifadə edilən
            most_accessed_rows = db.query(MemoryEntry).filter_by(
                user_id=user_id
            ).order_by(MemoryEntry.access_count.desc()).limit(5).all()

            most_accessed = [
                {
                    'key': e.key,
                    'type': e.type,
                    'access_count': e.access_count,
                    'importance': e.importance,
                }
                for e in most_accessed_rows
            ]

            return {
                'total': total,
                'by_type': by_type,
                'importance_distribution': {
                    'high': high,
                    'medium': medium,
                    'low': low,
                },
                'most_accessed': most_accessed,
            }

        finally:
            db.close()

    # ============================================
    # İSTİFADƏÇİ PROFİLİ YADDASI
    # ============================================

    def save_user_profile(self, user_id, profile_data):
        """İstifadəçi profil yaddaşını saxlayır"""
        return self.save(
            user_id=user_id,
            memory_type='user_profile',
            key='profile',
            value=json.dumps(profile_data, ensure_ascii=False),
            category='profile',
            importance=0.9
        )

    def get_user_profile(self, user_id):
        """İstifadəçi profil yaddaşını oxuyur"""
        result = self.get(user_id, 'user_profile', 'profile')
        if result:
            if isinstance(result, list) and len(result) > 0:
                try:
                    result[0]['parsed_value'] = json.loads(result[0]['value'])
                except (json.JSONDecodeError, IndexError):
                    pass
        return result

    # ============================================
    # SÖHBƏT YADDASI
    # ============================================

    def save_conversation_memory(self, user_id, conversation_id, summary, tags=None):
        """Söhbət yaddaşını saxlayır"""
        return self.save(
            user_id=user_id,
            memory_type='conversation',
            key=f'conv_{conversation_id}',
            value=json.dumps({
                'conversation_id': conversation_id,
                'summary': summary,
                'tags': tags or []
            }, ensure_ascii=False),
            category='conversation',
            importance=0.6
        )

    # ============================================
    # UZUNMÜDDƏTLİ YADDAS
    # ============================================

    def save_long_term(self, user_id, key, value, importance=0.7):
        """Uzunmüddətli yaddaş saxlayır"""
        return self.save(
            user_id=user_id,
            memory_type='long_term',
            key=key,
            value=value,
            category='long_term',
            importance=importance
        )

    # ============================================
    # LAYİHƏ YADDASI
    # ============================================

    def save_project_memory(self, user_id, project_id, project_data):
        """Layihə yaddaşını saxlayır"""
        return self.save(
            user_id=user_id,
            memory_type='project',
            key=f'project_{project_id}',
            value=json.dumps(project_data, ensure_ascii=False),
            category='project',
            importance=0.7
        )

    # ============================================
    # TİCARƏT YADDASI
    # ============================================

    def save_trading_memory(self, user_id, trade_id, lessons, emotion):
        """Ticarət yaddaşını saxlayır"""
        return self.save(
            user_id=user_id,
            memory_type='trading',
            key=f'trade_{trade_id}',
            value=json.dumps({
                'trade_id': trade_id,
                'lessons': lessons,
                'emotion': emotion
            }, ensure_ascii=False),
            category='trading',
            importance=0.8
        )

    # ============================================
    # VAXTI KEÇMİŞ YADDASLARI TƏMİZLƏ
    # ============================================

    def cleanup_expired(self, user_id=None):
        """Vaxtı keçmiş yaddaşları silir"""
        db = Session()
        try:
            now = datetime.now().isoformat()
            q = db.query(MemoryEntry).filter(
                MemoryEntry.expires_at.isnot(None),
                MemoryEntry.expires_at < now
            )

            if user_id:
                q = q.filter_by(user_id=user_id)

            count = q.count()
            q.delete(synchronize_session=False)
            db.commit()

            return {'success': True, 'deleted_count': count}

        except Exception as e:
            db.rollback()
            return {'error': str(e)}
        finally:
            db.close()

    # ============================================
    # KÖMƏKÇİ
    # ============================================

    def _to_dict(self, entry):
        """MemoryEntry obyektini dictionary-ə çevirir"""
        if entry is None:
            return None
        return {
            'id': entry.id,
            'user_id': entry.user_id,
            'type': entry.type,
            'category': entry.category,
            'key': entry.key,
            'value': entry.value,
            'importance': entry.importance,
            'access_count': entry.access_count,
            'last_accessed': entry.last_accessed,
            'expires_at': entry.expires_at,
            'created_at': entry.created_at,
            'updated_at': entry.updated_at,
        }