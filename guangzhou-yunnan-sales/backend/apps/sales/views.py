import csv
from django.http import HttpResponse
from rest_framework import generics, status
from rest_framework.decorators import api_view, permission_classes
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated

from .models import Product, Region, SalesRecord
from .serializers import ProductSerializer, RegionSerializer, SalesRecordSerializer
from apps.users.permissions import IsAdminOrReadOnly


class ProductListView(generics.ListAPIView):
    queryset = Product.objects.filter(is_active=True).order_by('id')
    serializer_class = ProductSerializer
    permission_classes = [IsAuthenticated]
    pagination_class = None


class RegionListView(generics.ListAPIView):
    queryset = Region.objects.filter(is_active=True).order_by('id')
    serializer_class = RegionSerializer
    permission_classes = [IsAuthenticated]
    pagination_class = None


class SalesRecordListCreateView(generics.ListCreateAPIView):
    serializer_class = SalesRecordSerializer
    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        qs = SalesRecord.objects.select_related('product', 'region', 'operator').all()
        params = self.request.query_params

        date_start = params.get('date_start')
        date_end = params.get('date_end')
        product_id = params.get('product_id')
        region_id = params.get('region_id')
        channel = params.get('channel')

        if date_start:
            qs = qs.filter(sale_date__gte=date_start)
        if date_end:
            qs = qs.filter(sale_date__lte=date_end)
        if product_id:
            qs = qs.filter(product_id=product_id)
        if region_id:
            qs = qs.filter(region_id=region_id)
        if channel:
            qs = qs.filter(channel=channel)

        return qs

    def perform_create(self, serializer):
        serializer.save(operator=self.request.user)


class SalesRecordDetailView(generics.RetrieveUpdateDestroyAPIView):
    queryset = SalesRecord.objects.select_related('product', 'region', 'operator').all()
    serializer_class = SalesRecordSerializer
    permission_classes = [IsAuthenticated, IsAdminOrReadOnly]

    def perform_update(self, serializer):
        serializer.save(operator=self.request.user)


@api_view(['GET'])
@permission_classes([IsAuthenticated])
def sales_export(request):
    """导出销售数据为CSV"""
    qs = SalesRecord.objects.select_related('product', 'region').all()
    params = request.query_params

    date_start = params.get('date_start')
    date_end = params.get('date_end')
    product_id = params.get('product_id')
    region_id = params.get('region_id')
    channel = params.get('channel')

    if date_start:
        qs = qs.filter(sale_date__gte=date_start)
    if date_end:
        qs = qs.filter(sale_date__lte=date_end)
    if product_id:
        qs = qs.filter(product_id=product_id)
    if region_id:
        qs = qs.filter(region_id=region_id)
    if channel:
        qs = qs.filter(channel=channel)

    response = HttpResponse(content_type='text/csv; charset=utf-8-sig')
    response['Content-Disposition'] = 'attachment; filename="sales_data.csv"'
    response.write('\ufeff')

    writer = csv.writer(response)
    writer.writerow(['销售日期', '产品名称', '区域', '渠道', '数量(支)', '单价(元)', '销售金额(元)'])
    channel_map = {'online': '线上电商', 'offline': '线下门店', 'distributor': '经销商'}

    for record in qs:
        writer.writerow([
            record.sale_date,
            record.product.name,
            record.region.name,
            channel_map.get(record.channel, record.channel),
            record.quantity,
            record.unit_price,
            record.total_amount,
        ])

    return response
