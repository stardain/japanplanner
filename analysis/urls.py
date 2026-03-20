from django.urls import path
from . import views
from django.contrib.auth import views as auth_views

# соединяет вью и пути

urlpatterns = [
    path('', views.home, name='home'),
    path("rest_search/", views.rest_search, name="rest_search"),
    path("search_result/", views.search_result, name="search_result"),
    path("sign_in_up/", views.sign_in_up, name="sign_in_up"),
    path('ajax/validate-username/', views.check_username, name='validate_username'),
    path('account/', views.account, name='account'),
    path('save_restaurant/', views.save_restaurant, name='save_restaurant'),
    path('logout/', auth_views.LogoutView.as_view(next_page='home'), name='logout'),
    path('delete_restaurant/', views.delete_restaurant, name='delete_restaurant'),
]