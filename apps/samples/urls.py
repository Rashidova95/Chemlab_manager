from django.urls import path
from .views import (
    SampleListView,
    SampleCreateView,
    SampleDetailView,
    SampleStatusUpdateView,
    SampleCSVExportView,
)

urlpatterns = [
    path('', SampleListView.as_view(), name='sample-list'),
    path('create/', SampleCreateView.as_view(), name='sample-create'),
    path('export/csv/', SampleCSVExportView.as_view(), name='sample-csv-export'),
    path('<int:pk>/', SampleDetailView.as_view(), name='sample-detail'),
    path('<int:pk>/status/', SampleStatusUpdateView.as_view(), name='sample-status-update'),
]