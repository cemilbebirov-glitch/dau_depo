"""
DAU Trading Bot API Routes
Flask Blueprint - Bot nəzarəti, strategiyalar, siqnallar
"""

from flask import Blueprint, request, jsonify
import json

from modules.trading_bot import TradingBotEngine, MT5Integration, StrategyEngine
from database import Session, TradingBot, BotTrade, StrategyTemplate, LearningEntry, MarketAlert

bot_bp = Blueprint('bot', __name__, url_prefix='/api/bot')

# Singleton mühərrik
bot_engine = TradingBotEngine()
mt5 = bot_engine.mt5


# =========================
# BOT CRUD ƏMƏLİYYATLARI
# =========================

@bot_bp.route('/create', methods=['POST'])
def create_bot():
    """Yeni bot yaradır"""
    try:
        data = request.get_json()
        if not data:
            return jsonify({"success": False, "error": "Məlumat göndərilməyib"}), 400

        user_id = data.get("user_id", "default-user")
        result = bot_engine.create_bot(user_id, data)
        
        if result["success"]:
            return jsonify(result), 201
        else:
            return jsonify(result), 400
    except Exception as e:
        return jsonify({"success": False, "error": str(e)}), 500


@bot_bp.route('/update/<bot_id>', methods=['PUT'])
def update_bot(bot_id):
    """Bot parametrlərini yeniləyir"""
    try:
        data = request.get_json()
        if not data:
            return jsonify({"success": False, "error": "Məlumat göndərilməyib"}), 400

        result = bot_engine.update_bot(bot_id, data)
        
        if result["success"]:
            return jsonify(result), 200
        else:
            return jsonify(result), 400
    except Exception as e:
        return jsonify({"success": False, "error": str(e)}), 500


@bot_bp.route('/delete/<bot_id>', methods=['DELETE'])
def delete_bot(bot_id):
    """Botu silir"""
    try:
        result = bot_engine.delete_bot(bot_id)
        
        if result["success"]:
            return jsonify(result), 200
        else:
            return jsonify(result), 400
    except Exception as e:
        return jsonify({"success": False, "error": str(e)}), 500


@bot_bp.route('/list', methods=['GET'])
def list_bots():
    """Bütün botları siyahılayır"""
    try:
        user_id = request.args.get("user_id", "default-user")
        result = bot_engine.list_bots(user_id)
        return jsonify(result), 200
    except Exception as e:
        return jsonify({"success": False, "error": str(e)}), 500


@bot_bp.route('/status/<bot_id>', methods=['GET'])
def get_bot_status(bot_id):
    """Bot statusunu alır"""
    try:
        result = bot_engine.get_bot_status(bot_id)
        
        if result["success"]:
            return jsonify(result), 200
        else:
            return jsonify(result), 404
    except Exception as e:
        return jsonify({"success": False, "error": str(e)}), 500


# =========================
# BOT NƏZARƏT (START/STOP/PAUSE)
# =========================

@bot_bp.route('/start/<bot_id>', methods=['POST'])
def start_bot(bot_id):
    """Botu başladır"""
    try:
        result = bot_engine.start_bot(bot_id)
        
        if result["success"]:
            return jsonify(result), 200
        else:
            return jsonify(result), 400
    except Exception as e:
        return jsonify({"success": False, "error": str(e)}), 500


@bot_bp.route('/stop/<bot_id>', methods=['POST'])
def stop_bot(bot_id):
    """Botu dayandırır"""
    try:
        result = bot_engine.stop_bot(bot_id)
        
        if result["success"]:
            return jsonify(result), 200
        else:
            return jsonify(result), 400
    except Exception as e:
        return jsonify({"success": False, "error": str(e)}), 500


@bot_bp.route('/pause/<bot_id>', methods=['POST'])
def pause_bot(bot_id):
    """Botu müvəqqəti dayandırır"""
    try:
        result = bot_engine.pause_bot(bot_id)
        
        if result["success"]:
            return jsonify(result), 200
        else:
            return jsonify(result), 400
    except Exception as e:
        return jsonify({"success": False, "error": str(e)}), 500


