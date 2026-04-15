from django.urls import path
from .views import prediction_list, run_prediction_view, prediction_export, ai_analyze_view

urlpatterns = [
    path('', prediction_list, name='prediction_list'),
    path('run/', run_prediction_view, name='prediction_run'),
    path('export/', prediction_export, name='prediction_export'),
    path('analyze/', ai_analyze_view, name='prediction_ai_analyze'),
]
