import pandas as pd
from sqlalchemy import create_engine, text
from app.models import Project, Task


# localhost // docker inspect -f '{{range .NetworkSettings.Networks}}{{.IPAddress}}{{end}}' db
db_url = "postgresql+psycopg2://postgres:API@host.docker.internal:5432/waste_management"
# db_url = "postgresql+psycopg2://postgres:ArcelorT3ch*2024!?@host.docker.internal:5432/postgres"


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

    df = get_all_flights(factory)  # all flights from a factory and all full dataset

    result = df.groupby('task_id').agg({
        'flightday': 'unique',
        'sector': 'unique',
        'factory': 'unique',
        'updated_at': 'unique',
        'pilot': 'unique',
        'pile': list,
        'volume_drone': list  # Collect all volumes into a list
    }).reset_index()

    result['flightday'] = result['flightday'].explode()
    result['flightday'] = pd.to_datetime(result['flightday'])
    flightday_array = result['flightday'].dt.strftime('%Y-%m-%d %H:%M:%S').tolist()

    result['updated_at'] = result['updated_at'].explode()
    result['updated_at'] = pd.to_datetime(result['updated_at'])
    update_at_array = result['updated_at'].dt.strftime('%Y-%m-%d %H:%M:%S').tolist()

    db_data: dict = {
        'task_ids': result['task_id'].values.tolist(),
        'piles_array': result['pile'].values.tolist(),
        'volumes_array': result['volume_drone'].values.tolist(),
        'flight_days': flightday_array,
        'factory': result['factory'].explode().tolist(),
        'sector': result['sector'].explode().tolist(),
        'updated_at': update_at_array,
        'pilot': result['pilot'].explode().tolist()
    }

    return db_data


def get_all_flights(factory: str) -> pd.DataFrame:
    """ gets all flights available in the database based on their <<flightday>> """

    query: str = ''
    df_full: pd.DataFrame = pd.DataFrame()

    if factory == 'Belval':
        query = "SELECT * FROM SCRAP_BLV;"

    if factory == 'Differdange':
        query = "SELECT * FROM SCRAP_DIFF;"

    if not query == '':
        engine = create_engine(db_url)
        df_full: pd.DataFrame = pd.read_sql(query, engine)
        engine.dispose()

        return df_full

    return df_full


def get_lookup_table() -> dict:
    _lookup = {}
    engine = create_engine(db_url)

    with engine.connect() as connection:
        result = connection.execute(text("""
            SELECT sector, angle, crop_left, crop_top, crop_right, crop_bottom, scale, quality 
            FROM SCRAP_PARAMS
        """))

        for row in result:
            sector, angle, crop_left, crop_top, crop_right, crop_bottom, scale, quality = row
            _lookup[sector] = {
                'angle': angle,
                'crop': (crop_left, crop_top, crop_right, crop_bottom),
                'scale': scale,
                'quality': quality
            }

    return _lookup
