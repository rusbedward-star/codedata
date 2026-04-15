from rest_framework import serializers
from .models import Product, Region, SalesRecord


class ProductSerializer(serializers.ModelSerializer):
    class Meta:
        model = Product
        fields = ['id', 'name', 'category', 'spec', 'unit_price', 'description', 'is_active']


class RegionSerializer(serializers.ModelSerializer):
    class Meta:
        model = Region
        fields = ['id', 'name', 'district', 'city', 'is_active']


class SalesRecordSerializer(serializers.ModelSerializer):
    product_name = serializers.CharField(source='product.name', read_only=True)
    region_name = serializers.CharField(source='region.name', read_only=True)
    region_district = serializers.CharField(source='region.district', read_only=True)
    channel_display = serializers.CharField(source='get_channel_display', read_only=True)
    operator_name = serializers.SerializerMethodField()
    quantity_wan = serializers.SerializerMethodField()
    remark = serializers.CharField(allow_blank=True, default='')

    class Meta:
        model = SalesRecord
        fields = [
            'id', 'sale_date', 'product', 'product_name',
            'region', 'region_name', 'region_district',
            'quantity', 'quantity_wan', 'unit_price', 'total_amount',
            'channel', 'channel_display', 'operator', 'operator_name',
            'remark', 'created_at'
        ]
        read_only_fields = ['id', 'total_amount', 'operator', 'created_at']

    def get_operator_name(self, obj):
        return obj.operator.full_name if obj.operator else ''

    def get_quantity_wan(self, obj):
        return round(obj.quantity / 10000, 4)
