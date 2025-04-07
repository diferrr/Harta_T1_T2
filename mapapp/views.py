from rest_framework import generics
from rest_framework.response import Response
from rest_framework.views import APIView
from .models import HeatPump
from .serializers import HeatPumpSerializer
from django.shortcuts import render
from .Update_Temperatures import get_live_temperature

# ===== Карта =====
def map_view(request):
    return render(request, "map.html")

# ===== API: список объектов =====
class HeatPumpList(generics.ListAPIView):
    queryset = HeatPump.objects.all()
    serializer_class = HeatPumpSerializer

# ===== API: температура в реальном времени =====
class LiveTemperatureView(APIView):
    def get(self, request, param_name):
        try:
            t1, t2 = get_live_temperature(param_name)
            return Response({
                "T1": t1 if t1 is not None else "—",
                "T2": t2 if t2 is not None else "—"
            })
        except Exception as e:
            return Response({"error": str(e)}, status=500)
