import pandas as pd
import numpy as np

def calculate_macd(hist: pd.DataFrame, fast: int = 12, slow: int = 26, signal: int = 9) -> pd.DataFrame:
    # Calculate MACD, Signal Line, and Histogram.
    exp1 = hist['Close'].ewm(span=fast, adjust=False).mean()
    exp2 = hist['Close'].ewm(span=slow, adjust=False).mean()
    macd = exp1 - exp2
    signal_line = macd.ewm(span=signal, adjust=False).mean()
    histogram = macd - signal_line
    hist['MACD'] = macd
    hist['MACD_signal'] = signal_line
    hist['MACD_histogram'] = histogram
    return hist

def calculate_vwap(hist: pd.DataFrame) -> pd.DataFrame:
    # Calculate Volume Weighted Average Price.
    typical_price = (hist['High'] + hist['Low'] + hist['Close']) / 3
    hist['VWAP'] = (typical_price * hist['Volume']).cumsum() / hist['Volume'].cumsum()
    return hist

def get_latest_indicators(hist: pd.DataFrame) -> dict:
    # Get latest values of indicators from hist df.
    latest = hist.iloc[-1]
    return {
        'close': latest['Close'],
        'macd': latest['MACD'],
        'macd_signal': latest['MACD_signal'],
        'vwap': latest['VWAP'],
    }