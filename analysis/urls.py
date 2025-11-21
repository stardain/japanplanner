from django.urls import path
from . import views

# соединяет вью и пути

urlpatterns = [
    path("", views.index, name="index"),
]