import pandas as pd
from .config import Config
from sqlalchemy import create_engine, text
from app.models import Project, Task

c: Config = Config()
db_url: str = c.db_url()


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
        factory_access = ['Belval', 'Differdange']

    if groups[1]:  # isDiffer
        factory_access = ['Differdange', 'Belval']

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
