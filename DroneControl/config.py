# Reminder:
# localhost // docker inspect -f '{{range .NetworkSettings.Networks}}{{.IPAddress}}{{end}}' db

from dataclasses import dataclass


@dataclass()
class Config:
    _dev: bool = False

    storage: str = 'http://droneslpl.arcelormittal.com:3333'
    get_url: str = f'http://host.docker.internal:3000/get/schedules'
    post_url: str = f'http://host.docker.internal:3000/add/schedule'
    token: str = 'xeXRK2RPc5dZLTPp2z2s4eAhfMH01bOaIZsqxbTzys12dL65e8KvKvszlalaoxOZaMhJyPGTECSSRc2j7VkZdGeJZm5Ypu02pdSoxbrxzY875vugEQ5x3aVeQu2UTAcIDwWdrgaWzuzE8u3RUz6igD'

    def get_api_url(self) -> str:
        return self.get_url

    def get_post_url(self) -> str:
        return self.post_url

    def get_token(self) -> str:
        return self.token

    def get_headers(self) -> dict:
        return {'Authorization': f'{self.token}'}

    def get_drones_storage(self) -> str:
        return self.storage