@bot_bp.route('/resume/<bot_id>', methods=['POST'])
def resume_bot(bot_id):
    """Dayanmış botu davam etdirir"""
    try:
        result = bot_engine.resume_bot(bot_id)
        
        if result["success"]:
            return jsonify(result), 200
        else:
            return jsonify(result), 400
    except Exception as e:
        return jsonify({"success": False, "error": str(e)}), 500


# =========================
# MT5 ƏLAQƏ
# =========================

@bot_bp.route('/mt5/connect', methods=['POST'])
def mt5_connect():
    """MT5 terminalına qoşulur"""
    try:
        data = request.get_json() or {}
        login = data.get("login")
        password = data.get("password")
        server = data.get("server")
        path = data.get("path")

        result = mt5.connect(login=login, password=password, server=server, path=path)
        
        if result["success"]:
            return jsonify(result), 200
        else:
            return jsonify(result), 400
    except Exception as e:
        return jsonify({"success": False, "error": str(e)}), 500


@bot_bp.route('/mt5/disconnect', methods=['POST'])
def mt5_disconnect():
    """MT5-dən ayrılır"""
    try:
        mt5.disconnect()
        return jsonify({"success": True, "message": "MT5 bağlantısı kəsildi"}), 200
    except Exception as e:
        return jsonify({"success": False, "error": str(e)}), 500


@bot_bp.route('/mt5/account', methods=['GET'])
def mt5_account():
    """MT5 hesab məlumatları"""
    try:
        result = mt5.get_account_info()
        
        if result["success"]:
            return jsonify(result), 200
        else:
            return jsonify(result), 400
    except Exception as e:
        return jsonify({"success": False, "error": str(e)}), 500


@bot_bp.route('/mt5/symbol/<symbol>', methods=['GET'])
def mt5_symbol_info(symbol):
    """Simvol məlumatları"""
    try:
        result = mt5.get_symbol_info(symbol)
        
        if result["success"]:
            return jsonify(result), 200
        else:
            return jsonify(result), 404
    except Exception as e:
        return jsonify({"success": False, "error": str(e)}), 500


@bot_bp.route('/mt5/positions', methods=['GET'])
def mt5_positions():
    """Açıq pozisiyalar"""
    try:
        symbol = request.args.get("symbol")
        result = mt5.get_positions(symbol=symbol)
        
        if result["success"]:
            return jsonify(result), 200
        else:
            return jsonify(result), 400
    except Exception as e:
        return jsonify({"success": False, "error": str(e)}), 500


@bot_bp.route('/mt5/candles', methods=['GET'])
def mt5_candles():
    """Şam məlumatları"""
    try:
        symbol = request.args.get("symbol", "XAUUSDm")
        timeframe = request.args.get("timeframe", "H1")
        count = int(request.args.get("count", 200))

        result = mt5.get_candles(symbol, timeframe, count)
        
        if result.get("success"):
            # DataFrame-i JSON-a çevir
            if "data" in result:
                import pandas as pd
                df = result["data"]
                candles = []
                for _, row in df.iterrows():
                    candles.append({
                        "time": str(row.get("time", "")),
                        "open": float(row.get("open", 0)),
                        "high": float(row.get("high", 0)),
                        "low": float(row.get("low", 0)),
                        "close": float(row.get("close", 0)),
                        "volume": int(row.get("volume", 0))
                    })
                return jsonify({"success": True, "candles": candles, "count": len(candles)}), 200
            else:
                return jsonify(result), 200
        else:
            return jsonify(result), 400
    except Exception as e:
        return jsonify({"success": False, "error": str(e)}), 500


# =========================
# MANUAL TİCARƏT
# =========================

@bot_bp.route('/trade/open', methods=['POST'])
def open_trade():
    """Manual ticarət açır"""
    try:
        data = request.get_json()
        if not data:
            return jsonify({"success": False, "error": "Məlumat göndərilməyib"}), 400

        symbol = data.get("symbol", "XAUUSDm")
        trade_type = data.get("type", "BUY")  # BUY və ya SELL
        lot = float(data.get("lot", 0.01))
        sl = float(data.get("sl", 0))
        tp = float(data.get("tp", 0))
        user_id = data.get("user_id", "default-user")
        bot_id = data.get("bot_id")

        result = bot_engine.manual_trade(user_id, symbol, trade_type, lot, sl, tp, bot_id)
        
        if result["success"]:
            return jsonify(result), 200
        else:
            return jsonify(result), 400
    except Exception as e:
        return jsonify({"success": False, "error": str(e)}), 500


