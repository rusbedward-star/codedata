from django.db import models
from django.conf import settings


class Product(models.Model):
    name = models.CharField('产品名称', max_length=100)
    category = models.CharField('产品类别', max_length=50, default='')
    spec = models.CharField('规格', max_length=50, default='')
    unit_price = models.DecimalField('单价(元)', max_digits=10, decimal_places=2, default=0)
    description = models.TextField('描述', default='')
    is_active = models.BooleanField('启用', default=True)
    created_at = models.DateTimeField('创建时间', auto_now_add=True)

    class Meta:
        db_table = 'sales_product'
        verbose_name = '产品'
        verbose_name_plural = '产品管理'
        ordering = ['id']

    def __str__(self):
        return self.name


class Region(models.Model):
    name = models.CharField('代理点名称', max_length=50)
    district = models.CharField('区域', max_length=50, default='')
    city = models.CharField('城市', max_length=50, default='广州')
    is_active = models.BooleanField('启用', default=True)

    class Meta:
        db_table = 'sales_region'
        verbose_name = '区域'
        verbose_name_plural = '区域管理'
        ordering = ['id']

    def __str__(self):
        return self.name


class SalesRecord(models.Model):
    CHANNEL_CHOICES = [
        ('online', '线上电商'),
        ('offline', '线下门店'),
        ('distributor', '经销商'),
    ]

    sale_date = models.DateField('销售日期')
    product = models.ForeignKey(Product, on_delete=models.PROTECT, verbose_name='产品')
    region = models.ForeignKey(Region, on_delete=models.PROTECT, verbose_name='区域')
    quantity = models.IntegerField('销售数量(支)', default=0)
    unit_price = models.DecimalField('单价(元)', max_digits=10, decimal_places=2, default=0)
    total_amount = models.DecimalField('销售金额(元)', max_digits=12, decimal_places=2, default=0)
    channel = models.CharField('渠道', max_length=20, choices=CHANNEL_CHOICES, default='offline')
    operator = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL, null=True, blank=True,
        verbose_name='操作员'
    )
    remark = models.CharField('备注', max_length=200, default='')
    created_at = models.DateTimeField('创建时间', auto_now_add=True)

    class Meta:
        db_table = 'sales_salesrecord'
        verbose_name = '销售记录'
        verbose_name_plural = '销售记录管理'
        ordering = ['-sale_date', '-id']
        indexes = [
            models.Index(fields=['sale_date']),
            models.Index(fields=['product']),
            models.Index(fields=['region']),
            models.Index(fields=['channel']),
        ]

    def __str__(self):
        return f'{self.sale_date} {self.product.name} {self.region.name} {self.quantity}支'

    def save(self, *args, **kwargs):
        self.total_amount = self.quantity * self.unit_price
        super().save(*args, **kwargs)
