"""
tabelog
https://www.kaggle.com/code/jenniferzheng0430/tabelog-restaurants-scraper
"""

import time
from bs4 import BeautifulSoup
import requests
import csv
import pandas as pd
from math import ceil
import lxml
import asyncio
import aiohttp
import json

DOMAIN = 'https://tabelog.com/'
targeted_region = 'tokyo'
RESTAURANT_URL = 'https://tabelog.com/en/' + targeted_region + "/rstLst/"
FEATURES = ""
url_customized_event = asyncio.Event()

"""

Функции ниже кастомизируют поиск.

"""

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

# Функции ниже получают ссылки на n ресторанов, подходящих под кастомизированный поиск. 

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
                          
    return [rest['href'] for rest in soup.find_all("a", {"class": "list-rst__rst-name-target cpy-rst-name"},href=True)]

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


jsonnn = "{\"specialty\":\"ramen\",\"sorting_method\":\"by_locals\",\"features\":[\"unlimited_drinks\",\"smoking\"]}"
customize_search(jsonnn)

gather_all_urls(exact_pages)

links = asyncio.run(scrape_urls(all_pages))

for ind, link in enumerate(links, start=1):
    print(f"{ind}. {link}")


"""

Функции ниже извлекают всю необходимую информацию из каждого ресторана. 

1. название + категория (высоко по выбранному рейтингу -> автоматически пиздато)
2. район + ближайшая станция (близко ехать)
3. время работы + когда закрыто (если) (чтобы не объебаться со днём)
4. описание + главная картинка (чтобы не забыть, что там прикольного)

"""


def scrape(url):
    r = requests.get(url)
    soup = BeautifulSoup(r.content, 'html.parser')

    # <table class="c-table rd-detail-info">
    table = soup.find("table", class_ = "c-table rd-detail-info")
    rows = table.tbody.find_all('tr')
    
    res_info = {}
    for row in rows:
        res_info[row.find('th').text.strip()] = row.find('td').text.strip().replace('\n','')
#     print(res_info)
    
    return res_info


#restaurants_info = []
#for url in links:
#    cur_restaurant = scrape(url)
#    restaurants_info.append(cur_restaurant)

#df = pd.DataFrame.from_dict(restaurants_info)
#df.to_csv('restaurants_tokyo.csv')