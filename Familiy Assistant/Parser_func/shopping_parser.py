import re

class ShoppingParser:
    # Sucht nach typischen Einkaufs-Befehlen
    TRIGGER_PATTERN = re.compile(
        r"\b(kaufe|besorge|setz|schreib|pack)\b.*\b(auf die einkaufsliste|einkaufsliste|liste)\b|\b(kaufe|besorge)\b", 
        re.IGNORECASE
    )
    
    # Wörter, die auf KEINEN Fall in die Einkaufsliste gehören
    BLOCK_PATTERN = re.compile(r"geburtstag|feier|party|uhr|\b\d{1,2}\.\d{1,2}\.", re.IGNORECASE)

    @classmethod
    def is_shopping_list(cls, text: str) -> bool:
        # Wenn ein Block-Wort (wie Geburtstag oder ein Datum) drin ist, ist es KEINE Einkaufsliste
        if cls.BLOCK_PATTERN.search(text):
            return False
        return bool(cls.TRIGGER_PATTERN.search(text))

    @classmethod
    def parse(cls, text: str) -> list[str]:
        cleaned = re.sub(r"\b(auf die einkaufsliste|einkaufsliste|liste|kaufe|besorge|setz|schreib|pack|und|bitte)\b", "", text, flags=re.IGNORECASE)
        items = [item.strip() for item in re.split(r",|\bund\b", cleaned) if item.strip()]
        return items if items else ["Unbekannter Artikel"]

