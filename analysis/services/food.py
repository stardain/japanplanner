"""
кастомизирует поиск, собирает инфу о ресторанах, получает время пути до ресторана, выдаёт карточку ресторана

! в какой-то момент, когда будет готово, добавить railways
! кнопка перевода ??

============== план

2. добавить фронт -- данные из поиска -> корректная выдача

- написать весь фронт (жс) для принятия данных в запросе -> открытия страницы результатов -> выдаче собранных рестов туда (проверить пока на 5)
-- принимать в адресе пока что станцию метро, а не конкретный адрес
-- изымать станцию из инфы реста -> считать путь -> возвращать подсчитанное в выдачу
- добавить возможность перелистывать страниц и логику на фронте и бэке, что на каждой странице свои ресты (damn)

3. создать бэк лк ПОЛНОСТЬЮ
4. добавить верстку и фронт лк
5. добавить коннекшн поп-апа ресторана и сохранения в лк
6. добавить время на метро в бэк, затем во фронт
7. добавить беслатное апи карт и добавить путь пешком
8. порешать долбаёбские проблемы какие-нибудь
9. деплой, to be continued...

"""

from pathlib import Path
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

data1 = '{"specialty": "japanese_cuisine", "sorting_method": "by_locals", "features": ["unlimited_food", "sake"]}'
data2 = '{"specialty": "izakaya", "sorting_method": "by_locals", "features": ["unlimited_drinks", "sake"]}'
data3 = '{"specialty": "grilled_meat", "sorting_method": "by_locals", "features": ["sake"]}'

rests_asked = 5
rests_actual_max = 50
rests_limit = min(rests_actual_max, 50)
rests_exact_num = min(rests_asked, rests_limit)
exact_pages = ceil(rests_exact_num/20)

all_pages = []
all_restaurants_info = []

def gather_all_urls(how_many_pages):
    """
    список страниц которые надо спарсить
    """
    global all_pages
    all_pages = []
    for page in range(1, how_many_pages+1):
        all_pages.append(RESTAURANT_URL + str(page) + '/' + FEATURES)
    print("All URLs are gathered.")

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

        # ИМЯ + КАТЕГОРИЯ + ОЦЕНКА
        parent1 = soup.find("div", class_="rstdtl-header")
        data["name"] = parent1.find("h2", class_="display-name").find('span').get_text(strip=True)
        data["rating"] = parent1.find("span", class_="rdheader-rating__score-val-dtl").get_text(strip=True)

        try:
            data["short_desc"] = parent1.find("span", class_="pillow-word").get_text(strip=True)
        except Exception: 
            data["short_desc"] = 0

        # РАЙОН + БЛИЖАЙШАЯ СТАНЦИЯ
        data["station"] = parent1.find("span", class_="linktree__parent-target-text").get_text(strip=True)

        # ВРЕМЯ РАБОТЫ + КОГДА ЗАКРЫТО
        parent2 = soup.find("ul", class_="rstinfo-table__business-list")
        data["hours_raw"] = parent2.find_all("li", class_="rstinfo-table__business-item")
        open_hours = {}
        for weekday_list in hours_raw:
            days = weekday_list.find("p", class_="rstinfo-table__business-title").get_text(strip=True).split(", ")
            hours = [re.sub(r'\s+', " ", hour.text.replace("\n", " ")) for hour in weekday_list.find_all("li", class_="rstinfo-table__business-dtl-text")]
            for day in days:
                open_hours[day] = hours

        try:
            open_hours["Closed on"] = [soup.find("div", class_="rstinfo-table__business-other").get_text(strip=True).split("on")[-1]]
        except Exception:
            open_hours["Closed on"] = None
        
        data["open_hours"] = open_hours

        # КОМИССИИ

        try:
            data['fee'] = soup.find("table", class_="c-table c-table--form rstinfo-table__table").find_all("tr")[-1].find("p", class_=None).get_text(strip=True)
        except:
            data['fee'] = None

        # ОПИСАНИЕ + ГЛАВНАЯ КАРТИНКА

        try:
            data['main_pic'] = soup.find("img", class_="p-main-photos__slider-image").get("src")
        except:
            data['main_pic'] = None
        
        try:
            data['long_desc'] = soup.find("div", class_="pr-comment-wrap").get_text(strip=True)
        except:
            data['long_desc'] = None

        return data

async def the_great_scraper(page_urls: list):

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

                current_timeout = aiohttp.ClientTimeout(total=180 + (attempt * 30), sock_read=15)
                
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

        global rests_actual_max, rests_exact_num, exact_pages, rests_limit

        rests_actual_max = await fix_max_number(session, page_urls)
        rests_limit = min(rests_actual_max, 50)
        rests_exact_num = min(rests_asked, rests_limit)
        exact_pages = ceil(rests_exact_num/20)

        print(f"exactly this many restaurants -- {rests_exact_num}")
        print(f"we download this many pages with 20 rests on them -- {exact_pages}")

        gather_all_urls(exact_pages)

        await url_customized_event.wait()

        for page in page_urls:

            proxy_params['url'] = page

            async with session.get(
                url=SCRAPEOPS_ENDPOINT,
                params=proxy_params,
                timeout=timeout
            ) as response:

                search_page = await response.text()
                soup = BeautifulSoup(search_page, 'lxml')

                if rests_exact_num == 0:
                    break

                all_restaurant_links = [rest['href'] for rest in soup.find_all("a", {"class": "list-rst__rst-name-target cpy-rst-name"}, href=True)]
                for link in all_restaurant_links:

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

@transaction.atomic
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

@transaction.atomic
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

@transaction.atomic
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

