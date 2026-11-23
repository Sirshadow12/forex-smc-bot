from market_data import (
    get_candles, check_data_freshness, nigeria_time
)
from smc_analysis import market_direction
from structure_1h import analyze_1h
from entry_5m import analyze_5m


def run_analysis():
    result = {
        "signal": "WAIT",
        "updated_at": nigeria_time() + " WAT",
        "direction": "--",
        "reason": "--",
        "trend": "--",
        "event": "--",
        "entry": None,
        "atr": None,
        "stop_loss": None,
        "take_profit": None,
        "data_4h": "NOT CHECKED",
        "data_1h": "NOT CHECKED",
        "data_5m": "NOT CHECKED",
        "news": "News alerts suna aiki ta Telegram."
    }

    print("\n========== XAUUSD SMC BOT ==========")
    print("Nigeria Time:", nigeria_time())

    candles4 = get_candles("4h", 100)
    candles1 = get_candles("1h", 200)
    candles5 = get_candles("5m", 100)

    datasets = [
        ("4h", candles4),
        ("1h", candles1),
        ("5m", candles5)
    ]

    valid_data = True

    for tf, candles in datasets:
        valid, message = check_data_freshness(tf, candles)
        result["data_" + tf] = message
        print(tf.upper(), ":", message)

        if not valid:
            valid_data = False

    if not valid_data:
        print("FINAL SIGNAL: WAIT - DATA NOT READY")
        return result

    direction, reason = market_direction(candles4)
    result["direction"] = direction
    result["reason"] = reason

    print("\n4H DIRECTION:", direction, reason)

    if direction not in ("BULLISH", "BEARISH"):
        return result

    one_hour = analyze_1h(candles1)

    if not one_hour or not one_hour.get("valid"):
        result["event"] = "1H ANALYSIS INVALID"
        return result

    trend = one_hour["trend"]
    event = one_hour["event"]

    result["trend"] = trend
    result["event"] = event

    if trend != direction:
        print("1H bai yi daidai da 4H ba.")
        return result

    if not event.startswith(direction):
        print("Babu BOS/CHoCH da ya dace da direction.")
        return result

    five = analyze_5m(candles5)

    if not five or not five.get("valid"):
        return result

    result["entry"] = five.get("close")
    result["atr"] = five.get("atr")

    expected = "BUY" if direction == "BULLISH" else "SELL"

    if five["signal"] != expected:
        print("5M bai tabbatar da entry ba.")
        return result

    if five["stop_loss"] is None or five["take_profit"] is None:
        print("Babu SL/TP mai inganci.")
        return result

    result["signal"] = expected
    result["stop_loss"] = five["stop_loss"]
    result["take_profit"] = five["take_profit"]

    result["key"] = f"{expected}_{five['candle_time']}"

    result["message"] = (
        "XAUUSD SMC SIGNAL\n\n"
        f"SIGNAL: {expected}\n"
        f"4H DIRECTION: {direction}\n"
        f"4H REASON: {reason}\n"
        f"1H TREND: {trend}\n"
        f"1H EVENT: {event}\n"
        f"5M ENTRY: {five['close']}\n"
        f"STOP LOSS: {five['stop_loss']:.3f}\n"
        f"TAKE PROFIT: {five['take_profit']:.3f}\n"
        "RISK/REWARD: 1:2\n"
        f"TIME: {nigeria_time()} WAT\n\n"
        "Check spread and lot size. Demo test first."
    )

    print("\nFINAL SIGNAL:", expected)
    return result
