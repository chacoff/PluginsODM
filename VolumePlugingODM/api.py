import datetime
import os
from rest_framework import serializers
from rest_framework import status
from rest_framework.response import Response
from app.api.workers import GetTaskResult, TaskResultOutputError, CheckTask
from app.models import Task
from app.plugins.views import TaskView
from django.utils.translation import gettext_lazy as _
from app.plugins.worker import run_function_async
import json

from .volume import calc_volume

class VolumeRequestSerializer(serializers.Serializer):
    area = serializers.JSONField(help_text="GeoJSON Polygon contour defining the volume area to compute")
    method = serializers.CharField(help_text="One of: [plane,triangulate,average,custom,highest,lowest]", default="triangulate", allow_blank=True)
    base = serializers.FloatField(help_text="Custom base value if method is 'custom'", required=False)
    isAbsolute = serializers.BooleanField(help_text="Calculate absolute Volume", required=False)

class TaskVolume(TaskView):
    def post(self, request, pk=None):
        task = self.get_and_check_task(request, pk)
        if task.dsm_extent is None:
            return Response({'error': _('No surface model available. From the Dashboard, select this task, press Edit, from the options make sure to check "dsm", then press Restart --> From DEM.')})

        serializer = VolumeRequestSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        area = serializer['area'].value
        method = serializer['method'].value
        custom_value = serializer.validated_data.get('base', 360)
        isAbsolute = serializer.validated_data.get('isAbsolute', False)
        points = [coord for coord in area['geometry']['coordinates'][0]]
        dsm = os.path.abspath(task.get_asset_download_path("dsm.tif"))

        try: 
            celery_task_id = run_function_async(calc_volume, input_dem=dsm, pts=points, pts_epsg=4326, base_method=method, custom_base_z=custom_value, isAbsolute=isAbsolute).task_id
            return Response({'celery_task_id': celery_task_id}, status=status.HTTP_200_OK)
        except Exception as e:
            return Response({'error': str(e)}, status=status.HTTP_200_OK)

class TaskVolumeCheck(CheckTask):
    pass

class TaskVolumeResult(GetTaskResult):
    def get(self, request, pk=None, celery_task_id=None):
        task = Task.objects.only('dsm_extent').get(pk=pk)
        return super().get(request, celery_task_id, task=task)

class SaveFile(TaskView):
    def post(self, request, pk=None, celery_task_id=None):
        data=request.data
        username = request.user.username

        try:
            cwd = os.getcwd()
            backup_dir = f'{cwd}/app/static/app/volumesfiles/{data["TaskID"]}/'
            if not os.path.exists(backup_dir):
                os.makedirs(backup_dir)

            existing_files = [f for f in os.listdir(backup_dir) if f.endswith('.geojson')]
            nbfile = len(existing_files) + 1

            date = datetime.datetime.now().isoformat(sep="-")

            file_path = f'{cwd}/app/static/app/volumesfiles/{data["TaskID"]}/{data["TaskID"]}-rev{nbfile}-{date}-{username}.geojson'
            directory = os.path.dirname(file_path)
            print(directory)
            if not os.path.exists(directory):
                os.makedirs(directory)
            with open(file_path, 'w', encoding='utf-8') as file:
                json.dump(data, file, indent=4)
            print(f"Fichier sauvegardé avec succès à : {file_path}")
            return Response('File saved', status=status.HTTP_200_OK)
        except Exception as e:
            return Response({'error': str(e)}, status=status.HTTP_200_OK)

class LoadFile(TaskView):
    def post(self, request, pk=None, celery_task_id=None):
        data=request.data

        try:
            cwd = os.getcwd()
            file_path = f'{cwd}/coreplugins/VolumePlugingODM/volumesfiles/{data["name"]}.geojson'
            directory = os.path.dirname(file_path)
            if not os.path.exists(directory):
                return
            with open(file_path, 'r', encoding='utf-8') as file:
                geojson = json.load(file)
            print(f"Fichier load avec succès à : {file_path}")
            return Response({'geoJSON' : geojson}, status=status.HTTP_200_OK)
        except json.JSONDecodeError as e:
            return Response({'error': f"Erreur de décodage JSON : {str(e)}"}, status=status.HTTP_400_BAD_REQUEST)
        except Exception as e:
            return Response({'error': str(e)}, status=status.HTTP_200_OK)