from market_data import get_candles

def find_swings(candles, left=2, right=2):
    highs, lows = [], []

    for i in range(left, len(candles) - right):
        high = float(candles[i]["high"])
        low = float(candles[i]["low"])

        before = candles[i-left:i]
        after = candles[i+1:i+right+1]

        if all(high > float(c["high"]) for c in before + after):
            highs.append(high)

        if all(low < float(c["low"]) for c in before + after):
            lows.append(low)

    return highs, lows


def market_direction(candles=None):
    if candles is None:
        candles = get_candles("4h", 100)

    highs, lows = find_swings(candles)

    if len(highs) < 2 or len(lows) < 2:
        return "NEUTRAL", "Ba a samu isassun swing points ba"

    previous_high, latest_high = highs[-2:]
    previous_low, latest_low = lows[-2:]

    print("Previous Swing High:", previous_high)
    print("Latest Swing High:", latest_high)
    print("Previous Swing Low:", previous_low)
    print("Latest Swing Low:", latest_low)

    if latest_high > previous_high and latest_low > previous_low:
        return "BULLISH", "HH + HL"

    if latest_high < previous_high and latest_low < previous_low:
        return "BEARISH", "LH + LL"

    return "NEUTRAL", "Structure bai bayyana sosai ba"
