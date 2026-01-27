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
# ЕСТЬ: нахождение быстрейшей функции + подсчёт минут
# ЕСТЬ: собирательной функции, которая будет запрашивать ВСЕ ВОЗМОЖНЫЕ ПУТИ (и линии, и прямые переходы), расшифровывать и те и те, находить быстрейший и выдавать время путешествия

def find_every_cross(start_line_id: str, end_line_id: str):
    """
    извлекает время из бд по длинным именам, находит все комбинации веток с 1-2 пересадкой
    """
    with connection.cursor() as cursor:

        line_list = ['G', 'M', 'Mb', 'H', 'T', 'C', 'Y', 'Z', 'N', 'F', 'A', 'I', 'S', 'E']
        cross_list = []

        # 1: краевой случай: оба на одной ветке (A-A)
        #if start_line_id[0] == end_line_id[0]:
        #    return ["None"]
        # 2: находит все прямые переходы со стартовой ветки на нужную (A-B)
        def are_there_straight_crosses(start, end):
            cursor.execute(f"SELECT station_id, station_neighbour FROM station_neighbours WHERE station_id LIKE '{start[0]}%' AND station_neighbour LIKE '{end[0]}%'")
            return len(cursor.fetchall())
        # 2: добавляем неопознаваемые прямые переходы (A-B)
        if are_there_straight_crosses(start_line_id, end_line_id) > 0:
            cross_list.append("Straight")
        # 3: добавляем линии переходов
        for line in line_list:
            if are_there_straight_crosses(start_line_id, line) > 0 and are_there_straight_crosses(line, end_line_id) > 0:
                cross_list.append(line)

        return (start_line_id, end_line_id, cross_list)


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

        elif route[1] == end:
            # после перехода сразу попадаем на корректную станцию, конец = станция перехода

            length = abs(int(start[-2:])-int(route[0][-2:]))
            quickest_count = min(quickest_count, length)
            if length == quickest_count:
                quickest_stations = route[:-1]

        elif route[0] == start:
            # после перехода сразу попадаем на корректную станцию, начало = станция перехода

            length = abs(int(route[1][-2:])-int(end[-2:]))
            quickest_count = min(quickest_count, length)
            if length == quickest_count:
                quickest_stations = route[1:]

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

        # ['A07', 'A10', 'G08'] 
        # 3 2 2 

        current_st = quickest_stations[ind]
        destination = quickest_stations[ind+1]

        if current_st[0] != quickest_stations[ind+1][0]:

            with connection.cursor() as cursor:

                cursor.execute(f"""

                SELECT time FROM station_neighbours WHERE station_id = '{current_st}' AND station_neighbour = '{destination}';

                """)

                res_time = cursor.fetchone()

            if res_time and res_time[0] is not None:
                time += res_time[0]
            
            continue
        
        direction = 1 if current_st[-2:] < quickest_stations[ind+1][-2:] else -1
        next_st = current_st[:-2] + f"{int(current_st[-2:])+direction:02d}"

        with connection.cursor() as cursor:

            cursor.execute(f"""
                    WITH RECURSIVE route AS (
                        SELECT station_id, station_neighbour, time AS total_time, 1 as depth
                        FROM station_neighbours
                        WHERE station_id = '{current_st}' AND station_neighbour = '{next_st}'

                    UNION ALL

                        SELECT sn.station_id, sn.station_neighbour, (r.total_time + sn.time), r.depth + 1
                        FROM station_neighbours sn
                        INNER JOIN route r ON sn.station_id = r.station_neighbour
                        WHERE r.station_neighbour <> '{destination}'
                        AND r.depth < 38
                        AND sn.station_neighbour LIKE '{current_st[:-2]}%'
                    )
                    
                    CYCLE station_neighbour SET is_cycle USING path

                    SELECT total_time FROM route 
                    WHERE station_neighbour = '{destination}'
                    AND NOT is_cycle
                    ORDER BY total_time ASC 
                    LIMIT 1; 

            """)

            res_time = cursor.fetchone()

        if res_time and res_time[0] is not None:
            time += res_time[0]

    return time


def home_to_restaurant_time(home_fullname: str, restaurant_fullname: str):

    # ищем все варианты станций, на которые можем спуститься в большой станции -- где несколько станций с одним именем
    with connection.cursor() as cursor:
        query = "SELECT station_id FROM station_info WHERE station_fullname = %s"
        cursor.execute(query, (home_fullname,))
        home_station_ids = [name[0] for name in cursor.fetchall()]
        cursor.execute(query, (restaurant_fullname,))
        rest_station_ids = [name[0] for name in cursor.fetchall()]
        combinations = [[start, end] for start in home_station_ids for end in rest_station_ids]

    best_travel_time = 100

    for comb in combinations:

        home_station, restaurant_station = comb

        # every suitable line
        # ['Straight', 'H', 'T', 'Z', 'A', 'I', 'S', 'E']
        home_st_id, rest_st_id, every_cross = find_every_cross(home_station, restaurant_station)

        for cross in every_cross:
            # every variant of getting on this line
            # [('A18', 'G19'), ('A13', 'G11'), ('A10', 'G08')]
            routes_for_a_line = find_all_line_routes(home_st_id, cross, rest_st_id)
            best_travel_time = min(best_travel_time, quickest_way(home_st_id, routes_for_a_line, rest_st_id))

    return best_travel_time


print(home_to_restaurant_time("Magome", "Shiodome"))