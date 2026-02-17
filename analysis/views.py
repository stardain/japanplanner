"""

план по финалайзингу поиска: 

- протестировать скорость поиска на 50, 25, 10, 5
- прихорошить выдачу бэка для вью
- создать логику перелистывания страниц по 5 ресторанов на каждой
- если что-то не укажут, сделать видимую ошибку
- ...

""" 

import json
from django.shortcuts import render, redirect
from django.urls import reverse
from django.http import JsonResponse
import asyncio
from urllib.parse import urlencode
from .services.food import customize_search, gather_all_urls, the_great_scraper

#def rest_search(request):
#    context = {'my_variable': 'Hello from Django!'}
#    return render(request, 'restaurant_search.html', context)

def rest_search(request):
    if request.method == "POST":
        data = json.loads(request.body)

        amount = data.get('amount')
        specialty = data.get('specialty')
        additions = data.get('additions', [])
        sorting = data.get('sorting')
        address = data.get('address')
        day = data.get('day')

        user_filters = {
            'best': amount,
            'spec': specialty,
            'adds': additions, 
            'sort': sorting,
            'day': day,
            'address': address,
        }

        #user_filters_json = json.dumps(user_filters)
        request.session['user_filters'] = user_filters
        
        tabelog_search_half = customize_search(user_filters)
        tabelog_search_list = gather_all_urls(amount, tabelog_search_half)
        all_restaurants_info = asyncio.run(the_great_scraper(tabelog_search_list))

        all_restaurants_info_cleaned = []
        for item in all_restaurants_info:
            all_restaurants_info_cleaned.append({
                'name': str(item.get('name', '')),
                'rating': str(item.get('rating', '')),
                'short_desc': str(item.get('short_desc', '')),
                'station': str(item.get('station', '')),
                'closed_on': str(item.get('closed_on', '')),
                'open_hours': str(item.get('open_hours', '')),
                'fee': str(item.get('fee', '')),
                'main_pic': str(item.get('main_pic', '')),
                'long_desc': str(item.get('long_desc', '')),
            })

        print(all_restaurants_info_cleaned)

        #parameters = urlencode(user_filters, doseq=True)
        request.session['restaurants'] = all_restaurants_info_cleaned

        url = f"{reverse('result')}"
        return JsonResponse({'redirect_url': url})

    context = {'ass': 'pussy'}

    return render(request, 'restaurant_search.html', context)

def search_result(request):

    context = {
        'restaurants': request.session.get('restaurants', []),
        'filters': request.session.get('user_filters', []) # This is the list of checked values
    }

    return render(request, 'search_result.html', context)
