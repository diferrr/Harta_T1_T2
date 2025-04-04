from rest_framework import serializers
from .models import HeatPump


class HeatPumpSerializer(serializers.ModelSerializer):
    class Meta:
        model = HeatPump
        fields = "__all__"