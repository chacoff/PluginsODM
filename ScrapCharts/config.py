import os
from dataclasses import dataclass
from dotenv import load_dotenv


@dataclass()
class Config:
    _dev: bool = True
    DB_DEV: str = 'DB_DEV'
    DB_PROD: str = 'DB_PROD'

    def db_url(self, ):
        load_dotenv('.env')
        _db: str = self.DB_DEV if self._dev else self.DB_PROD

        return os.getenv(_db)

# Reminder:
# localhost // docker inspect -f '{{range .NetworkSettings.Networks}}{{.IPAddress}}{{end}}' db