from django.urls import path
from .views import DashboardStatsView, ExposureLedgerView

urlpatterns = [
    path('stats/', DashboardStatsView.as_view(), name='dashboard-stats'),
    path('exposure/', ExposureLedgerView.as_view(), name='dashboard-exposure'),
]