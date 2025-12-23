from django.db import connections
from django.db import models
import os
import django

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'project.settings')
django.setup()

from analysis.models import StationInfo, StationNeighbours

line = [
    {
      "station_code": "E01",
      "station_name": "Shinjuku-nishiguchi",
      "neighbour_station": "Shinjuku",
      "neighbour_station_code": "M08",
      "time_minutes": 5
    },
    {
      "station_code": "M08",
      "station_name": "Shinjuku",
      "neighbour_station": "Shinjuku-nishiguchi",
      "neighbour_station_code": "E01",
      "time_minutes": 5
    },
    {
      "station_code": "H06",
      "station_name": "Toranomon Hills",
      "neighbour_station": "Toranomon",
      "neighbour_station_code": "G07",
      "time_minutes": 5
    },
    {
      "station_code": "G07",
      "station_name": "Toranomon",
      "neighbour_station": "Toranomon Hills",
      "neighbour_station_code": "H06",
      "time_minutes": 5
    },
    {
      "station_code": "I12",
      "station_name": "Kasuga",
      "neighbour_station": "Korakuen",
      "neighbour_station_code": "M22",
      "time_minutes": 5
    },
    {
      "station_code": "M22",
      "station_name": "Korakuen",
      "neighbour_station": "Kasuga",
      "neighbour_station_code": "I12",
      "time_minutes": 5
    },
    {
      "station_code": "Y18",
      "station_name": "Yurakucho",
      "neighbour_station": "Hibiya",
      "neighbour_station_code": "H08",
      "time_minutes": 5
    },
    {
      "station_code": "H08",
      "station_name": "Hibiya",
      "neighbour_station": "Yurakucho",
      "neighbour_station_code": "Y18",
      "time_minutes": 5
    },
    {
      "station_code": "S09",
      "station_name": "Bakuro yokoyama",
      "neighbour_station": "Higashi nihombashi",
      "neighbour_station_code": "A15",
      "time_minutes": 5
    },
    {
      "station_code": "A15",
      "station_name": "Higashi nihombashi",
      "neighbour_station": "Bakuro yokoyama",
      "neighbour_station_code": "S09",
      "time_minutes": 5
    },
    {
      "station_code": "E09",
      "station_name": "Ueno-okachimachi",
      "neighbour_station": "Naka-okachimachi",
      "neighbour_station_code": "H17",
      "time_minutes": 5
    },
    {
      "station_code": "E09",
      "station_name": "Ueno-okachimachi",
      "neighbour_station": "Ueno-hirokoji",
      "neighbour_station_code": "G15",
      "time_minutes": 5
    },
    {
      "station_code": "H17",
      "station_name": "Naka-okachimachi",
      "neighbour_station": "Ueno-okachimachi",
      "neighbour_station_code": "E09",
      "time_minutes": 5
    },
    {
      "station_code": "H17",
      "station_name": "Naka-okachimachi",
      "neighbour_station": "Ueno-hirokoji",
      "neighbour_station_code": "G15",
      "time_minutes": 5
    },
    {
      "station_code": "G15",
      "station_name": "Ueno-hirokoji",
      "neighbour_station": "Ueno-okachimachi",
      "neighbour_station_code": "E09",
      "time_minutes": 5
    },
    {
      "station_code": "G15",
      "station_name": "Ueno-hirokoji",
      "neighbour_station": "Naka-okachimachi",
      "neighbour_station_code": "H17",
      "time_minutes": 5
    },
    {
      "station_code": "C12",
      "station_name": "Shin-ochanomizu",
      "neighbour_station": "Ogawamachi",
      "neighbour_station_code": "S07",
      "time_minutes": 5
    },
    {
      "station_code": "C12",
      "station_name": "Shin-ochanomizu",
      "neighbour_station": "Awajicho",
      "neighbour_station_code": "M19",
      "time_minutes": 5
    },
    {
      "station_code": "S07",
      "station_name": "Ogawamachi",
      "neighbour_station": "Shin-ochanomizu",
      "neighbour_station_code": "C12",
      "time_minutes": 5
    },
    {
      "station_code": "S07",
      "station_name": "Ogawamachi",
      "neighbour_station": "Awajicho",
      "neighbour_station_code": "M19",
      "time_minutes": 5
    },
    {
      "station_code": "M19",
      "station_name": "Awajicho",
      "neighbour_station": "Shin-ochanomizu",
      "neighbour_station_code": "C12",
      "time_minutes": 5
    },
    {
      "station_code": "M19",
      "station_name": "Awajicho",
      "neighbour_station": "Ogawamachi",
      "neighbour_station_code": "S07",
      "time_minutes": 5
    }
]

for element in line:
    try:
        new_station = StationInfo.objects.create(station_id=element["station_code"], station_fullname=element["station_name"])
    except:
        pass
    
    try:
        StationNeighbours.objects.create(station_id=element["station_code"], station_neighbour=element["neighbour_station_code"], time=element["time_minutes"])
    except:
        pass

    try:
        StationNeighbours.objects.create(station_id=element["neighbour_station_code"], station_neighbour=element["station_code"], time=element["time_minutes"])
    except:
        pass

    print(f"Added {element["station_name"]} and one of its neighbours, {element["neighbour_station"]} as a both way connection")


