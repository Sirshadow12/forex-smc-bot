import json
import os
import urllib.request
import urllib.parse
from datetime import datetime, timedelta, timezone

from telegram_alert import send_telegram

URL = "https://biquote.io/api/calendar"
STATE_FILE = "news_state.json"
WAT = timezone(timedelta(hours=1), "WAT")


def load_state():
    try:
        with open(STATE_FILE, "r") as f:
            return json.load(f)
    except (FileNotFoundError, json.JSONDecodeError):
        return {"sent": []}


def save_state(state):
    with open(STATE_FILE, "w") as f:
        json.dump(state, f)


def get_calendar():
    now = datetime.now(timezone.utc)

    params = urllib.parse.urlencode({
        "from": (now - timedelta(days=2)).strftime("%Y-%m-%dT%H:%M:%S"),
        "to": (now + timedelta(days=7)).strftime("%Y-%m-%dT%H:%M:%S"),
        "countries": "US",
        "importance": "high",
        "limit": 200
    })

    request = urllib.request.Request(
        URL + "?" + params,
        headers={"User-Agent": "XAUUSD-SMC-Bot/1.0"}
    )

    with urllib.request.urlopen(request, timeout=25) as response:
        return json.loads(response.read().decode())


def parse_time(value):
    if not value:
        return None

    try:
        dt = datetime.fromisoformat(value.replace("Z", "+00:00"))
        if dt.tzinfo is None:
            dt = dt.replace(tzinfo=timezone.utc)
        return dt.astimezone(timezone.utc)
    except (ValueError, TypeError):
        return None


def number(value):
    try:
        if value is None or value == "":
            return None
        return float(value)
    except (ValueError, TypeError):
        return None


def get_gold_bias(name, actual, forecast):
    title = name.lower()

    if actual == forecast:
        return "NEUTRAL", "Actual ya yi daidai da forecast."

    higher = actual > forecast

    inflation = any(x in title for x in [
        "cpi", "pce", "inflation", "ppi", "price index"
    ])

    jobs = any(x in title for x in [
        "nonfarm", "non-farm", "payroll",
        "employment change", "adp employment"
    ])

    unemployment = any(x in title for x in [
        "jobless claims", "unemployment claims",
        "initial claims", "continuing claims"
    ])

    unemployment_rate = "unemployment rate" in title

    growth = any(x in title for x in [
        "gdp", "retail sales", "ism",
        "pmi", "durable goods"
    ])

    rates = any(x in title for x in [
        "interest rate", "federal funds",
        "rate decision", "policy rate"
    ])

    if inflation or jobs or growth or rates:
        usd_stronger = higher
    elif unemployment or unemployment_rate:
        usd_stronger = not higher
    else:
        return "NEUTRAL", (
            "Ba a ayyana tasirin wannan nau'in labari ba."
        )

    if usd_stronger:
        return "SELL BIAS", "Bayanan sun fi forecast karfi; USD na iya karfi, Gold na iya fuskantar matsin sauka."

    return "BUY BIAS", "Bayanan sun fi forecast rauni; USD na iya rauni, Gold na iya samun goyon bayan hawa."


def check_news_alerts():
    state = load_state()
    sent = set(state.get("sent", []))

    try:
        events = get_calendar()
        if not isinstance(events, list):
            print("NEWS ERROR: Calendar data ba list ba ne.")
            return

        now = datetime.now(timezone.utc)

        for event in events:
            if event.get("countryCode") != "US":
                continue

            if event.get("importance") != "high":
                continue

            name = event.get("name", "USD Economic News")
            event_id = str(event.get("id", ""))
            event_time = parse_time(event.get("time"))

            if not event_id or not event_time:
                continue

            wat_time = event_time.astimezone(WAT).strftime(
                "%Y-%m-%d %H:%M WAT"
            )

            actual = number(event.get("actual"))
            forecast = number(event.get("forecast"))

            # Sanarwar kafin labari
            upcoming_key = event_id + "_UPCOMING"

            if (
                upcoming_key not in sent
                and actual is None
                and timedelta(seconds=0) <= event_time - now <= timedelta(minutes=30)
            ):
                message = (
                    "XAUUSD HIGH IMPACT NEWS ALERT\n\n"
                    f"EVENT: {name}\n"
                    f"COUNTRY: USA / USD\n"
                    f"IMPACT: HIGH\n"
                    f"TIME: {wat_time}\n\n"
                    "NEWS STATUS: UPCOMING\n"
                    "GOLD BIAS: NOT YET CONFIRMED\n\n"
                    "A jira actual da forecast kafin tantance BUY/SELL bias."
                )

                if send_telegram(message):
                    sent.add(upcoming_key)

            # Sanarwar bayan fitar da actual
            result_key = event_id + "_RESULT"

            if (
                result_key not in sent
                and actual is not None
                and forecast is not None
                and timedelta(seconds=0) <= now - event_time <= timedelta(hours=2)
            ):
                bias, reason = get_gold_bias(name, actual, forecast)

                message = (
                    "XAUUSD ECONOMIC NEWS RESULT\n\n"
                    f"EVENT: {name}\n"
                    f"ACTUAL: {actual}\n"
                    f"FORECAST: {forecast}\n"
                    f"PREVIOUS: {event.get('previous')}\n"
                    f"TIME: {wat_time}\n\n"
                    f"NEWS GOLD BIAS: {bias}\n"
                    f"REASON: {reason}\n\n"
                    "WARNING: News bias ba SMC entry signal ba ne. "
                    "Tabbatar da market structure kafin trade."
                )

                if send_telegram(message):
                    sent.add(result_key)

        state["sent"] = list(sent)[-500:]
        save_state(state)
        print("NEWS CHECK: Completed")

    except Exception as error:
        print("NEWS ERROR:", error)


if __name__ == "__main__":
    check_news_alerts()
