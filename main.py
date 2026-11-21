import os
import threading

from kivy.app import App
from kivy.clock import Clock
from kivy.uix.boxlayout import BoxLayout
from kivy.uix.label import Label
from kivy.uix.button import Button
from kivy.uix.textinput import TextInput

from combined_signal import run_analysis
from telegram_alert import send_telegram


class TradingBotApp(App):

    def build(self):
        self.running = False
        self.worker_active = False
        self.last_sent_key = None

        layout = BoxLayout(
            orientation="vertical",
            padding=15,
            spacing=10
        )

        layout.add_widget(Label(
            text="XAUUSD SMC TRADING BOT",
            font_size=23,
            bold=True,
            size_hint_y=None,
            height=50
        ))

        self.token_input = TextInput(
            hint_text="Enter Telegram Bot Token",
            password=True,
            multiline=False,
            size_hint_y=None,
            height=48
        )
        layout.add_widget(self.token_input)

        self.chat_input = TextInput(
            hint_text="Enter Telegram Chat ID",
            multiline=False,
            size_hint_y=None,
            height=48
        )
        layout.add_widget(self.chat_input)

        self.status = Label(
            text="BOT STATUS: READY",
            font_size=18,
            size_hint_y=None,
            height=40
        )
        layout.add_widget(self.status)

        self.signal = Label(
            text="SIGNAL: WAIT",
            font_size=28,
            bold=True,
            size_hint_y=None,
            height=65
        )
        layout.add_widget(self.signal)

        self.details = Label(
            text="Waiting for market analysis...",
            size_hint_y=None,
            height=130
        )
        layout.add_widget(self.details)

        self.time_label = Label(
            text="Nigeria Time: --",
            size_hint_y=None,
            height=35
        )
        layout.add_widget(self.time_label)

        start = Button(
            text="START MONITOR",
            size_hint_y=None,
            height=55
        )
        start.bind(on_press=self.start_monitor)
        layout.add_widget(start)

        stop = Button(
            text="STOP MONITOR",
            size_hint_y=None,
            height=55
        )
        stop.bind(on_press=self.stop_monitor)
        layout.add_widget(stop)

        Clock.schedule_interval(self.update_time, 1)

        return layout

    def update_time(self, dt):
        from datetime import datetime, timezone, timedelta

        now = datetime.now(
            timezone(timedelta(hours=1))
        )
        self.time_label.text = (
            "Nigeria Time: " + now.strftime("%Y-%m-%d %H:%M:%S")
        )

    def start_monitor(self, instance):
        if self.running:
            return

        token = self.token_input.text.strip()
        chat_id = self.chat_input.text.strip()

        if not token or not chat_id:
            self.status.text = "Enter Telegram Token and Chat ID"
            return

        os.environ["TELEGRAM_BOT_TOKEN"] = token
        os.environ["TELEGRAM_CHAT_ID"] = chat_id

        self.running = True
        self.status.text = "BOT STATUS: MONITORING"
        self.details.text = "Starting XAUUSD analysis..."

        self.check_event = Clock.schedule_interval(
            self.run_check, 60
        )

        self.run_check(0)

    def stop_monitor(self, instance):
        self.running = False

        if hasattr(self, "check_event"):
            self.check_event.cancel()

        self.status.text = "BOT STATUS: STOPPED"
        self.details.text = "Monitoring stopped."

    def run_check(self, dt):
        if not self.running or self.worker_active:
            return

        self.worker_active = True

        threading.Thread(
            target=self.analysis_worker,
            daemon=True
        ).start()

    def analysis_worker(self):
        try:
            result = run_analysis()

            signal = result.get("signal", "WAIT")
            telegram_sent = False

            if signal in ("BUY", "SELL"):
                key = result.get("key")

                if key and key != self.last_sent_key:
                    telegram_sent = send_telegram(
                        result.get("message", "XAUUSD " + signal)
                    )

                    if telegram_sent:
                        self.last_sent_key = key

            output = {
                "signal": signal,
                "message": result.get("message", "No confirmed signal."),
                "telegram": telegram_sent
            }

        except Exception as error:
            output = {
                "signal": "WAIT",
                "message": "Analysis error: " + str(error),
                "telegram": False
            }

        self.worker_active = False
        Clock.schedule_once(
            lambda dt: self.show_result(output), 0
        )

    def show_result(self, result):
        if not self.running:
            return

        signal = result["signal"]
        self.signal.text = "SIGNAL: " + signal

        if signal in ("BUY", "SELL"):
            self.details.text = result["message"]

            if result["telegram"]:
                self.status.text = "SIGNAL CONFIRMED - TELEGRAM SENT"
            else:
                self.status.text = "SIGNAL FOUND - TELEGRAM NOT SENT"
        else:
            self.status.text = "MONITORING - WAIT"
            self.details.text = result["message"]


if __name__ == "__main__":
    TradingBotApp().run()
