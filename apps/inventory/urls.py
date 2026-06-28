from django.urls import path

from .views import (
    ChemicalListView, ChemicalCreateView,
    ChemicalDetailView, ChemicalUpdateView,
    ChemicalUpdateQuantityView,
    ChemicalAlertView, ChemicalDeactivateView
)

urlpatterns = [
    path('', ChemicalListView.as_view(), name='chemical-list'),
    path('create/', ChemicalCreateView.as_view(), name='chemical-create'),
    path('alerts/', ChemicalAlertView.as_view(), name='chemical-alerts'),
    path('<int:pk>/', ChemicalDetailView.as_view(), name='chemical-detail'),
    path('<int:pk>/update/', ChemicalUpdateView.as_view(), name='chemical-update'),
    path('<int:pk>/quantity/', ChemicalUpdateQuantityView.as_view(), name='chemical-quantity'),
    path('<int:pk>/deactivate/', ChemicalDeactivateView.as_view(), name='chemical-deactivate'),
]
