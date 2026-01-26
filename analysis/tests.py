from pathlib import Path
import unittest
from django.test import TestCase
from django.db import connection
import os
import sys
import django

BASE_DIR = Path(__file__).resolve().parent.parent

if str(BASE_DIR) not in sys.path:
    sys.path.append(str(BASE_DIR))

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'project.settings')
django.setup()

# ЕСТЬ: функция поиска ВСЕХ ЛИНИЙ: с кроссами и прямых переходов
# ЕСТЬ: функция находящая все пути для линий и прямых переходов

# НЕ ХВАТАЕТ: нахождение быстрейшей функции + подсчёт минут
# НЕ ХВАТАЕТ: собирательной функции, которая будет запрашивать ВСЕ ВОЗМОЖНЫЕ ПУТИ (и линии, и прямые переходы), расшифровывать и те и те, находить быстрейший и выдавать время путешествия

def find_all_line_routes(start_station_id: str, cross_line: str, end_station_id: str):

    with connection.cursor() as cursor:

        if cross_line == 'Straight':
            
            cursor.execute(f"""
                SELECT station_id, station_neighbour
                FROM station_neighbours
                WHERE station_id LIKE '{start_station_id[0]}%' AND station_neighbour LIKE '{end_station_id[0]}%'
            """)

            combinations = cursor.fetchall()
        
        else:

            # A-A-M -- ищем все станции-переходы и станции на М, на которые они переходят

            cursor.execute(f"""
                SELECT station_id, station_neighbour
                FROM station_neighbours
                WHERE station_id LIKE '{start_station_id[0]}%' AND station_neighbour LIKE '{cross_line}%'
            """)
            
            A_to_M = cursor.fetchall()

            
            # M-M-B -- делаем то же самое на финальную ветку

            cursor.execute(f"""
                SELECT station_id, station_neighbour
                FROM station_neighbours
                WHERE station_id LIKE '{cross_line}%' AND station_neighbour LIKE '{end_station_id[0]}%'
            """)

            M_to_B = cursor.fetchall()

            combinations = [(am + mb) for am in A_to_M for mb in M_to_B]

    return combinations


def quickest_way(start: str, routes: list, end: str):

    quickest_count = 100
    quickest_stations = []

    for route in routes:

        if len(route) == 4:

            A = abs(int(start[-2:])-int(route[0][-2:]))
            M = abs(int(route[1][-2:])-int(route[2][-2:]))
            B = abs(int(route[3][-2:])-int(end[-2:]))
            length = A+M+B
            quickest_count = min(quickest_count, A+M+B)
            if length == quickest_count:
                quickest_stations = route

        elif len(route) == 2:

            A = abs(int(start[-2:])-int(route[0][-2:]))
            B = abs(int(route[1][-2:])-int(end[-2:]))
            length = A+B
            quickest_count = min(quickest_count, A+B)
            if length == quickest_count:
                quickest_stations = route
    
    quickest_stations = [start] + list(quickest_stations) + [end]
    time = 0

    for ind in range(len(quickest_stations)-1):
        # ind + ind+1
        # (4, ['A07', 'A10', 'G08', 'G09'])
        # 3 2 2 5 2

        if quickest_stations[ind][0] != quickest_stations[ind+1][0]:
            next_st = quickest_stations[ind+1]

            with connection.cursor() as cursor:

                cursor.execute(f"""

                SELECT time FROM station_neighbours WHERE station_id = '{quickest_stations[ind]}' AND station_neighbour = '{next_st}';

                """)

                res_time = cursor.fetchone()

            if res_time and res_time[0] is not None:
                time += res_time[0]
            
            continue

        elif quickest_stations[ind][-2:] < quickest_stations[ind+1][-2:]:
            next_st = quickest_stations[ind][:-2] + f"{int(quickest_stations[ind][-2:])+1:02d}"

        else:
            next_st = quickest_stations[ind][:-2] + f"{int(quickest_stations[ind][-2:])-1:02d}"

        with connection.cursor() as cursor:

            cursor.execute(f"""
                    WITH RECURSIVE route AS (
                        SELECT station_id, station_neighbour, time AS total_time, 1 as depth
                        FROM station_neighbours
                        WHERE station_id = '{quickest_stations[ind]}' AND station_neighbour = '{next_st}'

                    UNION ALL

                        SELECT sn.station_id, sn.station_neighbour, (r.total_time + sn.time), r.depth + 1
                        FROM station_neighbours sn
                        INNER JOIN route r ON sn.station_id = r.station_neighbour
                        WHERE r.station_neighbour <> '{quickest_stations[ind+1]}'
                        AND r.depth < 15
                    )
                    
                    SELECT total_time FROM route 
                    WHERE station_neighbour = '{quickest_stations[ind+1]}'
                    ORDER BY total_time ASC 
                    LIMIT 1; 

            """)

            res_time = cursor.fetchone()

        if res_time and res_time[0] is not None:
            time += res_time[0]

    return time

routes = find_all_line_routes("A07", "Straight", "G09")
print(routes)
print(quickest_way("A06", routes, "G09"))
