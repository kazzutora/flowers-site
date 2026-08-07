from django.urls import path

from apps.stores import views

app_name = "stores"

urlpatterns = [
    path("", views.stores_page, name="list"),
]