@bot_bp.route('/trade/close/<int:ticket>', methods=['POST'])
def close_trade(ticket):
    """Manual ticarəti bağlayır"""
    try:
        user_id = request.args.get("user_id", "default-user")
        result = bot_engine.close_manual_trade(ticket, user_id)
        
        if result["success"]:
            return jsonify(result), 200
        else:
            return jsonify(result), 400
    except Exception as e:
        return jsonify({"success": False, "error": str(e)}), 500


@bot_bp.route('/trade/modify/<int:ticket>', methods=['PUT'])
def modify_trade(ticket):
    """Pozisiyanın SL/TP-ni dəyişir"""
    try:
        data = request.get_json() or {}
        sl = data.get("sl")
        tp = data.get("tp")

        if sl is not None:
            sl = float(sl)
        if tp is not None:
            tp = float(tp)

        result = mt5.modify_position(ticket, sl=sl, tp=tp)
        
        if result["success"]:
            return jsonify(result), 200
        else:
            return jsonify(result), 400
    except Exception as e:
        return jsonify({"success": False, "error": str(e)}), 500


# =========================
# STRATEJİYALAR
# =========================

@bot_bp.route('/strategies', methods=['GET'])
def get_strategies():
    """Strategiya şablonlarını siyahılayır"""
    try:
        result = bot_engine.get_strategies()
        return jsonify(result), 200
    except Exception as e:
        return jsonify({"success": False, "error": str(e)}), 500


@bot_bp.route('/strategies/<strategy_id>', methods=['GET'])
def get_strategy(strategy_id):
    """Bir strategiyanın detallarını alır"""
    try:
        db = Session()
        template = db.query(StrategyTemplate).filter_by(id=strategy_id).first()
        if not template:
            db.close()
            return jsonify({"success": False, "error": "Strategiya tapılmadı"}), 404

        result = {
            "success": True,
            "strategy": {
                "id": template.id,
                "name": template.name,
                "description": template.description,
                "category": template.category,
                "difficulty": template.difficulty,
                "suitable_symbols": json.loads(template.suitable_symbols) if template.suitable_symbols else [],
                "suitable_timeframes": json.loads(template.suitable_timeframes) if template.suitable_timeframes else [],
                "parameters": json.loads(template.parameters) if template.parameters else {},
                "entry_rules": json.loads(template.entry_rules) if template.entry_rules else {},
                "exit_rules": json.loads(template.exit_rules) if template.exit_rules else {},
                "risk_rules": json.loads(template.risk_rules) if template.risk_rules else {},
                "az_description": template.az_description,
                "az_rules": template.az_rules,
                "estimated_win_rate": template.estimated_win_rate,
                "max_drawdown": template.max_drawdown,
                "rating": template.rating,
                "usage_count": template.usage_count,
            }
        }
        db.close()
        return jsonify(result), 200
    except Exception as e:
        return jsonify({"success": False, "error": str(e)}), 500


@bot_bp.route('/strategies', methods=['POST'])
def create_strategy():
    """Yeni strategiya şablonu yaradır"""
    try:
        data = request.get_json()
        if not data:
            return jsonify({"success": False, "error": "Məlumat göndərilməyib"}), 400

        from database import generate_id
        db = Session()
        template = StrategyTemplate(
            id=data.get("id") or generate_id(),
            name=data.get("name", "Özəl Strategiya"),
            description=data.get("description", ""),
            category=data.get("category", "trend"),
            difficulty=data.get("difficulty", "intermediate"),
            suitable_symbols=json.dumps(data.get("suitable_symbols", ["XAUUSDm", "BTCUSDm", "ETHUSDm"])),
            suitable_timeframes=json.dumps(data.get("suitable_timeframes", ["H1", "H4"])),
            parameters=json.dumps(data.get("parameters", {})),
            entry_rules=json.dumps(data.get("entry_rules", {})),
            exit_rules=json.dumps(data.get("exit_rules", {})),
            risk_rules=json.dumps(data.get("risk_rules", {})),
            az_description=data.get("az_description", ""),
            az_rules=data.get("az_rules", ""),
            estimated_win_rate=data.get("estimated_win_rate", 50.0),
            max_drawdown=data.get("max_drawdown", 20.0),
            is_custom=1,
            user_id=data.get("user_id", "default-user"),
            is_active=1
        )
        db.add(template)
        db.commit()
        db.close()

        return jsonify({"success": True, "message": "Strategiya yaradıldı"}), 201
    except Exception as e:
        return jsonify({"success": False, "error": str(e)}), 500


