"""
Risk Manager Module - Risk Management System
Raw SQLite pattern: import database as db
"""

import database as db
import json
from datetime import datetime


class RiskManager:
    """Risk Management System"""

    def __init__(self, mt5_module, socketio=None):
        self.mt5_module = mt5_module
        self.socketio = socketio
        self._config = {
            'max_risk_per_trade': 2.0,
            'max_daily_loss': 500,
            'max_daily_trades': 10,
            'max_open_positions': 5,
            'max_drawdown_pct': 20,
        }
        self._daily_stats = {
            'date': datetime.now().date().isoformat(),
            'trades': 0,
            'pnl': 0,
            'starting_balance': 0
        }

    def configure(self, config):
        """Risk parametrlərini konfiqurasiya et"""
        try:
            if isinstance(config, dict):
                self._config.update(config)
                db.risk_log_add(
                    event_type='config_updated',
                    severity='info',
                    message='Risk parametrləri yeniləndi',
                    details=config
                )
            return True
        except Exception as e:
            print(f"configure xətası: {e}")
            return False

    def get_risk_report(self):
        """Risk hesabatı"""
        try:
            report = {
                'config': self._config,
                'daily_stats': self._daily_stats,
                'connected': self.mt5_module._connected if self.mt5_module else False
            }

            if self.mt5_module and self.mt5_module._connected:
                acc = self.mt5_module.get_account_info()
                if acc and acc.get('balance') is not None:
                    report['account'] = {
                        'balance': acc.get('balance', 0),
                        'equity': acc.get('equity', 0),
                        'margin': acc.get('margin', 0),
                        'free_margin': acc.get('free_margin', 0),
                        'profit': acc.get('profit', 0)
                    }

                    balance = acc.get('balance', 0)
                    equity = acc.get('equity', 0)
                    if balance > 0:
                        drawdown_pct = ((balance - equity) / balance) * 100
                        report['drawdown_pct'] = round(drawdown_pct, 2)
                        report['drawdown_warning'] = drawdown_pct > self._config.get('max_drawdown_pct', 20)

            return report
        except Exception as e:
            print(f"get_risk_report xətası: {e}")
            return {'config': self._config, 'daily_stats': self._daily_stats, 'error': str(e)}

    def can_trade(self, data=None):
        """Ticarətə icazə varmı yoxla"""
        try:
            # Gündəlik reset
            self._check_daily_reset()

            reasons = []

            # Gündəlik ticarət limiti
            if self._daily_stats['trades'] >= self._config.get('max_daily_trades', 10):
                reasons.append('Gündəlik ticarət limiti dolub')

            # Gündəlik zərər limiti
            if self._daily_stats['pnl'] <= -self._config.get('max_daily_loss', 500):
                reasons.append('Gündəlik zərər limiti keçilib')

            # MT5 bağlantı yoxlama
            if not self.mt5_module or not self.mt5_module._connected:
                reasons.append('MT5 qoşulmayıb')

            # Açıq pozisiyalar sayı
            if self.mt5_module and self.mt5_module._connected:
                positions = self.mt5_module.get_positions()
                pos_count = positions.get('count', 0) if isinstance(positions, dict) else 0
                if pos_count >= self._config.get('max_open_positions', 5):
                    reasons.append('Maksimum açıq pozisiya limiti dolub')

                # Drawdown yoxlama
                acc = self.mt5_module.get_account_info()
                if acc and acc.get('balance', 0) > 0:
                    equity = acc.get('equity', 0)
                    balance = acc.get('balance', 0)
                    drawdown_pct = ((balance - equity) / balance) * 100
                    if drawdown_pct > self._config.get('max_drawdown_pct', 20):
                        reasons.append(f'Drawdown limiti keçilib: {drawdown_pct:.1f}%')

            can = len(reasons) == 0

            result = {'can_trade': can, 'reasons': reasons}

            if not can:
                db.risk_log_add(
                    event_type='trade_blocked',
                    severity='warning',
                    message=f'Ticarət bloklandı: {"; ".join(reasons)}',
                    details={'reasons': reasons}
                )

            return result
        except Exception as e:
            print(f"can_trade xətası: {e}")
            return {'can_trade': False, 'reasons': [str(e)]}

    def calculate_position_size(self, symbol='XAUUSDm', sl_pips=0, risk_percent=None, account_balance=None):
        """Position size hesabla"""
        try:
            if risk_percent is None:
                risk_percent = self._config.get('max_risk_per_trade', 2.0)

            if account_balance is None:
                if self.mt5_module and self.mt5_module._connected:
                    acc = self.mt5_module.get_account_info()
                    account_balance = acc.get('balance', 0) if acc else 0
                else:
                    account_balance = 0

            if account_balance <= 0 or sl_pips <= 0:
                return {
                    'lot_size': 0.01,
                    'risk_amount': 0,
                    'symbol': symbol,
                    'error': 'Balance və ya SL pips düzgün deyil'
                }

            risk_amount = account_balance * (risk_percent / 100)

            # Sadə hesablama (1 pip = 1$ 0.01 lot üçün XAUUSD)
            pip_value = 0.01  # 0.01 lot üçün 1 pip dəyəri
            if sl_pips > 0:
                lot_size = risk_amount / (sl_pips * pip_value * 100)
            else:
                lot_size = 0.01

            lot_size = max(0.01, min(round(lot_size, 2), 10.0))

            return {
                'lot_size': lot_size,
                'risk_amount': round(risk_amount, 2),
                'risk_percent': risk_percent,
                'sl_pips': sl_pips,
                'symbol': symbol,
                'account_balance': account_balance
            }
        except Exception as e:
            print(f"calculate_position_size xətası: {e}")
            return {'lot_size': 0.01, 'error': str(e)}

    def update_equity(self, equity):
        """Equity yenilə"""
        try:
            if self._daily_stats['starting_balance'] == 0 and equity > 0:
                self._daily_stats['starting_balance'] = equity
        except Exception as e:
            print(f"update_equity xətası: {e}")

    def record_trade(self, pnl):
        """Ticarət nəticəsini qeyd et"""
        try:
            self._check_daily_reset()
            self._daily_stats['trades'] += 1
            self._daily_stats['pnl'] += pnl

            severity = 'info'
            if pnl < 0:
                severity = 'warning'
            if pnl < -50:
                severity = 'critical'

            db.risk_log_add(
                event_type='trade_recorded',
                severity=severity,
                message=f'Ticarət qeyd edildi: PnL={pnl}',
                details={'pnl': pnl, 'daily_trades': self._daily_stats['trades'], 'daily_pnl': self._daily_stats['pnl']}
            )
        except Exception as e:
            print(f"record_trade xətası: {e}")

    def _check_daily_reset(self):
        """Gündəlik statistikanı sıfırla"""
        today = datetime.now().date().isoformat()
        if self._daily_stats['date'] != today:
            self._daily_stats = {
                'date': today,
                'trades': 0,
                'pnl': 0,
                'starting_balance': 0
            }