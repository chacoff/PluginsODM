#
# it requires to add in urlpatterns of django:
#
# url(r'^media/project/(?P<path>.*)$', serve, {
#    'document_root': os.path.join(settings.MEDIA_ROOT, 'project')
# }),
#

import pandas as pd
from sqlalchemy import create_engine
import os

from django.contrib.auth.decorators import login_required
from django.shortcuts import render
from django.http import JsonResponse
from django.conf import settings

from app.models import Project, Task
from app.plugins import PluginBase, Menu, MountPoint

from PIL import Image


class Plugin(PluginBase):

    def main_menu(self):
        return [Menu("Reports", self.public_url(""), "fa fa-chart-line fa-fw")]

    def include_js_files(self):
        return ['Chart.min.js']

    def app_mount_points(self):
        @login_required
        def volume_graphs(request):
            x_values, y_values, updated_at_values, flights, task_id = get_data_from_db()
            label = "Volume [m³]"
            projects_tasks = get_projects_with_tasks()
            project_id = get_project_id_from_task_id(projects_tasks, task_id)
            orto = f'/media/project/{project_id}/task/{task_id}/assets/odm_orthophoto/odm_orthophoto.tif'

            template_args = {
                'x_values': x_values,
                'y_values': y_values,
                'updated_at_values': updated_at_values,
                'label': label,
                'xy_pairs': list(zip(x_values, y_values, updated_at_values)),
                'n_piles': len(x_values),
                'flights': flights,
                'task_id': task_id,
                'task_project_id': project_id,
                'projects_with_tasks': projects_tasks,
                'image_url': orto
            }

            return render(request, self.template_path("volume_graphs.html"), template_args)

        @login_required
        def get_flight_data(request):
            flight_day = request.GET.get("flightDay", "")
            x_values, y_values, updated_at_values, _, task_id = get_data_from_db(flight_day)
            projects_tasks = get_projects_with_tasks()
            project_id = get_project_id_from_task_id(projects_tasks, task_id)

            tiff_path = os.path.join(settings.MEDIA_ROOT,
                                     f'project/{project_id}/task/{task_id}/assets/odm_orthophoto/odm_orthophoto.tif')
            png_path = os.path.join(settings.MEDIA_ROOT,
                                    f'project/{project_id}/task/{task_id}/assets/odm_orthophoto/odm_orthophoto.png')

            print(png_path)

            if not os.path.exists(png_path):
                try:
                    with Image.open(tiff_path) as img:
                        img.save(png_path, 'PNG')
                        print(f'Properly converted from TIFF to PNG')
                except Exception as e:
                    print(f'Failed to convert TIFF to PNG: {str(e)}')

            orto_png = f'/media/project/{project_id}/task/{task_id}/assets/odm_orthophoto/odm_orthophoto.png'

            return JsonResponse({"x_values": list(x_values),
                                 "y_values": list(y_values),
                                 "updated_at_values": list(updated_at_values),
                                 "task_id": task_id,
                                 "task_project_id": project_id,
                                 "image_url": orto_png})

        return [
            MountPoint('$', volume_graphs), 
            MountPoint('get_flight_data', get_flight_data)
            ]


def get_data_from_db(specific_date=None):

    # localhost // docker inspect -f '{{range .NetworkSettings.Networks}}{{.IPAddress}}{{end}}' db
    db_url = "postgresql+psycopg2://postgres:API@host.docker.internal:5432/waste_management"

    engine = create_engine(db_url)

    query = "SELECT * FROM SCRAP_DIFF;"
    df = pd.read_sql(query, engine)

    engine.dispose()

    flight_days = get_all_flights(df)

    if not specific_date:
        specific_date = flight_days[0]  # get first in the list

    df = df[df['flightday'] == specific_date]

    df['volume_drone'] = df['volume_drone'].astype(float)
    df['pile'] = df['pile'].astype(str)
    df['updated_at'] = df['updated_at'].astype(str)

    piles_array = df['pile'].values.tolist()  # x_values
    volumes_array = df['volume_drone'].values.tolist()  # y_values
    updated_array = df['updated_at'].values.tolist()  # updated_at_values
    task_id = df['task_id'].unique().tolist()  # it should be only one, but in case. Anyway we choose element 0 later

    return piles_array, volumes_array, updated_array, flight_days, task_id[0]


def get_all_flights(df: pd.DataFrame):
    df['flightday'] = pd.to_datetime(df['flightday'])
    date_strings = df['flightday'].dt.strftime('%Y-%m-%d %H:%M:%S').unique().tolist()
    return date_strings


def get_projects_with_tasks():
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

