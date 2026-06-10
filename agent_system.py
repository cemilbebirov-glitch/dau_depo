"""
Agent System Module - AI Agent & Conversation Management
Raw SQLite pattern: import database as db

BU FAYL SADELESDIRILMIS VERSIYADIR - 
yalniz database.py-da movcud olan funksiyalari istifade edir:
  - db.chat_save(role, content, agent_name, conversation_id)
  - db.chat_list(conversation_id, limit)
  - db.model_get_active()
  - db.model_list()
  - db.model_switch()
"""

import database as db
import json
import re
import requests
from datetime import datetime


class AgentSystem:
    """AI Agent System - Chat & Model Management"""

    def __init__(self, socketio=None):
        self.socketio = socketio
        self._current_model = None

    # ============================
    # OLLAMA MODEL TAPMA
    # ============================

    def _get_ollama_model(self):
        """Ollama-da movcud modeli tap - DB-den ve ya birbasa Ollama-dan"""
        # 1. DB-den aktiv modeli yoxla
        try:
            active_model = db.model_get_active()
            if active_model:
                model_name = active_model.get('name', '')
                # Model adinin Ollama-da movcudlugunu yoxla
                try:
                    resp = requests.get('http://localhost:11434/api/tags', timeout=5)
                    if resp.status_code == 200:
                        ollama_models = [m.get('name', '') for m in resp.json().get('models', [])]
                        for om in ollama_models:
                            if om == model_name or om == model_name + ':latest':
                                print(f"[Ollama] DB model tapildi: {om}")
                                return om
                except:
                    pass
        except:
            pass

        # 2. Ollama-dan birbasa ilk movcud modeli gotur
        try:
            resp = requests.get('http://localhost:11434/api/tags', timeout=5)
            if resp.status_code == 200:
                models = resp.json().get('models', [])
                if models:
                    model_name = models[0].get('name', '')
                    print(f"[Ollama] Ollama-dan model tapildi: {model_name}")
                    return model_name
        except:
            pass

        # 3. Default olaraq qwen3:8b istifade et
        print("[Ollama] Default model istifade olunur: qwen3:8b")
        return 'qwen3:8b'

    def _clean_think_tags(self, text):
        """qwen3 modelinin <think>...</think> teglerini temizle"""
        text = re.sub(r'<think>.*?</think>', '', text, flags=re.DOTALL)
        text = re.sub(r'<think>.*', '', text, flags=re.DOTALL)
        text = text.strip()
        return text

    # ============================
    # CHAT - ESAS METOD
    # ============================

    def chat(self, message):
        """Chat mesaji gonder - birbasha Ollama-ya"""
        try:
            # Istifadeci mesajini DB-ya yaz
            try:
                db.chat_save(role='user', content=message)
            except:
                pass

            # Ollama-ya gonder
            response = self._simple_chat(message)

            # Cavabi DB-ya yaz
            if response:
                try:
                    db.chat_save(role='assistant', content=response)
                except:
                    pass

            return {'response': response, 'error': False}
        except Exception as e:
            print(f"chat xetasi: {e}")
            return {'response': f'Xeta: {str(e)}', 'error': True}

    def _simple_chat(self, message, agent_name=None):
        """Birbasha Ollama ile chat"""
        if not message:
            return "Mesaj bosdur."

        # Ollama modelini tap
        model_name = self._get_ollama_model()

        # Sohbet mesajlarini hazirla
        chat_messages = []

        # System prompt
        system_prompt = (
            "Sen DAU JARVIS adli AI assistentsen. Azerbaycan dilinde cavab ver. "
            "Sen bir ticaret ve analiz assistentsen. Istifadeciye komek et, suallara cavab ver. "
            "Qisa ve aydin cavablar ver. /no_think"
        )
        chat_messages.append({'role': 'system', 'content': system_prompt})

        # Sohbet tarixini DB-dan gotur
        try:
            history = db.chat_list(limit=10)
            for h in reversed(history):
                role = h.get('role', '')
                content = h.get('content', '')
                if role in ('user', 'assistant') and content:
                    chat_messages.append({'role': role, 'content': content})
        except:
            pass

        # Istifadeci mesajini elave et
        chat_messages.append({'role': 'user', 'content': message})

        # Ollama /api/chat endpoint-i ile gonder
        try:
            print(f"[Ollama] Model: {model_name} | Mesaj: {message[:50]}...")
            resp = requests.post('http://localhost:11434/api/chat', json={
                'model': model_name,
                'messages': chat_messages,
                'stream': False,
                'options': {
                    'temperature': 0.7,
                    'num_predict': 2048,
                }
            }, timeout=120)

            if resp.status_code == 200:
                data = resp.json()
                content = data.get('message', {}).get('content', '')
                if content:
                    content = self._clean_think_tags(content)
                    if content:
                        print(f"[Ollama] Cavab alindi: {content[:80]}...")
                        return content
                    else:
                        return "Cavab bos geldi. Zehmet olmasa yeniden yoxlayin."
                else:
                    return "Cavab alina bilmedi."
            else:
                print(f"[Ollama] HTTP xeta: {resp.status_code}")
                return f"Ollama xeta: HTTP {resp.status_code}"

        except requests.exceptions.ConnectionError:
            return "Ollama serveri qoshulmayib. Zehmet olmasa 'ollama serve' isletdirin."
        except requests.exceptions.Timeout:
            return "Cavab vaxti bitdi. Yeniden yoxlayin."
        except Exception as e:
            print(f"[Ollama] Xeta: {e}")
            return f"Ollama xetasi: {str(e)}"

    # ============================
    # DELEGATE - AGENT TAPSIRIQ
    # ============================

    def delegate(self, task, agent_name=None):
        """Agent-ye tapsiriq gonder"""
        try:
            full_task = f"[{agent_name}] {task}" if agent_name else task

            # Istifadeci mesajini DB-ya yaz
            try:
                db.chat_save(role='user', content=full_task, agent_name=agent_name)
            except:
                pass

            # Ollama-ya gonder
            response = self._simple_chat(full_task, agent_name=agent_name)

            # Cavabi DB-ya yaz
            if response:
                try:
                    db.chat_save(role='assistant', content=response, agent_name=agent_name)
                except:
                    pass

            return {'response': response, 'agent_name': agent_name, 'error': False}
        except Exception as e:
            print(f"delegate xetasi: {e}")
            return {'response': f'Xeta: {str(e)}', 'error': True}

    # ============================
    # SEND_CHAT - UYQUNLUQ METODU
    # ============================

    def send_chat(self, conversation_id, user_message, model_id=None):
        """Chat - birbasha Ollama-ya gonder (uyqunluq ucun)"""
        try:
            return self._simple_chat(user_message)
        except Exception as e:
            print(f"send_chat xetasi: {e}")
            return f"Xeta bas verdi: {str(e)}"

    # ============================
    # MODEL IDAREETME
    # ============================

    def set_model(self, model):
        """Aktiv modeli teyin et"""
        try:
            self._current_model = model
            print(f"[Agent] Model teyin edildi: {model.get('name', 'unknown')}")
            return True
        except Exception as e:
            print(f"set_model xetasi: {e}")
            return False

    def generate_code(self, prompt):
        """Kod generasiya et"""
        try:
            return {
                'code': f"# Generasiya edilmish kod\n# Prompt: {prompt}\n\nprint('Kod generasiyasi hele aktiv deyil')\n",
                'language': 'python',
                'prompt': prompt,
                'message': 'Kod generasiyasi LLM integrasiyasindan sonra aktivleshecek'
            }
        except Exception as e:
            print(f"generate_code xetasi: {e}")
            return {'error': str(e)}

    # ============================
    # STATISTIKA
    # ============================

    def get_stats(self):
        try:
            models = []
            try:
                models = db.model_list()
            except:
                pass
            active_models = [m for m in models if m.get('is_active')]

            total_messages = 0
            try:
                history = db.chat_list(limit=1000)
                total_messages = len(history)
            except:
                pass

            return {
                "total_conversations": 1,
                "active_conversations": 1,
                "total_models": len(models),
                "active_models": len(active_models),
                "total_messages": total_messages,
                "status": "active"
            }
        except Exception as e:
            print(f"get_stats xetasi: {e}")
            return {"total_conversations": 0, "active_conversations": 0, "total_models": 0, "active_models": 0, "total_messages": 0, "status": "error"}
