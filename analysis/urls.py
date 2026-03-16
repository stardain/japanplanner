from django.urls import path
from . import views

# соединяет вью и пути

urlpatterns = [
    path('', views.home, name='home'),
    path("rest_search/", views.rest_search, name="rest_search"),
    path("search_result/", views.search_result, name="search_result"),
    path("sign_in_up/", views.sign_in_up, name="sign_in_up"),
    path('ajax/validate-username/', views.check_username, name='validate_username'),
    path('account/', views.account, name='account')
]