from market_data import (
    get_candles, check_data_freshness, nigeria_time
)
from smc_analysis import market_direction
from structure_1h import analyze_1h
from entry_5m import analyze_5m


def run_analysis():
    print("\n========== XAUUSD SMC BOT ==========")
    print("Nigeria Time:", nigeria_time())

    candles4 = get_candles("4h", 100)
    candles1 = get_candles("1h", 200)
    candles5 = get_candles("5m", 100)

    datasets = [
        ("4H", "4h", candles4),
        ("1H", "1h", candles1),
        ("5M", "5m", candles5),
    ]

    for name, tf, candles in datasets:
        valid, message = check_data_freshness(tf, candles)
        print(name, ":", message)

        if not valid:
            print("FINAL SIGNAL: WAIT")
            return {"signal": "WAIT"}

    direction, reason = market_direction(candles4)
    print("\n4H DIRECTION:", direction, reason)

    if direction not in ("BULLISH", "BEARISH"):
        print("FINAL SIGNAL: WAIT")
        return {"signal": "WAIT"}

    one_hour = analyze_1h(candles1)

    if not one_hour or not one_hour.get("valid"):
        print("FINAL SIGNAL: WAIT")
        return {"signal": "WAIT"}

    trend = one_hour["trend"]
    event = one_hour["event"]

    if trend != direction:
        print("1H bai yi daidai da 4H ba.")
        print("FINAL SIGNAL: WAIT")
        return {"signal": "WAIT"}

    if not event.startswith(direction):
        print("Babu BOS/CHoCH da ya dace da direction.")
        print("FINAL SIGNAL: WAIT")
        return {"signal": "WAIT"}

    five = analyze_5m(candles5)

    if not five or not five.get("valid"):
        print("FINAL SIGNAL: WAIT")
        return {"signal": "WAIT"}

    expected = "BUY" if direction == "BULLISH" else "SELL"

    if five["signal"] != expected:
        print("5M bai tabbatar da entry ba.")
        print("FINAL SIGNAL: WAIT")
        return {"signal": "WAIT"}

    if five["stop_loss"] is None or five["take_profit"] is None:
        print("Babu SL/TP mai inganci.")
        print("FINAL SIGNAL: WAIT")
        return {"signal": "WAIT"}

    print("\nFINAL SIGNAL:", expected)

    message = (
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
        f"TIME: {nigeria_time()}\n\n"
        "Check spread and lot size. Demo test first."
    )

    return {
        "signal": expected,
        "key": f"{expected}_{five['candle_time']}",
        "message": message,
    }
