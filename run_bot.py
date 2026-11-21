import time
import json

from combined_signal import run_analysis
from telegram_alert import send_telegram
from market_data import nigeria_time
from news_alert import check_news_alerts

STATE_FILE = "last_signal.json"
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


def main():
    print("XAUUSD AUTO MONITOR + NEWS ALERT STARTED")
    print("Nigeria Time:", nigeria_time())
    print("Technical check:", CHECK_SECONDS, "seconds")
    print("News check:", NEWS_CHECK_SECONDS, "seconds")

    last_key = load_last_signal()
    last_news_check = 0

    while True:
        try:
            now = time.time()

            # NEWS CHECK - separate from technical analysis
            if now - last_news_check >= NEWS_CHECK_SECONDS:
                try:
                    check_news_alerts()
                except Exception as error:
                    print("NEWS ERROR (will retry):", error)

                last_news_check = time.time()

            # TECHNICAL ANALYSIS - continues if news fails
            try:
                result = run_analysis()

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

        except KeyboardInterrupt:
            print("\nBOT STOPPED")
            break

        print("Next check:", CHECK_SECONDS, "seconds")
        time.sleep(CHECK_SECONDS)


if __name__ == "__main__":
    main()
