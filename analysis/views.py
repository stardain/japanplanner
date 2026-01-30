from django.shortcuts import render
from django.http import HttpResponse


def index(request):
    return HttpResponse("Hello, world. You're at the polls index.")

def rest_search(request):
    context = {'my_variable': 'Hello from Django!'}
    return render(request, 'restaurant_search.html', context)

def search_result(request):
    context = {'my_variable': 'Hello from Django!'}
    return render(request, 'search_result.html', context)