from django.db import connections
from django.db import models
import os
import django

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'project.settings')
django.setup()

from analysis.models import StationInfo, StationNeighbours

line = [
    {
      "station_code": "E-01",
      "station_name": "Shinjuku-nishiguchi",
      "neighbour_station": "Higashi-shinjuku",
      "neighbour_station_code": "E-02",
      "time_minutes": 2
    },
    {
      "station_code": "E-02",
      "station_name": "Higashi-shinjuku",
      "neighbour_station": "Wakamatsu-kawada",
      "neighbour_station_code": "E-03",
      "time_minutes": 2
    },
    {
      "station_code": "E-03",
      "station_name": "Wakamatsu-kawada",
      "neighbour_station": "Ushigome-yanagicho",
      "neighbour_station_code": "E-04",
      "time_minutes": 2
    },
    {
      "station_code": "E-04",
      "station_name": "Ushigome-yanagicho",
      "neighbour_station": "Ushigome-kagurazaka",
      "neighbour_station_code": "E-05",
      "time_minutes": 2
    },
    {
      "station_code": "E-05",
      "station_name": "Ushigome-kagurazaka",
      "neighbour_station": "Iidabashi",
      "neighbour_station_code": "E-06",
      "time_minutes": 2
    },
    {
      "station_code": "E-06",
      "station_name": "Iidabashi",
      "neighbour_station": "Kasuga",
      "neighbour_station_code": "E-07",
      "time_minutes": 2
    },
    {
      "station_code": "E-07",
      "station_name": "Kasuga",
      "neighbour_station": "Hongo-sanchome",
      "neighbour_station_code": "E-08",
      "time_minutes": 2
    },
    {
      "station_code": "E-08",
      "station_name": "Hongo-sanchome",
      "neighbour_station": "Ueno-okachimachi",
      "neighbour_station_code": "E-09",
      "time_minutes": 2
    },
    {
      "station_code": "E-09",
      "station_name": "Ueno-okachimachi",
      "neighbour_station": "Shin-okachimachi",
      "neighbour_station_code": "E-10",
      "time_minutes": 2
    },
    {
      "station_code": "E-10",
      "station_name": "Shin-okachimachi",
      "neighbour_station": "Kuramae",
      "neighbour_station_code": "E-11",
      "time_minutes": 2
    },
    {
      "station_code": "E-11",
      "station_name": "Kuramae",
      "neighbour_station": "Ryogoku",
      "neighbour_station_code": "E-12",
      "time_minutes": 2
    },
    {
      "station_code": "E-12",
      "station_name": "Ryogoku",
      "neighbour_station": "Morishita",
      "neighbour_station_code": "E-13",
      "time_minutes": 2
    },
    {
      "station_code": "E-13",
      "station_name": "Morishita",
      "neighbour_station": "Kiyosumi-shirakawa",
      "neighbour_station_code": "E-14",
      "time_minutes": 2
    },
    {
      "station_code": "E-14",
      "station_name": "Kiyosumi-shirakawa",
      "neighbour_station": "Monzen-nakacho",
      "neighbour_station_code": "E-15",
      "time_minutes": 2
    },
    {
      "station_code": "E-15",
      "station_name": "Monzen-nakacho",
      "neighbour_station": "Tsukishima",
      "neighbour_station_code": "E-16",
      "time_minutes": 2
    },
    {
      "station_code": "E-16",
      "station_name": "Tsukishima",
      "neighbour_station": "Kachidoki",
      "neighbour_station_code": "E-17",
      "time_minutes": 2
    },
    {
      "station_code": "E-17",
      "station_name": "Kachidoki",
      "neighbour_station": "Tsukijishijo",
      "neighbour_station_code": "E-18",
      "time_minutes": 2
    },
    {
      "station_code": "E-18",
      "station_name": "Tsukijishijo",
      "neighbour_station": "Shiodome",
      "neighbour_station_code": "E-19",
      "time_minutes": 2
    },
    {
      "station_code": "E-19",
      "station_name": "Shiodome",
      "neighbour_station": "Daimon",
      "neighbour_station_code": "E-20",
      "time_minutes": 2
    },
    {
      "station_code": "E-20",
      "station_name": "Daimon",
      "neighbour_station": "Akabanebashi",
      "neighbour_station_code": "E-21",
      "time_minutes": 2
    },
    {
      "station_code": "E-21",
      "station_name": "Akabanebashi",
      "neighbour_station": "Azabu-juban",
      "neighbour_station_code": "E-22",
      "time_minutes": 2
    },
    {
      "station_code": "E-22",
      "station_name": "Azabu-juban",
      "neighbour_station": "Roppongi",
      "neighbour_station_code": "E-23",
      "time_minutes": 2
    },
    {
      "station_code": "E-23",
      "station_name": "Roppongi",
      "neighbour_station": "Aoyama-itchome",
      "neighbour_station_code": "E-24",
      "time_minutes": 2
    },
    {
      "station_code": "E-24",
      "station_name": "Aoyama-itchome",
      "neighbour_station": "Kokuritsu-kyogijo",
      "neighbour_station_code": "E-25",
      "time_minutes": 2
    },
    {
      "station_code": "E-25",
      "station_name": "Kokuritsu-kyogijo",
      "neighbour_station": "Yoyogi",
      "neighbour_station_code": "E-26",
      "time_minutes": 2
    },
    {
      "station_code": "E-26",
      "station_name": "Yoyogi",
      "neighbour_station": "Shinjuku",
      "neighbour_station_code": "E-27",
      "time_minutes": 2
    },
    {
      "station_code": "E-27",
      "station_name": "Shinjuku",
      "neighbour_station": "Tochomae",
      "neighbour_station_code": "E-28",
      "time_minutes": 2
    },
    {
      "station_code": "E-28",
      "station_name": "Tochomae",
      "neighbour_station": "Nishi-shinjuku-gochome",
      "neighbour_station_code": "E-29",
      "time_minutes": 2
    },
    {
      "station_code": "E-29",
      "station_name": "Nishi-shinjuku-gochome",
      "neighbour_station": "Nakano-sakaue",
      "neighbour_station_code": "E-30",
      "time_minutes": 2
    },
    {
      "station_code": "E-30",
      "station_name": "Nakano-sakaue",
      "neighbour_station": "Higashi-nakano",
      "neighbour_station_code": "E-31",
      "time_minutes": 2
    },
    {
      "station_code": "E-31",
      "station_name": "Higashi-nakano",
      "neighbour_station": "Nakai",
      "neighbour_station_code": "E-32",
      "time_minutes": 2
    },
    {
      "station_code": "E-32",
      "station_name": "Nakai",
      "neighbour_station": "Ochiai-minami-nagaski",
      "neighbour_station_code": "E-33",
      "time_minutes": 2
    },
    {
      "station_code": "E-33",
      "station_name": "Ochiai-minami-nagaski",
      "neighbour_station": "Shin-egota",
      "neighbour_station_code": "E-34",
      "time_minutes": 2
    },
    {
      "station_code": "E-34",
      "station_name": "Shin-egota",
      "neighbour_station": "Nerima",
      "neighbour_station_code": "E-35",
      "time_minutes": 2
    },
    {
      "station_code": "E-35",
      "station_name": "Nerima",
      "neighbour_station": "Toshimaen",
      "neighbour_station_code": "E-36",
      "time_minutes": 2
    },
    {
      "station_code": "E-36",
      "station_name": "Toshimaen",
      "neighbour_station": "Nerima-kasugacho",
      "neighbour_station_code": "E-37",
      "time_minutes": 2
    },
    {
      "station_code": "E-37",
      "station_name": "Nerima-kasugacho",
      "neighbour_station": "Hikarigaoka",
      "neighbour_station_code": "E-38",
      "time_minutes": 2
    },
    {
      "station_code": "E-38",
      "station_name": "Hikarigaoka",
      "neighbour_station": "Nerima-kasugacho",
      "neighbour_station_code": "E-37",
      "time_minutes": 2
    }
  ]


# ===========================================================================

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