# =========================
# BAZAR MƏLUMATLARI VƏ SİQNALLAR
# =========================

@bot_bp.route('/market', methods=['GET'])
def get_market_data():
    """Bazar məlumatları və indikatorlar"""
    try:
        symbol = request.args.get("symbol", "XAUUSDm")
        timeframe = request.args.get("timeframe", "H1")
        count = int(request.args.get("count", 200))

        result = bot_engine.get_market_data(symbol, timeframe, count)
        
        if result.get("success"):
            return jsonify(result), 200
        else:
            return jsonify(result), 400
    except Exception as e:
        return jsonify({"success": False, "error": str(e)}), 500


@bot_bp.route('/alerts', methods=['GET'])
def get_alerts():
    """Bazar siqnalları"""
    try:
        user_id = request.args.get("user_id", "default-user")
        limit = int(request.args.get("limit", 20))
        result = bot_engine.get_alerts(user_id, limit)
        return jsonify(result), 200
    except Exception as e:
        return jsonify({"success": False, "error": str(e)}), 500


@bot_bp.route('/alerts/<alert_id>/read', methods=['PUT'])
def mark_alert_read(alert_id):
    """Siqnalı oxunmuş kimi işarələ"""
    try:
        db = Session()
        alert = db.query(MarketAlert).filter_by(id=alert_id).first()
        if not alert:
            db.close()
            return jsonify({"success": False, "error": "Siqnal tapılmadı"}), 404

        alert.is_read = 1
        db.commit()
        db.close()
        return jsonify({"success": True, "message": "Oxunmuş kimi işarələndi"}), 200
    except Exception as e:
        return jsonify({"success": False, "error": str(e)}), 500


@bot_bp.route('/alerts/<alert_id>/act', methods=['PUT'])
def act_on_alert(alert_id):
    """Siqnala əməl edir (ticarət açır)"""
    try:
        db = Session()
        alert = db.query(MarketAlert).filter_by(id=alert_id).first()
        if not alert:
            db.close()
            return jsonify({"success": False, "error": "Siqnal tapılmadı"}), 404

        alert.is_acted = 1

        # Siqnal növünə görə ticarət aç
        if alert.alert_type in ["buy_signal", "strong_buy"]:
            trade_type = "BUY"
        elif alert.alert_type in ["sell_signal", "strong_sell"]:
            trade_type = "SELL"
        else:
            db.commit()
            db.close()
            return jsonify({"success": False, "error": "Bu siqnal növü üçün ticarət açıla bilməz"}), 400

        # Bot parametrlərini al
        bot = None
        if alert.bot_id:
            bot = db.query(TradingBot).filter_by(id=alert.bot_id).first()

        lot = bot.lot_size if bot else 0.01
        sl = int(bot.stop_loss) if bot else 500
        tp = int(bot.take_profit) if bot else 1000
        symbol = alert.symbol
        user_id = alert.user_id

        db.commit()
        db.close()

        # Ticarət aç
        result = bot_engine.manual_trade(user_id, symbol, trade_type, lot, sl, tp, alert.bot_id)
        return jsonify(result), 200
    except Exception as e:
        return jsonify({"success": False, "error": str(e)}), 500


# =========================
# BOT TİCARƏT JURNALI
# =========================

@bot_bp.route('/trades/<bot_id>', methods=['GET'])
def get_bot_trades(bot_id):
    """Botun ticarətlərini alır"""
    try:
        limit = int(request.args.get("limit", 50))
        result = bot_engine.get_bot_trades(bot_id, limit)
        return jsonify(result), 200
    except Exception as e:
        return jsonify({"success": False, "error": str(e)}), 500


