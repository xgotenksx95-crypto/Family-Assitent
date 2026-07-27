import asyncio
import threading
from datetime import datetime, timedelta

from config import LOCAL_TZ, logger
from database import Database


class ReminderScheduler:
    """Kapselt das Timing/Threading fuer Erinnerungen."""

    def __init__(self, db: Database, bot):
        self.db = db
        self.bot = bot
        self.loop = None

    def bind_loop(self, loop):
        self.loop = loop

    def _send_message(self, chat_id: int, text: str):
        if self.loop and self.loop.is_running():
            try:
                future = asyncio.run_coroutine_threadsafe(self.bot.send_message(chat_id, f"⏰ ERINNERUNG: {text}"), self.loop)
                return future.result(timeout=10)
            except Exception:
                pass
        return asyncio.run(self.bot.send_message(chat_id, f"⏰ ERINNERUNG: {text}"))

    def schedule(self, chat_id: int, text: str, when: datetime, db_id: int, recurring: str = None):
        delay = (when - datetime.now(LOCAL_TZ)).total_seconds()
        if delay < 0:
            delay = 1

        def job():
            try:
                self._send_message(chat_id, text)
                logger.info(f"Reminder gesendet an chat {chat_id}: {text}")

                if recurring == "daily":
                    next_when = when + timedelta(days=1)
                    self.db.update_reminder_time(db_id, next_when)
                    self.schedule(chat_id, text, next_when, db_id, recurring)
                else:
                    self.db.mark_reminder_done(db_id)
            except Exception as e:
                logger.error(f"Reminder Error (chat {chat_id}, '{text}'): {e}")

        threading.Timer(delay, job).start()

    def reload_pending(self):
        """Beim Start offene Reminder aus der DB wieder einplanen."""
        for rid, chat_id, text, time_str, recurring in self.db.get_open_reminders():
            when = datetime.fromisoformat(time_str)
            self.schedule(chat_id, text, when, rid, recurring)