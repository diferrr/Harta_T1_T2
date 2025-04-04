from django.urls import path
from .views import HeatPumpList, map_view, LiveTemperatureView

urlpatterns = [
    path("api/pumps/", HeatPumpList.as_view(), name="heat-pump-list"),
    path("api/live_temp/<str:param_name>/", LiveTemperatureView.as_view(), name="live-temp"),
    path("", map_view, name="map"),
]
