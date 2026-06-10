"""
Auto Trader Module - Autonomous Trading System
Raw SQLite pattern: import database as db
"""

import database as db
import json
import threading
import time
from datetime import datetime


class StrategyEngine:
    """Strategiya hesablama mühərriki"""

    @staticmethod
    def calculate_indicators(df, strategy_type='trend', params=None):
        """İndikatorları hesabla"""
        try:
            import pandas as pd
            import pandas_ta as ta

            if df is None or len(df) == 0:
                return None

            params = params or {}

            if strategy_type == 'ma_crossover':
                fast = params.get('fast_period', 9)
                slow = params.get('slow_period', 21)
                df['ma_fast'] = df['close'].rolling(window=fast).mean()
                df['ma_slow'] = df['close'].rolling(window=slow).mean()

            elif strategy_type == 'rsi':
                period = params.get('rsi_period', 14)
                overbought = params.get('overbought', 70)
                oversold = params.get('oversold', 30)
                df['rsi'] = ta.rsi(df['close'], length=period)

            elif strategy_type == 'macd':
                fast = params.get('fast', 12)
                slow = params.get('slow', 26)
                signal = params.get('signal', 9)
                macd = ta.macd(df['close'], fast=fast, slow=slow, signal=signal)
                if macd is not None:
                    df = pd.concat([df, macd], axis=1)

            elif strategy_type == 'bollinger':
                bb_period = params.get('bb_period', 20)
                bb_std = params.get('bb_std', 2.0)
                bb = ta.bbands(df['close'], length=bb_period, std=bb_std)
                if bb is not None:
                    df = pd.concat([df, bb], axis=1)

            elif strategy_type == 'scalping':
                df['ema_5'] = df['close'].rolling(window=5).mean()
                df['ema_13'] = df['close'].rolling(window=13).mean()
                df['rsi'] = ta.rsi(df['close'], length=7)

            elif strategy_type == 'combo':
                df['ma_fast'] = df['close'].rolling(window=9).mean()
                df['ma_slow'] = df['close'].rolling(window=21).mean()
                df['rsi'] = ta.rsi(df['close'], length=14)
                macd = ta.macd(df['close'])
                if macd is not None:
                    df = pd.concat([df, macd], axis=1)

            return df
        except Exception as e:
            print(f"calculate_indicators xətası: {e}")
            return df


class MT5Integration:
    """MT5 Candle Data Integration"""

    def __init__(self, mt5_module=None):
        self.mt5_module = mt5_module

    def get_candles_df(self, symbol='XAUUSDm', timeframe='H1', count=200):
        """Candle data DataFrame olaraq al"""
        try:
            if not self.mt5_module or not self.mt5_module._connected:
                return None

            import pandas as pd
            candles = self.mt5_module.get_candles(symbol, timeframe, count)
            if not candles:
                return None

            df = pd.DataFrame(candles)
            if 'time' in df.columns:
                df['time'] = pd.to_datetime(df['time'])
                df.set_index('time', inplace=True)

            return df
        except Exception as e:
            print(f"get_candles_df xətası: {e}")
            return None


