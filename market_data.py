import urllib.request
import json
from datetime import datetime, timezone, timedelta

WAT = timezone(timedelta(hours=1))

TIMEFRAME_SECONDS = {
    "5m": 300,
    "1h": 3600,
    "4h": 14400,
}

MAX_DATA_AGE = 15 * 60  # minti 15


def parse_candle_time(value):
    if isinstance(value, (int, float)):
        timestamp = value / 1000 if value > 10**12 else value
        return datetime.fromtimestamp(timestamp, timezone.utc)

    return datetime.fromisoformat(
        value.replace("Z", "+00:00")
    ).astimezone(timezone.utc)


def get_candles(timeframe, limit=100):
    if timeframe not in TIMEFRAME_SECONDS:
        raise ValueError(f"Unsupported timeframe: {timeframe}")

    url = (
        f"https://biquote.io/api/XAUUSD/ohlc"
        f"?interval={timeframe}&limit={limit}"
    )

    req = urllib.request.Request(
        url,
        headers={"User-Agent": "Mozilla/5.0"}
    )

    with urllib.request.urlopen(req, timeout=20) as response:
        data = json.loads(response.read())

    bars = data.get("bars", [])

    now = datetime.now(timezone.utc)
    candles = []

    for candle in bars:
        if candle.get("isOpen", False):
            continue

        try:
            candle_time = parse_candle_time(candle["openTime"])
            close_time = candle_time + timedelta(
                seconds=TIMEFRAME_SECONDS[timeframe]
            )

            if close_time <= now:
                candles.append(candle)

        except (KeyError, TypeError, ValueError):
            continue

    candles.sort(key=lambda c: parse_candle_time(c["openTime"]))

    return candles


def check_data_freshness(timeframe, candles):
    if not candles:
        return False, "Babu closed candles"

    last = candles[-1]
    candle_time = parse_candle_time(last["openTime"])

    interval = TIMEFRAME_SECONDS[timeframe]
    close_time = candle_time.timestamp() + interval

    now = datetime.now(timezone.utc).timestamp()

    # Lokacin rufewar candle na ƙarshe da ake tsammani
    expected_close = (int(now) // interval) * interval

    # Kada a karɓi candle na gaba ko wanda bai rufe ba
    if close_time > now:
        return False, "Candle bai rufe ba tukuna"

    # Idan candle ya makara fiye da minti 10, a ƙi data
    delay = expected_close - close_time

    if delay > 600:
        return False, f"API data ya makara: {int(delay)} seconds"

    return True, "Data ya yi daidai da lokacin kasuwa"

def nigeria_time():
    return datetime.now(WAT).strftime("%Y-%m-%d %H:%M:%S")


if __name__ == "__main__":
    print("XAUUSD DATA CHECK")
    print("Nigeria Time:", nigeria_time())

    for tf in ["4h", "1h", "5m"]:
        print("\nTIMEFRAME:", tf)

        try:
            candles = get_candles(tf, 10)
            valid, message = check_data_freshness(tf, candles)

            print("Closed candles:", len(candles))
            print("Freshness:", message)

            if candles:
                last = candles[-1]
                dt = parse_candle_time(last["openTime"])

                print("Last candle WAT:", dt.astimezone(WAT))
                print("Last Close:", last["close"])

            print("SAFE TO ANALYZE:", valid)

        except Exception as error:
            print("ERROR:", error)
            print("SAFE TO ANALYZE: False")
