"""
管理命令：初始化系统基础数据
用法：python manage.py init_data
"""
from django.core.management.base import BaseCommand
from django.contrib.auth import get_user_model
from apps.sales.models import Product, Region, SalesRecord
from apps.predictions.models import PredictionResult, PredictionParam
from decimal import Decimal
import random
from datetime import date

User = get_user_model()


class Command(BaseCommand):
    help = '初始化系统基础数据（用户、产品、区域、销售记录、预测结果）'

    def handle(self, *args, **options):
        self.stdout.write('开始初始化数据...')
        self._create_users()
        self._create_products()
        self._create_regions()
        self._create_sales_records()
        self._create_prediction_data()
        self.stdout.write(self.style.SUCCESS('数据初始化完成！'))

    def _create_users(self):
        if not User.objects.filter(username='admin').exists():
            User.objects.create_superuser(
                username='admin',
                password='admin123',
                full_name='系统管理员',
                email='admin@yunnan.com',
                role='admin',
            )
            self.stdout.write('  创建管理员用户: admin / admin123')

        if not User.objects.filter(username='operator').exists():
            User.objects.create_user(
                username='operator',
                password='op123456',
                full_name='销售操作员',
                email='operator@yunnan.com',
                role='operator',
            )
            self.stdout.write('  创建操作员用户: operator / op123456')

    def _create_products(self):
        products_data = [
            ('牙膏经典装',   '药物牙膏', '210g', Decimal('28.80'), '经典配方，防治牙龈出血、口腔溃疡'),
            ('牙膏薄荷爽型', '药物牙膏', '180g', Decimal('26.50'), '薄荷清凉配方，清新口气'),
            ('牙膏冰爽型',   '药物牙膏', '200g', Decimal('29.90'), '冰爽清凉，深层洁净'),
            ('牙膏留兰香型', '药物牙膏', '180g', Decimal('26.50'), '留兰香型，温和配方'),
            ('牙膏美白型',   '功效牙膏', '120g', Decimal('32.00'), '温和美白，去黄去渍'),
        ]
        for name, category, spec, price, desc in products_data:
            Product.objects.get_or_create(
                name=name,
                defaults={'category': category, 'spec': spec, 'unit_price': price, 'description': desc}
            )
        self.stdout.write(f'  产品数据：{Product.objects.count()}条')

    def _create_regions(self):
        regions_data = [
            ('天河区代理点', '天河区'),
            ('越秀区代理点', '越秀区'),
            ('海珠区代理点', '海珠区'),
            ('荔湾区代理点', '荔湾区'),
            ('番禺区代理点', '番禺区'),
            ('花都区代理点', '花都区'),
            ('白云区代理点', '白云区'),
            ('南沙区代理点', '南沙区'),
        ]
        for name, district in regions_data:
            Region.objects.get_or_create(name=name, defaults={'district': district, 'city': '广州'})
        self.stdout.write(f'  区域数据：{Region.objects.count()}条')

    def _create_sales_records(self):
        if SalesRecord.objects.exists():
            self.stdout.write('  销售记录已存在，跳过')
            return

        products = list(Product.objects.all())
        regions = list(Region.objects.all())
        operator = User.objects.filter(role='admin').first()

        # 月度总销量（万支） 2024-2025
        monthly_totals = {
            '2024-01': 580000, '2024-02': 540000, '2024-03': 610000,
            '2024-04': 760000, '2024-05': 570000, '2024-06': 590000,
            '2024-07': 640000, '2024-08': 700000, '2024-09': 880000,
            '2024-10': 670000, '2024-11': 820000, '2024-12': 490000,
            '2025-01': 600000, '2025-02': 560000, '2025-03': 630000,
            '2025-04': 790000, '2025-05': 590000, '2025-06': 610000,
            '2025-07': 660000, '2025-08': 720000, '2025-09': 910000,
            '2025-10': 700000, '2025-11': 850000, '2025-12': 510000,
        }

        # 分配比例
        product_ratios = [0.30, 0.25, 0.20, 0.15, 0.10]
        region_ratios  = [0.18, 0.15, 0.14, 0.12, 0.13, 0.10, 0.11, 0.07]
        channel_ratios = [('online', 0.35), ('offline', 0.45), ('distributor', 0.20)]

        records = []
        for month_str, total in monthly_totals.items():
            year, month = map(int, month_str.split('-'))
            sale_date = date(year, month, 15)

            for p_idx, product in enumerate(products):
                for r_idx, region in enumerate(regions):
                    for channel, c_ratio in channel_ratios:
                        qty = round(total * product_ratios[p_idx] * region_ratios[r_idx] * c_ratio)
                        if qty <= 0:
                            continue
                        price = product.unit_price
                        records.append(SalesRecord(
                            sale_date=sale_date,
                            product=product,
                            region=region,
                            quantity=qty,
                            unit_price=price,
                            total_amount=qty * price,
                            channel=channel,
                            operator=operator,
                            remark='',
                        ))

        SalesRecord.objects.bulk_create(records, batch_size=500)
        self.stdout.write(f'  销售记录：{SalesRecord.objects.count()}条')

    def _create_prediction_data(self):
        prediction_data = [
            ('2026-03', Decimal('62.45'),  None,              '节后常态化补货'),
            ('2026-04', Decimal('58.12'),  Decimal('-6.93'),  '市场平淡期'),
            ('2026-05', Decimal('65.78'),  Decimal('13.18'),  '劳动节促销预热'),
            ('2026-06', Decimal('82.34'),  Decimal('25.17'),  '年中618电商大促'),
            ('2026-07', Decimal('61.23'),  Decimal('-25.64'), '促后需求回落'),
            ('2026-08', Decimal('63.45'),  Decimal('3.63'),   '夏季口腔护理周'),
            ('2026-09', Decimal('68.91'),  Decimal('8.61'),   '开学季推广'),
            ('2026-10', Decimal('75.34'),  Decimal('9.33'),   '国庆长假效应'),
            ('2026-11', Decimal('94.56'),  Decimal('25.51'),  '双11年度巅峰'),
            ('2026-12', Decimal('72.18'),  Decimal('-23.67'), '年终库存清理'),
            ('2027-01', Decimal('88.67'),  Decimal('22.84'),  '春节前囤货季'),
            ('2027-02', Decimal('52.34'),  Decimal('-40.97'), '春节假期物流停运'),
        ]

        for month, qty, mom, factors in prediction_data:
            PredictionResult.objects.update_or_create(
                month=month,
                defaults={
                    'predicted_quantity': qty,
                    'mom_change_pct': mom,
                    'key_factors': factors,
                    'model_type': 'SARIMA',
                }
            )

        params_data = [
            ('base_value',       Decimal('61.200000'), '基础销量（万支）'),
            ('trend_rate',       Decimal('0.250000'),  '月度线性增长率（万支/月）'),
            ('seasonal_jan',     Decimal('1.424000'),  '1月季节指数'),
            ('seasonal_feb',     Decimal('0.842000'),  '2月季节指数'),
            ('seasonal_mar',     Decimal('1.003000'),  '3月季节指数'),
            ('seasonal_apr',     Decimal('0.934000'),  '4月季节指数'),
            ('seasonal_may',     Decimal('1.058000'),  '5月季节指数'),
            ('seasonal_jun',     Decimal('1.323000'),  '6月季节指数'),
            ('seasonal_jul',     Decimal('0.985000'),  '7月季节指数'),
            ('seasonal_aug',     Decimal('1.020000'),  '8月季节指数'),
            ('seasonal_sep',     Decimal('1.108000'),  '9月季节指数'),
            ('seasonal_oct',     Decimal('1.211000'),  '10月季节指数'),
            ('seasonal_nov',     Decimal('1.521000'),  '11月季节指数'),
            ('seasonal_dec',     Decimal('1.161000'),  '12月季节指数'),
        ]
        for name, val, desc in params_data:
            PredictionParam.objects.update_or_create(
                param_name=name,
                defaults={'param_value': val, 'description': desc}
            )

        self.stdout.write(f'  预测结果：{PredictionResult.objects.count()}条')
