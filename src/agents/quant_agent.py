"""
Quant Agent - Triple-barrier + trend analysis based on Marcos Lopez de Prado's
"Advances in Financial Machine Learning".

Provides objective, rules-based signals to complement LLM analysis.
"""

import pandas as pd
import numpy as np
from typing import Dict, Any, List, Optional
from datetime import datetime, timedelta


class QuantAgent:
    """Triple-barrier + trend analysis based on Lopez de Prado."""

    def analyze(self, symbol: str, investment_period: str,
                phase1_data: Dict[str, Any]) -> str:
        """
        Run quant analysis and return markdown output for Trading Plan.

        Args:
            symbol: Stock ticker
            investment_period: short+, short, medium, long
            phase1_data: Output from Phase 1 (technical, market, etc.)

        Returns:
            Markdown formatted quant analysis
        """
        try:
            # Fetch OHLCV data
            ohlcv = self._fetch_ohlcv(symbol)
            if ohlcv is None or len(ohlcv) < 50:
                return self._format_no_data(symbol)

            # Calculate indicators
            atr = self._calculate_atr(ohlcv, period=14)
            volatility = self._calculate_volatility(ohlcv, period=20)
            adx = self._calculate_adx(ohlcv, period=14)
            support_resistance = self._find_support_resistance(ohlcv)

            # Triple-barrier
            triple_barrier = self._triple_barrier(ohlcv, atr, investment_period)

            # Trend regime
            trend = self._analyze_trend(ohlcv, adx)

            # Volatility regime
            vol_regime = self._analyze_volatility(volatility, atr)

            # Meta-labels
            meta_label = self._meta_label(ohlcv, trend, vol_regime)

            # Format output
            return self._format_output(
                symbol, triple_barrier, trend, vol_regime,
                support_resistance, meta_label, ohlcv
            )

        except Exception as e:
            return f"## Quant Analysis\n\n⚠️ Analysis failed: {str(e)}"

    def _fetch_ohlcv(self, symbol: str) -> Optional[pd.DataFrame]:
        """Fetch OHLCV data from Yahoo Finance."""
        try:
            from ..utils.yfinance_compat import YahooFinanceCompat
            yf = YahooFinanceCompat(symbol)
            df = yf.get_history(period='1y', interval='1d')
            if df is not None and len(df) > 0:
                return df
        except Exception as e:
            print(f"WARNING: Could not fetch OHLCV for {symbol}: {e}")

        # Fallback to yfinance
        try:
            import yfinance as yf
            ticker = yf.Ticker(symbol)
            df = ticker.history(period='1y', interval='1d')
            if df is not None and len(df) > 0:
                return df[['Open', 'High', 'Low', 'Close', 'Volume']]
        except Exception as e:
            print(f"WARNING: yfinance fallback failed for {symbol}: {e}")

        return None

    def _calculate_atr(self, df: pd.DataFrame, period: int = 14) -> pd.Series:
        """Calculate Average True Range."""
        high = df['High']
        low = df['Low']
        close = df['Close']

        tr1 = high - low
        tr2 = abs(high - close.shift())
        tr3 = abs(low - close.shift())

        tr = pd.concat([tr1, tr2, tr3], axis=1).max(axis=1)
        atr = tr.rolling(window=period).mean()
        return atr

    def _calculate_volatility(self, df: pd.DataFrame, period: int = 20) -> pd.Series:
        """Calculate historical volatility (annualized)."""
        returns = df['Close'].pct_change()
        volatility = returns.rolling(window=period).std() * np.sqrt(252)
        return volatility

    def _calculate_adx(self, df: pd.DataFrame, period: int = 14) -> pd.DataFrame:
        """Calculate Average Directional Index (ADX)."""
        high = df['High']
        low = df['Low']
        close = df['Close']

        # True Range
        tr = pd.concat([
            high - low,
            abs(high - close.shift()),
            abs(low - close.shift())
        ], axis=1).max(axis=1)

        # Directional Movement
        up_move = high - high.shift()
        down_move = low.shift() - low

        plus_dm = pd.Series(np.where((up_move > down_move) & (up_move > 0), up_move, 0),
                           index=df.index)
        minus_dm = pd.Series(np.where((down_move > up_move) & (down_move > 0), down_move, 0),
                            index=df.index)

        # Smoothed averages
        atr_smooth = tr.rolling(window=period).mean()
        plus_di = 100 * (plus_dm.rolling(window=period).mean() / atr_smooth)
        minus_di = 100 * (minus_dm.rolling(window=period).mean() / atr_smooth)

        # ADX
        dx = 100 * abs(plus_di - minus_di) / (plus_di + minus_di)
        adx = dx.rolling(window=period).mean()

        return pd.DataFrame({
            'adx': adx,
            'plus_di': plus_di,
            'minus_di': minus_di
        })

    def _find_support_resistance(self, df: pd.DataFrame) -> Dict[str, List]:
        """Find support and resistance levels using swing highs/lows."""
        close = df['Close'].values
        high = df['High'].values
        low = df['Low'].values

        # Find swing highs and lows (simple implementation)
        lookback = 5
        swing_highs = []
        swing_lows = []

        for i in range(lookback, len(df) - lookback):
            if high[i] == max(high[i-lookback:i+lookback+1]):
                swing_highs.append(high[i])
            if low[i] == min(low[i-lookback:i+lookback+1]):
                swing_lows.append(low[i])

        # Get unique levels and sort
        resistance = sorted(set(swing_highs), reverse=True)[:3]
        support = sorted(set(swing_lows))[:3]

        # Ensure current price is considered
        current_price = close[-1]

        # Filter: support below price, resistance above
        support = [s for s in support if s < current_price][-3:]
        resistance = [r for r in resistance if r > current_price][:3]

        return {
            'support': support if support else [current_price * 0.95],
            'resistance': resistance if resistance else [current_price * 1.05]
        }

    def _triple_barrier(self, df: pd.DataFrame, atr: pd.Series,
                        investment_period: str) -> Dict[str, Any]:
        """Apply triple-barrier method from Lopez de Prado."""
        current_price = df['Close'].iloc[-1]
        current_atr = atr.iloc[-1] if not pd.isna(atr.iloc[-1]) else current_price * 0.02

        # Period multipliers
        period_days = {
            'short+': 7,
            'short': 21,
            'medium': 45,
            'long': 90
        }
        days = period_days.get(investment_period, 45)

        # Triple-barrier levels (based on ATR)
        profit_target_mult = 3.0  # 3x ATR for profit target
        stop_loss_mult = 1.5      # 1.5x ATR for stop loss

        profit_target = current_price + (current_atr * profit_target_mult)
        stop_loss = current_price - (current_atr * stop_loss_mult)

        profit_target_pct = ((profit_target - current_price) / current_price) * 100
        stop_loss_pct = ((stop_loss - current_price) / current_price) * 100

        risk_reward = abs(profit_target_pct / stop_loss_pct) if stop_loss_pct != 0 else 0

        # Simple trend-based entry signal
        recent_returns = df['Close'].pct_change().tail(10).mean()
        if recent_returns > 0.005:
            entry_signal = "long"
        elif recent_returns < -0.005:
            entry_signal = "short"
        else:
            entry_signal = "neutral"

        return {
            'entry_signal': entry_signal,
            'entry_price': round(current_price, 2),
            'profit_target': round(profit_target, 2),
            'profit_target_pct': round(profit_target_pct, 1),
            'stop_loss': round(stop_loss, 2),
            'stop_loss_pct': round(stop_loss_pct, 1),
            'time_barrier_days': days,
            'risk_reward_ratio': round(risk_reward, 2),
            'atr': round(current_atr, 2)
        }

    def _analyze_trend(self, df: pd.DataFrame, adx: pd.DataFrame) -> Dict[str, Any]:
        """Analyze trend regime."""
        current_adx = adx['adx'].iloc[-1] if not pd.isna(adx['adx'].iloc[-1]) else 20
        plus_di = adx['plus_di'].iloc[-1] if not pd.isna(adx['plus_di'].iloc[-1]) else 25
        minus_di = adx['minus_di'].iloc[-1] if not pd.isna(adx['minus_di'].iloc[-1]) else 25

        # Trend regime
        if current_adx > 30:
            if plus_di > minus_di:
                regime = "trending_up"
            else:
                regime = "trending_down"
        elif current_adx > 20:
            regime = "weak_trend"
        else:
            regime = "ranging"

        # Trend strength (0-1)
        strength = min(current_adx / 50, 1.0)

        # Momentum score (based on recent returns)
        returns = df['Close'].pct_change().tail(20)
        momentum = (returns.mean() / returns.std()) if returns.std() > 0 else 0
        momentum_score = min(max((momentum + 2) / 4, 0), 1)

        return {
            'regime': regime,
            'adx': round(current_adx, 1),
            'trend_strength': round(strength, 2),
            'plus_di': round(plus_di, 1),
            'minus_di': round(minus_di, 1),
            'momentum_score': round(momentum_score, 2)
        }

    def _analyze_volatility(self, volatility: pd.Series, atr: pd.Series) -> Dict[str, Any]:
        """Analyze volatility regime."""
        current_vol = volatility.iloc[-1] if not pd.isna(volatility.iloc[-1]) else 0.2
        historical_vol = volatility.mean()
        vol_percentile = (volatility.rank(pct=True).iloc[-1] * 100) if not pd.isna(volatility.iloc[-1]) else 50

        # Volatility regime
        if vol_percentile > 75:
            regime = "expanding"
        elif vol_percentile < 25:
            regime = "contracting"
        else:
            regime = "normal"

        current_atr = atr.iloc[-1] if not pd.isna(atr.iloc[-1]) else 0
        last_close = 100  # placeholder, will be overridden

        return {
            'current_volatility': round(current_vol, 2),
            'historical_avg': round(historical_vol, 2),
            'regime': regime,
            'volatility_percentile': round(vol_percentile, 0),
            'atr_14': round(current_atr, 2)
        }

    def _meta_label(self, df: pd.DataFrame, trend: Dict, vol_regime: Dict) -> Dict[str, Any]:
        """Generate meta-label prediction."""
        # Simple scoring based on trend and volatility
        score = 0

        # Trend contribution
        if trend['regime'] in ['trending_up']:
            score += 0.3
        elif trend['regime'] in ['trending_down']:
            score -= 0.3

        # Momentum contribution
        score += (trend['momentum_score'] - 0.5) * 0.4

        # Volatility contribution (high vol = less confident)
        if vol_regime['regime'] == 'expanding':
            score -= 0.1

        # Normalize to confidence (0-1)
        confidence = min(max((score + 0.5), 0), 1)

        # Prediction
        if score > 0.1:
            prediction = "buy"
        elif score < -0.1:
            prediction = "sell"
        else:
            prediction = "hold"

        return {
            'prediction': prediction,
            'confidence': round(confidence, 2),
            'score': round(score, 2)
        }

    def _format_no_data(self, symbol: str) -> str:
        """Format output when no data is available."""
        return f"""## Quant Analysis - {symbol}

⚠️ **Insufficient Data**

Unable to fetch OHLCV data for {symbol}. Quant analysis requires:
- Historical price data (Open, High, Low, Close, Volume)
- Minimum 50 trading days of data

**Possible reasons:**
- Symbol may be delisted or invalid
- Network connectivity issues
- Yahoo Finance API limitations

**Recommendation:** Proceed with LLM-based analysis only.
"""

    def _format_output(self, symbol: str, triple_barrier: Dict, trend: Dict,
                      vol_regime: Dict, sr_levels: Dict, meta_label: Dict,
                      df: pd.DataFrame) -> str:
        """Format quant analysis as markdown."""
        current_price = df['Close'].iloc[-1]

        # Trend emoji
        trend_emoji = {
            'trending_up': '📈',
            'trending_down': '📉',
            'weak_trend': '➡️',
            'ranging': '↔️'
        }.get(trend['regime'], '❓')

        # Volatility emoji
        vol_emoji = {
            'expanding': '⚠️',
            'contracting': '📉',
            'normal': '✅'
        }.get(vol_regime['regime'], '❓')

        # Signal emoji
        signal_emoji = {
            'long': '🟢',
            'short': '🔴',
            'neutral': '🟡'
        }.get(triple_barrier['entry_signal'], '❓')

        # Meta-label emoji
        meta_emoji = {
            'buy': '🟢',
            'sell': '🔴',
            'hold': '🟡'
        }.get(meta_label['prediction'], '❓')

        # Format support/resistance
        support_str = ' | '.join([f"${s:.2f}" for s in sr_levels['support']])
        resistance_str = ' | '.join([f"${r:.2f}" for r in sr_levels['resistance']])

        md = f"""## Quant Analysis - {symbol}

### Triple-Barrier Method
| Parameter | Value |
|-----------|-------|
| Entry Signal | {signal_emoji} **{triple_barrier['entry_signal'].upper()}** |
| Entry Price | ${triple_barrier['entry_price']:.2f} |
| Profit Target | ${triple_barrier['profit_target']:.2f} (+{triple_barrier['profit_target_pct']:.1f}%) |
| Stop Loss | ${triple_barrier['stop_loss']:.2f} ({triple_barrier['stop_loss_pct']:.1f}%) |
| Time Barrier | {triple_barrier['time_barrier_days']} days |
| Risk/Reward | **{triple_barrier['risk_reward_ratio']:.2f}** |
| ATR (14) | ${triple_barrier['atr']:.2f} |

### Trend Analysis
| Metric | Value |
|--------|-------|
| Regime | {trend_emoji} **{trend['regime'].replace('_', ' ').title()}** |
| ADX | {trend['adx']:.1f} |
| Trend Strength | {trend['trend_strength']:.0%} |
| +DI / -DI | {trend['plus_di']:.1f} / {trend['minus_di']:.1f} |
| Momentum | {trend['momentum_score']:.0%} |

### Volatility Regime
| Metric | Value |
|--------|-------|
| Regime | {vol_emoji} **{vol_regime['regime'].title()}** |
| Current Vol | {vol_regime['current_volatility']:.0%} |
| Historical Avg | {vol_regime['historical_avg']:.0%} |
| Percentile | {vol_regime['volatility_percentile']:.0f}th |

### Support / Resistance
| Type | Levels |
|------|--------|
| Resistance | {resistance_str} |
| Current | **${current_price:.2f}** |
| Support | {support_str} |

### Meta-Label
| Metric | Value |
|--------|-------|
| Prediction | {meta_emoji} **{meta_label['prediction'].upper()}** |
| Confidence | {meta_label['confidence']:.0%} |
| Score | {meta_label['score']:.2f} |

---
*Based on Marcos Lopez de Prado's Triple-Barrier Method*
"""
        return md
