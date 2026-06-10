"""
Trading Bot Engine Module - Bot Management
Raw SQLite pattern: import database as db
"""

import database as db
import json
import threading
import time
from datetime import datetime


class TradingBotEngine:
    """Trading Bot Management Engine"""

    def __init__(self, socketio=None, mt5_module=None):
        self.socketio = socketio
        self.mt5_module = mt5_module
        self._running_bots = {}
        self._bot_threads = {}

    def start_bot(self, bot_id):
        """Botu başlat"""
        try:
            bot = db.bot_get(bot_id)
            if not bot:
                return {'success': False, 'error': 'Bot tapılmadı'}

            if bot_id in self._running_bots:
                return {'success': False, 'error': 'Bot artıq işləyir'}

            self._running_bots[bot_id] = {
                'bot_id': bot_id,
                'status': 'running',
                'started_at': datetime.now().isoformat(),
                'symbol': bot.get('symbol', 'XAUUSDm'),
                'strategy_id': bot.get('strategy_id'),
                'timeframe': bot.get('timeframe', 'H1'),
                'lot_size': bot.get('lot_size', 0.01),
                'stop_loss': bot.get('stop_loss', 0),
                'take_profit': bot.get('take_profit', 0),
                'trailing_stop': bot.get('trailing_stop', 0),
                'max_daily_trades': bot.get('max_daily_trades', 5),
                'max_daily_loss': bot.get('max_daily_loss', 100),
                'risk_per_trade': bot.get('risk_per_trade', 2.0),
                'daily_trades': 0,
                'daily_pnl': 0,
                'last_reset': datetime.now().isoformat()
            }

            db.bot_update_status(bot_id, 'running')

            t = threading.Thread(target=self._bot_monitor, args=(bot_id,), daemon=True)
            t.start()
            self._bot_threads[bot_id] = t

            if self.socketio:
                self.socketio.emit('bot_started', {'bot_id': bot_id})

            return {'success': True, 'bot_id': bot_id, 'message': f'Bot "{bot.get("name", "")}" başladıldı'}
        except Exception as e:
            print(f"start_bot xətası: {e}")
            return {'success': False, 'error': str(e)}

    def stop_bot(self, bot_id):
        """Botu dayandır"""
        try:
            if bot_id in self._running_bots:
                self._running_bots[bot_id]['status'] = 'stopped'
                del self._running_bots[bot_id]

            db.bot_update_status(bot_id, 'stopped')

            if self.socketio:
                self.socketio.emit('bot_stopped', {'bot_id': bot_id})
        except Exception as e:
            print(f"stop_bot xətası: {e}")

    def pause_bot(self, bot_id):
        """Botu durdur"""
        try:
            if bot_id in self._running_bots:
                self._running_bots[bot_id]['status'] = 'paused'
                db.bot_update_status(bot_id, 'paused')

                if self.socketio:
                    self.socketio.emit('bot_paused', {'bot_id': bot_id})
        except Exception as e:
            print(f"pause_bot xətası: {e}")

    def resume_bot(self, bot_id):
        """Botu davam etdir"""
        try:
            if bot_id in self._running_bots:
                self._running_bots[bot_id]['status'] = 'running'
                db.bot_update_status(bot_id, 'running')

                if self.socketio:
                    self.socketio.emit('bot_resumed', {'bot_id': bot_id})
        except Exception as e:
            print(f"resume_bot xətası: {e}")

    def manual_trade(self, bot_id, direction):
        """Manual ticarət aç"""
        try:
            bot = db.bot_get(bot_id)
            if not bot:
                return {'success': False, 'error': 'Bot tapılmadı'}

            symbol = bot.get('symbol', 'XAUUSDm')
            lot_size = bot.get('lot_size', 0.01)
            sl = bot.get('stop_loss', 0)
            tp = bot.get('take_profit', 0)

            if self.mt5_module and self.mt5_module._connected:
                result = self.mt5_module.send_order(
                    symbol=symbol,
                    order_type=direction,
                    volume=lot_size,
                    sl=sl,
                    tp=tp,
                    comment=f'DAU_Bot_{bot_id}'
                )

                if result.get('success'):
                    ticket = result.get('ticket', 0)
                    entry_price = result.get('entry_price', 0)

                    db.bot_trade_create_with_ticket(
                        bot_id=bot_id,
                        symbol=symbol,
                        direction=direction,
                        lot_size=lot_size,
                        entry_price=entry_price,
                        ticket=ticket,
                        sl_price=sl,
                        tp_price=tp,
                        source='manual'
                    )

                    return {'success': True, 'ticket': ticket, 'price': entry_price}
                else:
                    return result
            else:
                return {'success': False, 'error': 'MT5 qoşulmayıb'}
        except Exception as e:
            print(f"manual_trade xətası: {e}")
            return {'success': False, 'error': str(e)}

    def run_simulation(self, params):
        """Simulyasiya işlət"""
        try:
            symbol = params.get('symbol', 'XAUUSDm')
            strategy = params.get('strategy', 'trend')
            days = params.get('days', 30)
            lot_size = params.get('lot_size', 0.01)

            result = {
                'symbol': symbol,
                'strategy': strategy,
                'days': days,
                'lot_size': lot_size,
                'total_trades': 0,
                'win_rate': 0,
                'total_pnl': 0,
                'max_drawdown': 0,
                'status': 'MT5 candle data lazımdır'
            }

            if self.mt5_module and self.mt5_module._connected:
                candles = self.mt5_module.get_candles(symbol, 'H1', days * 24)
                if candles:
                    result['total_trades'] = len(candles) // 10
                    result['status'] = 'Simulyasiya hazır (sadələşdirilmiş)'

            return result
        except Exception as e:
            print(f"run_simulation xətası: {e}")
            return {'error': str(e)}

    def _bot_monitor(self, bot_id):
        """Bot monitor thread (hər 30 saniyə)"""
        while bot_id in self._running_bots:
            try:
                bot_info = self._running_bots.get(bot_id)
                if not bot_info or bot_info.get('status') != 'running':
                    break

                today = datetime.now().date().isoformat()
                if bot_info.get('last_reset', '')[:10] != today:
                    bot_info['daily_trades'] = 0
                    bot_info['daily_pnl'] = 0
                    bot_info['last_reset'] = datetime.now().isoformat()

            except Exception as e:
                print(f"_bot_monitor xətası ({bot_id}): {e}")

            time.sleep(30)

    def get_running_bots(self):
        """İşləyən botların siyahısı"""
        return dict(self._running_bots)