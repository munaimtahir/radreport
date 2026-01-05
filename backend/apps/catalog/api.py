from rest_framework import viewsets, permissions
from .models import Modality, Service
from .serializers import ModalitySerializer, ServiceSerializer

class ModalityViewSet(viewsets.ModelViewSet):
    queryset = Modality.objects.all()
    serializer_class = ModalitySerializer
    permission_classes = [permissions.IsAuthenticated]
    search_fields = ["code", "name"]

class ServiceViewSet(viewsets.ModelViewSet):
    queryset = Service.objects.select_related("modality", "default_template").all()
    serializer_class = ServiceSerializer
    permission_classes = [permissions.IsAuthenticated]
    search_fields = ["name", "modality__code"]
    ordering_fields = ["name", "price", "tat_minutes"]
