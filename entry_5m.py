from market_data import get_candles


def calculate_atr(candles, period=14):
    if len(candles) < period + 1:
        return None

    true_ranges = []

    for i in range(1, len(candles)):
        high = float(candles[i]["high"])
        low = float(candles[i]["low"])
        previous_close = float(candles[i-1]["close"])

        tr = max(
            high - low,
            abs(high - previous_close),
            abs(low - previous_close)
        )
        true_ranges.append(tr)

    return sum(true_ranges[-period:]) / period


def analyze_5m(candles=None):
    if candles is None:
        candles = get_candles("5m", 100)

    if len(candles) < 20:
        return {"valid": False, "signal": "WAIT"}

    last = candles[-1]
    previous = candles[-2]

    o = float(last["open"])
    c = float(last["close"])

    po = float(previous["open"])
    pc = float(previous["close"])
    ph = float(previous["high"])
    pl = float(previous["low"])

    bullish_engulfing = (
        c > o and pc < po and o <= pc and c >= po
    )

    bearish_engulfing = (
        c < o and pc > po and o >= pc and c <= po
    )

    bullish_break = c > ph
    bearish_break = c < pl

    bullish_confirm = c > o and (
        bullish_engulfing or bullish_break
    )

    bearish_confirm = c < o and (
        bearish_engulfing or bearish_break
    )

    if bullish_confirm:
        signal = "BUY"
    elif bearish_confirm:
        signal = "SELL"
    else:
        signal = "WAIT"

    atr = calculate_atr(candles)

    stop_loss = None
    take_profit = None

    if signal != "WAIT" and atr is not None and atr > 0:
        sl_distance = atr * 1.5
        tp_distance = atr * 3.0

        if signal == "BUY":
            stop_loss = c - sl_distance
            take_profit = c + tp_distance
        else:
            stop_loss = c + sl_distance
            take_profit = c - tp_distance

    else:
        signal = "WAIT"

    print("\n========== XAUUSD 5M ==========")
    print("Last Close:", c)
    print("ATR:", atr)
    print("5M SIGNAL:", signal)

    if signal != "WAIT":
        print("STOP LOSS:", round(stop_loss, 3))
        print("TAKE PROFIT:", round(take_profit, 3))

    return {
        "valid": True,
        "signal": signal,
        "close": c,
        "atr": atr,
        "stop_loss": stop_loss,
        "take_profit": take_profit,
        "candle_time": last["openTime"],
    }
