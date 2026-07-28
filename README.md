🤖 Family Assistant Pro

## Motivation

Family Assistant Pro is a modular assistant designed to automate everyday tasks while providing a clean architecture that can later be extended with local Large Language Models.

Ein modularer, lösungsorientierter Alltagsassistent in Python. Das Projekt kombiniert ein benutzerfreundliches grafisches Interface (UI) mit fortschrittlicher Textmustererkennung (Regex) für Erinnerungen und Einkaufslisten. Die Architektur ist von Grund auf so aufgebaut, dass sie als stabiles Fundament für die Anbindung lokaler Large Language Models (LLMs) wie Llama 3.1 dient.
✨ Besondere Highlights

    Zero-Configuration & Sicherheit: Beim ersten Start öffnet sich eine Setup-UI. Der Nutzer gibt seinen Telegram-Token ein, und das System generiert die config.json sowie die SQLite-Datenbank vollautomatisch lokal auf dem PC. Der Quellcode bleibt dadurch zu 100 % frei von sensiblen Passwörtern.
    Intelligenter Intent-Router: Ein zentraler IntentRouter analysiert eingehende Nachrichten und entscheidet autonom über die Weiterleitung (Einkaufsliste vs. Erinnerung).
    Mitdenkender Zeit-Parser: Der ReminderParser versteht komplexe deutsche Formulierungen (z. B. "14:30 Uhr", "in 20 Minuten", "jeden Morgen"). Er erkennt automatisch, ob eine Uhrzeit für den aktuellen Tag bereits in der Vergangenheit liegt, und verschiebt den Termin logisch auf morgen.

📁 Projekt-Struktur und Software-Architektur

Das Projekt folgt dem Software-Engineering-Prinzip "Separation of Concerns" (Trennung von Zuständigkeiten) und ist absolut modular aufgebaut:

    main.py: Der zentrale Startpunkt der Anwendung.
    ui.py: Das grafische Benutzerinterface für das Onboarding und die Token-Eingabe.
    bot.py: Die Schnittstelle zur offiziellen Telegram-Bot-API für den Chat-Austausch.
    scheduler.py: Der autonome Hintergrund-Dienst, der Termine sekundengenau überwacht.
    database.py: Die Kapselung aller Datenbankzugriffe auf die lokale SQLite-Datenbank.
    Parser_func/:
        router.py: Das logische Herzstück zur Intent-Erkennung.
        text_parser.py: Die leistungsstarke Regex-Engine zur Extraktion von Aufgaben und relativen Zeiten.

🛠️ Technischer Stack

    Sprache: Python 3.x
    GUI-Framework: Tkinter / CustomTkinter (für die Onboarding-UI)
    Datenbank: SQLite (sqlite3) für relationale, ausfallsichere Datenhaltung
    API: Telegram Bot API
    Konfiguration: Dynamisches JSON-Parsing (config.json)
