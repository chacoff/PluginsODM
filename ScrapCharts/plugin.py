#
# it requires to add in urlpatterns of django:
#
# url(r'^media/project/(?P<path>.*)$', serve, {
#    'document_root': os.path.join(settings.MEDIA_ROOT, 'project')
# }),
#

import pandas as pd
from sqlalchemy import create_engine, text
import os

from django.contrib.auth.decorators import login_required
from django.shortcuts import render
from django.http import JsonResponse
from django.conf import settings
from django.conf.urls import include, url
from django.views.static import serve

from app.models import Project, Task
from app.plugins import PluginBase, Menu, MountPoint

from PIL import Image
from concurrent.futures import ThreadPoolExecutor
from .image_processing import pipeline

executor = ThreadPoolExecutor(max_workers=4)


def init_urls() -> None:
    urlpatterns = [
        url(r'^media/project/(?P<path>.*)$', serve, {
            'document_root': os.path.join(settings.MEDIA_ROOT, 'project')
        }),
    ]

    root_urlconf = __import__(settings.ROOT_URLCONF, {}, {}, [''])

    if hasattr(root_urlconf, 'urlpatterns'):
        root_urlconf.urlpatterns += urlpatterns
        print('Added media/project urls')


class Plugin(PluginBase):

    def main_menu(self):
        return [Menu("Reports", self.public_url(""), "fa fa-industry fa-fw")]

    def include_js_files(self):
        return ['Chart.min.js']

    def app_mount_points(self):
        init_urls()

        @login_required
        def volume_graphs(request):
            groups: list[bool] = get_user_group(request)
            factory_access = get_factory_access(groups)

            if not factory_access:
                print(f'Error getting data from db. Factory Access: {factory_access}. Most likely is empty.')
                args = {'error': 'Factory access is unknown. Most likely user does not belong to any group.'}
                return render(request, self.template_path("volume_error.html"), args)

            db_data = get_data_from_db(None, factory_access[0])

            label: str = "Volume [m³]"
            projects_tasks: list[dict[str, any]] = get_projects_with_tasks()
            project_id: int = get_project_id_from_task_id(projects_tasks, db_data['task_id'])
            orto: str = f'/media/project/{project_id}/task/{db_data["task_id"]}/assets/odm_orthophoto/odm_orthophoto.tif'

            template_args = {
                'x_values': db_data['piles_array'],
                'y_values': db_data['volumes_array'],
                'updated_at_values': db_data['updated_array'],
                'label': label,
                # 'xy_pairs': list(zip(x_values, y_values, updated_at_values)),
                'n_piles': 0,  # len(x_values),
                'flights': db_data['flight_days'],
                'task_id': db_data['task_id'],
                'task_project_id': project_id,
                'projects_with_tasks': projects_tasks,
                'image_url': orto,
                'isFirstOpen': True,
                'isBelval': groups[0],
                'isDiffer': groups[1],
                'isGlobal': groups[2],
                'isDev': groups[3],
                'factory_access': factory_access
            }

            return render(request, self.template_path("volume_graphs.html"), template_args)

        @login_required
        def get_flight_data(request):
            """"
            Get flight goes by the following pipeline:
                get_data_from_db() using flight_day (specific_date) and factory in question
                get_projects_with_tasks() gets all projects and tasks in webODM DB
                get_project_id_from_task_id() will get the project_id of a task
                convert_tif_to_png will() will run in background
            """

            flight_day = request.GET.get("flightDay", "")
            factory = request.GET.get("factory", "")

            future_db_data = executor.submit(get_data_from_db, flight_day, factory)
            future_projects_tasks = executor.submit(get_projects_with_tasks)

            db_data = future_db_data.result()
            projects_tasks = future_projects_tasks.result()

            future_project_id = executor.submit(get_project_id_from_task_id, projects_tasks, db_data['task_id'])
            project_id = future_project_id.result()

            executor.submit(convert_tif_to_jpg, project_id, db_data['task_id'], db_data['sector'])

            orto_jpg: str = f'/media/project/{project_id}/task/{db_data["task_id"]}/assets/odm_orthophoto/odm_orthophoto.jpg'
            print(f"Completed: {orto_jpg}")

            return JsonResponse({"x_values": list(db_data['piles_array']),
                                 "y_values": list(db_data['volumes_array']),
                                 "updated_at_values": list(db_data['updated_array']),
                                 "task_id": db_data['task_id'],
                                 "task_project_id": project_id,
                                 "image_url": orto_jpg,
                                 'isFirstOpen': False,
                                 'sector_place': db_data['place']})

        @login_required
        def get_factory_flights(request):
            factory = request.GET.get("factory", "")

            db_data = get_data_from_db(None, factory)

            return JsonResponse({"flightList": db_data['flight_days']})

        return [
            MountPoint('$', volume_graphs), 
            MountPoint('get_flight_data', get_flight_data),
            MountPoint('get_factory_flights', get_factory_flights)
            ]


def convert_tif_to_jpg(_project_id, _task_id, sector) -> None:
    """ convert tif to jpg with rotation, scaling and cropping """

    lookup = get_lookup_table()

    tiff_path = os.path.join(settings.MEDIA_ROOT,
                             f'project/{_project_id}/task/{_task_id}/assets/odm_orthophoto/odm_orthophoto.tif')
    jpg_path = os.path.join(settings.MEDIA_ROOT,
                            f'project/{_project_id}/task/{_task_id}/assets/odm_orthophoto/odm_orthophoto.jpg')

    if not os.path.exists(jpg_path):
        output_image = pipeline(tiff_path,
                                angle=lookup[sector]['angle'] if sector in lookup else lookup['unknown']['angle'],
                                crop_values=lookup[sector]['crop'] if sector in lookup else lookup['unknown']['crop'],
                                scaling=True if sector in lookup else False,
                                scale=lookup[sector]['scale'] if sector in lookup else lookup['unknown']['scale'],
                                rotate=True if sector in lookup else False,
                                crop=True if sector in lookup else False,
                                draw=False)
        output_image = output_image.convert('RGB')
        output_image.save(jpg_path, quality=80)


