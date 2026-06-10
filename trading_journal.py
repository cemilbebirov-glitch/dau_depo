"""
DAU Dashboard - Ticarət Jurnalı
Ticarət tarixi, statistika, emosiya analizi, risk metrikaları
SQLAlchemy ilə database əməliyyatları
"""

import json
from datetime import datetime
from database import Session, generate_id, Trade, Strategy


class TradingJournal:
    """Ticarət Jurnalı - Ticarətlərin və strategiyaların idarəetməsi"""

    # ============================================
    # TİCARƏT ƏLAVƏ ET
    # ============================================

    def add_trade(self, user_id, symbol, trade_type, entry_price, lot_size,
                  stop_loss=None, take_profit=None, emotion=None,
                  confidence=None, setup_quality=None, notes=None,
                  strategy_id=None):
        """Yeni ticarət əlavə edir"""

        # RR ratio hesabla
        rr_ratio = None
        if stop_loss and take_profit and entry_price:
            risk = abs(entry_price - stop_loss)
            reward = abs(take_profit - entry_price)
            if risk > 0:
                rr_ratio = round(reward / risk, 2)

        db = Session()
        try:
            now = datetime.now().isoformat()
            trade = Trade(
                id=generate_id(),
                user_id=user_id,
                strategy_id=strategy_id,
                symbol=symbol.upper(),
                type=trade_type.lower(),
                entry_price=float(entry_price),
                lot_size=float(lot_size),
                stop_loss=float(stop_loss) if stop_loss else None,
                take_profit=float(take_profit) if take_profit else None,
                status='open',
                rr_ratio=rr_ratio,
                emotion=emotion,
                confidence=int(confidence) if confidence else None,
                setup_quality=int(setup_quality) if setup_quality else None,
                notes=notes,
                entry_time=now,
                created_at=now,
                updated_at=now,
            )
            db.add(trade)
            db.commit()

            return {'success': True, 'trade_id': trade.id, 'rr_ratio': rr_ratio}

        except Exception as e:
            db.rollback()
            return {'error': str(e)}
        finally:
            db.close()

    # ============================================
    # TİCARƏT BAĞLA
    # ============================================

    def close_trade(self, trade_id, user_id, exit_price, emotion=None, notes=None, lessons=None):
        """Açıq ticarəti bağlayır və PnL hesablayır"""
        db = Session()
        try:
            trade = db.query(Trade).filter_by(id=trade_id, user_id=user_id).first()

            if not trade:
                return {'error': 'Ticarət tapılmadı'}

            if trade.status != 'open':
                return {'error': 'Bu ticarət artıq bağlıdır'}

            exit_price = float(exit_price)
            trade.exit_price = exit_price

            # PnL hesabla
            if trade.type == 'buy':
                pnl = (exit_price - trade.entry_price) * trade.lot_size
            else:
                pnl = (trade.entry_price - exit_price) * trade.lot_size

            trade.pnl = round(pnl - trade.commission - trade.swap, 2)

            # Pips hesabla
            if trade.type == 'buy':
                pips = (exit_price - trade.entry_price)
            else:
                pips = (trade.entry_price - exit_price)
            trade.pips = round(pips, 2)

            # Müddət hesabla
            entry_dt = datetime.fromisoformat(trade.entry_time)
            exit_dt = datetime.now()
            trade.duration = int((exit_dt - entry_dt).total_seconds() / 60)

            trade.exit_time = exit_dt.isoformat()
            trade.status = 'closed'

            if emotion:
                trade.emotion = emotion
            if notes:
                trade.notes = notes
            if lessons:
                trade.lessons = lessons

            trade.updated_at = datetime.now().isoformat()

            db.commit()

            return {
                'success': True,
                'trade_id': trade.id,
                'pnl': trade.pnl,
                'pips': trade.pips,
                'duration': trade.duration,
            }

        except Exception as e:
            db.rollback()
            return {'error': str(e)}
        finally:
            db.close()

    # ============================================
    # TİCARƏT YENILƏ
    # ============================================

    def update_trade(self, trade_id, user_id, **kwargs):
        """Ticarəti yeniləyir"""
        db = Session()
        try:
            trade = db.query(Trade).filter_by(id=trade_id, user_id=user_id).first()

            if not trade:
                return {'error': 'Ticarət tapılmadı'}

            allowed_fields = ['stop_loss', 'take_profit', 'emotion', 'confidence',
                              'setup_quality', 'notes', 'lessons', 'screenshot',
                              'commission', 'swap']

            for field in allowed_fields:
                if field in kwargs and kwargs[field] is not None:
                    setattr(trade, field, kwargs[field])

            # RR ratio yenidən hesabla
            if trade.stop_loss and trade.take_profit and trade.entry_price:
                risk = abs(trade.entry_price - trade.stop_loss)
                reward = abs(trade.take_profit - trade.entry_price)
                if risk > 0:
                    trade.rr_ratio = round(reward / risk, 2)

            trade.updated_at = datetime.now().isoformat()
            db.commit()

            return {'success': True}

        except Exception as e:
            db.rollback()
            return {'error': str(e)}
        finally:
            db.close()

    # ============================================
    # TİCARƏT SİL
    # ============================================

    def delete_trade(self, trade_id, user_id):
        """Ticarəti silir"""
        db = Session()
        try:
            trade = db.query(Trade).filter_by(id=trade_id, user_id=user_id).first()

            if not trade:
                return {'error': 'Ticarət tapılmadı'}

            db.delete(trade)
            db.commit()
            return {'success': True, 'message': 'Ticarət silindi'}

        except Exception as e:
            db.rollback()
            return {'error': str(e)}
        finally:
            db.close()

    # ============================================
    # TİCARƏT SİYAHISI
    # ============================================

    def get_trades(self, user_id, status=None, symbol=None, limit=100):
        """Ticarətlərin siyahısını qaytarır"""
        db = Session()
        try:
            q = db.query(Trade).filter_by(user_id=user_id)

            if status:
                q = q.filter_by(status=status)

            if symbol:
                q = q.filter_by(symbol=symbol.upper())

            trades = q.order_by(Trade.entry_time.desc()).limit(limit).all()

            return [self._trade_to_dict(t) for t in trades]

        finally:
            db.close()

    # ============================================
    # TİCARƏT OXU
    # ============================================

    def get_trade(self, trade_id, user_id):
        """Bir ticarətin detallarını qaytarır"""
        db = Session()
        try:
            trade = db.query(Trade).filter_by(id=trade_id, user_id=user_id).first()
            return self._trade_to_dict(trade) if trade else None
        finally:
            db.close()

    # ============================================
    # STATİSTİKA
    # ============================================

    def get_stats(self, user_id):
        """Ticarət statistikasını hesablayır - yalnız bağlı ticarətlərdən"""
        db = Session()
        try:
            closed_trades = db.query(Trade).filter_by(
                user_id=user_id, status='closed'
            ).all()

            if not closed_trades:
                return {
                    'total_trades': 0,
                    'win_rate': 0,
                    'average_rr': 0,
                    'total_pnl': 0,
                    'best_setup': '-',
                    'worst_setup': '-',
                    'average_win': 0,
                    'average_loss': 0,
                    'max_consecutive_wins': 0,
                    'max_consecutive_losses': 0,
                    'profit_factor': 0,
                }

            wins = [t for t in closed_trades if (t.pnl or 0) > 0]
            losses = [t for t in closed_trades if (t.pnl or 0) <= 0]

            total_pnl = sum(t.pnl or 0 for t in closed_trades)
            average_win = sum(t.pnl for t in wins) / len(wins) if wins else 0
            average_loss = abs(sum(t.pnl for t in losses) / len(losses)) if losses else 0

            # Emosiya analizi
            emotion_stats = {}
            for t in closed_trades:
                if t.emotion:
                    if t.emotion not in emotion_stats:
                        emotion_stats[t.emotion] = {'count': 0, 'total_pnl': 0}
                    emotion_stats[t.emotion]['count'] += 1
                    emotion_stats[t.emotion]['total_pnl'] += t.pnl or 0

            best_setup = '-'
            worst_setup = '-'
            best_avg = -float('inf')
            worst_avg = float('inf')

            for emotion, stats in emotion_stats.items():
                avg = stats['total_pnl'] / stats['count']
                if avg > best_avg:
                    best_avg = avg
                    best_setup = emotion
                if avg < worst_avg:
                    worst_avg = avg
                    worst_setup = emotion

            # Ardıcıl qalb/məğlubiyyət
            pnls = [(t.pnl or 0) > 0 for t in closed_trades]
            max_consecutive_wins = self._max_consecutive(pnls, True)
            max_consecutive_losses = self._max_consecutive(pnls, False)

            # Profit Factor
            total_wins = sum(t.pnl for t in wins) if wins else 0
            total_losses = abs(sum(t.pnl for t in losses)) if losses else 0
            profit_factor = round(total_wins / total_losses, 2) if total_losses > 0 else 0

            # Ortalama RR
            rr_values = [t.rr_ratio for t in closed_trades if t.rr_ratio]
            average_rr = round(sum(rr_values) / len(rr_values), 2) if rr_values else 0

            return {
                'total_trades': len(closed_trades),
                'win_rate': round(len(wins) / len(closed_trades) * 100, 1),
                'average_rr': average_rr,
                'total_pnl': round(total_pnl, 2),
                'best_setup': best_setup,
                'worst_setup': worst_setup,
                'average_win': round(average_win, 2),
                'average_loss': round(average_loss, 2),
                'max_consecutive_wins': max_consecutive_wins,
                'max_consecutive_losses': max_consecutive_losses,
                'profit_factor': profit_factor,
                'emotion_stats': emotion_stats,
            }

        finally:
            db.close()

    # ============================================
    # STRATEQİYALAR
    # ============================================

    def add_strategy(self, user_id, name, description=None, strategy_type=None,
                     rules=None, risk_per_trade=None):
        """Yeni strategiya əlavə edir"""
        db = Session()
        try:
            now = datetime.now().isoformat()
            strategy = Strategy(
                id=generate_id(),
                user_id=user_id,
                name=name,
                description=description,
                type=strategy_type,
                rules=json.dumps(rules, ensure_ascii=False) if rules else None,
                risk_per_trade=float(risk_per_trade) if risk_per_trade else None,
                is_active=1,
                created_at=now,
                updated_at=now,
            )
            db.add(strategy)
            db.commit()

            return {'success': True, 'strategy_id': strategy.id}

        except Exception as e:
            db.rollback()
            return {'error': str(e)}
        finally:
            db.close()

    def get_strategies(self, user_id, active_only=False):
        """Strategiyaların siyahısını qaytarır"""
        db = Session()
        try:
            q = db.query(Strategy).filter_by(user_id=user_id)

            if active_only:
                q = q.filter_by(is_active=1)

            strategies = q.order_by(Strategy.created_at.desc()).all()

            result = []
            for s in strategies:
                s_dict = self._strategy_to_dict(s)
                # Strategiya üzrə ticarət sayı
                trade_count = db.query(Trade).filter_by(strategy_id=s.id).count()
                s_dict['trade_count'] = trade_count
                result.append(s_dict)

            return result

        finally:
            db.close()

    def toggle_strategy(self, strategy_id, user_id):
        """Strategiyanı aktiv/deaktiv edir"""
        db = Session()
        try:
            strategy = db.query(Strategy).filter_by(id=strategy_id, user_id=user_id).first()

            if not strategy:
                return {'error': 'Strategiya tapılmadı'}

            strategy.is_active = 0 if strategy.is_active else 1
            strategy.updated_at = datetime.now().isoformat()
            db.commit()

            return {'success': True, 'is_active': bool(strategy.is_active)}

        except Exception as e:
            db.rollback()
            return {'error': str(e)}
        finally:
            db.close()

    def delete_strategy(self, strategy_id, user_id):
        """Strategiyanı silir"""
        db = Session()
        try:
            strategy = db.query(Strategy).filter_by(id=strategy_id, user_id=user_id).first()

            if not strategy:
                return {'error': 'Strategiya tapılmadı'}

            db.delete(strategy)
            db.commit()
            return {'success': True}

        except Exception as e:
            db.rollback()
            return {'error': str(e)}
        finally:
            db.close()

    # ============================================
    # SİMVOL STATİSTİKASI
    # ============================================

    def get_symbol_stats(self, user_id):
        """Simvollar üzrə statistika"""
        db = Session()
        try:
            from sqlalchemy import func

            results = db.query(
                Trade.symbol,
                func.count(Trade.id).label('count'),
                func.avg(Trade.pnl).label('avg_pnl'),
                func.sum(Trade.pnl).label('total_pnl'),
            ).filter_by(user_id=user_id, status='closed').group_by(Trade.symbol).all()

            return [
                {
                    'symbol': row.symbol,
                    'count': row.count,
                    'avg_pnl': round(row.avg_pnl, 2) if row.avg_pnl else 0,
                    'total_pnl': round(row.total_pnl, 2) if row.total_pnl else 0,
                }
                for row in results
            ]

        finally:
            db.close()

    # ============================================
    # KÖMƏKÇİ
    # ============================================

    def _trade_to_dict(self, trade):
        """Trade obyektini dictionary-ə çevirir"""
        if trade is None:
            return None
        return {
            'id': trade.id,
            'user_id': trade.user_id,
            'strategy_id': trade.strategy_id,
            'symbol': trade.symbol,
            'type': trade.type,
            'entry_price': trade.entry_price,
            'exit_price': trade.exit_price,
            'lot_size': trade.lot_size,
            'stop_loss': trade.stop_loss,
            'take_profit': trade.take_profit,
            'status': trade.status,
            'pnl': trade.pnl,
            'pips': trade.pips,
            'commission': trade.commission,
            'swap': trade.swap,
            'rr_ratio': trade.rr_ratio,
            'emotion': trade.emotion,
            'confidence': trade.confidence,
            'setup_quality': trade.setup_quality,
            'screenshot': trade.screenshot,
            'notes': trade.notes,
            'lessons': trade.lessons,
            'entry_time': trade.entry_time,
            'exit_time': trade.exit_time,
            'duration': trade.duration,
            'created_at': trade.created_at,
            'updated_at': trade.updated_at,
        }

    def _strategy_to_dict(self, strategy):
        """Strategy obyektini dictionary-ə çevirir"""
        return {
            'id': strategy.id,
            'user_id': strategy.user_id,
            'name': strategy.name,
            'description': strategy.description,
            'type': strategy.type,
            'rules': strategy.rules,
            'risk_per_trade': strategy.risk_per_trade,
            'is_active': strategy.is_active,
            'created_at': strategy.created_at,
            'updated_at': strategy.updated_at,
        }

    def _max_consecutive(self, bool_list, target=True):
        """Ardıcıl True və ya False sayını hesablayır"""
        max_count = 0
        current = 0
        for val in bool_list:
            if val == target:
                current += 1
                max_count = max(max_count, current)
            else:
                current = 0
        return max_count