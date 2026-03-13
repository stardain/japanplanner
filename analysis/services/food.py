"""
кастомизирует поиск, собирает инфу о ресторанах, получает время пути до ресторана, выдаёт карточку ресторана

! в какой-то момент, когда будет готово, добавить railways
! кнопка перевода ??

============== план

когда буду ускорять -- sync_to_async, bulk_create в моделях, 

3. создать бэк лк ПОЛНОСТЬЮ

- намутить сетап регистрации (вью, темплейт, урл)
- сделать фронт лк с фокусом на промотке (сделать инструкцию по использованию ресторанов)
- фича: кнопка "зарег/войти" должна заменяться на имя
- фича: сразу после зарега seamless вход
- сделать фронт лк с фокусом на промотке 
- кнопка: сохранение реста в избранные в лк
- фича: сделать названия ресторанов в избранном сохраняемой по клику информацией

7. добавить беслатное апи карт (захостить сервер в докере) и добавить путь пешком
8. порешать долбаёбские проблемы какие-нибудь
9. деплой, to be continued...

!
если наткнулся на ошибку с 0 результатами, больше не тратить попытки
!

"""

from pathlib import Path
import unicodedata
import codecs
import re
import json
import sys
import os
from math import ceil
import asyncio
import random
import time
from urllib.parse import urlencode
import django
from bs4 import BeautifulSoup
import requests
import aiohttp
from osrm import OsrmAsyncClient
from django.db import connection
from django.db import transaction

HEADERS = {
    'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/121.0.0.0 Safari/537.36',
    'Accept-Language': 'ja-JP,ja;q=0.9,en-US;q=0.8,en;q=0.7',
    'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,image/apng,*/*;q=0.8,application/signed-exchange;v=b3;q=0.7',
    'Referer': 'https://www.google.com/',
    'Upgrade-Insecure-Requests': '1',
    'Sec-Fetch-Dest': 'document',
    'Sec-Fetch-Mode': 'navigate',
    'Sec-Fetch-Site': 'cross-site',
    'Sec-Fetch-User': '?1',
    'Cache-Control': 'max-age=0',
}

API_KEY = '03735d65-c5c0-4c64-9871-ae924d6d9748'
SCRAPEOPS_ENDPOINT = 'https://proxy.scrapeops.io/v1/'


DOMAIN = 'https://tabelog.com/'
targeted_region = 'tokyo'
RESTAURANT_URL = 'https://tabelog.com/en/tokyo/rstLst/'
FEATURES = ""
url_customized_event = asyncio.Event()