@bot_bp.route('/trades/all', methods=['GET'])
def get_all_trades():
    """Bütün ticarətləri alır"""
    try:
        user_id = request.args.get("user_id", "default-user")
        limit = int(request.args.get("limit", 100))
        status = request.args.get("status")  # open, closed, all

        db = Session()
        query = db.query(BotTrade).filter_by(user_id=user_id)
        
        if status and status != "all":
            query = query.filter_by(status=status)
        
        trades = query.order_by(BotTrade.created_at.desc()).limit(limit).all()
        
        trade_list = []
        for t in trades:
            trade_list.append({
                "id": t.id,
                "bot_id": t.bot_id,
                "ticket": t.ticket,
                "symbol": t.symbol,
                "type": t.trade_type,
                "entry_price": t.entry_price,
                "exit_price": t.exit_price,
                "lot_size": t.lot_size,
                "stop_loss": t.stop_loss,
                "take_profit": t.take_profit,
                "status": t.status,
                "pnl": t.pnl,
                "pips": t.pips,
                "signal_source": t.signal_source,
                "signal_reason": t.signal_reason,
                "entry_time": t.entry_time,
                "exit_time": t.exit_time,
                "duration_minutes": t.duration_minutes,
                "created_at": t.created_at,
            })

        db.close()
        return jsonify({"success": True, "trades": trade_list, "count": len(trade_list)}), 200
    except Exception as e:
        return jsonify({"success": False, "error": str(e)}), 500


# =========================
# ÖYRƏNMƏ SİSTEMİ
# =========================

@bot_bp.route('/learning', methods=['GET'])
def get_learning_entries():
    """Öyrənmə qeydləri"""
    try:
        user_id = request.args.get("user_id", "default-user")
        limit = int(request.args.get("limit", 20))
        result = bot_engine.get_learning_entries(user_id, limit)
        return jsonify(result), 200
    except Exception as e:
        return jsonify({"success": False, "error": str(e)}), 500


@bot_bp.route('/learning/<entry_id>/apply', methods=['PUT'])
def apply_learning(entry_id):
    """Öyrənmə qeydini tətbiq etmiş kimi işarələ"""
    try:
        db = Session()
        entry = db.query(LearningEntry).filter_by(id=entry_id).first()
        if not entry:
            db.close()
            return jsonify({"success": False, "error": "Qeyd tapılmadı"}), 404

        entry.is_applied = 1
        from datetime import datetime
        entry.applied_at = datetime.now().isoformat()
        db.commit()
        db.close()

        return jsonify({"success": True, "message": "Dərs tətbiq olundu kimi işarələndi"}), 200
    except Exception as e:
        return jsonify({"success": False, "error": str(e)}), 500


@bot_bp.route('/learning/<entry_id>/rate', methods=['PUT'])
def rate_learning(entry_id):
    """Öyrənmə qeydinin effektivliyini qiymətləndir"""
    try:
        data = request.get_json() or {}
        effectiveness = data.get("effectiveness")  # 1-10

        if effectiveness is None:
            return jsonify({"success": False, "error": "effectiveness göndərilməyib (1-10)"}), 400

        db = Session()
        entry = db.query(LearningEntry).filter_by(id=entry_id).first()
        if not entry:
            db.close()
            return jsonify({"success": False, "error": "Qeyd tapılmadı"}), 404

        entry.effectiveness = int(effectiveness)
        # Etibarlılığı artır
        if effectiveness >= 7:
            entry.confidence = min(1.0, entry.confidence + 0.1)
        else:
            entry.confidence = max(0.1, entry.confidence - 0.1)

        db.commit()
        db.close()

        return jsonify({"success": True, "message": f"Effektivlik: {effectiveness}/10, Etibarlılıq: {entry.confidence:.2f}"}), 200
    except Exception as e:
        return jsonify({"success": False, "error": str(e)}), 500


# =========================
# STATİSTİKA
# =========================

