
import json
import os
import tkinter as tk
from tkinter import messagebox

import telegram

from bot import ReminderBot
from config import logger
from database import Database

# ---------------------------
# UI
# ---------------------------

class App:
    """Tkinter-Startfenster + Verdrahtung."""

    def __init__(self, db_file: str, config_file: str):
        self.db_file = db_file
        self.config_file = config_file

    # --- Token-Persistenz ---

    def _load_saved_token(self):
        if not os.path.exists(self.config_file):
            return None
        try:
            with open(self.config_file, "r", encoding="utf-8") as f:
                return json.load(f).get("token")
        except Exception as e:
            logger.error(f"Config konnte nicht gelesen werden: {e}")
            return None

    def _save_token(self, token: str):
        try:
            with open(self.config_file, "w", encoding="utf-8") as f:
                json.dump({"token": token}, f)
        except Exception as e:
            logger.error(f"Config konnte nicht gespeichert werden: {e}")

    def _clear_saved_token(self):
        if os.path.exists(self.config_file):
            try:
                os.remove(self.config_file)
            except Exception as e:
                logger.error(f"Config konnte nicht gelöscht werden: {e}")

    # --- Start-Flow ---

    def _run_bot(self, token: str):
        """Startet den Bot; faengt ungueltige Token / sonstige Fehler ab."""
        try:
            db = Database(self.db_file)
            bot = ReminderBot(token, db)
            self._save_token(token)
            bot.run()
        except telegram.error.InvalidToken:
            logger.error("Ungueltiger Telegram-Token.")
            self._clear_saved_token()
            messagebox.showerror(
                "Fehler",
                "Der Telegram-Token ist ungültig. Bitte prüfe ihn und starte das Programm neu."
            )
        except Exception as e:
            logger.error(f"Unerwarteter Fehler beim Bot-Start: {e}")
            messagebox.showerror(
                "Fehler",
                f"Der Bot konnte nicht gestartet werden:\n{e}\n\nDetails in bot.log."
            )

    def _launch(self, token: str, root: tk.Tk):
        if not token:
            messagebox.showerror("Fehler", "Token fehlt")
            return

        root.destroy()
        self._run_bot(token)

    def _show_token_prompt(self):
        root = tk.Tk()
        root.title("Family Assistant PRO")
        root.geometry("400x200")

        tk.Label(root, text="Telegram Token").pack(pady=10)

        token_entry = tk.Entry(root, width=40)
        token_entry.pack()

        tk.Button(
            root, text="Start",
            command=lambda: self._launch(token_entry.get().strip(), root)
        ).pack(pady=20)

        root.mainloop()

    def start(self):
        """Startet direkt mit gespeichertem Token, sonst Eingabemaske."""
        saved_token = self._load_saved_token()
        if saved_token:
            self._run_bot(saved_token)
        else:
            self._show_token_prompt()