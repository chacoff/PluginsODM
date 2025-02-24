import os

from django.contrib.auth.decorators import login_required
from django.shortcuts import render, redirect
from django.http import JsonResponse
from django.conf import settings
from django.conf.urls import include, url
from django.views.static import serve
from django.utils.translation import gettext as _

import requests
from requests import Response
from requests.exceptions import RequestException

import json, shutil
from app.plugins import PluginBase, Menu, MountPoint

from .config import Config

c: Config = Config()

URL: str = c.get_api_url()
URL_POST: str = c.get_post_url()
TOKEN: str = c.get_token()
HEADERS: dict = c.get_headers()
_page: str = c.get_drones_storage()


class Plugin(PluginBase):

    def main_menu(self):
        return [Menu(_("Drone Control"), self.public_url(''), "fa fa-gamepad fa-fw")]

    def app_mount_points(self):

        @login_required
        def drone_control(request):
            
            args = {
                'title': 'Drone Control',
                'target_url': _page,
            }
            
            return render(request, self.template_path('control.html'), args)

        @login_required()
        def get_schedules(request):
            try:
                response = requests.get(URL, headers=HEADERS, timeout=10)
                response.raise_for_status()
                return JsonResponse(response.json(), safe=False)
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

        return [
            MountPoint('$', drone_control),
            MountPoint('get_schedules', get_schedules)
            ]
