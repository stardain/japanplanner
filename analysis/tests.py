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
    quickest = []

    for route in routes:

        if len(route) == 4:

            A = abs(int(start[-2:])-int(route[0][-2:]))
            M = abs(int(route[1][-2:])-int(route[2][-2:]))
            B = abs(int(route[3][-2:])-int(end[-2:]))
            length = A+M+B
            quickest_count = min(quickest_count, A+M+B)
            if length == quickest_count:
                quickest = route

        elif len(route) == 2:

            A = abs(int(start[-2:])-int(route[0][-2:]))
            B = abs(int(route[1][-2:])-int(end[-2:]))
            length = A+B
            quickest_count = min(quickest_count, A+B)
            if length == quickest_count:
                quickest = route
    
    quickest = [start] + list(quickest) + [end]
    time = 0

    for ind in range(0, len(quickest)-2):
        # ind + ind+1
        # (4, ['A07', 'A10', 'G08', 'G09'])

        if quickest[ind[-1]] < quickest[ind+1[-1]]:
            next_st = quickest[ind[:-1]] + str(int(quickest[ind[-1]])+1)
        else:
            next_st = quickest[ind[:-1]] + str(int(quickest[ind[-1]])-1)

        with connection.cursor() as cursor:

            cursor.execute(f"""
                    WITH RECURSIVE route AS (
                    SELECT station_id, station_neighbour, time
                    FROM station_neighbours
                    WHERE station_id == '{quickest[ind]}' AND station_neighbour == '{next_st}'

                    UNION ALL

                    SELECT station_id, station_neighbour, time
                    FROM station_neighbours sn
                    INNER JOIN route r ON sn.station_neighbour = r.station_id
                    WHERE r.station_neighbour <> '{quickest[ind+1]}'
                    )

                    SELECT SUM(time) FROM route
                    WHERE 

            """)


    return quickest_count, quickest

routes = find_all_line_routes("A07", "Straight", "G09")
print(quickest_way("A07", routes, "G09"))

#print(find_full_route("A07", "I", "N04"))
#routes = find_all_line_routes("A01", "G", "C01")
#print(quickest_way("A01", routes, "C01"))