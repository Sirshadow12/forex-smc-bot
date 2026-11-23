import time
import json
import os

from combined_signal import run_analysis
from telegram_alert import send_telegram
from market_data import nigeria_time
from news_alert import check_news_alerts

STATE_FILE = "last_signal.json"
DASHBOARD_FILE = "dashboard_state.json"
CHECK_SECONDS = 60
NEWS_CHECK_SECONDS = 300


def load_last_signal():
    try:
        with open(STATE_FILE, "r") as f:
            return json.load(f).get("key", "")
    except (FileNotFoundError, json.JSONDecodeError):
        return ""


def save_last_signal(key):
    with open(STATE_FILE, "w") as f:
        json.dump({"key": key}, f)


def save_dashboard(result):
    result["updated_at"] = nigeria_time() + " WAT"
    temp_file = DASHBOARD_FILE + ".tmp"

    with open(temp_file, "w") as f:
        json.dump(result, f, indent=2)

    os.replace(temp_file, DASHBOARD_FILE)


def main():
    print("XAUUSD AUTO MONITOR + NEWS ALERT STARTED")
    print("Nigeria Time:", nigeria_time())

    last_key = load_last_signal()
    last_news_check = 0

    while True:
        try:
            now = time.time()

            if now - last_news_check >= NEWS_CHECK_SECONDS:
                try:
                    check_news_alerts()
                except Exception as error:
                    print("NEWS ERROR (will retry):", error)

                last_news_check = time.time()

            try:
                result = run_analysis()
                save_dashboard(result)

                if result.get("signal") in ("BUY", "SELL"):
                    key = result.get("key", "")

                    if key and key != last_key:
                        if send_telegram(result["message"]):
                            save_last_signal(key)
                            last_key = key
                    else:
                        print("An riga aika wannan signal din.")

            except Exception as error:
                print("TECHNICAL ERROR (will retry):", error)

                save_dashboard({
                    "signal": "WAIT",
                    "updated_at": nigeria_time() + " WAT",
                    "error": str(error),
                    "news": "News alerts suna aiki ta Telegram."
                })

        except KeyboardInterrupt:
            print("\nBOT STOPPED")
            break

        print("Next check:", CHECK_SECONDS, "seconds")
        time.sleep(CHECK_SECONDS)


if __name__ == "__main__":
    main()
