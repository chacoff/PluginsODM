# Reminder:
# localhost // docker inspect -f '{{range .NetworkSettings.Networks}}{{.IPAddress}}{{end}}' db

from dataclasses import dataclass


@dataclass()
class Config:
    _dev: bool = False
    DB_DEV: str = 'postgresql+psycopg2://postgres:API@host.docker.internal:5432/scrap'
    DB_PROD: str = 'postgresql+psycopg2://postgres:ArcelorT3ch*2024!?@host.docker.internal:5432/Volumes_DB'

    api_url: str = f'http://host.docker.internal:3000/get'
    token: str = 'xeXRK2RPc5dZLTPp2z2s4eAhfMH01bOaIZsqxbTzys12dL65e8KvKvszlalaoxOZaMhJyPGTECSSRc2j7VkZdGeJZm5Ypu02pdSoxbrxzY875vugEQ5x3aVeQu2UTAcIDwWdrgaWzuzE8u3RUz6igD'

    def db_url(self, ) -> str:
        _db: str = self.DB_DEV if self._dev else self.DB_PROD
        return _db

    def get_api_url(self) -> str:
        return self.api_url

    def get_token(self) -> str:
        return self.token

    def get_headers(self) -> dict:
        return {'Authorization': f'{self.token}'}
