from django.urls import path
from .views import SamplePDFReportView

urlpatterns = [
    path('samples/<int:pk>/pdf/', SamplePDFReportView.as_view(), name='sample-report-pdf'),
]
