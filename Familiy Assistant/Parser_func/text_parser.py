import re
from datetime import datetime, time, timedelta
from config import LOCAL_TZ
from Parser_func.date_parser import DateParser


class ReminderParser:
    TIME_PATTERN = re.compile(r"\b(\d{1,2}:\d{2})\b")
    UHR_PATTERN = re.compile(r"\b(\d{1,2})\s*uhr(?:\s*(\d{1,2}))?\b", re.IGNORECASE)
    RECURRING_PATTERN = re.compile(r"jeden tag|jeden morgen|jeden abend|täglich|taeglich|immer", re.IGNORECASE)
    RELATIVE_TIME_PATTERN = re.compile(
        r"\b(?:in\s+(?:einer|\d+)\s*(?:sekunde|sekunden|minute|minuten|stunde|stunden|tag|tagen)|nach\s+\d+\s*(?:sekunde|sekunden|minute|minuten|stunde|stunden|tag|tagen))\b",
        re.IGNORECASE,
    )

    @classmethod
    def _extract_time(cls, text: str):
        match = cls.TIME_PATTERN.search(text)
        if match:
            hour, minute = map(int, match.group(1).split(":"))
            return hour, minute, match.group(0)

        match = cls.UHR_PATTERN.search(text)
        if match:
            hour = int(match.group(1))
            minute = int(match.group(2)) if match.group(2) else 0
            return hour, minute, match.group(0)

        relative_match = cls.RELATIVE_TIME_PATTERN.search(text)
        if relative_match:
            return None, None, relative_match.group(0)
        return None, None, None

    @classmethod
    def parse(cls, text: str):
        hour, minute, matched_text = cls._extract_time(text)
        recurring = "daily" if cls.RECURRING_PATTERN.search(text) else None

        if hour is not None and 0 <= hour <= 23 and 0 <= minute <= 59:
            target_date = DateParser.parse_date(text)
            target_time = time(hour=hour, minute=minute)
            target = datetime.combine(target_date, target_time).replace(tzinfo=LOCAL_TZ)

            if target < datetime.now(LOCAL_TZ) and not DateParser.DATE_PATTERN.search(text) and not DateParser.RELATIVE_PATTERN.search(text):
                target += timedelta(days=1)

            task = re.sub(
                r"/add reminder|erinner mich an|erinner mich|jeden tag|jeden morgen|jeden abend|täglich|taeglich|immer|\buhr\b|um\b|" + (
                    matched_text if matched_text else ""), "", text, flags=re.IGNORECASE)
            task = " ".join(task.split()).strip()
            return {"task": task or "Erinnerung", "datetime": target, "recurring": recurring}

        relative_match = cls.RELATIVE_TIME_PATTERN.search(text)
        if relative_match:
            now = datetime.now(LOCAL_TZ)
            amount = 1
            unit = "minute"
            relative_text = relative_match.group(0).lower()
            if re.search(r"\b(\d+)\b", relative_text):
                amount = int(re.search(r"\b(\d+)\b", relative_text).group(1))
            if "sekunde" in relative_text:
                unit = "second"
            elif "minute" in relative_text:
                unit = "minute"
            elif "stunde" in relative_text:
                unit = "hour"
            elif "tag" in relative_text:
                unit = "day"

            if unit == "second":
                target = now + timedelta(seconds=amount)
            elif unit == "minute":
                target = now + timedelta(minutes=amount)
            elif unit == "hour":
                target = now + timedelta(hours=amount)
            else:
                target = now + timedelta(days=amount)

            task = re.sub(rf"\b{re.escape(relative_match.group(0))}\b", "", text, flags=re.IGNORECASE)
            task = re.sub(r"/add reminder|erinner mich an|erinner mich|jeden tag|jeden morgen|jeden abend|täglich|taeglich|immer|\buhr\b|um\b", "", task, flags=re.IGNORECASE)
            task = " ".join(task.split()).strip()
            return {"task": task or "Erinnerung", "datetime": target, "recurring": None}

        return None

    @classmethod
    def contains_time(cls, text: str) -> bool:
        hour, minute, _ = cls._extract_time(text)
        if hour is not None and 0 <= hour <= 23 and 0 <= minute <= 59:
            return True
        return bool(cls.RELATIVE_TIME_PATTERN.search(text))

    @classmethod
    def parse_full(cls, text: str):
        parsed = cls.parse(text)
        if not parsed:
            return None, None, None
        return parsed["task"], parsed["datetime"], parsed["recurring"]
