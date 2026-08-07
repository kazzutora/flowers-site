from django.urls import path

from apps.stores import views

app_name = "stores_api"

urlpatterns = [
    path("", views.stores_api, name="list"),
]