def customize_search(choice: dict):

    global RESTAURANT_URL, FEATURES

    specialty_dict = {
        "washoku": "washoku",
        "izakaya": "izakaya", 
        "sushi_conveyor": "RC010202", 
        "crab": "RC011213", 
        "seafood": "seafood", 
        "ramen": "ramen", 
        "yakiniku": "yakiniku"
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

    #full_custom = json.loads(choice)

    search_url = RESTAURANT_URL + specialty_dict[choice["spec"]] + "/"
    custom_features = "?utf8=✓&" + sorting_dict[choice["sort"]] + "&"

    for addition in choice["adds"]:
        custom_features += features_dict[addition]
        custom_features += "&"

    FEATURES = custom_features
    url_customized_event.set()
    return search_url

data1 = '{"specialty": "japanese_cuisine", "sorting_method": "by_locals", "features": ["unlimited_food", "sake"]}'
data2 = '{"specialty": "izakaya", "sorting_method": "by_locals", "features": ["unlimited_drinks", "sake"]}'
data3 = '{"specialty": "grilled_meat", "sorting_method": "by_locals", "features": ["sake"]}'

#rests_asked = 5

all_pages = []
all_restaurants_info = []

def clean_text(text):
    if not text or not isinstance(text, str):
        return text
    
    # 1. Handle literal '\u0022' etc. WITHOUT using json.loads
    if '\\u' in text:
        try:
            # We use 'unicode_escape' to turn the TEXT \u0022 into the CHAR "
            # 'raw_unicode_escape' is often safer for web-scraped text
            text = text.encode('latin-1').decode('unicode_escape')
        except Exception:
            # If it fails, we just keep the original text
            pass

    # 2. Normalize (fixes the \u00A0 non-breaking spaces from Tabelog)
    text = unicodedata.normalize('NFKC', text)
    
    # 3. Clean up whitespace
    return " ".join(text.split())

def gather_all_urls(how_many_pages, search_url):
    """
    список страниц которые надо спарсить
    """
    #global all_pages
    all_pages = []
    for page in range(1, int(how_many_pages)+1):
        all_pages.append(search_url + str(page) + '/' + FEATURES)
    print("All URLs are gathered.")

    return all_pages

async def get_page_contents(session, url):

    proxy_params = {
        'api_key': API_KEY,
        'url': url,
        'country': 'jp',
    }

    scrapeops_url = f"{SCRAPEOPS_ENDPOINT}?{urlencode(proxy_params)}"

    async with session.get(scrapeops_url, timeout=120, headers=HEADERS) as response:
        html = await response.text()
        soup = BeautifulSoup(html, 'lxml') 
        data = {}

        # NAME + RATING + CATEGORY
        header = soup.find("div", class_="rstdtl-header")
        if header:
            data["name"] = clean_text(header.find("h2", class_="display-name").get_text())

            data["rating"] = clean_text(header.find("span", class_="rdheader-rating__score-val-dtl").get_text())
            
            short_desc_tag = header.find("span", class_="pillow-word")
            data["short_desc"] = clean_text(short_desc_tag.get_text()) if short_desc_tag else "0"
            
            # STATION
            station_tag = header.find("span", class_="linktree__parent-target-text")
            data["station"] = clean_text(station_tag.get_text()) if station_tag else ""

        # HOURS & CLOSED ON
        parent2 = soup.find("ul", class_="rstinfo-table__business-list")
        open_hours = {}
        if parent2:
            business_items = parent2.find_all("li", class_="rstinfo-table__business-item")
            for item in business_items:
                title_tag = item.find("p", class_="rstinfo-table__business-title")
                if title_tag:
                    # Clean day names
                    days = clean_text(title_tag.get_text()).split(", ")
                    # Clean hours list
                    hours = [clean_text(h.get_text()) for h in item.find_all("li", class_="rstinfo-table__business-dtl-text")]
                    for day in days:
                        open_hours[day] = hours

            # CLOSED ON logic
            other_info = soup.find("div", class_="rstinfo-table__business-other")
            if other_info:
                closed_text = clean_text(other_info.get_text())
                data["closed_on"] = [closed_text.split("on")[-1].strip()]
            else:
                data["closed_on"] = None
        
        data["open_hours"] = open_hours

        # FEE, PIC, LONG DESC
        try:
            fee_table = soup.find("table", class_="c-table c-table--form rstinfo-table__table")
            data['fee'] = clean_text(fee_table.find_all("tr")[-1].find("p", class_=None).get_text())
        except:
            data['fee'] = None

        pic_tag = soup.find("img", class_="p-main-photos__slider-image")
        data['main_pic'] = pic_tag.get("src") if pic_tag else None
        
        desc_tag = soup.find("div", class_="pr-comment-wrap")
        data['long_desc'] = clean_text(desc_tag.get_text()) if desc_tag else None

        print(repr(data["long_desc"]))

        return data

async def the_great_scraper(page_urls: list, rests_asked: int):

    async def fix_max_number(session, htmls, max_retries=5):
        target_url = htmls[0] if isinstance(htmls, list) else htmls
        
        for attempt in range(max_retries):
            try:
                print(f"Attempt {attempt + 1} to get max restaurant count...")
                
                proxy_params = {
                    'api_key': API_KEY,
                    'url': target_url,
                    'country': 'jp',
                    'render_js': 'true',
                    'wait_for_selector': '.c-page-count__num'
                }
                scrapeops_url = f"{SCRAPEOPS_ENDPOINT}?{urlencode(proxy_params)}"

                current_timeout = aiohttp.ClientTimeout(total=180 + (attempt * 30))
                
                async with session.get(scrapeops_url, timeout=current_timeout) as response:
                    if response.status != 200:
                        print(f"Proxy returned {response.status}. Retrying...")
                        continue

                    chunks = []
                    try:
                        while True:
                            chunk = await asyncio.wait_for(response.content.read(16384), timeout=10.0)
                            if not chunk:
                                break
                            chunks.append(chunk)
                    except asyncio.TimeoutError:
                        pass

                    html_content = b"".join(chunks).decode('utf-8', 'ignore')
                    if not html_content or len(html_content) < 500:
                        continue

                    soup = BeautifulSoup(html_content, 'lxml')
                    count_tag = soup.select('.c-page-count__num strong') or \
                                soup.select('.list-rst__page-count strong')
                    
                    if count_tag:
                        num_text = count_tag[-1].get_text(strip=True).replace(',', '')
                        result = int(num_text)
                        print(f"Found an exact limit: {result}")
                        return result

            except Exception as e:
                print(f"Attempt {attempt + 1} failed with error: {e}")
            
            wait_time = (2 ** attempt) + random.uniform(1, 3)
            print(f"Waiting {wait_time:.2f}s before retrying...")
            await asyncio.sleep(wait_time)

        print("CRITICAL: All retries failed for max restaurant count.")
        return 0

    proxy_params = {
        'api_key': API_KEY,
        'url': 'https://tabelog.com',
        'country': 'jp',
        'render_js': 'true',
    }

    ### собирает всю инфу для всех ресторанов

    async with aiohttp.ClientSession() as session:

        timeout = aiohttp.ClientTimeout(total=120)
        all_restaurant_info = []

        rests_actual_max = await fix_max_number(session, page_urls)
        rests_limit = min(rests_actual_max, 50)
        rests_exact_num = min(int(rests_asked), rests_limit)
        exact_pages = ceil(rests_exact_num/20)

        print(f"exactly this many restaurants -- {rests_exact_num}")
        print(f"we download this many pages with 20 rests on them -- {exact_pages}")

        #gather_all_urls(exact_pages, RESTAURANT_URL)

        if not url_customized_event.is_set():
            print("Event not set yet — waiting...")  # debug
            await url_customized_event.wait()
        else:
            pass

        print("is not connected yet")

        for page in page_urls:

            proxy_params['url'] = page

            async with session.get(
                url=SCRAPEOPS_ENDPOINT,
                params=proxy_params,
                timeout=timeout
            ) as response:

                print("connection created, scrapinh all links")

                search_page = await response.text()
                soup = BeautifulSoup(search_page, 'lxml')

                if rests_exact_num == 0:
                    break

                all_restaurant_links = [rest['href'] for rest in soup.find_all("a", {"class": "list-rst__rst-name-target cpy-rst-name"}, href=True)]
                for link in all_restaurant_links:

                    print(f"link is -- {link}")

                    if rests_exact_num == 0:
                        break

                    info = await get_page_contents(session, link)
                    all_restaurant_info.append(info)
                    print("One rest appended!")

                    rests_exact_num -= 1

        return all_restaurant_info

# ТЕСТ
#customize_search(random.choice([data1, data2, data3]))
#print(RESTAURANT_URL)
#gather_all_urls(exact_pages)
#print(asyncio.run(the_great_scraper(all_pages)))

###

BASE_DIR = Path(__file__).resolve().parent.parent.parent

if str(BASE_DIR) not in sys.path:
    sys.path.append(str(BASE_DIR))

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'project.settings')
django.setup()

