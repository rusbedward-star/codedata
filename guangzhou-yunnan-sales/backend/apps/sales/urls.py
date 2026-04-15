from django.urls import path
from .views import (
    ProductListView, RegionListView,
    SalesRecordListCreateView, SalesRecordDetailView, sales_export
)

urlpatterns = [
    path('products/', ProductListView.as_view(), name='product_list'),
    path('regions/', RegionListView.as_view(), name='region_list'),
    path('sales/', SalesRecordListCreateView.as_view(), name='sales_list'),
    path('sales/<int:pk>/', SalesRecordDetailView.as_view(), name='sales_detail'),
    path('sales/export/', sales_export, name='sales_export'),
]
