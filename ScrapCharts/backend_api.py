import requests
from requests import Response
from requests.exceptions import RequestException
from collections import defaultdict
from typing import List, Dict

from .config import Config

c: Config = Config()

URL: str = c.get_api_url()
TOKEN: str = c.get_token()
HEADERS: dict = c.get_headers()


def get_all_flights_per_factory(_factory: str) -> Response:

    _fact: str = ''

    if _factory == 'Belval':
        _fact = 'blv'

    if _factory == 'Differdange':
        _fact = 'diff'

    url: str = f'{URL}/all/scraps/{_fact}'

    return perform_request(url)


def get_flight_per_task_id(_fact: str, _id: str) -> Response:

    _fact: str = _fact.lower()

    url: str = f'{URL}/scraps/{_fact}/{_id}'

    return perform_request(url)


def perform_request(_url: str):

    try:
        response = requests.get(_url, headers=HEADERS, timeout=10)
        response.raise_for_status()
        return response.json()

    except requests.exceptions.HTTPError as http_err:
        print(f'HTTP error: {http_err}')
        return None
    except requests.exceptions.ConnectionError:
        print('Connection error: Could not connect to server')
        return None
    except requests.exceptions.Timeout:
        print('Timeout error: Request took too long')
        return None
    except requests.exceptions.JSONDecodeError:
        print('JSON error: Could not parse response')
        return None
    except RequestException as e:
        print(f'Error: {e}')
        return None


def group_by_task_id(data: Response):
    grouped = defaultdict(list)
    for item in data:
        task_id = item.get('TaskID')  # Adjust field name if different
        grouped[task_id].append(item)
    return dict(grouped)


def organize_flight_data(data: Response) -> Dict:
    """ data: List[Dict] >> Response """

    organized: dict = {}

    for item in data:
        task_id = item.get('TaskID')
        if task_id not in organized:
            organized[task_id] = {
                'Flightday': item.get('Flightday'),
                'Factory': item.get('Factory'),
                'Sector': item.get('Sector'),
                'Pilot': item.get('Pilot'),
                'UpdatedAt': item.get('UpdatedAt'),
                'Volumes_ODM': []
            }
        organized[task_id]['Volumes_ODM'].append(item.get('Volume_ODM'))

    return organized


def reorganize_data(data: dict) -> dict:
    return {
        'task_ids': list(data.keys()),
        'volumes_odm': [item['Volumes_ODM'] for item in data.values()],
        'flight_days': [item['Flightday'].split('.')[0] for item in data.values()],
        'factory': [item['Factory'] for item in data.values()],
        'sector': [item['Sector'] for item in data.values()],
        'updated_at': [item['UpdatedAt'].split('.')[0] for item in data.values()],
        'pilot': [item['Pilot'] for item in data.values()]
    }


def create_flight_list(data: list) -> list:
    grouped = defaultdict(lambda: defaultdict(list))

    for item in data:
        grouped[item['TaskID']]['piles'].append(item['Pile'])
        grouped[item['TaskID']]['volume_odm'].append(item['Volume_ODM'])
        grouped[item['TaskID']]['volume_pix4d'].append(item['Volume_pix4d'])
        grouped[item['TaskID']]['volume_delta'].append(item['Volume_Delta'])
        grouped[item['TaskID']]['volume_trench'].append(item['Volume_Trench'])
        grouped[item['TaskID']]['volume_total'].append(item['Volume_Total'])

    result = []
    for task_id, volumes in grouped.items():
        first_item = next(item for item in data if item['TaskID'] == task_id)
        result.append([
            task_id,
            first_item['Flightday'],
            first_item['Factory'],
            first_item['Sector'],
            first_item['UpdatedAt'].split('.')[0],
            first_item['Pilot'],
            volumes['piles'],
            volumes['volume_odm'],
            volumes['volume_pix4d'],
            volumes['volume_delta'],
            volumes['volume_trench'],
            volumes['volume_total']
        ])

    return result[0]  # Return first list since all data is for same TaskID