from analysis.models import StationInfo, StationNeighbours

@transaction.atomic
def find_every_cross(start_line_id: str, end_line_id: str):
    """
    извлекает время из бд по длинным именам, находит все комбинации веток с 1-2 пересадкой
    """

    line_list = ['G', 'M', 'Mb', 'H', 'T', 'C', 'Y', 'Z', 'N', 'F', 'A', 'I', 'S', 'E']
    cross_list = []

        # 1: краевой случай: оба на одной ветке (A-A)
        #if start_line_id[0] == end_line_id[0]:
        #    return ["None"]
        # 2: находит все прямые переходы со стартовой ветки на нужную (A-B)
    def are_there_straight_crosses(start, end):
        prefix_start = start[0]
        prefix_end = end[0]
        count = StationNeighbours.objects.filter(
            station_id__startswith=prefix_start,
            station_neighbour__startswith=prefix_end
        ).count()
        return count > 0
        # 2: добавляем неопознаваемые прямые переходы (A-B)
    if are_there_straight_crosses(start_line_id, end_line_id) > 0:
        cross_list.append("Straight")
        # 3: добавляем линии переходов
    for line in line_list:
        if are_there_straight_crosses(start_line_id, line) > 0 and are_there_straight_crosses(line, end_line_id) > 0:
            cross_list.append(line)

    return (start_line_id, end_line_id, cross_list)

