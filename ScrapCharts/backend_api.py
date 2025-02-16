import pandas as pd
import requests
from requests import Response
from requests.exceptions import RequestException
from collections import defaultdict
from typing import List, Dict

from .config import Config

c: Config = Config()

URL: str = c.get_api_url()
URL_POST: str = c.get_post_url()
TOKEN: str = c.get_token()
HEADERS: dict = c.get_headers()


def factory_format(_factory) -> str:

    if _factory == 'Belval':
        return 'blv'

    if _factory == 'Differdange':
        return 'diff'

    return ''


def get_all_flights_per_factory(_factory: str) -> Response:

    _fact: str = factory_format(_factory)

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
                'flightday': item.get('flightday'),
                'factory': item.get('factory'),
                'sector': item.get('sector'),
                'pilot': item.get('pilot'),
                'updatedAt': item.get('updatedAt'),
                'volumes_odm': []
            }
        organized[task_id]['volumes_odm'].append(item.get('volume_odm'))

    return organized


def reorganize_data(data: dict) -> dict:

    return {
        'task_ids': list(data.keys()),
        'volumes_odm': [item['volumes_odm'] for item in data.values()],
        'flight_days': [item['flightday'].split('.')[0] for item in data.values()],
        'factory': [item['factory'] for item in data.values()],
        'sector': [item['sector'] for item in data.values()],
        'updated_at': [item['updatedAt'].split('.')[0] for item in data.values()],
        'pilot': [item['pilot'] for item in data.values()]
    }


def create_flight_list(data: list) -> list:
    """ single flights only """

    grouped = defaultdict(lambda: defaultdict(list))

    for item in data:
        grouped[item['TaskID']]['piles'].append(item['pile'])
        grouped[item['TaskID']]['volume_odm'].append(item['volume_odm'])
        grouped[item['TaskID']]['volume_pix4d'].append(item['volume_pix4d'])
        grouped[item['TaskID']]['volume_delta'].append(item['volume_delta'])
        grouped[item['TaskID']]['volume_trench'].append(item['volume_trench'])
        grouped[item['TaskID']]['volume_total'].append(item['volume_total'])

    result = []
    for task_id, volumes in grouped.items():
        first_item = next(item for item in data if item['TaskID'] == task_id)
        result.append([
            task_id,
            first_item['flightday'],
            first_item['factory'],
            first_item['sector'],
            first_item['updatedAt'].split('.')[0],
            first_item['pilot'],
            volumes['piles'],
            volumes['volume_odm'],
            volumes['volume_pix4d'],
            volumes['volume_delta'],
            volumes['volume_trench'],
            volumes['volume_total']
        ])

    return result[0]  # Return first list since all data is for same TaskID


def create_flight_df(data: Response) -> dict:
    """ dev mode only """

    df = pd.DataFrame(data)
    # print(df.columns.tolist())

    df['TaskID'] = df['TaskID'].str.strip()

    df['updatedAt'] = pd.to_datetime(df['updatedAt'], format='ISO8601')
    df['flightday'] = pd.to_datetime(df['flightday'], format='ISO8601')

    df['flightday'] = df['flightday'].dt.strftime('%Y-%m-%dT%H:%M:%S')
    df['updatedAt'] = df['updatedAt'].dt.strftime('%Y-%m-%dT%H:%M:%S')

    to_drop: list[str] = ['flightday', 'Counter', 'TaskID', 'sector', 'factory', 'polygon', 'area',
                          'length', 'pilot', 'reviewer', 'type', 'color']
    df = df.drop(columns=to_drop, axis=1)

    return df.to_dict(orient="split")


def update_db_via_dev(_factory: str, _data: Response) -> Response:
    """ dev mode only """

    _fact: str = _factory.lower()

    url: str = f'{URL_POST}/{_fact}'

    response = requests.post(url, headers=HEADERS, json=_data, timeout=10)

    return response.json()
