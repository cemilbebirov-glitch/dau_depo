"""
Agent System Module - AI Agent & Conversation Management
Raw SQLite pattern: import database as db
"""

import database as db
import json
from datetime import datetime


class AgentSystem:
    """AI Agent System - Conversations, Messages, Model Management"""

    def __init__(self, socketio=None):
        self.socketio = socketio
        self.active_conversations = {}
        self._default_models_initialized = False
        self._current_model = None

    # ============================
    # CONVERSATION MANAGEMENT
    # ============================

    def create_conversation(self, title="Yeni Sohbet", metadata=None):
        try:
            conv = db.conversation_create(title=title, metadata=metadata)
            if conv and self.socketio:
                self.socketio.emit('agent_conversation_created', conv)
            return conv
        except Exception as e:
            print(f"create_conversation xətası: {e}")
            return None

    def get_conversation(self, conv_id):
        try:
            return db.conversation_get(conv_id)
        except Exception as e:
            print(f"get_conversation xətası: {e}")
            return None

    def list_conversations(self, active_only=True):
        try:
            return db.conversation_list(active_only=active_only)
        except Exception as e:
            print(f"list_conversations xətası: {e}")
            return []

    def update_conversation(self, conv_id, **kwargs):
        try:
            conv = db.conversation_update(conv_id, **kwargs)
            if conv and self.socketio:
                self.socketio.emit('agent_conversation_updated', conv)
            return conv
        except Exception as e:
            print(f"update_conversation xətası: {e}")
            return None

    def delete_conversation(self, conv_id):
        try:
            result = db.conversation_delete(conv_id)
            if result and self.socketio:
                self.socketio.emit('agent_conversation_deleted', {'id': conv_id})
            return result
        except Exception as e:
            print(f"delete_conversation xətası: {e}")
            return False

    # ============================
    # MESSAGE MANAGEMENT
    # ============================

    def add_message(self, conversation_id, role, content, metadata=None):
        try:
            msg = db.conversation_message_add(
                conversation_id=conversation_id,
                role=role,
                content=content,
                metadata=metadata
            )
            if msg and self.socketio:
                self.socketio.emit('agent_message_added', msg)
            return msg
        except Exception as e:
            print(f"add_message xətası: {e}")
            return None

    def get_messages(self, conversation_id, limit=50):
        try:
            return db.conversation_messages_get(conversation_id, limit=limit)
        except Exception as e:
            print(f"get_messages xətası: {e}")
            return []

    def clear_messages(self, conversation_id):
        try:
            return db.conversation_messages_delete(conversation_id)
        except Exception as e:
            print(f"clear_messages xətası: {e}")
            return False

    # ============================
    # AI MODEL MANAGEMENT
    # ============================

    def add_model(self, name, provider, model_id, config=None):
        try:
            model = db.ai_model_add(name=name, provider=provider, model_id=model_id, config=config)
            if model and self.socketio:
                self.socketio.emit('agent_model_added', model)
            return model
        except Exception as e:
            print(f"add_model xətası: {e}")
            return None

    def get_model(self, model_id):
        try:
            return db.ai_model_get(model_id)
        except Exception as e:
            print(f"get_model xətası: {e}")
            return None

    def list_models(self, active_only=True):
        try:
            return db.ai_model_list(active_only=active_only)
        except Exception as e:
            print(f"list_models xətası: {e}")
            return []

    def update_model(self, model_id, **kwargs):
        try:
            model = db.ai_model_update(model_id, **kwargs)
            if model and self.socketio:
                self.socketio.emit('agent_model_updated', model)
            return model
        except Exception as e:
            print(f"update_model xətası: {e}")
            return None

    def delete_model(self, model_id):
        try:
            result = db.ai_model_delete(model_id)
            if result and self.socketio:
                self.socketio.emit('agent_model_deleted', {'id': model_id})
            return result
        except Exception as e:
            print(f"delete_model xətası: {e}")
            return False

    def init_default_models(self):
        if self._default_models_initialized:
            return
        try:
            existing = db.ai_model_list()
            if not existing:
                defaults = [
                    {"name": "GPT-4", "provider": "openai", "model_id": "gpt-4", "config": {"temperature": 0.7, "max_tokens": 4096}},
                    {"name": "GPT-3.5 Turbo", "provider": "openai", "model_id": "gpt-3.5-turbo", "config": {"temperature": 0.7, "max_tokens": 4096}},
                    {"name": "Claude 3", "provider": "anthropic", "model_id": "claude-3-opus", "config": {"temperature": 0.7, "max_tokens": 4096}},
                    {"name": "Local LLM", "provider": "local", "model_id": "local-llm", "config": {"temperature": 0.7, "max_tokens": 2048}},
                ]
                for m in defaults:
                    db.ai_model_add(name=m["name"], provider=m["provider"], model_id=m["model_id"], config=m["config"])
            self._default_models_initialized = True
        except Exception as e:
            print(f"init_default_models xətası: {e}")

    # ============================
    # CHAT / AI INTERACTION
    # ============================

    def send_chat(self, conversation_id, user_message, model_id=None):
        try:
            self.add_message(conversation_id=conversation_id, role="user", content=user_message)
            messages = self.get_messages(conversation_id, limit=20)
            ai_response = self._generate_response(messages, model_id)
            if ai_response:
                self.add_message(
                    conversation_id=conversation_id,
                    role="assistant",
                    content=ai_response,
                    metadata={"model_id": model_id}
                )
            conv = db.conversation_get(conversation_id)
            if conv and conv.get('title') == 'Yeni Sohbet':
                title = user_message[:50] + ('...' if len(user_message) > 50 else '')
                db.conversation_update(conversation_id, title=title)
            return ai_response
        except Exception as e:
            print(f"send_chat xətası: {e}")
            return f"Xəta baş verdi: {str(e)}"

    def _generate_response(self, messages, model_id=None):
        last_user_msg = ""
        for msg in reversed(messages):
            if msg.get('role') == 'user':
                last_user_msg = msg.get('content', '')
                break

        # Ollama ilə əlaqə yoxla
        try:
            import requests
            active_model = db.model_get_active()
            if active_model:
                model_name = active_model.get('name', 'llama3.1:8b')
                resp = requests.post('http://localhost:11434/api/generate', json={
                    'model': model_name,
                    'prompt': last_user_msg,
                    'stream': False
                }, timeout=30)
                if resp.status_code == 200:
                    data = resp.json()
                    return data.get('response', 'Cavab alına bilmədi')
        except:
            pass

        return f"JARVIS: '{last_user_msg[:30]}...' mesajınız alındı. Ollama server-i işləmir və ya model seçilməyib."

    # ============================
    # COMPATIBILITY METHODS (app.py üçün)
    # ============================

    def chat(self, message):
        try:
            convs = db.conversation_list(active_only=True)
            if convs:
                conv_id = convs[0]['id']
            else:
                conv = db.conversation_create(title="JARVIS Chat")
                conv_id = conv['id'] if conv else None

            if not conv_id:
                return {'response': 'Söhbət yaradıla bilmədi', 'error': True}

            response = self.send_chat(conv_id, message)
            return {'response': response, 'error': False}
        except Exception as e:
            print(f"chat xətası: {e}")
            return {'response': f'Xəta: {str(e)}', 'error': True}

    def delegate(self, task, agent_name=None):
        try:
            convs = db.conversation_list(active_only=True)
            if convs:
                conv_id = convs[0]['id']
            else:
                conv = db.conversation_create(title="Agent Task")
                conv_id = conv['id'] if conv else None

            if not conv_id:
                return {'response': 'Söhbət yaradıla bilmədi', 'error': True}

            full_task = f"[{agent_name}] {task}" if agent_name else task
            response = self.send_chat(conv_id, full_task)
            return {'response': response, 'agent_name': agent_name, 'error': False}
        except Exception as e:
            print(f"delegate xətası: {e}")
            return {'response': f'Xəta: {str(e)}', 'error': True}

    def set_model(self, model):
        try:
            self._current_model = model
            print(f"[Agent] Model təyin edildi: {model.get('name', 'unknown')}")
            return True
        except Exception as e:
            print(f"set_model xətası: {e}")
            return False

    def generate_code(self, prompt):
        try:
            return {
                'code': f"# Generasiya edilmiş kod\n# Prompt: {prompt}\n\nprint('Kod generasiyası hələ aktiv deyil')\n",
                'language': 'python',
                'prompt': prompt,
                'message': 'Kod generasiyası LLM inteqrasiyasından sonra aktivləşəcək'
            }
        except Exception as e:
            print(f"generate_code xətası: {e}")
            return {'error': str(e)}

    # ============================
    # STATISTICS & INFO
    # ============================

    def get_stats(self):
        try:
            conversations = db.conversation_list(active_only=False)
            active_convs = [c for c in conversations if c.get('is_active')]
            models = db.ai_model_list(active_only=False)
            active_models = [m for m in models if m.get('is_active')]

            total_messages = 0
            for conv in active_convs:
                msgs = db.conversation_messages_get(conv['id'], limit=1000)
                total_messages += len(msgs)

            return {
                "total_conversations": len(conversations),
                "active_conversations": len(active_convs),
                "total_models": len(models),
                "active_models": len(active_models),
                "total_messages": total_messages,
                "status": "active"
            }
        except Exception as e:
            print(f"get_stats xətası: {e}")
            return {"total_conversations": 0, "active_conversations": 0, "total_models": 0, "active_models": 0, "total_messages": 0, "status": "error"}

    def search_conversations(self, query):
        try:
            conn = db.get_connection()
            try:
                rows = conn.execute(
                    "SELECT * FROM conversations WHERE title LIKE ? AND is_active = 1 ORDER BY updated_at DESC",
                    (f"%{query}%",)
                ).fetchall()
                result = []
                for row in rows:
                    d = dict(row)
                    if d.get('metadata'):
                        try:
                            d['metadata'] = json.loads(d['metadata'])
                        except:
                            pass
                    result.append(d)
                return result
            finally:
                conn.close()
        except Exception as e:
            print(f"search_conversations xətası: {e}")
            return []