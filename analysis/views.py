"""

план по финалайзингу поиска: 

- если что-то не укажут, сделать видимую ошибку
- ...

""" 

import json
import ast
from django.shortcuts import render, redirect
from django.urls import reverse
from django.http import JsonResponse
from django.core.paginator import Paginator
import asyncio
from urllib.parse import urlencode
from .services.food import customize_search, gather_all_urls, the_great_scraper, home_to_restaurant_time


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

        hotel_fullname = user_filters['address'].removesuffix(" Sta.")

        #user_filters_json = json.dumps(user_filters)
        request.session['user_filters'] = user_filters
        
        tabelog_search_half = customize_search(user_filters)
        tabelog_search_list = gather_all_urls(amount, tabelog_search_half)
        all_restaurants_info = asyncio.run(the_great_scraper(tabelog_search_list, amount))

        all_restaurants_info_cleaned = []
        for item in all_restaurants_info:

            rest_info = {
                'name': item.get('name', ''),
                'rating': item.get('rating', ''),
                'short_desc': item.get('short_desc', ''),
                'station': item.get('station', ''),
                'closed_on': item.get('closed_on', ''),
                'open_hours': item.get('open_hours', ''),
                'fee': item.get('fee', ''),
                'main_pic': item.get('main_pic', ''),
                'long_desc': item.get('long_desc', ''),
            }

            print(rest_info['station'].strip())
            rest_info['travel_time'] = home_to_restaurant_time(hotel_fullname, rest_info['station'].strip())
            #rest_info_cleaned = clean_whole_dict(rest_info)
            all_restaurants_info_cleaned.append(rest_info)

        print(all_restaurants_info_cleaned)

        #parameters = urlencode(user_filters, doseq=True)
        request.session['restaurants'] = all_restaurants_info_cleaned

        url = f"{reverse('result')}"
        return JsonResponse({'redirect_url': url})

    context = {'ass': 'pussy'}

    return render(request, 'restaurant_search.html', context)


def search_result(request):

    all_rests = request.session.get('restaurants', [])
    filters = request.session.get('user_filters', {})

    if all_rests:
        # 1. We iterate through each restaurant INDIVIDUALLY 
        # This prevents one bad restaurant from breaking the whole page
        for rest in all_rests:
            for key, value in rest.items():
                if isinstance(value, str) and '\\u' in value:
                    try:
                        # Surgical fix for \u0026 etc.
                        rest[key] = value.encode('latin-1').decode('unicode_escape')
                    except:
                        pass
            
            # 2. THE THAW: Now specifically fix the hours
            hours = rest.get('open_hours')
            if isinstance(hours, str):
                try:
                    # Clean the string before thawing
                    # This turns "{'Mon': ...}" text into a real Dict
                    rest['open_hours'] = ast.literal_eval(hours.strip())
                except Exception as e:
                    print(f"Thaw failed for {rest.get('name')}: {e}")
                    rest['open_hours'] = {}

        # Now check the first one
        if all_rests:
             print(f"SUCCESS: {type(all_rests[0]['open_hours'])}")
    
    # 2. Setup Paginator (5 per page)
    paginator = Paginator(all_rests, 5)
    
    # 3. Get current page number from URL (defaults to 1)
    page_number = request.GET.get('page', 1)
    page_obj = paginator.get_page(page_number)

    return render(request, 'search_result.html', {
        'page_obj': page_obj,
        'filters': filters,
    })

#    context = {
#        'restaurants': request.session.get('restaurants', []),
#        'filters': request.session.get('user_filters', []) # This is the list of checked values
#    }

#    return render(request, 'search_result.html', context)
