from django.urls import path
from .views import sales_trend, product_mix, region_distribution, channel_distribution, summary

urlpatterns = [
    path('trend/', sales_trend, name='analytics_trend'),
    path('product-mix/', product_mix, name='analytics_product_mix'),
    path('region-dist/', region_distribution, name='analytics_region_dist'),
    path('channel-dist/', channel_distribution, name='analytics_channel_dist'),
    path('summary/', summary, name='analytics_summary'),
]