@transaction.atomic
def find_all_line_routes(start_station_id: str, cross_line: str, end_station_id: str):

    start_prefix = start_station_id[0]
    end_prefix = end_station_id[0]

    if cross_line == 'Straight':
        combinations = list(StationNeighbours.objects.filter(
            station_id__startswith=start_prefix,
            station_neighbour__startswith=end_prefix
        ).values_list('station_id', 'station_neighbour'))
    
    else:
        A_to_M = list(StationNeighbours.objects.filter(
            station_id__startswith=start_prefix,
            station_neighbour__startswith=cross_line
        ).values_list('station_id', 'station_neighbour'))

        M_to_B = list(StationNeighbours.objects.filter(
            station_id__startswith=cross_line,
            station_neighbour__startswith=end_prefix
        ).values_list('station_id', 'station_neighbour'))

        combinations = [(am + mb) for am in A_to_M for mb in M_to_B]

    return combinations

@transaction.atomic
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
    time_local = 0

    for ind in range(len(quickest_stations)-1):
        # ind + ind+1
        # (4, ['A07', 'A10', 'G08', 'G09'])
        # 3 2 2 5 2

        # ['A07', 'A10', 'G08'] 
        # 3 2 2 

        current_st = quickest_stations[ind]
        destination = quickest_stations[ind+1]

        if current_st[0] != quickest_stations[ind+1][0]:
            res_time = StationNeighbours.objects.filter(
                station_id=current_st, 
                station_neighbour=destination
            ).values_list('time', flat=True).first()
            if res_time is not None:
                time_local += res_time
            continue
        
        direction = 1 if current_st[-2:] < quickest_stations[ind+1][-2:] else -1
        next_st = current_st[:-2] + f"{int(current_st[-2:])+direction:02d}"
        line_prefix = f"{current_st[:-2]}%"

        query = """
            WITH RECURSIVE route AS (
                SELECT station_id, station_neighbour, time AS total_time, 1 as depth
                FROM station_neighbours
                WHERE station_id = %s AND station_neighbour = %s

            UNION ALL

                SELECT sn.station_id, sn.station_neighbour, (r.total_time + sn.time), r.depth + 1
                FROM station_neighbours sn
                INNER JOIN route r ON sn.station_id = r.station_neighbour
                WHERE r.station_neighbour <> %s
                AND r.depth < 38
                AND sn.station_neighbour LIKE %s
            )
            
            CYCLE station_neighbour SET is_cycle USING path

            SELECT total_time FROM route 
            WHERE station_neighbour = %s
            AND NOT is_cycle
            ORDER BY total_time ASC 
            LIMIT 1;
        """

        with connection.cursor() as cursor:
            # Pass variables as a tuple to the execute method
            cursor.execute(query, [current_st, next_st, destination, line_prefix, destination])
            res_time = cursor.fetchone()

        if res_time and res_time[0] is not None:
            time_local += res_time[0]

    return time_local

@transaction.atomic
def home_to_restaurant_time(home_fullname: str, restaurant_fullname: str):

    print("We're inside the home-restaurant-time function!")
    # ищем все варианты станций, на которые можем спуститься в большой станции -- где несколько станций с одним именем
    home_station_ids = list(StationInfo.objects.filter(
        station_fullname=home_fullname
    ).values_list('station_id', flat=True))

    clean_rest_name = restaurant_fullname.removesuffix(" Sta.").replace(" ", "-")

    rest_station_ids = list(StationInfo.objects.filter(
        station_fullname__iexact=clean_rest_name
    ).values_list('station_id', flat=True))

    if not rest_station_ids:
        rest_station_ids = ['M17']
    
    print(f"Home IDs: {home_station_ids}, Rest IDs: {rest_station_ids}")

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
            fast = quickest_way(home_st_id, routes_for_a_line, rest_st_id)
            print(fast)
            if fast > 0:
                best_travel_time = min(best_travel_time, fast)
    return best_travel_time

