from datetime import datetime
import pandas as pd
import numpy as np
import psycopg2

from django import forms
from django.contrib.auth.decorators import login_required
from django.db.models import Count
from django.db.models.functions import TruncMonth
from django.shortcuts import render
from django.utils.translation import gettext as _
from django.http import JsonResponse

from app.plugins import PluginBase, Menu, MountPoint


class Plugin(PluginBase):

    def main_menu(self):
        return [Menu("Reports", self.public_url(""), "fa fa-chart-line fa-fw")]

    def include_js_files(self):
        return ['Chart.min.js']

    def app_mount_points(self):
        @login_required
        def volume_graphs(request):
            x_values, y_values, updated_at_values, flights = get_data_from_db()
            label = "Volume [m³]"

            template_args = {
                'x_values': x_values,
                'y_values': y_values,
                'updated_at_values': updated_at_values,
                'label': label,
                'xy_pairs': list(zip(x_values, y_values, updated_at_values)),
                'n_piles': len(x_values),
                'flights': flights
            }

            return render(request, self.template_path("volume_graphs.html"), template_args)

        @login_required
        def get_flight_data(request):
            flight_day = request.GET.get("flightDay", "")
            x_values, y_values, updated_at_values, _ = get_data_from_db(flight_day)
            return JsonResponse({"x_values": list(x_values), "y_values": list(y_values), "updated_at_values": list(updated_at_values)})

        return [
            MountPoint('$', volume_graphs), 
            MountPoint('get_flight_data', get_flight_data)
            ]


def get_data_from_db(specific_date=None):

    conn_params = {
        "dbname": "waste_management",
        "user": "postgres",
        "password": "API",
        "host": "host.docker.internal",  # localhost // docker inspect -f '{{range .NetworkSettings.Networks}}{{.IPAddress}}{{end}}' db
        "port": "5432"
    }

    connection = psycopg2.connect(**conn_params)
    query = "SELECT * FROM SCRAP_BLV;"
    df = pd.read_sql(query, connection)
    connection.close()

    flight_days = get_all_flights(df)

    if not specific_date:
        specific_date = flight_days[0]  # get first in the list

    df = df[df['flightday'] == specific_date]

    df['volume'] = df['volume'].astype(float)
    df['pile'] = df['pile'].astype(str)
    df['updated_at'] = df['updated_at'].astype(str)

    piles_array = df['pile'].values.tolist()  # x_values
    volumes_array = df['volume'].values.tolist()  # y_values
    updated_array = df['updated_at'].values.tolist()  # updated_at_values

    return piles_array, volumes_array, updated_array, flight_days


def get_all_flights(df: pd.DataFrame):
    df['flightday'] = pd.to_datetime(df['flightday'])
    date_strings = df['flightday'].dt.strftime('%Y-%m-%d').unique().tolist()
    return date_strings


# ----------------------
#
#
# ODBC 17 not supported in ubuntu 21.04
# https://learn.microsoft.com/en-us/sql/connect/odbc/linux-mac/installing-the-microsoft-odbc-driver-for-sql-server?view=sql-server-ver16&tabs=ubuntu18-install%2Cubuntu17-install%2Cdebian8-install%2Credhat7-13-install%2Crhel7-offline
#
# connection_string = (
# r"Driver={ODBC Driver 17 for SQL Server};"
# r"Server=\\.\pipe\LOCALDB#C27096BB\tsql\query;"
# r"Database=scraps;"
# r"Trusted_Connection=yes;"
# )
# conn = pyodbc.connect(connection_string)
# query = "SELECT * FROM dbo.BLV"
# df = pd.read_sql(query, conn)
# conn.close()