import os

from django.contrib.auth.decorators import login_required
from django.shortcuts import render
from django.http import JsonResponse
from django.conf import settings
from django.conf.urls import include, url
from django.views.static import serve
from django.utils.translation import gettext as _

from app.models import Project, Task
from app.plugins import PluginBase, Menu, MountPoint

import json
from .image_processing import generate_mini_ortho
from .webodm_access import (get_factory_access,
                            get_user_group,
                            get_data_from_db,
                            get_projects_with_tasks,
                            get_project_id_from_task_id,
                            get_lookup_table)
from .volumes_db import get_scrap_params, insert_to_scrap_params, delete_scrap_param_row


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
        return [Menu(_("Rapports"), self.public_url(""), "fa fa-industry fa-fw")]

    def app_mount_points(self):
        init_urls()

        @login_required
        def volume_graphs(request):
            groups: list[bool] = get_user_group(request)
            factory_access = get_factory_access(groups)

            if not factory_access:
                print(f'Error getting data from db. Factory Access: {factory_access}. Most likely is empty.')
                args = {'error': 'Factory access is unknown. Most likely user does not belong to any group.',
                        'title': 'Drone Reporting'}
                return render(request, self.template_path("volume_error.html"), args)

            args = {
                'label': "Volume [m³]",
                'isBelval': groups[0],
                'isDiffer': groups[1],
                'isGlobal': groups[2],
                'isDev': groups[3],
                'factory_access': factory_access,
                'title': 'Drone Reporting'
            }

            return render(request, self.template_path('volume_graphs.html'), args)

        @login_required
        def get_factory_flights(request):
            """ gets all the available flights in the volumes database"""

            factory = request.GET.get("factory", "")

            db_data: dict = get_data_from_db(None, factory)

            return JsonResponse({
                'task_ids': db_data['task_ids'],
                'piles_array': db_data['piles_array'],
                'volumes_odm': db_data['volumes_odm'],
                'volumes_pix4d': db_data['volumes_pix4d'],
                'volumes_delta': db_data['volumes_delta'],
                'volumes_trench': db_data['volumes_trench'],
                'volumes_total': db_data['volumes_total'],
                'flightList': db_data['flight_days'],
                'factory': db_data['factory'],
                'sector': db_data['sector'],
                'updated_at': db_data['updated_at'],
                'pilot': db_data['pilot']
            })

        @login_required
        def get_single_flight(request):

            flight_data = request.GET.get('flightData')

            row_data = json.loads(flight_data) if flight_data else []
            row_data[0] = row_data[0].strip()  # @bug fix: removes \t\t

            project_and_tasks: list[dict] = get_projects_with_tasks()
            project_id: int = get_project_id_from_task_id(project_and_tasks, row_data[0])

            orto_jpg: str = f'/media/project/{project_id}/task/{row_data[0]}/assets/odm_orthophoto/odm_orthophoto.jpg'

            row_data.append(project_id)
            row_data.append(orto_jpg)

            print(row_data)

            # TODO: mini ortho is generating manually for now
            # generate_mini_ortho(project_id, row_data[0], row_data[3])
            title: str = 'Report ' + row_data[2] + '-' + row_data[3]
            args = {'row_data': row_data, 'title': title}

            return render(request, self.template_path('volume_graphs_single.html'), args)

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
            MountPoint('get_factory_flights', get_factory_flights),
            MountPoint('get_single_flight', get_single_flight),
            MountPoint('dev_mode', dev_mode),
            MountPoint('update_dev_db', update_dev_db),
            MountPoint('delete_scrap_param', delete_scrap_param)
            ]
