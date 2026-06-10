"""
DAU Dashboard - MT5 Modulu API Routes
"""

from flask import Blueprint, request, jsonify
from modules.mt5_module import MT5Module

mt5_bp = Blueprint('mt5', __name__, url_prefix='/api/mt5')
mt5 = MT5Module()


@mt5_bp.route('/status', methods=['GET'])
def get_status():
    """MT5 qoşulma statusu"""
    result = mt5.get_connection_status()
    return jsonify(result), 200


@mt5_bp.route('/connect', methods=['POST'])
def connect():
    """MT5-ə qoşulur"""
    data = request.get_json() or {}

    login = data.get('login')
    password = data.get('password')
    server = data.get('server')
    path = data.get('path')

    result = mt5.connect(
        login=login,
        password=password,
        server=server,
        path=path,
    )

    if 'error' in result:
        return jsonify(result), 400

    return jsonify(result), 200


@mt5_bp.route('/disconnect', methods=['POST'])
def disconnect():
    """MT5 bağlantısını kəsir"""
    result = mt5.disconnect()
    return jsonify(result), 200


@mt5_bp.route('/account', methods=['GET'])
def get_account_info():
    """Hesab məlumatları"""
    result = mt5.get_account_info()

    if 'error' in result:
        return jsonify(result), 400

    return jsonify(result), 200


@mt5_bp.route('/account/save', methods=['POST'])
def save_account_credentials():
    """Hesab məlumatlarını saxlayır"""
    data = request.get_json()

    if not data:
        return jsonify({'error': 'Məlumat göndərilməyib'}), 400

    login = data.get('login')
    password = data.get('password')
    server = data.get('server')
    path = data.get('path')

    if not login or not password or not server:
        return jsonify({'error': 'login, password və server tələb olunur'}), 400

    result = mt5.save_account_credentials(
        login=login,
        password=password,
        server=server,
        path=path,
    )

    if 'error' in result:
        return jsonify(result), 400

    return jsonify(result), 200


@mt5_bp.route('/positions', methods=['GET'])
def get_positions():
    """Açıq pozisiyalar"""
    result = mt5.get_positions()

    if 'error' in result:
        return jsonify(result), 400

    return jsonify(result), 200


@mt5_bp.route('/orders', methods=['GET'])
def get_orders():
    """Gözləyən əmrlər"""
    result = mt5.get_orders()

    if 'error' in result:
        return jsonify(result), 400

    return jsonify(result), 200


@mt5_bp.route('/market/<symbol>', methods=['GET'])
def get_market_data(symbol):
    """Bazar datası"""
    count = request.args.get('count', 100, type=int)

    result = mt5.get_market_data(symbol=symbol, count=count)

    if 'error' in result:
        return jsonify(result), 400

    return jsonify(result), 200


@mt5_bp.route('/symbols', methods=['GET'])
def get_symbols():
    """Mövcud simvollar"""
    group = request.args.get('group', '*')

    result = mt5.get_symbols(group=group)

    if 'error' in result:
        return jsonify(result), 400

    return jsonify(result), 200


@mt5_bp.route('/trade', methods=['POST'])
def execute_trade():
    """Ticarət əməliyyatı icra edir"""
    data = request.get_json()

    if not data:
        return jsonify({'error': 'Məlumat göndərilməyib'}), 400

    symbol = data.get('symbol', '')
    order_type = data.get('order_type', '')
    volume = data.get('volume')
    sl = data.get('sl', 0)
    tp = data.get('tp', 0)
    comment = data.get('comment', '')
    magic = data.get('magic', 0)

    if not symbol or not order_type or volume is None:
        return jsonify({'error': 'symbol, order_type və volume tələb olunur'}), 400

    result = mt5.execute_trade(
        symbol=symbol,
        order_type=order_type,
        volume=volume,
        sl=sl,
        tp=tp,
        comment=comment,
        magic=magic,
    )

    if 'error' in result:
        return jsonify(result), 400

    return jsonify(result), 200


@mt5_bp.route('/position/<int:ticket>/close', methods=['POST'])
def close_position(ticket):
    """Pozisiyanı bağlayır"""
    result = mt5.close_position(ticket=ticket)

    if 'error' in result:
        return jsonify(result), 400

    return jsonify(result), 200


@mt5_bp.route('/position/<int:ticket>/modify', methods=['POST'])
def modify_position(ticket):
    """Pozisiyanın SL/TP-ni dəyişdirir"""
    data = request.get_json() or {}

    sl = data.get('sl')
    tp = data.get('tp')

    if sl is None and tp is None:
        return jsonify({'error': 'sl və ya tp tələb olunur'}), 400

    result = mt5.modify_position(ticket=ticket, sl=sl, tp=tp)

    if 'error' in result:
        return jsonify(result), 400

    return jsonify(result), 200


@mt5_bp.route('/order/<int:ticket>/cancel', methods=['POST'])
def cancel_order(ticket):
    """Gözləyən əmri ləğv edir"""
    result = mt5.cancel_order(ticket=ticket)

    if 'error' in result:
        return jsonify(result), 400

    return jsonify(result), 200


@mt5_bp.route('/history/deals', methods=['GET'])
def get_history_deals():
    """Tarixi əməliyyatlar"""
    days = request.args.get('days', 30, type=int)

    result = mt5.get_history_deals(days=days)

    if 'error' in result:
        return jsonify(result), 400

    return jsonify(result), 200


@mt5_bp.route('/history/orders', methods=['GET'])
def get_history_orders():
    """Tarixi əmrlər"""
    days = request.args.get('days', 30, type=int)

    result = mt5.get_history_orders(days=days)

    if 'error' in result:
        return jsonify(result), 400

    return jsonify(result), 200


@mt5_bp.route('/stats', methods=['GET'])
def get_trading_stats():
    """Ticarət statistikası"""
    days = request.args.get('days', 30, type=int)

    result = mt5.get_trading_stats(days=days)

    if 'error' in result:
        return jsonify(result), 400

    return jsonify(result), 200


@mt5_bp.route('/terminal', methods=['GET'])
def get_terminal_info():
    """Terminal məlumatları"""
    result = mt5.get_terminal_info()

    if 'error' in result:
        return jsonify(result), 400

    return jsonify(result), 200