from market_data import get_candles


def get_swing_points(candles, left=2, right=2):
    highs = []
    lows = []

    for i in range(left, len(candles) - right):
        high = float(candles[i]["high"])
        low = float(candles[i]["low"])

        before = candles[i-left:i]
        after = candles[i+1:i+right+1]

        if all(high > float(c["high"]) for c in before + after):
            highs.append({"index": i, "price": high})

        if all(low < float(c["low"]) for c in before + after):
            lows.append({"index": i, "price": low})

    return highs, lows


def analyze_1h(candles=None, max_event_age=12):
    if candles is None:
        candles = get_candles("1h", 200)

    if len(candles) < 30:
        return {"valid": False, "error": "Not enough candles"}

    highs, lows = get_swing_points(candles)

    if len(highs) < 2 or len(lows) < 2:
        return {"valid": False, "error": "Not enough swings"}

    previous_high, latest_high = highs[-2:]
    previous_low, latest_low = lows[-2:]

    if (latest_high["price"] > previous_high["price"]
            and latest_low["price"] > previous_low["price"]):
        trend = "BULLISH"
    elif (latest_high["price"] < previous_high["price"]
            and latest_low["price"] < previous_low["price"]):
        trend = "BEARISH"
    else:
        trend = "NEUTRAL"

    events = []

    # Neman karyewar swing high ta hanyar candle close
    for swing in highs:
        level = swing["price"]
        start = swing["index"] + 3

        for i in range(start, len(candles)):
            previous_close = float(candles[i-1]["close"])
            current_close = float(candles[i]["close"])

            if previous_close <= level and current_close > level:
                events.append({
                    "index": i,
                    "direction": "BULLISH",
                    "level": level
                })
                break

    # Neman karyewar swing low ta hanyar candle close
    for swing in lows:
        level = swing["price"]
        start = swing["index"] + 3

        for i in range(start, len(candles)):
            previous_close = float(candles[i-1]["close"])
            current_close = float(candles[i]["close"])

            if previous_close >= level and current_close < level:
                events.append({
                    "index": i,
                    "direction": "BEARISH",
                    "level": level
                })
                break

    events.sort(key=lambda x: x["index"])

    event = "NO CONFIRMED BREAK"
    event_age = None
    broken_level = None

    if events:
        latest_event = events[-1]
        age = len(candles) - 1 - latest_event["index"]

        if age <= max_event_age:
            event_age = age
            broken_level = latest_event["level"]

            if latest_event["direction"] == "BULLISH":
                event = (
                    "BULLISH BOS" if trend == "BULLISH"
                    else "BULLISH CHoCH"
                )
            else:
                event = (
                    "BEARISH BOS" if trend == "BEARISH"
                    else "BEARISH CHoCH"
                )

    last_close = float(candles[-1]["close"])

    result = {
        "valid": True,
        "trend": trend,
        "event": event,
        "previous_high": previous_high["price"],
        "latest_high": latest_high["price"],
        "previous_low": previous_low["price"],
        "latest_low": latest_low["price"],
        "last_close": last_close,
        "event_age": event_age,
        "broken_level": broken_level,
    }

    print("\n========== XAUUSD 1H ==========")
    print("Trend:", trend)
    print("Structure Event:", event)
    print("Last Close:", last_close)

    if event_age is not None:
        print("Break Age (1H candles):", event_age)
        print("Broken Level:", broken_level)

    return result
