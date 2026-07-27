import re
from datetime import datetime, timedelta
from config import LOCAL_TZ


class DateParser:
    DATE_PATTERN = re.compile(r"\b(\d{1,2})\.(\d{1,2})\.(\d{2,4})?\b")
    RELATIVE_PATTERN = re.compile(r"\b(heute|morgen|übermorgen)\b", re.IGNORECASE)

    @classmethod
    def parse_date(cls, text: str) -> datetime:
        """Gibt das gefundene Datum zurück (Default: heute)."""
        now = datetime.now(LOCAL_TZ).date()

        # Relativ: morgen, übermorgen
        rel_match = cls.RELATIVE_PATTERN.search(text)
        if rel_match:
            word = rel_match.group(1).lower()
            if word == "morgen": return now + timedelta(days=1)
            if word == "übermorgen": return now + timedelta(days=2)
            return now

        # Absolut: 12.08.2026
        abs_match = cls.DATE_PATTERN.search(text)
        if abs_match:
            day = int(abs_match.group(1))
            month = int(abs_match.group(2))
            year = int(abs_match.group(3)) if abs_match.group(3) else now.year
            if year < 100: year += 2000
            try:
                return datetime(year, month, day).date()
            except ValueError:
                return now

        return now
