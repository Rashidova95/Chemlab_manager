from django.urls import path

from .views import (
    ExperimentListView,
    ExperimentCreateView,
    ExperimentDetailView,
    ExperimentUpdateView,
    ExperimentApproveView,
    ExperimentRejectView,
)

urlpatterns = [
    path('', ExperimentListView.as_view(), name='experiment-list'),
    path('create/', ExperimentCreateView.as_view(), name='experiment-create'),
    path('<int:pk>/', ExperimentDetailView.as_view(), name='experiment-detail'),
    path('<int:pk>/update/', ExperimentUpdateView.as_view(), name='experiment-update'),
    path('<int:pk>/approve/', ExperimentApproveView.as_view(), name='experiment-approve'),
    path('<int:pk>/reject/', ExperimentRejectView.as_view(), name='experiment-reject'),
]
