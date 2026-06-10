"""
MT5 Module - MetaTrader5 Connection & Data
Raw SQLite pattern: import database as db
"""

import database as db
import json
from datetime import datetime, timedelta


class MT5Module:
    """MetaTrader5 Connection & Account Management"""

    def __init__(self):
        self._connected = False
        self._mt5 = None
        self._account_info = None
        self._last_symbol_list = []

    def connect(self, login=0, password='', server=''):
        """MT5-ə qoşul"""
        try:
            import MetaTrader5 as mt5

            if not mt5.initialize():
                return {'success': False, 'error': 'MT5 initialize edilə bilmədi', 'connected': False}

            if login and password and server:
                authorized = mt5.login(login, password=password, server=server)
                if not authorized:
                    mt5.shutdown()
                    return {'success': False, 'error': f'MT5 login uğursuz: {mt5.last_error()}', 'connected': False}

            self._mt5 = mt5
            self._connected = True
            self._account_info = self._get_account_raw()

            if self._account_info:
                db.mt5_snapshot_save(
                    balance=self._account_info.get('balance', 0),
                    equity=self._account_info.get('equity', 0),
                    margin=self._account_info.get('margin', 0),
                    free_margin=self._account_info.get('free_margin', 0),
                    margin_level=self._account_info.get('margin_level', 0),
                    profit=self._account_info.get('profit', 0),
                    open_positions=0
                )

            return {
                'success': True,
                'connected': True,
                'account': self._account_info.get('login', 'unknown') if self._account_info else 'unknown',
                'server': self._account_info.get('server', 'unknown') if self._account_info else 'unknown'
            }
        except ImportError:
            return {'success': False, 'error': 'MetaTrader5 paketi quraşdırılmayıb', 'connected': False}
        except Exception as e:
            return {'success': False, 'error': str(e), 'connected': False}

    def disconnect(self):
        """MT5-dən ayrıl"""
        try:
            if self._mt5:
                self._mt5.shutdown()
            self._connected = False
            self._mt5 = None
            self._account_info = None
            return {'success': True, 'connected': False}
        except Exception as e:
            return {'success': False, 'error': str(e)}

    def get_status(self):
        """MT5 bağlantı statusu"""
        return {
            'connected': self._connected,
            'mt5_available': self._mt5 is not None,
            'account_login': self._account_info.get('login') if self._account_info else None,
            'server': self._account_info.get('server') if self._account_info else None
        }

    def _get_account_raw(self):
        """Raw MT5 account info al"""
        try:
            if not self._mt5 or not self._connected:
                return None

            info = self._mt5.account_info()
            if not info:
                return None

            return {
                'login': info.login,
                'server': info.server,
                'balance': info.balance,
                'equity': info.equity,
                'margin': info.margin,
                'free_margin': info.margin_free,
                'margin_level': info.margin_level if info.margin_level else 0,
                'profit': info.profit,
                'currency': info.currency,
                'leverage': info.leverage,
                'trade_mode': info.trade_mode,
                'name': info.name
            }
        except Exception as e:
            print(f"_get_account_raw xətası: {e}")
            return None

    def get_account_info(self):
        """Hesab məlumatlarını qaytar (flat dict)"""
        try:
            if not self._connected:
                return {'connected': False, 'error': 'MT5 qoşulmayıb'}

            self._account_info = self._get_account_raw()
            if self._account_info:
                return self._account_info
            return {'connected': False, 'error': 'Hesab məlumatı alına bilmədi'}
        except Exception as e:
            return {'connected': False, 'error': str(e)}

    def get_positions(self):
        """Açıq pozisiyaları al"""
        try:
            if not self._mt5 or not self._connected:
                return {'positions': [], 'count': 0}

            positions = self._mt5.positions_get()
            if positions is None:
                return {'positions': [], 'count': 0}

            result = []
            for pos in positions:
                result.append({
                    'ticket': pos.ticket,
                    'symbol': pos.symbol,
                    'type': 'BUY' if pos.type == 0 else 'SELL',
                    'volume': pos.volume,
                    'price_open': pos.price_open,
                    'price_current': pos.price_current,
                    'sl': pos.sl,
                    'tp': pos.tp,
                    'profit': pos.profit,
                    'comment': pos.comment,
                    'time': datetime.fromtimestamp(pos.time).isoformat() if pos.time else None
                })

            return {'positions': result, 'count': len(result)}
        except Exception as e:
            print(f"get_positions xətası: {e}")
            return {'positions': [], 'count': 0, 'error': str(e)}

    def get_price(self, symbol):
        """Simvol qiymətini al"""
        try:
            if not self._mt5 or not self._connected:
                return {'error': 'MT5 qoşulmayıb'}

            tick = self._mt5.symbol_info_tick(symbol)
            if not tick:
                return {'error': f'{symbol} üçün qiymət alına bilmədi'}

            return {
                'symbol': symbol,
                'bid': tick.bid,
                'ask': tick.ask,
                'spread': tick.ask - tick.bid,
                'time': datetime.fromtimestamp(tick.time).isoformat() if tick.time else None
            }
        except Exception as e:
            return {'error': str(e)}

    def get_symbols(self):
        """Mövcud simvolları al"""
        try:
            if not self._mt5 or not self._connected:
                return {'symbols': [], 'count': 0}

            symbols = self._mt5.symbols_get()
            if symbols is None:
                return {'symbols': [], 'count': 0}

            result = []
            for s in symbols:
                result.append({
                    'name': s.name,
                    'description': s.description,
                    'point': s.point,
                    'digits': s.digits,
                    'trade_mode': s.trade_mode
                })

            self._last_symbol_list = result
            return {'symbols': result, 'count': len(result)}
        except Exception as e:
            return {'symbols': [], 'count': 0, 'error': str(e)}

    def close_position(self, ticket):
        """Pozisiya bağla"""
        try:
            if not self._mt5 or not self._connected:
                return {'success': False, 'error': 'MT5 qoşulmayıb'}

            position = self._mt5.positions_get(ticket=ticket)
            if not position or len(position) == 0:
                return {'success': False, 'error': f'Pozisiya tapılmadı: {ticket}'}

            pos = position[0]
            order_type = self._mt5.ORDER_TYPE_SELL if pos.type == 0 else self._mt5.ORDER_TYPE_BUY

            request = {
                "action": self._mt5.TRADE_ACTION_DEAL,
                "symbol": pos.symbol,
                "volume": pos.volume,
                "type": order_type,
                "position": ticket,
                "price": self._mt5.symbol_info_tick(pos.symbol).bid if pos.type == 0 else self._mt5.symbol_info_tick(pos.symbol).ask,
                "deviation": 20,
                "magic": 234000,
                "comment": "DAU JARVIS Close",
                "type_time": self._mt5.ORDER_TIME_GTC,
                "type_filling": self._mt5.ORDER_FILLING_IOC,
            }

            result = self._mt5.order_send(request)

            if result and result.retcode == self._mt5.TRADE_RETCODE_DONE:
                return {
                    'success': True,
                    'ticket': ticket,
                    'price': result.price,
                    'volume': result.volume,
                    'comment': 'Pozisiya bağlandı'
                }
            else:
                error_msg = result.comment if result else 'Naməlum xəta'
                return {'success': False, 'error': f'Bağlama uğursuz: {error_msg}'}
        except Exception as e:
            return {'success': False, 'error': str(e)}

    def send_order(self, symbol, order_type, volume, sl=0, tp=0, comment=''):
        """Əmr göndər"""
        try:
            if not self._mt5 or not self._connected:
                return {'success': False, 'error': 'MT5 qoşulmayıb'}

            tick = self._mt5.symbol_info_tick(symbol)
            if not tick:
                return {'success': False, 'error': f'{symbol} qiymət alına bilmədi'}

            if order_type == 'BUY':
                price = tick.ask
                mt5_type = self._mt5.ORDER_TYPE_BUY
            else:
                price = tick.bid
                mt5_type = self._mt5.ORDER_TYPE_SELL

            request = {
                "action": self._mt5.TRADE_ACTION_DEAL,
                "symbol": symbol,
                "volume": volume,
                "type": mt5_type,
                "price": price,
                "sl": sl,
                "tp": tp,
                "deviation": 20,
                "magic": 234000,
                "comment": comment or "DAU JARVIS",
                "type_time": self._mt5.ORDER_TIME_GTC,
                "type_filling": self._mt5.ORDER_FILLING_IOC,
            }

            result = self._mt5.order_send(request)

            if result and result.retcode == self._mt5.TRADE_RETCODE_DONE:
                return {
                    'success': True,
                    'ticket': result.order,
                    'entry_price': result.price,
                    'volume': result.volume,
                    'order_type': order_type,
                    'symbol': symbol
                }
            else:
                error_msg = result.comment if result else 'Naməlum xəta'
                return {'success': False, 'error': f'Əmr uğursuz: {error_msg}'}
        except Exception as e:
            return {'success': False, 'error': str(e)}

    def modify_position(self, ticket, sl=None, tp=None):
        """Pozisiyanın SL/TP-ni dəyiş"""
        try:
            if not self._mt5 or not self._connected:
                return {'success': False, 'error': 'MT5 qoşulmayıb'}

            position = self._mt5.positions_get(ticket=ticket)
            if not position or len(position) == 0:
                return {'success': False, 'error': f'Pozisiya tapılmadı: {ticket}'}

            pos = position[0]

            request = {
                "action": self._mt5.TRADE_ACTION_SLTP,
                "symbol": pos.symbol,
                "position": ticket,
                "sl": sl if sl is not None else pos.sl,
                "tp": tp if tp is not None else pos.tp,
            }

            result = self._mt5.order_send(request)

            if result and result.retcode == self._mt5.TRADE_RETCODE_DONE:
                return {'success': True, 'ticket': ticket, 'sl': sl, 'tp': tp}
            else:
                error_msg = result.comment if result else 'Naməlum xəta'
                return {'success': False, 'error': f'Modify uğursuz: {error_msg}'}
        except Exception as e:
            return {'success': False, 'error': str(e)}

    def get_candles(self, symbol, timeframe='H1', count=100):
        """Candle data al"""
        try:
            if not self._mt5 or not self._connected:
                return []

            timeframe_map = {
                'M1': self._mt5.TIMEFRAME_M1,
                'M5': self._mt5.TIMEFRAME_M5,
                'M15': self._mt5.TIMEFRAME_M15,
                'M30': self._mt5.TIMEFRAME_M30,
                'H1': self._mt5.TIMEFRAME_H1,
                'H4': self._mt5.TIMEFRAME_H4,
                'D1': self._mt5.TIMEFRAME_D1,
                'W1': self._mt5.TIMEFRAME_W1,
            }

            tf = timeframe_map.get(timeframe, self._mt5.TIMEFRAME_H1)
            rates = self._mt5.copy_rates_from_pos(symbol, tf, 0, count)

            if rates is None:
                return []

            import pandas as pd
            df = pd.DataFrame(rates)
            df['time'] = pd.to_datetime(df['time'], unit='s')

            result = []
            for _, row in df.iterrows():
                result.append({
                    'time': row['time'].isoformat() if hasattr(row['time'], 'isoformat') else str(row['time']),
                    'open': float(row['open']),
                    'high': float(row['high']),
                    'low': float(row['low']),
                    'close': float(row['close']),
                    'tick_volume': int(row['tick_volume'])
                })

            return result
        except Exception as e:
            print(f"get_candles xətası: {e}")
            return []

    def get_history_deals(self, days=7):
        """Ticarət tarixi (deals) al"""
        try:
            if not self._mt5 or not self._connected:
                return []

            from_date = datetime.now() - timedelta(days=days)
            to_date = datetime.now()

            deals = self._mt5.history_deals_get(from_date, to_date)
            if deals is None:
                return []

            result = []
            for d in deals:
                result.append({
                    'ticket': d.ticket,
                    'order': d.order,
                    'symbol': d.symbol,
                    'type': 'BUY' if d.type == 0 else 'SELL',
                    'volume': d.volume,
                    'price': d.price,
                    'profit': d.profit,
                    'time': datetime.fromtimestamp(d.time).isoformat() if d.time else None,
                    'comment': d.comment
                })

            return result
        except Exception as e:
            print(f"get_history_deals xətası: {e}")
            return []