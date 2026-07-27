from config import DB_FILE, CONFIG_FILE
from ui import App
from Parser_func.router import IntentRouter


import database

# 1. Text vom Nutzer empfangen (z.B. per Sprache-zu-Text oder Chat)
nutzer_eingabe = "Erinner mich jeden morgen um 08:00 Uhr an meine Herztabletten"

# 2. Durch den Router jagen (dieser speichert es automatisch in der DB)
antwort_an_nutzer = IntentRouter.route_and_save(nutzer_eingabe)

# 3. Dem Nutzer Rückmeldung geben
print(antwort_an_nutzer)
# Ausgabe: Als tägliche Routine gespeichert: 'meine Herztabletten' um 08:00 Uhr.

print("\n--- Aktuelle Einkaufsliste in der DB ---")
# Beispiel: So zeigst du dem Nutzer seine aktuelle Einkaufsliste an
for item_id, name in database.Database.get_shopping_list():
  print(f"[{item_id}] {name}")


if __name__ == "__main__":
    App(DB_FILE, CONFIG_FILE).start()