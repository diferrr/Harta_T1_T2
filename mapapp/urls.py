from django.urls import path
from .views import HeatPumpList, map_view

urlpatterns = [
    path("api/pumps/", HeatPumpList.as_view(), name="heat-pump-list"),  # API
    path("", map_view, name="map"),  # Карта
]
