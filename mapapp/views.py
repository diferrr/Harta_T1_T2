from rest_framework import generics
from rest_framework.response import Response
from rest_framework.views import APIView
from .models import HeatPump
from .serializers import HeatPumpSerializer
from django.shortcuts import render
import requests
from lxml import etree
from datetime import datetime, timedelta
import pytz

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
            pump = HeatPump.objects.get(param_name=param_name)
            if not pump.id_T1 or not pump.id_T2 or not pump.datasource_id:
                return Response({"error": "Missing param IDs or datasource"}, status=400)

            # IP источника (временно вручную или через запрос, если будет модель)
            from django.db import connection
            with connection.cursor() as cursor:
                cursor.execute("SELECT address FROM datasources_http WHERE id = %s", [pump.datasource_id])
                result = cursor.fetchone()
                if not result:
                    return Response({"error": "IP not found"}, status=400)
                ip = result[0]

            # Время
            now = datetime.now(tz=pytz.utc)
            start_ts = int((now - timedelta(hours=1)).timestamp())
            stop_ts = int(now.timestamp())

            def get_temp(param_id):
                url = f"http://{ip}/cgi-bin/xml/getrep.pl?param={param_id}&start={start_ts}&stop={stop_ts}"
                xml = requests.get(url, timeout=5).content
                root = etree.fromstring(xml)
                records = root.findall(".//record")
                if records:
                    return records[-1].findtext("value")
                return None

            t1 = get_temp(pump.id_T1)
            t2 = get_temp(pump.id_T2)

            return Response({"T1": t1, "T2": t2})

        except HeatPump.DoesNotExist:
            return Response({"error": "Not found"}, status=404)
        except Exception as e:
            return Response({"error": str(e)}, status=500)
