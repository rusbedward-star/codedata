from django.db import models
from django.utils import timezone


class PredictionResult(models.Model):
    month = models.CharField('月份', max_length=7, unique=True, help_text='YYYY-MM格式')
    predicted_quantity = models.DecimalField('预测销量(万支)', max_digits=10, decimal_places=2, default=0)
    mom_change_pct = models.DecimalField('环比变化(%)', max_digits=8, decimal_places=2, null=True, blank=True)
    key_factors = models.CharField('预测关键因素', max_length=200, default='')
    model_type = models.CharField('预测模型', max_length=50, default='SARIMA')
    created_at = models.DateTimeField('创建时间', auto_now_add=True)

    class Meta:
        db_table = 'predictions_predictionresult'
        verbose_name = '预测结果'
        verbose_name_plural = '预测结果管理'
        ordering = ['month']

    def __str__(self):
        return f'{self.month}: {self.predicted_quantity}万支'


class PredictionParam(models.Model):
    param_name = models.CharField('参数名', max_length=50, unique=True)
    param_value = models.DecimalField('参数值', max_digits=15, decimal_places=6)
    description = models.CharField('描述', max_length=200, default='')

    class Meta:
        db_table = 'predictions_predictionparam'
        verbose_name = '预测参数'
        verbose_name_plural = '预测参数管理'

    def __str__(self):
        return f'{self.param_name}={self.param_value}'
