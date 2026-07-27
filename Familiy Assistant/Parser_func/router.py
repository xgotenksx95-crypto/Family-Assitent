from Parser_func.shopping_parser import ShoppingParser
from Parser_func.text_parser import ReminderParser
import database

# Datenbank beim Start der App direkt initialisieren
database.Database.init_db()


class IntentRouter:
    @classmethod
    def route_and_save(cls, text: str) -> str:
        """Verarbeitet den Text und speichert das Ergebnis direkt in der DB."""
        text_lower = text.lower()

        # 1. Fall: Einkaufsliste
        if ShoppingParser.is_shopping_list(text_lower):
            items = ShoppingParser.parse(text)
            for item in items:
             database.Database.add_shopping_item(item)
             return f"Gespeichert auf der Einkaufsliste: {', '.join(items)}"

        # 2. Fall: Erinnerung oder Routine
        reminder_data = ReminderParser.parse(text)
        if reminder_data:
            task = reminder_data["task"]
            
            # Wenn es täglich wiederholt werden soll (Routine)
            if reminder_data["recurring"] == "daily":
                time_str = reminder_data["datetime"].strftime("%H:%M")
                database.Database.add_routine(task, time_str)
                return f"Als tägliche Routine gespeichert: '{task}' um {time_str} Uhr."
            
            # Wenn es ein einmaliger Termin ist
            else:
                dt = reminder_data["datetime"]
                database.Database.add_reminder(task, dt)
            return f"Termin gespeichert: '{task}' am {dt.strftime('%d.%m.%Y um %H:%M')} Uhr."

        # 3. Fallback
        return "Entschuldigung, das habe ich nicht verstanden. Bitte nenne eine Uhrzeit oder sag mir, was ich einkaufen soll."
