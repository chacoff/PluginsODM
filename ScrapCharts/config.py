from dataclasses import dataclass


@dataclass()
class Config:
    _dev: bool = True
    DB_DEV: str = 'postgresql+psycopg2://postgres:API@host.docker.internal:5432/scrap'
    DB_PROD: str = 'postgresql+psycopg2://postgres:ArcelorT3ch*2024!?@host.docker.internal:5432/Volumes_DB'

    def db_url(self, ) -> str:
        _db: str = self.DB_DEV if self._dev else self.DB_PROD
        return _db

# Reminder:
# localhost // docker inspect -f '{{range .NetworkSettings.Networks}}{{.IPAddress}}{{end}}' db