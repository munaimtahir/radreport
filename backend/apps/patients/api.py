from rest_framework import viewsets, permissions
from .models import Patient
from .serializers import PatientSerializer

class PatientViewSet(viewsets.ModelViewSet):
    queryset = Patient.objects.all()
    serializer_class = PatientSerializer
    permission_classes = [permissions.IsAuthenticated]
    search_fields = ["mrn", "patient_reg_no", "name", "phone"]
    ordering_fields = ["created_at", "mrn", "name"]
