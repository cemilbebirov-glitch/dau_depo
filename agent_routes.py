"""
DAU Dashboard - Agent Sistemi API Routes
"""

from flask import Blueprint, request, jsonify
from modules.agent_system import AgentSystem

agent_bp = Blueprint('agent', __name__, url_prefix='/api/agent')
agent = AgentSystem()


@agent_bp.route('/send', methods=['POST'])
def send_message():
    """Agentə mesaj göndərir"""
    data = request.get_json()

    if not data:
        return jsonify({'error': 'Məlumat göndərilməyib'}), 400

    user_id = data.get('user_id', 'default_user')
    message = data.get('message', '')
    agent_type = data.get('agent_type', 'dau_core')
    conversation_id = data.get('conversation_id')

    if not message:
        return jsonify({'error': 'message tələb olunur'}), 400

    result = agent.send_message(
        user_id=user_id,
        message=message,
        agent_type=agent_type,
        conversation_id=conversation_id,
    )

    if 'error' in result:
        return jsonify(result), 400

    return jsonify(result), 200


@agent_bp.route('/delegate', methods=['POST'])
def delegate_task():
    """Avtomatik olaraq uyğun agentə yönləndirir"""
    data = request.get_json()

    if not data:
        return jsonify({'error': 'Məlumat göndərilməyib'}), 400

    user_id = data.get('user_id', 'default_user')
    message = data.get('message', '')
    conversation_id = data.get('conversation_id')

    if not message:
        return jsonify({'error': 'message tələb olunur'}), 400

    result = agent.delegate_task(
        user_id=user_id,
        message=message,
        conversation_id=conversation_id,
    )

    if 'error' in result:
        return jsonify(result), 400

    return jsonify(result), 200


@agent_bp.route('/list', methods=['GET'])
def list_agents():
    """Mövcud agentlərin siyahısı"""
    agents = []

    for agent_type, config in agent.agents.items():
        agents.append({
            'type': agent_type,
            'name': config['name'],
            'description': config['description'],
        })

    return jsonify({'agents': agents, 'count': len(agents)}), 200


@agent_bp.route('/conversations', methods=['GET'])
def get_conversations():
    """Söhbət siyahısı"""
    user_id = request.args.get('user_id', 'default_user')
    limit = request.args.get('limit', 20, type=int)

    result = agent.get_conversations(user_id=user_id, limit=limit)

    return jsonify(result), 200


@agent_bp.route('/conversation/<conversation_id>', methods=['GET'])
def get_conversation(conversation_id):
    """Bir söhbətin mesajları"""
    user_id = request.args.get('user_id', 'default_user')
    result = agent.get_conversation_messages(
        conversation_id=conversation_id,
        user_id=user_id,
    )

    if result is None:
        return jsonify({'error': 'Söhbət tapılmadı'}), 404

    return jsonify(result), 200


@agent_bp.route('/conversation/<conversation_id>', methods=['DELETE'])
def delete_conversation(conversation_id):
    """Söhbəti silir"""
    user_id = request.args.get('user_id', 'default_user')
    result = agent.delete_conversation(
        conversation_id=conversation_id,
        user_id=user_id,
    )

    if 'error' in result:
        return jsonify(result), 400

    return jsonify(result), 200


@agent_bp.route('/active-model', methods=['GET'])
def get_active_model():
    """Aktiv AI modeli haqqında məlumat"""
    result = agent.get_active_model_info()
    return jsonify(result), 200