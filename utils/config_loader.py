from configparser import ConfigParser
from pathlib import Path

class Config:
    def __init__(self):
        self.config = ConfigParser()
        config_path = Path("config.cfg")
        
        if not config_path.exists():
            raise FileNotFoundError("Конфиг файл не найден!")
        
        self.config.read(config_path, encoding="utf-8")
        
        # Бот
        self.token = self.config.get("bot", "token")
        self.admins = list(map(int, self.config.get("bot", "admins").split(",")))
        self.items_per_page = self.config.getint("bot", "items_per_page", fallback=5)
        self.ref_percent = self.config.getint("bot", "ref_percent", fallback=15)
        
        # ОП каналы
        self.op_channels = self.config.get("op_channels", "channels").split(",")

config = Config()