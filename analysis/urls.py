from django.urls import path
from . import views

# соединяет вью и пути

urlpatterns = [
    path("rest_search/", views.rest_search, name="search"),
    path("search_result/", views.search_result, name="result")
]