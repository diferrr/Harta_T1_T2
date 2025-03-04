from rest_framework import generics
from .models import HeatPump
from .serializers import HeatPumpSerializer  # ✅ Теперь импорт работает!

class HeatPumpList(generics.ListAPIView):
    queryset = HeatPump.objects.all()
    serializer_class = HeatPumpSerializer

# Представление для отображения карты
from django.shortcuts import render

def map_view(request):
    return render(request, 'map.html')