@bot_bp.route('/stats', methods=['GET'])
def get_stats():
    """Ümumi ticarət statistikası"""
    try:
        user_id = request.args.get("user_id", "default-user")
        db = Session()

        # Bütün ticarətlər
        all_trades = db.query(BotTrade).filter_by(user_id=user_id).all()
        total_trades = len(all_trades)
        open_trades = len([t for t in all_trades if t.status == "open"])
        closed_trades = len([t for t in all_trades if t.status == "closed"])
        wins = len([t for t in all_trades if t.status == "closed" and t.pnl and t.pnl > 0])
        losses = len([t for t in all_trades if t.status == "closed" and t.pnl and t.pnl <= 0])
        total_pnl = sum(t.pnl or 0 for t in all_trades if t.status == "closed")
        win_rate = (wins / closed_trades * 100) if closed_trades > 0 else 0

        # Simvol üzrə
        symbol_stats = {}
        for t in all_trades:
            if t.symbol not in symbol_stats:
                symbol_stats[t.symbol] = {"trades": 0, "wins": 0, "losses": 0, "pnl": 0}
            symbol_stats[t.symbol]["trades"] += 1
            if t.status == "closed" and t.pnl:
                if t.pnl > 0:
                    symbol_stats[t.symbol]["wins"] += 1
                else:
                    symbol_stats[t.symbol]["losses"] += 1
                symbol_stats[t.symbol]["pnl"] += t.pnl

        # Botlar
        bots = db.query(TradingBot).filter_by(user_id=user_id).all()
        bot_stats = []
        for b in bots:
            bot_stats.append({
                "id": b.id,
                "name": b.name,
                "symbol": b.symbol,
                "status": b.status,
                "mode": b.mode,
                "total_trades": b.total_trades,
                "total_wins": b.total_wins,
                "total_losses": b.total_losses,
                "total_pnl": b.total_pnl,
                "win_rate": b.win_rate,
            })

        # Öyrənmə
        learning_count = db.query(LearningEntry).filter_by(user_id=user_id).count()
        applied_learning = db.query(LearningEntry).filter_by(user_id=user_id, is_applied=1).count()

        db.close()

        return jsonify({
            "success": True,
            "stats": {
                "total_trades": total_trades,
                "open_trades": open_trades,
                "closed_trades": closed_trades,
                "wins": wins,
                "losses": losses,
                "win_rate": round(win_rate, 2),
                "total_pnl": round(total_pnl, 2),
                "symbol_stats": symbol_stats,
                "learning_total": learning_count,
                "learning_applied": applied_learning,
            },
            "bots": bot_stats
        }), 200
    except Exception as e:
        return jsonify({"success": False, "error": str(e)}), 500


# =========================
# BOT SİMULYASİYA (MT5 olmadan test)
# =========================

@bot_bp.route('/simulate', methods=['POST'])
def simulate_strategy():
    """MT5 olmadan strategiya simulyasiyası (test rejimi)"""
    try:
        data = request.get_json() or {}
        strategy_id = data.get("strategy_id", "strat-ma-crossover")
        symbol = data.get("symbol", "XAUUSDm")

        # Əgər MT5 qoşulubsa real məlumatla, yoxsa süni məlumatla
        if mt5.connected:
            timeframe = data.get("timeframe", "H1")
            market_result = bot_engine.get_market_data(symbol, timeframe, 200)
            if market_result.get("success"):
                indicators = market_result.get("indicators", {}).get(strategy_id, {})
                return jsonify({
                    "success": True,
                    "mode": "real",
                    "symbol": symbol,
                    "signal": indicators.get("signal", "HOLD"),
                    "strength": indicators.get("strength", 0),
                    "reason": indicators.get("reason", ""),
                    "indicators": indicators.get("indicators", {}),
                    "market_condition": market_result.get("market_condition", "unknown")
                }), 200
            else:
                return jsonify(market_result), 400
        else:
            # MT5 yoxdursa - simulyasiya rejimi
            import random
            from datetime import datetime

            signal = random.choice(["BUY", "SELL", "HOLD"])
            strength = random.randint(30, 90)

            return jsonify({
                "success": True,
                "mode": "simulation",
                "symbol": symbol,
                "strategy": strategy_id,
                "signal": signal,
                "strength": strength,
                "reason": f"[SİMULYASİYA] {strategy_id} strategiyası {symbol} üçün {signal} siqnalı verir (güc: {strength}%)",
                "indicators": {
                    "fast_ema": round(random.uniform(2300, 2400), 2),
                    "slow_ema": round(random.uniform(2300, 2400), 2),
                    "rsi": round(random.uniform(20, 80), 2),
                    "macd": round(random.uniform(-5, 5), 4),
                },
                "market_condition": random.choice(["trending", "ranging", "volatile", "quiet"]),
                "note": "Bu simulyasiyadır. MT5 qoşulanda real məlumatlar göstəriləcək."
            }), 200
    except Exception as e:
        return jsonify({"success": False, "error": str(e)}), 500