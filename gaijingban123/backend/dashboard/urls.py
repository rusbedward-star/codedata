from django.urls import path

from . import views


urlpatterns = [
    path("overview/", views.overview, name="overview"),
    path("metrics/", views.metrics, name="metrics"),
    path("forecast/", views.forecast, name="forecast"),
    path("ai-analysis/", views.ai_analysis, name="ai_analysis"),
    path("images/", views.images, name="images"),
    path("modules/", views.modules, name="modules"),
    path("sample-data/", views.sample_data, name="sample_data"),
    path("sample-data/import/", views.sample_data_import, name="sample_data_import"),
    path("sample-data/<str:date_key>/", views.sample_data_detail, name="sample_data_detail"),
    path("forecast-jobs/", views.forecast_job_create, name="forecast_job_create"),
    path("forecast-jobs/<str:job_id>/", views.forecast_job_detail, name="forecast_job_detail"),
    path("insights/", views.insights, name="insights"),
    path("model-detail/", views.model_detail, name="model_detail"),
    path("charts/model-forecast/", views.pyecharts_model_chart, name="pyecharts_model_chart"),
    path("charts/<str:chart_key>/", views.pyecharts_chart, name="pyecharts_chart"),
    path("media/results/<str:filename>/", views.result_image, name="result_image"),
]
