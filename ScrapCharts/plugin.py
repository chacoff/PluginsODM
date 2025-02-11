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
from requests import Response
from .webodm_access import get_factory_access, get_user_group
from .backend_api import (get_all_flights_per_factory,
                          get_flight_per_task_id,
                          organize_flight_data,
                          reorganize_data,
                          create_flight_list,
                          create_flight_df)


class Plugin(PluginBase):

    def main_menu(self):
        return [Menu(_("Rapports"), self.public_url(""), "fa fa-industry fa-fw")]

    def app_mount_points(self):

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
                'title': 'Volumes Rapports'
            }

            return render(request, self.template_path('volume_graphs.html'), args)

        @login_required
        def get_factory_flights(request):
            """ gets all the available flights in the volumes database"""

            factory = request.GET.get("factory", "")

            data: Response = get_all_flights_per_factory(factory)
            organized_data: dict = organize_flight_data(data)
            db_data: dict = reorganize_data(organized_data)

            return JsonResponse({
                'task_ids': db_data['task_ids'],
                'piles_array': [],  # db_data['piles_array'],
                'volumes_odm': db_data['volumes_odm'],
                'volumes_pix4d': [],  # db_data['volumes_pix4d'],
                'volumes_delta': [],  # db_data['volumes_delta'],
                'volumes_trench': [],  # db_data['volumes_trench'],
                'volumes_total': [],  # db_data['volumes_total'],
                'flightList': db_data['flight_days'],
                'factory': db_data['factory'],
                'sector': db_data['sector'],
                'updated_at': db_data['updated_at'],
                'pilot': db_data['pilot']
            })

        @login_required
        def get_single_flight(request):

            _id = request.GET.get('id')
            _isDev = request.GET.get('isDev')
            _fact = request.GET.get('fact')

            data = get_flight_per_task_id(_fact, _id)
            flight_data: list = create_flight_list(data)

            orto_jpg: str = f'/media/CACHE/images/settings/orthos/{_id}.jpg'

            flight_data.append(orto_jpg)

            title: str = 'Rapport ' + _fact + '-'
            args = {'row_data': flight_data, 'title': title, 'isDev': _isDev}

            return render(request, self.template_path('volume_graphs_single.html'), args)

        @login_required
        def dev_mode(request):
            """ renders page with the options for developer """

            task_id: str = request.GET.get('task_id')
            factory: str = request.GET.get('factory')
            sector: str = request.GET.get('sector')
            date: str = request.GET.get('flightdate')

            groups: list[bool] = get_user_group(request)

            data: Response = get_flight_per_task_id(factory, task_id)
            df: dict = create_flight_df(data)

            args: dict = {
                'current_user': request.user,
                'isBelval': groups[0],
                'isDiffer': groups[1],
                'isGlobal': groups[2],
                'isDev': groups[3],
                'df': df,
                'task_id': task_id,
                'factory': factory,
                'sector': sector,
                'date': date,
                'title': '-- Rapport DEV --',
            }

            return render(request, self.template_path("volume_developer.html"), args)

        @login_required
        def update_dev_db(request):
            _factory = request.GET.get('factory')
            print(_factory)

            if request.method == "POST":
                try:
                    data: list[dict[any]] = json.loads(request.body)

                    print(data)

                    return JsonResponse({'status': 'successfully updated the DB'})
                except json.JSONDecodeError:
                    return JsonResponse({'error': 'Invalid JSON data'}, status=400)
            else:
                return JsonResponse({'error': 'Invalid request method'}, status=405)

        return [
            MountPoint('$', volume_graphs),
            MountPoint('get_factory_flights', get_factory_flights),
            MountPoint('get_single_flight', get_single_flight),
            MountPoint('dev_mode', dev_mode),
            MountPoint('update_dev_db', update_dev_db)
            ]