class MT5AutoTrader:
    """Avtomatik Ticarət Sistemi"""

    def __init__(self, mt5_module, risk_manager, bot_engine, socketio=None):
        self.mt5_module = mt5_module
        self.risk_manager = risk_manager
        self.bot_engine = bot_engine
        self.socketio = socketio
        self.mt5_integration = MT5Integration(mt5_module=mt5_module)
        self._active_bots = {}
        self._monitor_thread = None
        self._monitor_running = False

    def connect_mt5(self):
        """MT5 bağlantısı qurulanda çağırılır"""
        self.mt5_integration = MT5Integration(mt5_module=self.mt5_module)
        print("[AutoTrader] MT5 bağlantısı yeniləndi")

    def start_autotrader(self, bot_id):
        """Avtotrader-i bot üçün başlat"""
        try:
            bot = db.bot_get(bot_id)
            if not bot:
                return {'success': False, 'error': 'Bot tapılmadı'}

            if bot_id in self._active_bots:
                return {'success': False, 'error': 'Bot artıq avtotrader-də aktivdir'}

            self._active_bots[bot_id] = {
                'bot_id': bot_id,
                'symbol': bot.get('symbol', 'XAUUSDm'),
                'strategy_id': bot.get('strategy_id'),
                'timeframe': bot.get('timeframe', 'H1'),
                'lot_size': bot.get('lot_size', 0.01),
                'stop_loss': bot.get('stop_loss', 0),
                'take_profit': bot.get('take_profit', 0),
                'status': 'running',
                'started_at': datetime.now().isoformat()
            }

            db.bot_update_status(bot_id, 'running')
            db.autotrader_log_add(
                bot_id=bot_id,
                event_type='autotrader_started',
                symbol=bot.get('symbol', 'XAUUSDm'),
                details={'message': 'Avtotrader başladıldı'}
            )

            # Monitor thread başlat (əgər işləmirsə)
            if not self._monitor_running:
                self._start_monitor()

            if self.socketio:
                self.socketio.emit('autotrader_started', {'bot_id': bot_id})

            return {'success': True, 'bot_id': bot_id, 'message': 'Avtotrader başladıldı'}
        except Exception as e:
            print(f"start_autotrader xətası: {e}")
            return {'success': False, 'error': str(e)}

    def stop_autotrader(self, bot_id):
        """Avtotrader-i dayandır"""
        try:
            if bot_id not in self._active_bots:
                return {'success': False, 'error': 'Bot avtotrader-də deyil'}

            self._active_bots[bot_id]['status'] = 'stopped'
            del self._active_bots[bot_id]

            db.bot_update_status(bot_id, 'stopped')
            db.autotrader_log_add(
                bot_id=bot_id,
                event_type='autotrader_stopped',
                details={'message': 'Avtotrader dayandırıldı'}
            )

            if self.socketio:
                self.socketio.emit('autotrader_stopped', {'bot_id': bot_id})

            return {'success': True, 'bot_id': bot_id, 'message': 'Avtotrader dayandırıldı'}
        except Exception as e:
            print(f"stop_autotrader xətası: {e}")
            return {'success': False, 'error': str(e)}

    def pause_autotrader(self, bot_id):
        """Avtotrader-i durdur"""
        try:
            if bot_id not in self._active_bots:
                return {'success': False, 'error': 'Bot avtotrader-də deyil'}

            self._active_bots[bot_id]['status'] = 'paused'
            db.bot_update_status(bot_id, 'paused')

            return {'success': True, 'bot_id': bot_id, 'message': 'Avtotrader durduruldu'}
        except Exception as e:
            print(f"pause_autotrader xətası: {e}")
            return {'success': False, 'error': str(e)}

    def resume_autotrader(self, bot_id):
        """Avtotrader-i davam etdir"""
        try:
            if bot_id not in self._active_bots:
                return {'success': False, 'error': 'Bot avtotrader-də deyil'}

            self._active_bots[bot_id]['status'] = 'running'
            db.bot_update_status(bot_id, 'running')

            return {'success': True, 'bot_id': bot_id, 'message': 'Avtotrader davam etdirildi'}
        except Exception as e:
            print(f"resume_autotrader xətası: {e}")
            return {'success': False, 'error': str(e)}

    def evaluate_strategy(self, strategy_type='trend', params=None, symbol='XAUUSDm', timeframe='H1'):
        """Strategiya siqnalını qiymətləndir"""
        try:
            df = self.mt5_integration.get_candles_df(symbol, timeframe, 200)
            if df is None or len(df) == 0:
                return {'signal': 'NONE', 'strength': 0, 'error': 'Candle data alına bilmədi'}

            df = StrategyEngine.calculate_indicators(df, strategy_type, params)

            if df is None:
                return {'signal': 'NONE', 'strength': 0, 'error': 'İndikatorlar hesablana bilmədi'}

            signal = 'NONE'
            strength = 0
            reason = ''

            last = df.iloc[-1]

            if strategy_type == 'ma_crossover':
                if 'ma_fast' in df.columns and 'ma_slow' in df.columns:
                    prev = df.iloc[-2]
                    if prev['ma_fast'] <= prev['ma_slow'] and last['ma_fast'] > last['ma_slow']:
                        signal = 'BUY'
                        strength = 70
                        reason = 'MA Crossover: Fast MA Slow-nu yuxarı kəsdi'
                    elif prev['ma_fast'] >= prev['ma_slow'] and last['ma_fast'] < last['ma_slow']:
                        signal = 'SELL'
                        strength = 70
                        reason = 'MA Crossover: Fast MA Slow-nu aşağı kəsdi'

            elif strategy_type == 'rsi':
                if 'rsi' in df.columns and not df['rsi'].isna().all():
                    rsi_val = last['rsi']
                    if rsi_val < 30:
                        signal = 'BUY'
                        strength = min(90, 50 + (30 - rsi_val))
                        reason = f'RSI Oversold: {rsi_val:.1f}'
                    elif rsi_val > 70:
                        signal = 'SELL'
                        strength = min(90, 50 + (rsi_val - 70))
                        reason = f'RSI Overbought: {rsi_val:.1f}'

            elif strategy_type == 'scalping':
                if 'ema_5' in df.columns and 'ema_13' in df.columns and 'rsi' in df.columns:
                    if last['ema_5'] > last['ema_13'] and last['rsi'] < 40:
                        signal = 'BUY'
                        strength = 65
                        reason = 'Scalping: EMA5>EMA13 + RSI low'
                    elif last['ema_5'] < last['ema_13'] and last['rsi'] > 60:
                        signal = 'SELL'
                        strength = 65
                        reason = 'Scalping: EMA5<EMA13 + RSI high'

            else:
                # Default: trend
                if 'ma_fast' in df.columns and 'ma_slow' in df.columns:
                    if last['ma_fast'] > last['ma_slow']:
                        signal = 'BUY'
                        strength = 55
                        reason = 'Trend: MA_fast > MA_slow'
                    else:
                        signal = 'SELL'
                        strength = 55
                        reason = 'Trend: MA_fast < MA_slow'

            return {
                'signal': signal,
                'strength': strength,
                'reason': reason,
                'strategy': strategy_type,
                'symbol': symbol,
                'timeframe': timeframe
            }
        except Exception as e:
            print(f"evaluate_strategy xətası: {e}")
            return {'signal': 'NONE', 'strength': 0, 'error': str(e)}

    def get_candles(self, symbol, timeframe, count):
        """Candle data al"""
        try:
            if self.mt5_module and self.mt5_module._connected:
                return self.mt5_module.get_candles(symbol, timeframe, count)
            return []
        except Exception as e:
            print(f"get_candles xətası: {e}")
            return []

    def execute_trade(self, symbol, direction, volume, sl=0, tp=0, comment=''):
        """Ticarət icra et"""
        try:
            # Risk yoxlama
            risk_check = self.risk_manager.can_trade()
            if not risk_check.get('can_trade', False):
                return {'success': False, 'error': f"Risk blokladı: {'; '.join(risk_check.get('reasons', []))}"}

            if not self.mt5_module or not self.mt5_module._connected:
                return {'success': False, 'error': 'MT5 qoşulmayıb'}

            result = self.mt5_module.send_order(
                symbol=symbol,
                order_type=direction,
                volume=volume,
                sl=sl,
                tp=tp,
                comment=comment or 'DAU_AutoTrader'
            )

            if result.get('success'):
                ticket = result.get('ticket', 0)
                entry_price = result.get('entry_price', 0)

                db.autotrader_log_add(
                    bot_id='autotrader',
                    event_type='trade_opened',
                    symbol=symbol,
                    direction=direction,
                    price=entry_price,
                    volume=volume,
                    details={'sl': sl, 'tp': tp, 'ticket': ticket}
                )

                self.risk_manager.record_trade(0)

                if self.socketio:
                    self.socketio.emit('autotrader_trade_opened', {
                        'symbol': symbol,
                        'direction': direction,
                        'ticket': ticket,
                        'price': entry_price
                    })

            return result
        except Exception as e:
            print(f"execute_trade xətası: {e}")
            return {'success': False, 'error': str(e)}

    def close_trade_by_ticket(self, ticket):
        """Ticareti ticket ilə bağla"""
        try:
            if not self.mt5_module or not self.mt5_module._connected:
                return {'success': False, 'error': 'MT5 qoşulmayıb'}

            result = self.mt5_module.close_position(ticket)

            if result.get('success'):
                db.autotrader_log_add(
                    bot_id='autotrader',
                    event_type='trade_closed',
                    details={'ticket': ticket, 'price': result.get('price', 0)}
                )

                if self.socketio:
                    self.socketio.emit('autotrader_trade_closed', {
                        'ticket': ticket,
                        'price': result.get('price', 0)
                    })

            return result
        except Exception as e:
            print(f"close_trade_by_ticket xətası: {e}")
            return {'success': False, 'error': str(e)}

    def modify_position(self, ticket, sl=None, tp=None):
        """Pozisiya SL/TP dəyiş"""
        try:
            if not self.mt5_module or not self.mt5_module._connected:
                return {'success': False, 'error': 'MT5 qoşulmayıb'}

            return self.mt5_module.modify_position(ticket, sl=sl, tp=tp)
        except Exception as e:
            print(f"modify_position xətası: {e}")
            return {'success': False, 'error': str(e)}

    def get_trading_history(self, days=7):
        """Ticarət tarixi al"""
        try:
            if self.mt5_module and self.mt5_module._connected:
                return self.mt5_module.get_history_deals(days)
            return []
        except Exception as e:
            print(f"get_trading_history xətası: {e}")
            return []

    def get_active_bots(self):
        """Aktiv botları al"""
        return [b for b in self._active_bots.values() if b.get('status') == 'running']

    def _start_monitor(self):
        """Monitor thread başlat"""
        if self._monitor_running:
            return
        self._monitor_running = True
        self._monitor_thread = threading.Thread(target=self._monitor_loop, daemon=True)
        self._monitor_thread.start()
        print("[AutoTrader] Monitor thread başladıldı")

    def _monitor_loop(self):
        """Monitor dövrü - hər 15 saniyədə botları yoxlayır"""
        while self._monitor_running:
            try:
                for bot_id, bot_info in list(self._active_bots.items()):
                    if bot_info.get('status') != 'running':
                        continue

                    try:
                        strategy_type = 'trend'
                        strategy_id = bot_info.get('strategy_id')
                        if strategy_id:
                            strategies = db.strategy_list()
                            for s in strategies:
                                if s.get('id') == strategy_id:
                                    strategy_type = s.get('strategy_type', 'trend')
                                    break

                        result = self.evaluate_strategy(
                            strategy_type=strategy_type,
                            symbol=bot_info.get('symbol', 'XAUUSDm'),
                            timeframe=bot_info.get('timeframe', 'H1')
                        )

                        signal = result.get('signal', 'NONE')
                        strength = result.get('strength', 0)

                        if signal != 'NONE' and strength >= 60:
                            db.autotrader_log_add(
                                bot_id=bot_id,
                                event_type='signal',
                                symbol=bot_info.get('symbol', 'XAUUSDm'),
                                direction=signal,
                                signal_strength=strength,
                                signal_reason=result.get('reason', ''),
                                details=result
                            )

                            if self.socketio:
                                self.socketio.emit('autotrader_signal', {
                                    'bot_id': bot_id,
                                    'signal': signal,
                                    'strength': strength,
                                    'reason': result.get('reason', '')
                                })

                    except Exception as e:
                        print(f"_monitor_loop bot {bot_id} xətası: {e}")

            except Exception as e:
                print(f"_monitor_loop xətası: {e}")

            time.sleep(15)