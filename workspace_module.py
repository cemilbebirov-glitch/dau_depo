"""
DAU Dashboard - Kod İş Sahəsi Modulu
Fayl meneceri, kod redaktoru, layihə idarəetməsi, terminal, kod generasiyası
SQLAlchemy ilə database əməliyyatları
Ollama AI ilə kod generasiyası
"""

import os
import json
import subprocess
import importlib
from datetime import datetime
from database import Session, generate_id, CodeFile, Project, AIModel


class WorkspaceModule:
    """Kod İş Sahəsi - Fayl və layihə idarəetməsi"""

    def __init__(self):
        self.base_dir = os.path.join(os.path.dirname(os.path.dirname(__file__)), 'workspace')
        os.makedirs(self.base_dir, exist_ok=True)

    # ============================================
    # FAYL ƏMƏLİYYATLARI
    # ============================================

    def list_directory(self, path=None):
        """
        Kataloqun məzmununu qaytarır
        path: iş sahəsinə nisbi yol (None = kök)
        """
        target_dir = self.base_dir
        if path:
            target_dir = os.path.join(self.base_dir, path)

        # Təhlükəsizlik: iş sahəsindən kənara çıxmağa icazə vermə
        target_dir = os.path.realpath(target_dir)
        if not target_dir.startswith(os.path.realpath(self.base_dir)):
            return {'error': 'İcazə verilməyən yol'}

        if not os.path.exists(target_dir):
            return {'error': f'Kataloq tapılmadı: {path}'}

        if not os.path.isdir(target_dir):
            return {'error': f'Bu kataloq deyil: {path}'}

        items = []
        try:
            for item in sorted(os.listdir(target_dir)):
                full_path = os.path.join(target_dir, item)
                rel_path = os.path.relpath(full_path, self.base_dir)

                try:
                    stat = os.stat(full_path)
                    is_dir = os.path.isdir(full_path)

                    items.append({
                        'name': item,
                        'path': rel_path.replace('\\', '/'),
                        'is_dir': is_dir,
                        'size': stat.st_size if not is_dir else 0,
                        'modified': datetime.fromtimestamp(stat.st_mtime).isoformat(),
                        'extension': os.path.splitext(item)[1] if not is_dir else None,
                    })
                except (PermissionError, OSError):
                    continue
        except PermissionError:
            return {'error': 'Kataloqa giriş icazəsi yoxdur'}

        return {
            'items': items,
            'current_path': path or '/',
            'count': len(items),
        }

    def read_file(self, path):
        """Faylın məzmununu oxuyur"""
        full_path = os.path.join(self.base_dir, path)
        full_path = os.path.realpath(full_path)

        if not full_path.startswith(os.path.realpath(self.base_dir)):
            return {'error': 'İcazə verilməyən yol'}

        if not os.path.exists(full_path):
            return {'error': f'Fayl tapılmadı: {path}'}

        if os.path.isdir(full_path):
            return {'error': f'Bu kataloqdur, fayl deyil: {path}'}

        # Fayl ölçüsünü yoxla (10MB-dan böyük faylları oxuma)
        file_size = os.path.getsize(full_path)
        if file_size > 10 * 1024 * 1024:
            return {'error': f'Fayl çox böyükdür ({file_size} bayt). Maksimum: 10MB'}

        # Fayl növünü müəyyən et
        extension = os.path.splitext(path)[1].lower()
        binary_extensions = {'.png', '.jpg', '.jpeg', '.gif', '.bmp', '.ico', '.zip', '.rar',
                           '.7z', '.exe', '.dll', '.so', '.pyc', '.pyd', '.pdf', '.docx',
                           '.xlsx', '.pptx', '.mp3', '.mp4', '.avi', '.mov', '.wav'}

        if extension in binary_extensions:
            return {
                'content': None,
                'is_binary': True,
                'size': file_size,
                'extension': extension,
                'message': 'Bu ikili fayldır, mətn kimi oxuna bilməz'
            }

        # Mətn faylını oxu
        encodings = ['utf-8', 'utf-8-sig', 'latin-1', 'cp1252']
        for encoding in encodings:
            try:
                with open(full_path, 'r', encoding=encoding) as f:
                    content = f.read()
                return {
                    'content': content,
                    'is_binary': False,
                    'size': file_size,
                    'extension': extension,
                    'line_count': content.count('\n') + 1,
                }
            except (UnicodeDecodeError, UnicodeError):
                continue

        return {'error': 'Faylın kodlaşdırması müəyyən edilə bilmədi'}

    def write_file(self, path, content):
        """Faylın məzmununu yazır (yeni və ya mövcud)"""
        full_path = os.path.join(self.base_dir, path)
        full_path = os.path.realpath(full_path)

        if not full_path.startswith(os.path.realpath(self.base_dir)):
            return {'error': 'İcazə verilməyən yol'}

        # Kataloqu yarat
        dir_path = os.path.dirname(full_path)
        os.makedirs(dir_path, exist_ok=True)

        try:
            with open(full_path, 'w', encoding='utf-8') as f:
                f.write(content)

            file_size = os.path.getsize(full_path)

            # Database-ə saxla
            self._save_file_record(path, content, file_size)

            return {
                'success': True,
                'path': path,
                'size': file_size,
                'message': f'Fayl saxlanıldı: {path}',
            }
        except Exception as e:
            return {'error': f'Fayl yazma xətası: {str(e)}'}

    def create_directory(self, path):
        """Yeni kataloq yaradır"""
        full_path = os.path.join(self.base_dir, path)
        full_path = os.path.realpath(full_path)

        if not full_path.startswith(os.path.realpath(self.base_dir)):
            return {'error': 'İcazə verilməyən yol'}

        if os.path.exists(full_path):
            return {'error': f'Bu yol artıq mövcuddur: {path}'}

        try:
            os.makedirs(full_path, exist_ok=True)
            return {'success': True, 'path': path, 'message': f'Kataloq yaradıldı: {path}'}
        except Exception as e:
            return {'error': f'Kataloq yaratma xətası: {str(e)}'}

    def delete_item(self, path):
        """Fayl və ya kataloqu silir"""
        full_path = os.path.join(self.base_dir, path)
        full_path = os.path.realpath(full_path)

        if not full_path.startswith(os.path.realpath(self.base_dir)):
            return {'error': 'İcazə verilməyən yol'}

        if not os.path.exists(full_path):
            return {'error': f'Tapılmadı: {path}'}

        # Kök kataloqu silməyə icazə vermə
        if full_path == os.path.realpath(self.base_dir):
            return {'error': 'İş sahəsinin kök kataloqu silinə bilməz'}

        try:
            import shutil
            if os.path.isdir(full_path):
                shutil.rmtree(full_path)
            else:
                os.remove(full_path)

            # Database-dən də sil
            self._delete_file_record(path)

            return {'success': True, 'message': f'Silindi: {path}'}
        except Exception as e:
            return {'error': f'Silmə xətası: {str(e)}'}

    def rename_item(self, old_path, new_name):
        """Fayl və ya kataloqun adını dəyişir"""
        full_old = os.path.join(self.base_dir, old_path)
        full_old = os.path.realpath(full_old)

        if not full_old.startswith(os.path.realpath(self.base_dir)):
            return {'error': 'İcazə verilməyən yol'}

        if not os.path.exists(full_old):
            return {'error': f'Tapılmadı: {old_path}'}

        parent_dir = os.path.dirname(full_old)
        full_new = os.path.join(parent_dir, new_name)

        if os.path.exists(full_new):
            return {'error': f'Bu ad artıq mövcuddur: {new_name}'}

        try:
            os.rename(full_old, full_new)
            new_path = os.path.relpath(full_new, self.base_dir).replace('\\', '/')
            return {'success': True, 'old_path': old_path, 'new_path': new_path, 'message': f'Yenidən adlandırıldı: {new_name}'}
        except Exception as e:
            return {'error': f'Yenidən adlandırma xətası: {str(e)}'}

    # ============================================
    # LAYİHƏ İDARƏETMƏSİ
    # ============================================

    def create_project(self, user_id, name, description='', project_type='general'):
        """Yeni layihə yaradır"""
        db = Session()
        try:
            project_id = generate_id()
            now = datetime.now().isoformat()

            # Layihə kataloqunu yarat
            safe_name = ''.join(c if c.isalnum() or c in '-_' else '_' for c in name)
            project_path = os.path.join(self.base_dir, safe_name)
            os.makedirs(project_path, exist_ok=True)

            # Əsas strukturu yarat
            subdirs = {
                'general': ['src', 'docs'],
                'python': ['src', 'tests', 'docs'],
                'web': ['src', 'static', 'templates', 'docs'],
                'data': ['data', 'scripts', 'docs'],
            }

            for subdir in subdirs.get(project_type, ['src', 'docs']):
                os.makedirs(os.path.join(project_path, subdir), exist_ok=True)

            project = Project(
                id=project_id,
                user_id=user_id,
                name=name,
                description=description,
                path=safe_name,
                settings=json.dumps({
                    'type': project_type,
                    'created_with': 'dau_dashboard',
                }),
                created_at=now,
                updated_at=now,
            )
            db.add(project)
            db.commit()

            return {
                'success': True,
                'project_id': project_id,
                'name': name,
                'path': safe_name,
                'message': f'Layihə yaradıldı: {name}',
            }
        except Exception as e:
            db.rollback()
            return {'error': f'Layihə yaratma xətası: {str(e)}'}
        finally:
            db.close()

    def get_projects(self, user_id):
        """İstifadəçinin layihələrini qaytarır"""
        db = Session()
        try:
            projects = db.query(Project).filter_by(user_id=user_id).order_by(Project.updated_at.desc()).all()

            result = []
            for p in projects:
                project_path = os.path.join(self.base_dir, p.path) if p.path else None
                file_count = 0

                if project_path and os.path.exists(project_path):
                    for root, dirs, files in os.walk(project_path):
                        file_count += len(files)

                result.append({
                    'id': p.id,
                    'name': p.name,
                    'description': p.description,
                    'path': p.path,
                    'settings': json.loads(p.settings) if p.settings else {},
                    'file_count': file_count,
                    'created_at': p.created_at,
                    'updated_at': p.updated_at,
                })

            return result
        finally:
            db.close()

    def get_project(self, project_id, user_id):
        """Bir layihənin məlumatlarını qaytarır"""
        db = Session()
        try:
            project = db.query(Project).filter_by(id=project_id, user_id=user_id).first()
            if not project:
                return None

            project_path = os.path.join(self.base_dir, project.path) if project.path else None
            files = []

            if project_path and os.path.exists(project_path):
                for root, dirs, filenames in os.walk(project_path):
                    for filename in filenames:
                        full = os.path.join(root, filename)
                        rel = os.path.relpath(full, project_path).replace('\\', '/')
                        try:
                            stat = os.stat(full)
                            files.append({
                                'name': filename,
                                'path': rel,
                                'size': stat.st_size,
                                'modified': datetime.fromtimestamp(stat.st_mtime).isoformat(),
                                'extension': os.path.splitext(filename)[1],
                            })
                        except (PermissionError, OSError):
                            continue

            return {
                'id': project.id,
                'name': project.name,
                'description': project.description,
                'path': project.path,
                'settings': json.loads(project.settings) if project.settings else {},
                'files': files,
                'file_count': len(files),
                'created_at': project.created_at,
                'updated_at': project.updated_at,
            }
        finally:
            db.close()

    def delete_project(self, project_id, user_id):
        """Layihəni və fayllarını silir"""
        db = Session()
        try:
            project = db.query(Project).filter_by(id=project_id, user_id=user_id).first()
            if not project:
                return {'error': 'Layihə tapılmadı'}

            # Faylları diskdən sil
            if project.path:
                project_path = os.path.join(self.base_dir, project.path)
                if os.path.exists(project_path):
                    import shutil
                    shutil.rmtree(project_path)

            db.delete(project)
            db.commit()

            return {'success': True, 'message': f'Layihə silindi: {project.name}'}
        except Exception as e:
            db.rollback()
            return {'error': str(e)}
        finally:
            db.close()

    # ============================================
    # KOD GENERASİYASI (AI)
    # ============================================

    def generate_code(self, user_id, prompt, language='python', context=None):
        """
        Ollama AI ilə kod generasiya edir
        Database-dəki aktiv modeldən istifadə edir
        """
        db = Session()
        try:
            active_model = db.query(AIModel).filter_by(is_active=True).first()
            model_name = active_model.model_id if active_model else 'qwen3:8b'
        finally:
            db.close()

        system_prompt = f"""Sən peşəkar bir proqramçı və kod assistentisən.
Görev: İstifadəçinin tələbinə uyğun {language} kodu yaz.

Qaydalar:
1. Yalnız kod yaz, izahat minimum olsun
2. Kod tam və işlək olmalıdır
3. Təmiz və oxunaqlı kod stilində yaz
4. Lazım olan import-ları daxil et
5. Əgər kontekst verilibsə, ona uyğun yaz

Cavab formatı:
```{language}
// kod burada
```"""

        user_message = prompt
        if context:
            user_message = f"Kontekst:\n{context}\n\nTələb: {prompt}"

        try:
            import requests
            response = requests.post(
                'http://localhost:11434/api/generate',
                json={
                    'model': model_name,
                    'prompt': f"{system_prompt}\n\nİstifadəçi: {user_message}\n\nKod:",
                    'stream': False,
                    'options': {
                        'temperature': 0.3,
                        'top_p': 0.9,
                    }
                },
                timeout=120,
            )

            if response.status_code != 200:
                return {'error': f'Ollama xətası: {response.status_code}'}

            data = response.json()
            generated_text = data.get('response', '')

            # Think tag-ləri təmizlə
            generated_text = self._clean_think_tags(generated_text)

            # Kodu çıxar
            code = self._extract_code(generated_text)

            return {
                'success': True,
                'code': code,
                'raw_response': generated_text,
                'model': model_name,
                'language': language,
            }

        except requests.exceptions.ConnectionError:
            return {'error': 'Ollama qoşulu deyil. Əvvəlcə Ollama-nı başladın.'}
        except requests.exceptions.Timeout:
            return {'error': 'Ollama cavab vaxtı bitdi (120 saniyə)'}
        except Exception as e:
            return {'error': f'Kod generasiya xətası: {str(e)}'}

    def _clean_think_tags(self, text):
        """Qwen3 think tag-lərini təmizləyir"""
        import re
        text = re.sub(r'<think[^>]*>.*?</think\s*>', '', text, flags=re.DOTALL)
        text = re.sub(r'</?think[^>]*>', '', text)
        return text.strip()

    def _extract_code(self, text):
        """Mətn içindən kod blokunu çıxarır"""
        import re

        # ```language ... ``` formatında kod axtar
        pattern = r'```(?:\w+)?\s*\n(.*?)```'
        matches = re.findall(pattern, text, re.DOTALL)

        if matches:
            return matches[0].strip()

        # Kod bloku tapılmasa, bütün mətni qaytar
        return text.strip()

    # ============================================
    # TERMİNAL ƏMƏLİYYATLARI
    # ============================================

    def execute_command(self, command, working_dir=None, timeout=30):
        """
        Terminal əmrini icra edir
        Əmrlər yalnız iş sahəsi daxilində işləyir
        """
        # Təhlükəli əmrləri blokla
        dangerous_commands = ['rm -rf /', 'format', 'del /f /s /q C:', 'shutdown', 'rmdir /s /q']
        command_lower = command.lower().strip()
        for dangerous in dangerous_commands:
            if dangerous in command_lower:
                return {'error': f'Təhlükəli əmr bloklandı: {command}'}

        # İş kataloqu
        cwd = self.base_dir
        if working_dir:
            cwd = os.path.join(self.base_dir, working_dir)
            cwd = os.path.realpath(cwd)
            if not cwd.startswith(os.path.realpath(self.base_dir)):
                return {'error': 'İcazə verilməyən iş kataloqu'}

        if not os.path.exists(cwd):
            return {'error': f'İş kataloqu tapılmadı: {working_dir}'}

        try:
            result = subprocess.run(
                command,
                shell=True,
                capture_output=True,
                text=True,
                cwd=cwd,
                timeout=timeout,
            )

            return {
                'success': result.returncode == 0,
                'stdout': result.stdout[-5000:] if result.stdout else '',
                'stderr': result.stderr[-5000:] if result.stderr else '',
                'return_code': result.returncode,
                'command': command,
                'working_dir': working_dir or '/',
            }
        except subprocess.TimeoutExpired:
            return {'error': f'Əmr vaxtı bitdi ({timeout} saniyə)'}
        except Exception as e:
            return {'error': f'Əmr icra xətası: {str(e)}'}

    # ============================================
    # FAYL AXTARIŞI
    # ============================================

    def search_files(self, query, path=None, search_content=False):
        """
        Fayl adı və ya məzmunu ilə axtarış edir
        """
        target_dir = self.base_dir
        if path:
            target_dir = os.path.join(self.base_dir, path)

        target_dir = os.path.realpath(target_dir)
        if not target_dir.startswith(os.path.realpath(self.base_dir)):
            return {'error': 'İcazə verilməyən yol'}

        if not os.path.exists(target_dir):
            return {'error': 'Kataloq tapılmadı'}

        results = []
        query_lower = query.lower()

        for root, dirs, files in os.walk(target_dir):
            # Gizli kataloqları atla
            dirs[:] = [d for d in dirs if not d.startswith('.')]

            for filename in files:
                full_path = os.path.join(root, filename)
                rel_path = os.path.relpath(full_path, self.base_dir).replace('\\', '/')

                # Fayl adı ilə axtarış
                if query_lower in filename.lower():
                    results.append({
                        'name': filename,
                        'path': rel_path,
                        'match_type': 'filename',
                    })
                    continue

                # Məzmun ilə axtarış
                if search_content:
                    extension = os.path.splitext(filename)[1].lower()
                    binary_extensions = {'.png', '.jpg', '.jpeg', '.gif', '.bmp', '.ico',
                                       '.zip', '.rar', '.exe', '.dll', '.pyc', '.pdf'}

                    if extension not in binary_extensions:
                        try:
                            with open(full_path, 'r', encoding='utf-8', errors='ignore') as f:
                                content = f.read()
                                if query_lower in content.lower():
                                    # Uyğun sətirləri tap
                                    matching_lines = []
                                    for i, line in enumerate(content.split('\n'), 1):
                                        if query_lower in line.lower():
                                            matching_lines.append({
                                                'line_number': i,
                                                'line': line.strip()[:200],
                                            })
                                            if len(matching_lines) >= 5:
                                                break

                                    results.append({
                                        'name': filename,
                                        'path': rel_path,
                                        'match_type': 'content',
                                        'matching_lines': matching_lines,
                                    })
                        except (PermissionError, OSError):
                            continue

        return {
            'results': results,
            'count': len(results),
            'query': query,
        }

    # ============================================
    # FAYL STATİSTİKASI
    # ============================================

    def get_stats(self, user_id=None):
        """İş sahəsi statistikasını qaytarır"""
        total_files = 0
        total_dirs = 0
        total_size = 0
        extensions = {}

        for root, dirs, files in os.walk(self.base_dir):
            dirs[:] = [d for d in dirs if not d.startswith('.')]
            total_dirs += len(dirs)

            for filename in files:
                full_path = os.path.join(root, filename)
                try:
                    stat = os.stat(full_path)
                    total_files += 1
                    total_size += stat.st_size

                    ext = os.path.splitext(filename)[1].lower()
                    if ext:
                        extensions[ext] = extensions.get(ext, 0) + 1
                except (PermissionError, OSError):
                    continue

        # Ən çox istifadə olunan uzantılar
        sorted_extensions = sorted(extensions.items(), key=lambda x: x[1], reverse=True)[:10]

        # Layihə sayı
        db = Session()
        try:
            project_count = db.query(Project).count() if user_id is None else db.query(Project).filter_by(user_id=user_id).count()
        finally:
            db.close()

        return {
            'total_files': total_files,
            'total_dirs': total_dirs,
            'total_size': total_size,
            'project_count': project_count,
            'extensions': [{'extension': ext, 'count': count} for ext, count in sorted_extensions],
            'base_dir': self.base_dir,
        }

    # ============================================
    # DATABASE KÖMƏKÇİLƏRİ
    # ============================================

    def _save_file_record(self, path, content, file_size):
        """Fayl məlumatlarını database-ə saxlayır"""
        db = Session()
        try:
            existing = db.query(CodeFile).filter_by(path=path).first()
            now = datetime.now().isoformat()

            if existing:
                existing.content = content
                existing.size = file_size
                existing.language = os.path.splitext(path)[1].lstrip('.')
                existing.updated_at = now
            else:
                code_file = CodeFile(
                    id=generate_id(),
                    path=path,
                    name=os.path.basename(path),
                    content=content,
                    language=os.path.splitext(path)[1].lstrip('.'),
                    size=file_size,
                    created_at=now,
                    updated_at=now,
                )
                db.add(code_file)

            db.commit()
        except Exception:
            db.rollback()
        finally:
            db.close()

    def _delete_file_record(self, path):
        """Fayl məlumatlarını database-dən silir"""
        db = Session()
        try:
            code_file = db.query(CodeFile).filter_by(path=path).first()
            if code_file:
                db.delete(code_file)
                db.commit()
        except Exception:
            db.rollback()
        finally:
            db.close()