import os

from django.contrib.auth.decorators import login_required
from django.shortcuts import render, redirect
from django.http import JsonResponse
from django.conf import settings
from django.conf.urls import include, url
from django.views.static import serve
from django.utils.translation import gettext as _

import json, shutil
from app.plugins import PluginBase, Menu, MountPoint

_page: str = 'http://droneslpl.arcelormittal.com:3333'

def get_memory_stats():
    """
    Get node total memory and memory usage (Linux only)
    https://stackoverflow.com/questions/17718449/determine-free-ram-in-python
    """
    try:
        with open('/proc/meminfo', 'r') as mem:
            ret = {}
            tmp = 0
            for i in mem:
                sline = i.split()
                if str(sline[0]) == 'MemTotal:':
                    ret['total'] = int(sline[1])
                elif str(sline[0]) in ('MemFree:', 'Buffers:', 'Cached:'):
                    tmp += int(sline[1])
            ret['free'] = tmp
            ret['used'] = int(ret['total']) - int(ret['free'])

            ret['total'] *= 1024
            ret['free'] *= 1024
            ret['used'] *= 1024
        return ret
    except:
        return {}


class Plugin(PluginBase):

    def main_menu(self):
        return [Menu(_("Drone Storage"), self.public_url(''), "fa fa-cloud fa-fw")]

    def app_mount_points(self):

        @login_required
        def storage(request):
            total_disk_space, used_disk_space, free_disk_space = shutil.disk_usage('./')
            
            args = {
                'target_url': _page,
                'title': 'Diagnostic',
                'total_disk_space': total_disk_space,
                'used_disk_space': used_disk_space,
                'free_disk_space': free_disk_space
            }
            
            # Memory (Linux only)
            memory_stats = get_memory_stats()
            if 'free' in memory_stats:
                args['free_memory'] = memory_stats['free']
                args['used_memory'] = memory_stats['used']
                args['total_memory'] = memory_stats['total']
            
            return render(request, self.template_path('storage.html'), args)

        return [
            MountPoint('$', storage)
            ]
