from django.db.models import Sum, Count, F
from django.db.models.functions import TruncMonth, TruncYear
from rest_framework.decorators import api_view, permission_classes
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated

from apps.sales.models import SalesRecord, Product, Region


@api_view(['GET'])
@permission_classes([IsAuthenticated])
def sales_trend(request):
    """月度销售趋势（万支）"""
    year = request.query_params.get('year', '')
    qs = SalesRecord.objects.all()
    if year:
        qs = qs.filter(sale_date__year=year)

    data = (
        qs
        .annotate(month=TruncMonth('sale_date'))
        .values('month')
        .annotate(total_qty=Sum('quantity'))
        .order_by('month')
    )

    result = []
    for item in data:
        result.append({
            'month': item['month'].strftime('%Y-%m'),
            'quantity': round(item['total_qty'] / 10000, 2),
        })
    return Response(result)


@api_view(['GET'])
@permission_classes([IsAuthenticated])
def product_mix(request):
    """产品结构占比"""
    year = request.query_params.get('year', '')
    qs = SalesRecord.objects.all()
    if year:
        qs = qs.filter(sale_date__year=year)

    data = (
        qs
        .values('product__name')
        .annotate(total_qty=Sum('quantity'))
        .order_by('-total_qty')
    )

    result = [{'name': item['product__name'], 'value': item['total_qty']} for item in data]
    return Response(result)


@api_view(['GET'])
@permission_classes([IsAuthenticated])
def region_distribution(request):
    """区域销售分布"""
    year = request.query_params.get('year', '')
    qs = SalesRecord.objects.all()
    if year:
        qs = qs.filter(sale_date__year=year)

    data = (
        qs
        .values('region__district')
        .annotate(total_qty=Sum('quantity'))
        .order_by('-total_qty')
    )

    result = [
        {'name': item['region__district'], 'value': round(item['total_qty'] / 10000, 2)}
        for item in data
    ]
    return Response(result)


@api_view(['GET'])
@permission_classes([IsAuthenticated])
def channel_distribution(request):
    """渠道分布"""
    year = request.query_params.get('year', '')
    qs = SalesRecord.objects.all()
    if year:
        qs = qs.filter(sale_date__year=year)

    channel_map = {'online': '线上电商', 'offline': '线下门店', 'distributor': '经销商'}
    data = (
        qs
        .values('channel')
        .annotate(total_qty=Sum('quantity'))
        .order_by('-total_qty')
    )

    result = [
        {'name': channel_map.get(item['channel'], item['channel']), 'value': item['total_qty']}
        for item in data
    ]
    return Response(result)


@api_view(['GET'])
@permission_classes([IsAuthenticated])
def summary(request):
    """KPI汇总数据"""
    from django.db.models import Avg
    from decimal import Decimal

    # 总销量（万支）
    total_qty = SalesRecord.objects.aggregate(s=Sum('quantity'))['s'] or 0
    # 总销售额（万元）
    total_amount = SalesRecord.objects.aggregate(s=Sum('total_amount'))['s'] or Decimal('0')
    # 2025年销量
    qty_2025 = SalesRecord.objects.filter(sale_date__year=2025).aggregate(s=Sum('quantity'))['s'] or 0
    # 2024年销量
    qty_2024 = SalesRecord.objects.filter(sale_date__year=2024).aggregate(s=Sum('quantity'))['s'] or 0
    # 同比增长率
    yoy_growth = round((qty_2025 - qty_2024) / qty_2024 * 100, 2) if qty_2024 else 0

    return Response({
        'total_quantity_wan': round(total_qty / 10000, 2),
        'total_amount_wan': round(float(total_amount) / 10000, 2),
        'quantity_2025_wan': round(qty_2025 / 10000, 2),
        'quantity_2024_wan': round(qty_2024 / 10000, 2),
        'yoy_growth_pct': yoy_growth,
        'product_count': Product.objects.filter(is_active=True).count(),
        'region_count': Region.objects.filter(is_active=True).count(),
    })
