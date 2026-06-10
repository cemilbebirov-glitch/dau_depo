"""
DAU Dashboard - Ticarət Jurnalı API Routes
"""

from flask import Blueprint, request, jsonify
from modules.trading_journal import TradingJournal

trading_bp = Blueprint('trading', __name__, url_prefix='/api/trading')
journal = TradingJournal()


@trading_bp.route('/trades', methods=['GET'])
def get_trades():
    """Ticarət siyahısı"""
    user_id = request.args.get('user_id', 'default_user')
    status = request.args.get('status')
    symbol = request.args.get('symbol')
    strategy_id = request.args.get('strategy_id')
    limit = request.args.get('limit', 50, type=int)
    offset = request.args.get('offset', 0, type=int)

    result = journal.get_trades(
        user_id=user_id,
        status=status,
        symbol=symbol,
        strategy_id=strategy_id,
        limit=limit,
        offset=offset,
    )

    return jsonify(result), 200


@trading_bp.route('/trade', methods=['POST'])
def add_trade():
    """Yeni ticarət əlavə edir"""
    data = request.get_json()

    if not data:
        return jsonify({'error': 'Məlumat göndərilməyib'}), 400

    user_id = data.get('user_id', 'default_user')
    symbol = data.get('symbol', '')
    direction = data.get('direction', '')
    entry_price = data.get('entry_price')
    exit_price = data.get('exit_price')
    lot_size = data.get('lot_size')
    stop_loss = data.get('stop_loss')
    take_profit = data.get('take_profit')
    strategy_id = data.get('strategy_id')
    emotion_before = data.get('emotion_before')
    emotion_after = data.get('emotion_after')
    notes = data.get('notes', '')
    screenshots = data.get('screenshots')

    if not symbol or not direction:
        return jsonify({'error': 'symbol və direction tələb olunur'}), 400

    if entry_price is None:
        return jsonify({'error': 'entry_price tələb olunur'}), 400

    result = journal.add_trade(
        user_id=user_id,
        symbol=symbol,
        direction=direction,
        entry_price=entry_price,
        exit_price=exit_price,
        lot_size=lot_size,
        stop_loss=stop_loss,
        take_profit=take_profit,
        strategy_id=strategy_id,
        emotion_before=emotion_before,
        emotion_after=emotion_after,
        notes=notes,
        screenshots=screenshots,
    )

    if 'error' in result:
        return jsonify(result), 400

    return jsonify(result), 200


@trading_bp.route('/trade/<trade_id>/close', methods=['POST'])
def close_trade(trade_id):
    """Ticarəti bağlayır"""
    data = request.get_json() or {}

    exit_price = data.get('exit_price')
    emotion_after = data.get('emotion_after')
    notes = data.get('notes')

    if exit_price is None:
        return jsonify({'error': 'exit_price tələb olunur'}), 400

    result = journal.close_trade(
        trade_id=trade_id,
        exit_price=exit_price,
        emotion_after=emotion_after,
        notes=notes,
    )

    if 'error' in result:
        return jsonify(result), 400

    return jsonify(result), 200


@trading_bp.route('/trade/<trade_id>', methods=['PUT'])
def update_trade(trade_id):
    """Ticarəti yeniləyir"""
    data = request.get_json()

    if not data:
        return jsonify({'error': 'Məlumat göndərilməyib'}), 400

    result = journal.update_trade(trade_id=trade_id, **data)

    if 'error' in result:
        return jsonify(result), 400

    return jsonify(result), 200


@trading_bp.route('/trade/<trade_id>', methods=['DELETE'])
def delete_trade(trade_id):
    """Ticarəti silir"""
    result = journal.delete_trade(trade_id=trade_id)

    if 'error' in result:
        return jsonify(result), 400

    return jsonify(result), 200


@trading_bp.route('/stats', methods=['GET'])
def get_stats():
    """Ticarət statistikası"""
    user_id = request.args.get('user_id', 'default_user')
    days = request.args.get('days', 30, type=int)

    result = journal.get_stats(user_id=user_id, days=days)

    return jsonify(result), 200


@trading_bp.route('/symbol-stats', methods=['GET'])
def get_symbol_stats():
    """Simvol statistikası"""
    user_id = request.args.get('user_id', 'default_user')

    result = journal.get_symbol_stats(user_id=user_id)

    return jsonify(result), 200


# ============================================
# STRATEJİ ROUTE-LARI
# ============================================

@trading_bp.route('/strategies', methods=['GET'])
def get_strategies():
    """Strateji siyahısı"""
    user_id = request.args.get('user_id', 'default_user')

    result = journal.get_strategies(user_id=user_id)

    return jsonify({'strategies': result, 'count': len(result)}), 200


@trading_bp.route('/strategy', methods=['POST'])
def add_strategy():
    """Yeni strateji əlavə edir"""
    data = request.get_json()

    if not data:
        return jsonify({'error': 'Məlumat göndərilməyib'}), 400

    user_id = data.get('user_id', 'default_user')
    name = data.get('name', '')
    description = data.get('description', '')
    rules = data.get('rules', '')
    risk_reward_ratio = data.get('risk_reward_ratio')

    if not name:
        return jsonify({'error': 'name tələb olunur'}), 400

    result = journal.add_strategy(
        user_id=user_id,
        name=name,
        description=description,
        rules=rules,
        risk_reward_ratio=risk_reward_ratio,
    )

    if 'error' in result:
        return jsonify(result), 400

    return jsonify(result), 200


@trading_bp.route('/strategy/<strategy_id>', methods=['PUT'])
def update_strategy(strategy_id):
    """Stratejeni yeniləyir"""
    data = request.get_json()

    if not data:
        return jsonify({'error': 'Məlumat göndərilməyib'}), 400

    result = journal.update_strategy(strategy_id=strategy_id, **data)

    if 'error' in result:
        return jsonify(result), 400

    return jsonify(result), 200


@trading_bp.route('/strategy/<strategy_id>', methods=['DELETE'])
def delete_strategy(strategy_id):
    """Stratejeni silir"""
    result = journal.delete_strategy(strategy_id=strategy_id)

    if 'error' in result:
        return jsonify(result), 400

    return jsonify(result), 200