"""
DAU Dashboard - Model İdarəetmə Modulu
AI modellərinin idarə olunması, keçid, konfiqurasiya
Dəstəklənən: Ollama (Qwen3, DeepSeek, Llama), OpenAI API, Anthropic API
Model dəyişdirmək üçün kod dəyişikliyi tələb olunmur
SQLAlchemy ilə database əməliyyatları
"""

import os
import json
import importlib
from datetime import datetime
from database import Session, generate_id, AIModel


class ModelManagement:
    """Model İdarəetmə - AI modellərinin idarə olunması"""

    # Ollama defolt konfiqurasiyası
    OLLAMA_BASE_URL = 'http://localhost:11434'

    # ============================================
    # MODEL SİYAHISI
    # ============================================

    def get_models(self):
        """Bütün qeydiyyatlı modelləri qaytarır"""
        db = Session()
        try:
            models = db.query(AIModel).order_by(AIModel.created_at).all()

            result = []
            for m in models:
                model_dict = {
                    'id': m.id,
                    'name': m.name,
                    'model_id': m.model_id,
                    'provider': m.provider,
                    'is_active': m.is_active,
                    'description': m.description,
                    'max_tokens': m.max_tokens,
                    'temperature': m.temperature,
                    'api_endpoint': m.api_endpoint,
                    'api_key_set': bool(m.api_key),
                    'created_at': m.created_at,
                    'updated_at': m.updated_at,
                }

                # Ollama üçün status yoxla
                if m.provider == 'ollama':
                    model_dict['available'] = self._check_ollama_model(m.model_id)
                else:
                    model_dict['available'] = bool(m.api_key)

                result.append(model_dict)

            return result
        finally:
            db.close()

    def get_active_model(self):
        """Aktiv modeli qaytarır"""
        db = Session()
        try:
            model = db.query(AIModel).filter_by(is_active=True).first()

            if not model:
                return None

            return {
                'id': model.id,
                'name': model.name,
                'model_id': model.model_id,
                'provider': model.provider,
                'is_active': True,
                'max_tokens': model.max_tokens,
                'temperature': model.temperature,
                'api_endpoint': model.api_endpoint,
            }
        finally:
            db.close()

    # ============================================
    # MODEL ƏLAVƏ ET
    # ============================================

    def add_model(self, name, model_id, provider, description='',
                  max_tokens=4096, temperature=0.7,
                  api_endpoint=None, api_key=None):
        """Yeni model əlavə edir"""
        db = Session()
        try:
            # Eyni model_id var mı yoxla
            existing = db.query(AIModel).filter_by(model_id=model_id, provider=provider).first()
            if existing:
                return {'error': f'Bu model artıq mövcuddur: {model_id}'}

            model = AIModel(
                id=generate_id(),
                name=name,
                model_id=model_id,
                provider=provider,
                is_active=False,
                description=description,
                max_tokens=max_tokens,
                temperature=temperature,
                api_endpoint=api_endpoint or self._get_default_endpoint(provider),
                api_key=api_key,
                created_at=datetime.now().isoformat(),
                updated_at=datetime.now().isoformat(),
            )
            db.add(model)
            db.commit()

            return {
                'success': True,
                'model_id': model.id,
                'message': f'Model əlavə edildi: {name}',
            }
        except Exception as e:
            db.rollback()
            return {'error': f'Model əlavə etmə xətası: {str(e)}'}
        finally:
            db.close()

    # ============================================
    # MODEL AKTİVLƏŞDİR
    # ============================================

    def set_active_model(self, model_db_id):
        """Modeli aktivləşdirir (digərlərini deaktiv edir)"""
        db = Session()
        try:
            model = db.query(AIModel).filter_by(id=model_db_id).first()
            if not model:
                return {'error': 'Model tapılmadı'}

            # Ollama modeli var mı yoxla
            if model.provider == 'ollama':
                available = self._check_ollama_model(model.model_id)
                if not available:
                    return {
                        'error': f'{model.model_id} Ollama-da yüklü deyil. Əvvəlcə "ollama pull {model.model_id}" ilə yükləyin.',
                        'hint': f'Terminalda çalışdırın: ollama pull {model.model_id}'
                    }

            # API açarı var mı yoxla
            if model.provider in ['openai', 'anthropic'] and not model.api_key:
                return {'error': f'{model.provider} üçün API açarı tələb olunur'}

            # Bütün modelləri deaktiv et
            db.query(AIModel).update({'is_active': False})

            # Seçilən modeli aktiv et
            model.is_active = True
            db.commit()

            return {
                'success': True,
                'active_model': {
                    'name': model.name,
                    'model_id': model.model_id,
                    'provider': model.provider,
                },
                'message': f'Aktiv model: {model.name} ({model.model_id})',
            }
        except Exception as e:
            db.rollback()
            return {'error': str(e)}
        finally:
            db.close()

    # ============================================
    # MODEL YENİLƏ
    # ============================================

    def update_model(self, model_db_id, **kwargs):
        """Model parametrlərini yeniləyir"""
        db = Session()
        try:
            model = db.query(AIModel).filter_by(id=model_db_id).first()
            if not model:
                return {'error': 'Model tapılmadı'}

            updatable_fields = ['name', 'description', 'max_tokens', 'temperature',
                              'api_endpoint', 'api_key', 'model_id']

            for field in updatable_fields:
                if field in kwargs and kwargs[field] is not None:
                    setattr(model, field, kwargs[field])

            model.updated_at = datetime.now().isoformat()
            db.commit()

            return {
                'success': True,
                'message': f'Model yeniləndi: {model.name}',
            }
        except Exception as e:
            db.rollback()
            return {'error': str(e)}
        finally:
            db.close()

    # ============================================
    # MODEL SİL
    # ============================================

    def delete_model(self, model_db_id):
        """Modeli silir"""
        db = Session()
        try:
            model = db.query(AIModel).filter_by(id=model_db_id).first()
            if not model:
                return {'error': 'Model tapılmadı'}

            if model.is_active:
                return {'error': 'Aktiv modeli silə bilməzsiniz. Əvvəlcə başqa modeli aktivləşdirin.'}

            db.delete(model)
            db.commit()

            return {'success': True, 'message': f'Model silindi: {model.name}'}
        except Exception as e:
            db.rollback()
            return {'error': str(e)}
        finally:
            db.close()

    # ============================================
    # OLLAMA İNTEQRASİYASI
    # ============================================

    def get_ollama_models(self):
        """Ollama-da yüklü modelləri qaytarır"""
        try:
            import requests
            response = requests.get(
                f'{self.OLLAMA_BASE_URL}/api/tags',
                timeout=10,
            )

            if response.status_code != 200:
                return {'error': f'Ollama xətası: {response.status_code}', 'available': False}

            data = response.json()
            models = data.get('models', [])

            result = []
            for m in models:
                result.append({
                    'name': m.get('name', ''),
                    'size': m.get('size', 0),
                    'size_gb': round(m.get('size', 0) / (1024 ** 3), 2),
                    'modified_at': m.get('modified_at', ''),
                    'family': m.get('details', {}).get('family', ''),
                    'parameter_size': m.get('details', {}).get('parameter_size', ''),
                    'quantization_level': m.get('details', {}).get('quantization_level', ''),
                })

            return {
                'models': result,
                'count': len(result),
                'available': True,
            }
        except requests.exceptions.ConnectionError:
            return {
                'models': [],
                'count': 0,
                'available': False,
                'error': 'Ollama qoşulu deyil',
            }
        except Exception as e:
            return {
                'models': [],
                'count': 0,
                'available': False,
                'error': str(e),
            }

    def _check_ollama_model(self, model_id):
        """Ollama-da modelin olub-olmadığını yoxlayır"""
        try:
            import requests
            response = requests.get(
                f'{self.OLLAMA_BASE_URL}/api/tags',
                timeout=5,
            )

            if response.status_code != 200:
                return False

            data = response.json()
            models = data.get('models', [])

            for m in models:
                name = m.get('name', '')
                if name == model_id or name.startswith(model_id.split(':')[0]):
                    return True

            return False
        except Exception:
            return False

    def pull_ollama_model(self, model_id):
        """Ollama-dan model yükləyir"""
        try:
            import requests
            response = requests.post(
                f'{self.OLLAMA_BASE_URL}/api/pull',
                json={'name': model_id, 'stream': False},
                timeout=600,
            )

            if response.status_code != 200:
                return {'error': f'Yükləmə uğursuz: {response.status_code}'}

            return {
                'success': True,
                'message': f'{model_id} uğurla yükləndi',
            }
        except requests.exceptions.ConnectionError:
            return {'error': 'Ollama qoşulu deyil'}
        except requests.exceptions.Timeout:
            return {'error': 'Yükləmə vaxtı bitdi (model çox böyük ola bilər)'}
        except Exception as e:
            return {'error': str(e)}

    # ============================================
    # OPENAI API İNTEQRASİYASI
    # ============================================

    def test_openai_connection(self, api_key, model='gpt-3.5-turbo'):
        """OpenAI API bağlantısını sınayır"""
        try:
            import requests
            response = requests.post(
                'https://api.openai.com/v1/chat/completions',
                headers={
                    'Authorization': f'Bearer {api_key}',
                    'Content-Type': 'application/json',
                },
                json={
                    'model': model,
                    'messages': [{'role': 'user', 'content': 'Salam'}],
                    'max_tokens': 10,
                },
                timeout=30,
            )

            if response.status_code == 200:
                return {'success': True, 'message': 'OpenAI API bağlantısı uğurlu'}
            elif response.status_code == 401:
                return {'error': 'Yanlış API açarı'}
            else:
                return {'error': f'API xətası: {response.status_code}'}
        except requests.exceptions.ConnectionError:
            return {'error': 'İnternet bağlantısı yoxdur'}
        except Exception as e:
            return {'error': str(e)}

    # ============================================
    # ANTHROPIC API İNTEQRASİYASI
    # ============================================

    def test_anthropic_connection(self, api_key, model='claude-3-haiku-20240307'):
        """Anthropic API bağlantısını sınayır"""
        try:
            import requests
            response = requests.post(
                'https://api.anthropic.com/v1/messages',
                headers={
                    'x-api-key': api_key,
                    'anthropic-version': '2023-06-01',
                    'Content-Type': 'application/json',
                },
                json={
                    'model': model,
                    'max_tokens': 10,
                    'messages': [{'role': 'user', 'content': 'Salam'}],
                },
                timeout=30,
            )

            if response.status_code == 200:
                return {'success': True, 'message': 'Anthropic API bağlantısı uğurlu'}
            elif response.status_code == 401:
                return {'error': 'Yanlış API açarı'}
            else:
                return {'error': f'API xətası: {response.status_code}'}
        except requests.exceptions.ConnectionError:
            return {'error': 'İnternet bağlantısı yoxdur'}
        except Exception as e:
            return {'error': str(e)}

    # ============================================
    # UNİVERSAL ÇAĞIRMA
    # ============================================

    def call_model(self, prompt, system_prompt=None, history=None):
        """
        Aktiv modelə müraciət edir
        Provider-dan asılı olmayaraq eyni interfeys
        """
        db = Session()
        try:
            model = db.query(AIModel).filter_by(is_active=True).first()
            if not model:
                return {'error': 'Aktiv model yoxdur'}
        finally:
            db.close()

        if model.provider == 'ollama':
            return self._call_ollama(model, prompt, system_prompt, history)
        elif model.provider == 'openai':
            return self._call_openai(model, prompt, system_prompt, history)
        elif model.provider == 'anthropic':
            return self._call_anthropic(model, prompt, system_prompt, history)
        else:
            return {'error': f'Dəstəklənməyən provider: {model.provider}'}

    def _call_ollama(self, model, prompt, system_prompt=None, history=None):
        """Ollama API ilə model çağırır"""
        try:
            import requests

            full_prompt = ''
            if system_prompt:
                full_prompt += f'System: {system_prompt}\n\n'

            if history:
                for msg in history:
                    role = msg.get('role', 'user')
                    content = msg.get('content', '')
                    if role == 'user':
                        full_prompt += f'İstifadəçi: {content}\n'
                    elif role == 'assistant':
                        full_prompt += f'Köməkçi: {content}\n'

            full_prompt += f'İstifadəçi: {prompt}\nKöməkçi:'

            response = requests.post(
                f'{self.OLLAMA_BASE_URL}/api/generate',
                json={
                    'model': model.model_id,
                    'prompt': full_prompt,
                    'stream': False,
                    'options': {
                        'temperature': model.temperature,
                        'num_predict': model.max_tokens,
                    }
                },
                timeout=120,
            )

            if response.status_code != 200:
                return {'error': f'Ollama xətası: {response.status_code}'}

            data = response.json()
            text = data.get('response', '')

            # Think tag-ləri təmizlə
            import re
            text = re.sub(r'<think[^>]*>.*?</think\s*>', '', text, flags=re.DOTALL)
            text = re.sub(r'</?think[^>]*>', '', text)
            text = text.strip()

            return {
                'success': True,
                'response': text,
                'model': model.model_id,
                'provider': 'ollama',
            }
        except requests.exceptions.ConnectionError:
            return {'error': 'Ollama qoşulu deyil'}
        except requests.exceptions.Timeout:
            return {'error': 'Ollama cavab vaxtı bitdi'}
        except Exception as e:
            return {'error': str(e)}

    def _call_openai(self, model, prompt, system_prompt=None, history=None):
        """OpenAI API ilə model çağırır"""
        try:
            import requests

            messages = []
            if system_prompt:
                messages.append({'role': 'system', 'content': system_prompt})

            if history:
                messages.extend(history)

            messages.append({'role': 'user', 'content': prompt})

            response = requests.post(
                model.api_endpoint or 'https://api.openai.com/v1/chat/completions',
                headers={
                    'Authorization': f'Bearer {model.api_key}',
                    'Content-Type': 'application/json',
                },
                json={
                    'model': model.model_id,
                    'messages': messages,
                    'max_tokens': model.max_tokens,
                    'temperature': model.temperature,
                },
                timeout=60,
            )

            if response.status_code != 200:
                error_data = response.json() if response.headers.get('content-type', '').startswith('application/json') else {}
                error_msg = error_data.get('error', {}).get('message', f'HTTP {response.status_code}')
                return {'error': f'OpenAI xətası: {error_msg}'}

            data = response.json()
            text = data.get('choices', [{}])[0].get('message', {}).get('content', '')

            return {
                'success': True,
                'response': text,
                'model': model.model_id,
                'provider': 'openai',
                'usage': data.get('usage', {}),
            }
        except requests.exceptions.ConnectionError:
            return {'error': 'İnternet bağlantısı yoxdur'}
        except requests.exceptions.Timeout:
            return {'error': 'OpenAI cavab vaxtı bitdi'}
        except Exception as e:
            return {'error': str(e)}

    def _call_anthropic(self, model, prompt, system_prompt=None, history=None):
        """Anthropic API ilə model çağırır"""
        try:
            import requests

            messages = []
            if history:
                messages.extend(history)

            messages.append({'role': 'user', 'content': prompt})

            request_body = {
                'model': model.model_id,
                'max_tokens': model.max_tokens,
                'messages': messages,
            }

            if system_prompt:
                request_body['system'] = system_prompt

            response = requests.post(
                model.api_endpoint or 'https://api.anthropic.com/v1/messages',
                headers={
                    'x-api-key': model.api_key,
                    'anthropic-version': '2023-06-01',
                    'Content-Type': 'application/json',
                },
                json=request_body,
                timeout=60,
            )

            if response.status_code != 200:
                error_data = response.json() if response.headers.get('content-type', '').startswith('application/json') else {}
                error_msg = error_data.get('error', {}).get('message', f'HTTP {response.status_code}')
                return {'error': f'Anthropic xətası: {error_msg}'}

            data = response.json()
            text = ''
            content_blocks = data.get('content', [])
            for block in content_blocks:
                if block.get('type') == 'text':
                    text += block.get('text', '')

            return {
                'success': True,
                'response': text,
                'model': model.model_id,
                'provider': 'anthropic',
                'usage': data.get('usage', {}),
            }
        except requests.exceptions.ConnectionError:
            return {'error': 'İnternet bağlantısı yoxdur'}
        except requests.exceptions.Timeout:
            return {'error': 'Anthropic cavab vaxtı bitdi'}
        except Exception as e:
            return {'error': str(e)}

    # ============================================
    # DEFAULT HELPERS
    # ============================================

    @staticmethod
    def _get_default_endpoint(provider):
        """Provider üçün defolt API endpoint"""
        endpoints = {
            'ollama': 'http://localhost:11434',
            'openai': 'https://api.openai.com/v1/chat/completions',
            'anthropic': 'https://api.anthropic.com/v1/messages',
        }
        return endpoints.get(provider, '')

    # ============================================
    # STATİSTİKA
    # ============================================

    def get_stats(self):
        """Model idarəetmə statistikasını qaytarır"""
        db = Session()
        try:
            total = db.query(AIModel).count()
            active = db.query(AIModel).filter_by(is_active=True).first()

            provider_counts = {}
            models = db.query(AIModel).all()
            for m in models:
                provider_counts[m.provider] = provider_counts.get(m.provider, 0) + 1

            # Ollama status
            ollama_status = self.get_ollama_models()

            return {
                'total_models': total,
                'active_model': {
                    'name': active.name,
                    'model_id': active.model_id,
                    'provider': active.provider,
                } if active else None,
                'provider_distribution': provider_counts,
                'ollama_available': ollama_status.get('available', False),
                'ollama_model_count': ollama_status.get('count', 0),
            }
        finally:
            db.close()

    # ============================================
    # İLKLƏŞDİRMƏ - DEFOLT MODELLƏR
    # ============================================

    def ensure_default_models(self):
        """Defolt modelləri yaratır (əgər yoxdursa)"""
        db = Session()
        try:
            existing_count = db.query(AIModel).count()
            if existing_count > 0:
                return {'message': f'{existing_count} model artıq mövcuddur', 'created': 0}

            now = datetime.now().isoformat()
            defaults = [
                {
                    'name': 'Qwen3 8B',
                    'model_id': 'qwen3:8b',
                    'provider': 'ollama',
                    'description': 'Qwen3 8B - Əsas model, sürətli və balanslı',
                    'is_active': True,
                    'max_tokens': 4096,
                    'temperature': 0.7,
                },
                {
                    'name': 'Qwen3 14B',
                    'model_id': 'qwen3:14b',
                    'provider': 'ollama',
                    'description': 'Qwen3 14B - Daha güclü, daha dəqiq cavablar',
                    'is_active': False,
                    'max_tokens': 4096,
                    'temperature': 0.7,
                },
                {
                    'name': 'Qwen3 32B',
                    'model_id': 'qwen3:32b',
                    'provider': 'ollama',
                    'description': 'Qwen3 32B - Ən güclü Qwen3 variantı',
                    'is_active': False,
                    'max_tokens': 4096,
                    'temperature': 0.7,
                },
                {
                    'name': 'DeepSeek R1 8B',
                    'model_id': 'deepseek-r1:8b',
                    'provider': 'ollama',
                    'description': 'DeepSeek R1 8B - Məntiq və riyaziyyat üçün',
                    'is_active': False,
                    'max_tokens': 4096,
                    'temperature': 0.7,
                },
                {
                    'name': 'Llama 3.1 8B',
                    'model_id': 'llama3.1:8b',
                    'provider': 'ollama',
                    'description': 'Llama 3.1 8B - Meta-nın açıq modeli',
                    'is_active': False,
                    'max_tokens': 4096,
                    'temperature': 0.7,
                },
                {
                    'name': 'GPT-4o',
                    'model_id': 'gpt-4o',
                    'provider': 'openai',
                    'description': 'OpenAI GPT-4o - Ən güclü kommersiya modeli',
                    'is_active': False,
                    'max_tokens': 4096,
                    'temperature': 0.7,
                },
                {
                    'name': 'GPT-4o Mini',
                    'model_id': 'gpt-4o-mini',
                    'provider': 'openai',
                    'description': 'OpenAI GPT-4o Mini - Sürətli və ucuz',
                    'is_active': False,
                    'max_tokens': 4096,
                    'temperature': 0.7,
                },
                {
                    'name': 'Claude 3.5 Sonnet',
                    'model_id': 'claude-3-5-sonnet-20241022',
                    'provider': 'anthropic',
                    'description': 'Anthropic Claude 3.5 Sonnet - Kod və analiz üçün',
                    'is_active': False,
                    'max_tokens': 4096,
                    'temperature': 0.7,
                },
            ]

            created = 0
            for d in defaults:
                model = AIModel(
                    id=generate_id(),
                    name=d['name'],
                    model_id=d['model_id'],
                    provider=d['provider'],
                    is_active=d['is_active'],
                    description=d['description'],
                    max_tokens=d['max_tokens'],
                    temperature=d['temperature'],
                    api_endpoint=self._get_default_endpoint(d['provider']),
                    api_key=None,
                    created_at=now,
                    updated_at=now,
                )
                db.add(model)
                created += 1

            db.commit()

            return {
                'success': True,
                'created': created,
                'message': f'{created} defolt model yaradıldı',
            }
        except Exception as e:
            db.rollback()
            return {'error': str(e)}
        finally:
            db.close()