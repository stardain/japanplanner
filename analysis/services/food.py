"""
кастомизирует поиск, собирает инфу о ресторанах, получает время пути до ресторана, выдаёт карточку ресторана

! в какой-то момент, когда будет готово, добавить railways

"""

from pathlib import Path
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

2/// Поиск пути (для каждой комбинации).

3/// Растяжка путей и подсчёт минут (для каждого пути).

4/// Цикл, запускающий предыдущие функции для поиска наилучшего пути. 

pgbouncer для единоразового подключения к бд

"""

BASE_DIR = Path(__file__).resolve().parent.parent.parent

if str(BASE_DIR) not in sys.path:
    sys.path.append(str(BASE_DIR))

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'project.settings')
django.setup()

def find_every_cross(start_fullname: str, end_fullname: str):
    """
    извлекает время из бд по длинным именам, находит все комбинации веток с 1-2 пересадкой
    """
    with connection.cursor() as cursor:
        query = "SELECT station_id FROM station_info WHERE station_fullname = %s"
        cursor.execute(query, (start_fullname,))
        start_line_id = cursor.fetchone()[0][0]
        cursor.execute(query, (end_fullname,))
        end_line_id = cursor.fetchone()[0][0]

        line_list = ['G', 'M', 'Mb', 'H', 'T', 'C', 'Y', 'Z', 'N', 'F', 'A', 'I', 'S', 'E']
        cross_list = []

        # 1: краевой случай: оба на одной ветке (A-A)
        if start_line_id[0] == end_line_id[0]:
            return ["None"]
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

        return cross_list

#print(find_every_cross('Sengakuji', 'Yurakucho'))
print(find_every_cross('Sengakuji', 'Shibakoen'))



#print(line_combos_search("Tokyo", "Ginza"))