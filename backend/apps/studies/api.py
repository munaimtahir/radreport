from rest_framework import viewsets, permissions
from .models import Study
from .serializers import StudySerializer

class StudyViewSet(viewsets.ModelViewSet):
    queryset = Study.objects.select_related("patient","service","service__modality").all()
    serializer_class = StudySerializer
    permission_classes = [permissions.IsAuthenticated]
    search_fields = ["accession", "patient__name", "patient__mrn", "service__name"]
    filterset_fields = ["status", "service__modality__code", "service"]
    ordering_fields = ["created_at", "accession", "status"]
