"""
кастомизирует поиск, собирает инфу о ресторанах, получает время пути до ресторана, выдаёт карточку ресторана

! в какой-то момент, когда будет готово, добавить railways

"""

import re
import json
import sys
import os
import django
from math import ceil
import asyncio
from bs4 import BeautifulSoup
import requests
import aiohttp
from osrm import OsrmAsyncClient
from django.db import connection

DOMAIN = 'https://tabelog.com/'
targeted_region = 'tokyo'
RESTAURANT_URL = 'https://tabelog.com/en/' + targeted_region + "/rstLst/"
FEATURES = ""
url_customized_event = asyncio.Event()

def customize_search(choice):

    global RESTAURANT_URL, FEATURES

    specialty_dict = {
        "japanese_cuisine": "washoku/",
        "izakaya": "izakaya/", 
        "sushi_conveyor": "RC010202/", 
        "crab": "RC011213/", 
        "seafood": "seafood/", 
        "ramen": "ramen/", 
        "grilled_meat": "yakiniku/"
    }

    sorting_dict = {
        "by_locals": "SrtT=inbound_vacancy_net_yoyaku", 
        "by_rating": "SrtT=rt", 
        "by_reservations": "SrtT=inbound_most_reserved" 
    }

    features_dict = {
        "unlimited_drinks": "ChkNomihoudai=1",
        "unlimited_food": "ChkTabehoudai=1",
        "smoking": "LstSmoking=3", 
        "sake": "ChkSake=1", 
        "shochu": "ChkShochu=1"
    }

    full_custom = json.loads(choice)

    RESTAURANT_URL = RESTAURANT_URL + specialty_dict[full_custom["specialty"]]
    custom_features = "?utf8=✓&" + sorting_dict[full_custom["sorting_method"]] + "&"

    for feature in full_custom["features"]:
        custom_features += features_dict[feature]
        custom_features += "&"

    FEATURES = custom_features
    url_customized_event.set()
    return RESTAURANT_URL

rests_asked = 3
rests_actual_max = 100
rests_limit = min(rests_actual_max, 100)
rests_exact_num = min(rests_asked, rests_limit)
#rests_exact_num = min(rests_asked, 100)
exact_pages = ceil(rests_exact_num/20)
all_pages = []

def gather_all_urls(how_many_pages):
    """
    список страниц которые надо спарсить
    """
    for page in range(1, how_many_pages+1):
        all_pages.append(RESTAURANT_URL + str(page) + '/' + FEATURES)

async def fetch_one_html(session, url):
    """
    полностью скачать страницу 
    """
    async with session.get(url) as response:
        return await response.text()

def parse_all_rests_from_one_page(html):
    """
    извлечь только нужное со страницы т.е. все ссылки на рестораны
    """
    soup = BeautifulSoup(html, 'lxml')
                          
    return [rest['href'] for rest in soup.find_all("a", {"class": "list-rst__rst-name-target cpy-rst-name"}, href=True)]

async def fetch_and_parse(session, url):
    """
    одновременно ебашит обе функции выше
    """
    html = await fetch_one_html(session, url)
    return parse_all_rests_from_one_page(html)

async def scrape_urls(urls: list):
    """
    делает основную работу
    """

    async def fix_max_number(htmls):
        async with aiohttp.ClientSession() as sess:
            page = await fetch_one_html(sess, htmls[0])
            soup = BeautifulSoup(page, 'lxml')
            return soup.find_all('span', class_='c-page-count__num')[-1].find('strong').text

    global rests_actual_max
    rests_actual_max = await fix_max_number(urls)

    await url_customized_event.wait()
    async with aiohttp.ClientSession() as main_session:
        all = await asyncio.gather(*[fetch_and_parse(main_session, url) for url in urls])
        all_together = [rest for page in all for rest in page]
        rests_correct_num = []

        for rest in range(rests_exact_num):
            rests_correct_num.append(all_together[rest])

        return rests_correct_num

def get_page_contents(url):
    r = requests.get(url, timeout=5)
    soup = BeautifulSoup(r.content, 'lxml')

    # ИМЯ + КАТЕГОРИЯ + ОЦЕНКА
    parent1 = soup.find("div", class_="rstdtl-header")
    name = parent1.find("h2", class_="display-name").find('span').text
    short_desc = parent1.find("span", class_="pillow-word").text
    rating = parent1.find("span", class_="rdheader-rating__score-val-dtl").text

    # РАЙОН + БЛИЖАЙШАЯ СТАНЦИЯ
    station = parent1.find("span", class_="linktree__parent-target-text").text

    # ВРЕМЯ РАБОТЫ + КОГДА ЗАКРЫТО
    parent2 = soup.find("ul", class_="rstinfo-table__business-list")
    hours_raw = parent2.find_all("li", class_="rstinfo-table__business-item")
    open_hours = {}

    for weekday_list in hours_raw:
        days = weekday_list.find("p", class_="rstinfo-table__business-title").text.strip().split(", ")
        hours = [re.sub(r'\s+', " ", hour.text.replace("\n", " ")) for hour in weekday_list.find_all("li", class_="rstinfo-table__business-dtl-text")]
        for day in days:
            open_hours[day] = hours

    open_hours["Closed on"] = [soup.find("div", class_="rstinfo-table__business-other").text.split("on")[-1].strip()]

    # КОМИССИИ

    fee = soup.find("table", class_="c-table c-table--form rstinfo-table__table").find_all("tr")[-1].find("p", class_=None).text

    # ОПИСАНИЕ + ГЛАВНАЯ КАРТИНКА

    main_pic = soup.find("img", class_="p-main-photos__slider-image").get("src")
    long_desc = soup.find("div", class_="pr-comment-wrap").text.strip()

    return name, station, rating, short_desc, long_desc, open_hours, fee, main_pic

"""
Этапы:

1. Написать связи веток в таблицу с соседями.

2. Написать функцию-помощника, принимающую стартовую станцию, станцию-цель, список путей по веткам (глобально) и направление поиска (вверх/вниз). 
Наматывает свой личный счётчик пройденных станций и сами станции, возвращает их. 
По нахождении станции-перехода на нужную ветку, запускает себя для неё. 
Если мы находимся на нужной ветке, то игнорирует направление, это краевой случай. 
3. Написать функцию, собирающую по лучшему пути общее время в метро. Это итоговая функция. 

pgbouncer для единоразового подключения к бд

            WITH RECURSIVE ? AS (
                       SELECT n

                       UNION ALL

                       SELECT m
                       FROM ?
                       WHERE n = m

                       )
            SELECT ?? from ?

"""

PARENT_DIR = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
sys.path.append(PARENT_DIR)

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'project.settings')
django.setup()

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
                    cursor.execute(f"INSERT INTO station_neighbours (station_id, station_neighbours, time) VALUES ('{version1}', '{version2}', 5)")
        
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









def line_combos_search(start_fullname: str, end_fullname: str):
    """
    извлекает время из бд по длинным именам, находит все комбинации веток для достижения нужной
    """
    with connection.cursor() as cursor:
        query = "SELECT station_id FROM station_info WHERE station_fullname = %s"
        cursor.execute(query, (start_fullname,))
        start_ids = cursor.fetchall()
        cursor.execute(query, (end_fullname,))
        end_ids = cursor.fetchall()


        
        cursor.close()
        return start_ids, end_ids

    
#print(line_combos_search("Tokyo", "Ginza"))