"""

план по финалайзингу поиска: 

- протестировать скорость поиска на 50, 25, 10, 5
- создать логику передачи выбранных пунктов в поиске в запрос + передаче запроса на бэк с фронта
- сделать переход с поиска на страницу выдачи
- создать крутилку для загрузки
- прихорошить выдачу бэка для вью
- создать коннекшн вью и модели, чтобы функция вью приняла результат/вызвала функции модели
- проверить, правильно ли данные со вью ложатся на хтмл, на поиске 5 ресторанов
- создать логику перелистывания страниц по 5 ресторанов на каждой
- ...

"""

from django.shortcuts import render, redirect
from django.urls import reverse
from django.http import HttpResponse
from .services.food import gather_all_urls, get_page_contents, the_great_scraper

def rest_search(request):
    context = {'my_variable': 'Hello from Django!'}
    return render(request, 'restaurant_search.html', context)

def search_result(request):
    context = {'my_variable': 'Hello from Django!'}
    return render(request, 'search_result.html', context)

# VIEW 1: The simple search landing page
#def rest_search_page(request):
#    if request.method == "POST":
#        data = json.loads(request.body)
#        category = data.POST.get('category')
#        price_limit = data.POST.get('price')
#        additions = data.POST.getlist('additions')
#        
#        response_url = reverse('results_page') 
#        return redirect(f"{response_url}?cat={category}&max={price_limit}")

#    return render(request, 'rest_search.html')


#def search_result_page(request):
    # 1. Extract the data from the URL (request.GET)
#    cat = request.GET.get('cat')
#    max_price = request.GET.get('max')

    # 2. Call your logic from services.py
    # We pass the filters we extracted from the URL
#    data = perform_search_logic(category=cat, price=max_price)

    # 3. Inject data into the Results HTML
#    context = {
#        'items': data,
#        'filters': {'category': cat, 'price': max_price}
#    }
#    return render(request, 'search_result.html', context)