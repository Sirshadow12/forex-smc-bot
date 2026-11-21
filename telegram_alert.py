import os
import json
import urllib.request
import urllib.parse


def send_telegram(message):
    token = os.environ.get("TELEGRAM_BOT_TOKEN")
    chat_id = os.environ.get("TELEGRAM_CHAT_ID")

    if not token or not chat_id:
        print("TELEGRAM ERROR: Bot token ko Chat ID bai samu ba.")
        return False

    url = f"https://api.telegram.org/bot{token}/sendMessage"

    data = urllib.parse.urlencode({
        "chat_id": chat_id,
        "text": message
    }).encode()

    request = urllib.request.Request(url, data=data)

    try:
        with urllib.request.urlopen(request, timeout=20) as response:
            result = json.loads(response.read())

        if result.get("ok"):
            print("TELEGRAM: MESSAGE SENT")
            return True

        print("TELEGRAM: FAILED")
        return False

    except Exception as error:
        print("TELEGRAM ERROR:", error)
        return False


if __name__ == "__main__":
    send_telegram(
        "XAUUSD SMC BOT\n"
        "Telegram connection successful!\n"
        "Signal engine integration test."
    )
