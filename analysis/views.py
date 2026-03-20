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
from django.contrib.auth import login
from django.contrib.auth.forms import AuthenticationForm
from django.contrib.auth.decorators import login_required
from django.contrib import messages
import asyncio
from urllib.parse import urlencode
from .services.food import customize_search, gather_all_urls, the_great_scraper, home_to_restaurant_time
from .forms import CustomUserCreationForm
from .models import SavedRestaurant, UserToRestaurant

def home(request):
    # This is where your search results logic usually lives
    return render(request, 'home.html')

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
                'link': item.get('link', ''),
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

        url = f"{reverse('search_result')}"
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

def check_username(request):

    username = request.GET.get('username', None)
    # Check if a user with this name already exists
    data = {
        'is_taken': CustomUserCreationForm.objects.filter(username__iexact=username).exists()
    }
    return JsonResponse(data)

def sign_in_up(request):
    # 1. Always start with empty forms for a GET request
    login_form = AuthenticationForm()
    register_form = CustomUserCreationForm()

    if request.method == 'POST':
        # 2. Check WHICH button was clicked
        if 'login_submit' in request.POST:
            # ONLY fill the login form with data
            login_form = AuthenticationForm(request, data=request.POST)
            if login_form.is_valid():
                user = login_form.get_user()
                login(request, user)
                return redirect('home')
            # If invalid, register_form stays as an empty object (no errors)

        elif 'register_submit' in request.POST:
            # ONLY fill the register form with data
            register_form = CustomUserCreationForm(request.POST)
            if register_form.is_valid():
                user = register_form.save()
                login(request, user)
                return redirect('home')
            # If invalid, login_form stays as an empty object (no errors)

    return render(request, 'registration.html', {
        'login_form': login_form,
        'register_form': register_form,
    })

@login_required
def account(request):
    # Fetch relations instead of just restaurants
    user_relations = UserToRestaurant.objects.filter(user=request.user).select_related('restaurant')
    
    return render(request, 'account.html', {'saved_items': user_relations})

def save_restaurant(request):
    if not request.user.is_authenticated:
        return JsonResponse({'status': 'error', 'message': 'Войдите в аккаунт'}, status=401)

    link = request.POST.get('link')
    print(f"DEBUG: Saving link -> {link}") # Check your terminal for this!
    
    if not link:
        return JsonResponse({'status': 'error', 'message': 'No link provided'})

    if request.method == 'POST':
        # 1. Clean the rating
        raw_rating = request.POST.get('rating')
        try:
            # Splits "4.5 / 5" and takes "4.5"
            clean_rating = float(raw_rating.split('/')[0].strip()) 
        except (ValueError, AttributeError, TypeError):
            clean_rating = None

        # 2. Find or Create the restaurant in the global DB
        # We only use 'link' to identify it uniquely
        restaurant, created = SavedRestaurant.objects.get_or_create(
            link=request.POST.get('link'),
            defaults={
                'name': request.POST.get('name'),
                'rating': clean_rating,
                'short_desc': request.POST.get('short_desc'),
                'long_desc': request.POST.get('long_desc'),
                'station': request.POST.get('station'),
                'closed_on': request.POST.get('closed_on'),
                'open_hours': request.POST.get('open_hours'),
                'fee': request.POST.get('fee'),
                'main_pic': request.POST.get('main_pic'),
                'time': request.POST.get('time')
            }
        )

        relation, rel_created = UserToRestaurant.objects.update_or_create(
            user=request.user,
            restaurant=restaurant,
            defaults={'travel_time': request.POST.get('time')}
        )

        # 3. Check if THIS specific user is already linked to THIS restaurant
        if restaurant.users.filter(id=request.user.id).exists():
            return JsonResponse({'status': 'exists', 'message': 'Уже сохранено'})
        
        # 4. Link the user to the restaurant
        restaurant.users.add(request.user)
        return JsonResponse({'status': 'success', 'message': 'Сохранено!'})

    return JsonResponse({'status': 'error', 'message': 'Invalid request'}, status=400)