import asyncio
import re
from datetime import datetime

import telegram
from telegram import InlineKeyboardButton, InlineKeyboardMarkup, Update
from telegram.ext import ApplicationBuilder, CallbackQueryHandler, CommandHandler, ContextTypes, MessageHandler, filters

from config import LOCAL_TZ, logger
from database import Database
from scheduler import ReminderScheduler
from Parser_func.text_parser import ReminderParser


# ---------------------------
# BOT
# ---------------------------

class ReminderBot:
    """Telegram-Handler-Logik.

    Kein Button-Zwang mehr: jede Nachricht wird automatisch eingeordnet -
    enthaelt sie eine Uhrzeit, wird sie zum Reminder (taeglich, wenn
    "jeden Tag"/"täglich" dabei steht), sonst wird sie der Einkaufsliste
    hinzugefuegt. "📋 Liste" oder /list zeigt die Einkaufsliste an.
    """

    LIST_WORDS = {"liste", "einkaufsliste", "📋 einkaufsliste", "📋 liste", "/list shop", "/list"}
    # Kurze Fueller-/Gruss-Woerter, die NICHT automatisch auf die Einkaufsliste sollen
    IGNORE_WORDS = {
        "hi", "hallo", "hey", "ok", "okay", "danke", "dankeschön", "ja", "nein",
        "test", "moin", "servus", "tschüss", "bye", "👍", "👋",
    }

    def __init__(self, token: str, db: Database):
        self.db = db
        self.app = ApplicationBuilder().token(token).build()
        self.scheduler = ReminderScheduler(db, self.app.bot)

        self.app.add_handler(CommandHandler("start", self.handle_start))
        self.app.add_handler(CommandHandler("reminders", self.handle_reminders))
        self.app.add_handler(MessageHandler(filters.TEXT, self.handle_message))
        self.app.add_handler(CallbackQueryHandler(self.handle_shop_callback, pattern=r"^shop_done:"))

    async def handle_start(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        await update.message.reply_text(
            "Hi! Schreib mir einfach:\n"
            "• \"Milch\" → kommt auf die Einkaufsliste\n"
            "• \"Trinken 12:30\" → einmalige Erinnerung\n"
            "• \"Jeden Tag 12:30 trinken\" → tägliche Erinnerung\n"
            "• \"Liste\" → zeigt die Einkaufsliste\n"
            "• /reminders → zeigt offene Erinnerungen"
        )

    async def handle_reminders(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        chat_id = update.effective_chat.id
        reminders = self.db.get_open_reminders()
        user_reminders = [r for r in reminders if r[1] == chat_id]

        if not user_reminders:
            await update.message.reply_text("📭 Keine offenen Erinnerungen")
            return

        lines = []
        for reminder_id, _, task, due_datetime, recurring in user_reminders:
            when = due_datetime
            if isinstance(when, str):
                try:
                    when = datetime.fromisoformat(when)
                except ValueError:
                    when = when
            if recurring == "daily":
                lines.append(f"• {task} — täglich um {when.strftime('%H:%M') if hasattr(when, 'strftime') else when}")
            else:
                lines.append(f"• {task} — {when.strftime('%d.%m.%Y %H:%M') if hasattr(when, 'strftime') else when}")

        await update.message.reply_text("📝 Offene Erinnerungen:\n" + "\n".join(lines))

    async def handle_message(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        self.scheduler.bind_loop(asyncio.get_running_loop())

        raw_text = update.message.text
        text = raw_text.lower().strip()
        chat_id = update.effective_chat.id

        if text in self.LIST_WORDS:
            await self._handle_list_shop(update)
            return

        if text in self.IGNORE_WORDS:
            return

        # --- Reminder automatisch erkennen (einmalig oder taeglich) ---
        if ReminderParser.contains_time(text):
            await self._handle_add_reminder(update, chat_id, text)
            return

        # --- Sonst: automatisch der Einkaufsliste hinzufuegen ---
        await self._handle_add_shop_multi(update, raw_text)

    async def _handle_add_reminder(self, update, chat_id, text):
        task, when, recurring = ReminderParser.parse_full(text)

        if not when:
            await update.message.reply_text("❌ Zeit fehlt (z.B. 20:15)")
            return

        db_id = self.db.add_reminder(chat_id, task, when, recurring)
        if db_id is None:
            try:
                await update.message.reply_text(f"ℹ️ Diese Erinnerung ist bereits gespeichert: {task}")
            except Exception as exc:
                logger.warning(f"Bot reply failed: {exc}")
            return

        self.scheduler.schedule(chat_id, task, when, db_id, recurring)

        try:
            if recurring == "daily":
                await update.message.reply_text(
                    f"🔁 Gespeichert, wiederholt sich täglich um {when.strftime('%H:%M')}: {task}"
                )
            else:
                await update.message.reply_text(f"✔ Gespeichert: {task}")
        except Exception as exc:
            logger.warning(f"Bot reply failed: {exc}")

    async def _handle_add_shop_multi(self, update, raw_text: str):
        """Erlaubt mehrere Artikel in einer Nachricht (Komma oder Zeilenumbruch getrennt)."""
        parts = re.split(r"[,\n]", raw_text)
        items = [p.strip() for p in parts if p.strip()]

        if not items:
            await update.message.reply_text("❌ Kein Text erkannt, bitte nochmal.")
            return

        for item in items:
            self.db.add_shopping_item(item)

        added = ", ".join(items)
        await update.message.reply_text(f"🛒 Hinzugefügt: {added}")

    async def _handle_add_shop(self, update, item: str):
        if not item:
            await update.message.reply_text("❌ Kein Text erkannt, bitte nochmal.")
            return
        self.db.add_shopping_item(item)
        await update.message.reply_text(f"🛒 Hinzugefügt: {item}")

    def _shop_list_message(self):
        """Baut (Text, Keyboard) fuer die aktuelle Einkaufsliste."""
        items = self.db.get_shop_items()

        if not items:
            return "🛒 Liste ist leer", None

        text = "🛒 Einkaufsliste:\n" + "\n".join([f"• {i[1]}" for i in items])
        keyboard = InlineKeyboardMarkup(
            [[InlineKeyboardButton(f"✅ {name}", callback_data=f"shop_done:{item_id}")]
             for item_id, name in items]
        )
        return text, keyboard

    async def _handle_list_shop(self, update):
        text, keyboard = self._shop_list_message()
        await update.message.reply_text(text, reply_markup=keyboard)

    async def handle_shop_callback(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        query = update.callback_query
        item_id = int(query.data.split(":")[1])

        self.db.mark_shop_item_done(item_id)
        await query.answer("✅ Erledigt")

        text, keyboard = self._shop_list_message()
        try:
            await query.edit_message_text(text, reply_markup=keyboard)
        except telegram.error.BadRequest:
            # Nachricht war unveraendert (z.B. gleichzeitiger Klick von 2 Leuten)
            pass

    def run(self):
        self.scheduler.bind_loop(None)
        self.scheduler.reload_pending()
        logger.info("Bot läuft...")
        self.app.run_polling()