# =============================

def add_a_cross(fullname, lines): 

    all_platform_versions = []

    with connection.cursor() as cursor:
        # находим все версии нынешней станции и сохраняем их
        for line in lines:
            cursor.execute(f"SELECT station_id FROM station_info WHERE station_id LIKE '{line}%' AND station_fullname = '{fullname}';")
            all_platform_versions.append(cursor.fetchone()[0])

        for version1 in all_platform_versions:
            for version2 in all_platform_versions:
                if version1 != version2:
                    cursor.execute(f"INSERT INTO station_neighbours (station_id, station_neighbour, time) VALUES ('{version1}', '{version2}', 5)")
        
        return f"Inserted all {fullname} stations on every line!"


stations = [
    {"station": "Akasaka-mitsuke", "lines": ["G", "M"], "levels": "2"},
    {"station": "Aoyama-itchome", "lines": ["G", "E", "Z"], "levels": "2"},
    {"station": "Asakusa", "lines": ["G", "A"], "levels": "2"},
    {"station": "Azabu-juban", "lines": ["N", "E"], "levels": "2"},
    {"station": "Daimon", "lines": ["E", "A"], "levels": "3"},
    {"station": "Ginza", "lines": ["G", "H", "M"], "levels": "2"},
    {"station": "Hibiya", "lines": ["H", "C", "I"], "levels": "3"},
    {"station": "Higashi-ginza", "lines": ["H", "A"], "levels": "2"},
    {"station": "Higashi-shinjuku", "lines": ["F", "E"], "levels": "2"},
    {"station": "Hongo-sanchome", "lines": ["E", "M"], "levels": "2"},
    {"station": "Ichigaya", "lines": ["Y", "S", "N"], "levels": "2"},
    {"station": "Iidabashi", "lines": ["T", "Y", "N", "E"], "levels": "4"},
    {"station": "Ikebukuro", "lines": ["Y", "F", "M"], "levels": "5"},
    {"station": "Jimbocho", "lines": ["Z", "I", "S"], "levels": "3"},
    {"station": "Kasumigaseki", "lines": ["M", "C", "H"], "levels": "3"},
    {"station": "Kayabacho", "lines": ["H", "T"], "levels": "2"},
    {"station": "Kita-senju", "lines": ["C", "H"], "levels": "3"},
    {"station": "Kiyosumi-shirakawa", "lines": ["Z", "E"], "levels": "2"},
    {"station": "Kokkai-gijidomae", "lines": ["M", "C"], "levels": "2"},
    {"station": "Korakuen", "lines": ["N", "M"], "levels": "3"},
    {"station": "Kasuga", "lines": ["E", "I"], "levels": "3"},
    {"station": "Kudanshita", "lines": ["T", "Z", "S"], "levels": "3"},
    {"station": "Meiji-jingumae", "lines": ["C", "F"], "levels": "2"},
    {"station": "Mita", "lines": ["A", "I"], "levels": "2"},
    {"station": "Mitsukoshimae", "lines": ["G", "Z"], "levels": "2"},
    {"station": "Monzen-nakacho", "lines": ["T", "E"], "levels": "2"},
    {"station": "Morishita", "lines": ["S", "E"], "levels": "3"},
    {"station": "Nagatacho", "lines": ["Z", "Y", "N"], "levels": "3"},
    {"station": "Nakano-sakaue", "lines": ["M", "E"], "levels": "2"},
    {"station": "Nihombashi", "lines": ["G", "T", "A"], "levels": "2"},
    {"station": "Ningyocho", "lines": ["H", "A"], "levels": "2"},
    {"station": "Omote-sando", "lines": ["G", "Z", "C"], "levels": "1"},
    {"station": "Oshiage", "lines": ["A", "Z"], "levels": "3"},
    {"station": "Otemachi", "lines": ["M", "T", "C", "Z", "I"], "levels": "5"},
    {"station": "Roppongi", "lines": ["H", "E"], "levels": "2"},
    {"station": "Shibuya", "lines": ["G", "Z", "F"], "levels": "4"},
    {"station": "Shimbashi", "lines": ["G", "A"], "levels": "2"},
    {"station": "Shirokane-takanawa", "lines": ["N", "I"], "levels": "2"},
    {"station": "Shinjuku", "lines": ["M", "S", "E"], "levels": "5"},
    {"station": "Shinjuku-sanchome", "lines": ["F", "M", "S"], "levels": "3"},
    {"station": "Sumiyoshi", "lines": ["Z", "S"], "levels": "2"},
    {"station": "Tameike-sanno", "lines": ["G", "N"], "levels": "2"},
    {"station": "Tsukishima", "lines": ["Y", "E"], "levels": "2"},
    {"station": "Ueno", "lines": ["G", "H"], "levels": "3"},
    {"station": "Yotsuya", "lines": ["M", "N"], "levels": "2"}
]

for s in stations:
    fullname = s["station"]
    lines = s["lines"]
    print(add_a_cross(fullname, lines))