def get_factory_access(groups: list[bool]) -> list[str]:
    """" gets factory access according the user """

    factory_access: list[str] = []

    if groups[0]:  # isBelval
        factory_access = ['Belval']

    if groups[1]:  # isDiffer
        factory_access = ['Differdange']

    if groups[2] or groups[3]:  # isGlobal or isDev
        factory_access = ['Belval', 'Differdange']

    return factory_access


def get_user_group(request) -> list[bool]:
    """ gets user group of every user in database """

    # user_groups = request.user.groups.all()
    is_belval: bool = request.user.groups.filter(name='Belval').exists()
    is_differ: bool = request.user.groups.filter(name='Differdange').exists()
    is_global: bool = request.user.groups.filter(name='Global').exists()
    is_dev: bool = request.user.groups.filter(name='Dev').exists()

    return [is_belval, is_differ, is_global, is_dev]


def get_data_from_db(specific_date=None, factory='') -> dict:
    """ gets all data from the DB and returns a dataframe with it based on flightday = specific_date"""

    if factory == '':
        return {'error': 'factory is unknown.'}

    flight_days, df = get_all_flights(factory)  # all flights from a factory and all full dataset

    db_data: dict = {
        'piles_array': [],
        'volumes_array': [],
        'updated_array': [],
        'flight_days': flight_days,
        'task_id': 0,
        'place': 'unknown',
        'sector': 'unknown'
    }

    if not specific_date:
        return db_data

    df = df[df['flightday'] == specific_date]  # filter df according flight day

    df['volume_drone'] = df['volume_drone'].astype(float)
    df['pile'] = df['pile'].astype(str)
    df['updated_at'] = df['updated_at'].astype(str)

    db_data['piles_array'] = df['pile'].values.tolist()  # x_values
    db_data['volumes_array'] = df['volume_drone'].values.tolist()  # y_values
    db_data['updated_array'] = df['updated_at'].values.tolist()  # updated_at_values
    task_id = df['task_id'].unique().tolist()  # it should be only one, in case, we choose element 0 later
    db_data['task_id'] = task_id[0]
    factory: list = df['factory'].unique().tolist()
    sector: list = df['sector'].unique().tolist()
    db_data['sector'] = sector[0]
    db_data['place'] = f'{factory[0]} - {sector[0]}'

    return db_data


def get_all_flights(factory: str) -> tuple[pd.DataFrame, pd.DataFrame]:
    """ gets all flights available in the database based on their <<flightday>> """

    query: str = ''
    df: pd.DataFrame = pd.DataFrame()
    df_full: pd.DataFrame = pd.DataFrame()

    if factory == 'Belval':
        query = "SELECT * FROM SCRAP_BLV;"

    if factory == 'Differdange':
        query = "SELECT * FROM SCRAP_DIFF;"

    if not query == '':
        # localhost // docker inspect -f '{{range .NetworkSettings.Networks}}{{.IPAddress}}{{end}}' db
        db_url = "postgresql+psycopg2://postgres:API@host.docker.internal:5432/waste_management"
        # db_url = "postgresql+psycopg2://postgres:ArcelorT3ch*2024!?@host.docker.internal:5432/postgres"
        engine = create_engine(db_url)
        df_full: pd.DataFrame = pd.read_sql(query, engine)
        df = df_full.copy()
        engine.dispose()

        df['flightday'] = pd.to_datetime(df['flightday'])
        date_strings = df['flightday'].dt.strftime('%Y-%m-%d %H:%M:%S').unique().tolist()

        return date_strings, df_full

    return df, df_full


def get_projects_with_tasks() -> list[dict[str, any]]:
    """ gets all projects/tasks available in webODM DB """

    projects_with_tasks = []
    all_projects = Project.objects.all()

    for project in all_projects:
        project_tasks = Task.objects.filter(project=project)
        projects_with_tasks.append({
            'project': project,
            'tasks': project_tasks,
        })

    return projects_with_tasks


def get_project_id_from_task_id(_projects_tasks: list, _task_id: str) -> int:
    """ gets the project id from a specific tasks available in webODM DB """

    for project_data in _projects_tasks:
        project = project_data['project']
        tasks = project_data['tasks']

        for task in tasks:
            task_id: str = task.id  # it is a class uuid.UUID
            project_id: int = task.project_id
            if str(task_id) == _task_id:
                print(f'Task ID: {task_id}, Project ID: {project_id}')
                return project_id

    return 0


def get_lookup_table() -> dict:
    _lookup = {}

    db_url = "postgresql+psycopg2://postgres:API@host.docker.internal:5432/waste_management"
    engine = create_engine(db_url)

    with engine.connect() as connection:
        result = connection.execute(text("""
            SELECT sector, angle, crop_left, crop_top, crop_right, crop_bottom, scale 
            FROM SCRAP_PARAMS
        """))

        for row in result:
            sector, angle, crop_left, crop_top, crop_right, crop_bottom, scale = row
            _lookup[sector] = {
                'angle': angle,
                'crop': (crop_left, crop_top, crop_right, crop_bottom),
                'scale': scale
            }

    return _lookup


