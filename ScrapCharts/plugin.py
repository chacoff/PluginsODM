import os

from django.contrib.auth.decorators import login_required
from django.shortcuts import render
from django.http import JsonResponse
from django.conf import settings
from django.conf.urls import include, url
from django.views.static import serve

from app.models import Project, Task
from app.plugins import PluginBase, Menu, MountPoint

import json
from concurrent.futures import ThreadPoolExecutor
from .image_processing import convert_tif_to_jpg
from .webodm_access import (get_factory_access,
                            get_user_group,
                            get_data_from_db,
                            get_projects_with_tasks,
                            get_project_id_from_task_id,
                            get_lookup_table)
from .volumes_db import get_scrap_params, insert_to_scrap_params, delete_scrap_param_row

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

            template_args = {
                'label': "Volume [m³]",
                'isBelval': groups[0],
                'isDiffer': groups[1],
                'isGlobal': groups[2],
                'isDev': groups[3],
                'factory_access': factory_access
            }

            return render(request, self.template_path("volume_graphs.html"), template_args)

        @login_required
        def get_flight_data(request):
            """
            gets the data for a specific flight using the following pipeline:
                1. get_data_from_db() using flight_day (specific_date) and factory in question
                2. get_projects_with_tasks() gets all projects and tasks in webODM DB
                3. get_project_id_from_task_id() will get the project_id of a task
                4. convert_tif_to_png() will run in background
            """

            flight_day: request = request.GET.get("flightDay", "")
            factory: request = request.GET.get("factory", "")
            lookup: dict = get_lookup_table()
            media_root: str = settings.MEDIA_ROOT

            future_db_data = executor.submit(get_data_from_db, flight_day, factory)
            future_projects_tasks = executor.submit(get_projects_with_tasks)

            db_data = future_db_data.result()
            projects_tasks = future_projects_tasks.result()

            future_project_id = executor.submit(get_project_id_from_task_id, projects_tasks, db_data['task_id'])
            project_id = future_project_id.result()

            executor.submit(convert_tif_to_jpg, media_root, project_id, db_data['task_id'], db_data['sector'], lookup)

            orto_jpg: str = f'/media/project/{project_id}/task/{db_data["task_id"]}/assets/odm_orthophoto/odm_orthophoto.jpg'

            return JsonResponse({"x_values": list(db_data['piles_array']),
                                 "y_values": list(db_data['volumes_array']),
                                 "updated_at_values": list(db_data['updated_array']),
                                 "task_id": db_data['task_id'],
                                 "task_project_id": project_id,
                                 "image_url": orto_jpg,
                                 'sector_place': db_data['place']})

        @login_required
        def get_factory_flights(request):
            """ gets all the available flights in the volumes database"""

            factory = request.GET.get("factory", "")

            db_data: dict = get_data_from_db(None, factory)

            print(db_data)

            return JsonResponse({
                'piles_array': db_data['piles_array'],
                'volumes_array': db_data['volumes_array'],
                'flightList': db_data['flight_days'],
                'factory': db_data['factory'],
                'sector': db_data['sector'],
                'updated_at': db_data['updated_at'],
                'pilot': db_data['pilot']
            })

        @login_required
        def dev_mode(request):
            """ renders page with the options for developer, i.e., parameters for orthomosaic """

            groups: list[bool] = get_user_group(request)

            df = get_scrap_params(request)

            args: dict = {
                'current_user': request.user,
                'isBelval': groups[0],
                'isDiffer': groups[1],
                'isGlobal': groups[2],
                'isDev': groups[3],
                'df': df
            }

            return render(request, self.template_path("volume_developer.html"), args)

        @login_required
        def update_dev_db(request):
            if request.method == "POST":
                try:
                    data: list[dict[any]] = json.loads(request.body)
                    insert_to_scrap_params(data)
                    return JsonResponse({'status': 'successfully updated the DB'})
                except json.JSONDecodeError:
                    return JsonResponse({'error': 'Invalid JSON data'}, status=400)
            else:
                return JsonResponse({'error': 'Invalid request method'}, status=405)

        @login_required
        def delete_scrap_param(request):
            if request.method == "POST":
                try:
                    sector = request.POST.get('sector')
                    if not sector:
                        return JsonResponse({'success': False, 'error': 'No sector provided'}, status=400)

                    result = delete_scrap_param_row(sector)

                    if result.rowcount > 0:
                        return JsonResponse({'success': True, 'status': f'Sector {sector} deleted successfully'})
                    else:
                        return JsonResponse({'success': False, 'error': 'No matching sector found'}, status=404)

                except Exception as e:
                    return JsonResponse({'success': False, 'error': str(e)}, status=500)

        return [
            MountPoint('$', volume_graphs), 
            MountPoint('get_flight_data', get_flight_data),
            MountPoint('get_factory_flights', get_factory_flights),
            MountPoint('dev_mode', dev_mode),
            MountPoint('update_dev_db', update_dev_db),
            MountPoint('delete_scrap_param', delete_scrap_param)
            ]
