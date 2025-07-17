import json
from pathlib import Path
from typing import Dict

class Localization:
    def __init__(self):
        self.locales: Dict[str, Dict[str, str]] = {}
        self.load_locales()

    def load_locales(self):
        locales_path = Path("locales")
        for locale_file in locales_path.glob("*.json"):
            with open(locale_file, "r", encoding="utf-8") as f:
                lang = locale_file.stem
                self.locales[lang] = json.load(f)

    def get(self, key: str, lang: str = "ru") -> str:
        return self.locales.get(lang, {}).get(key, key)

_ = Localization().get  