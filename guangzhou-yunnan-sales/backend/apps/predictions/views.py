import csv
from django.http import HttpResponse
from rest_framework import status
from rest_framework.decorators import api_view, permission_classes
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated

from .models import PredictionResult
from .prediction_service import run_prediction
from .ai_service import analyze_predictions
from apps.users.permissions import IsAdmin


@api_view(['GET'])
@permission_classes([IsAuthenticated])
def prediction_list(request):
    """获取已存储的预测结果"""
    start_month = request.query_params.get('start_month', '2026-03')
    end_month = request.query_params.get('end_month', '2027-02')

    qs = PredictionResult.objects.filter(
        month__gte=start_month,
        month__lte=end_month
    ).order_by('month')

    data = []
    for item in qs:
        data.append({
            'id': item.id,
            'month': item.month,
            'predicted_quantity': float(item.predicted_quantity),
            'mom_change_pct': float(item.mom_change_pct) if item.mom_change_pct is not None else None,
            'key_factors': item.key_factors,
            'model_type': item.model_type,
            'created_at': item.created_at.strftime('%Y-%m-%d %H:%M:%S'),
        })
    return Response(data)


@api_view(['POST'])
@permission_classes([IsAuthenticated, IsAdmin])
def run_prediction_view(request):
    """执行预测并保存结果"""
    start_month = request.data.get('start_month', '2026-03')
    end_month = request.data.get('end_month', '2027-02')

    try:
        results = run_prediction(start_month, end_month)
    except Exception as e:
        return Response({'detail': f'预测失败：{str(e)}'}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

    saved = []
    for item in results:
        obj, created = PredictionResult.objects.update_or_create(
            month=item['month'],
            defaults={
                'predicted_quantity': item['predicted_quantity'],
                'mom_change_pct': item['mom_change_pct'],
                'key_factors': item['key_factors'],
                'model_type': item['model_type'],
            }
        )
        saved.append({
            'month': obj.month,
            'predicted_quantity': float(obj.predicted_quantity),
            'mom_change_pct': float(obj.mom_change_pct) if obj.mom_change_pct is not None else None,
            'key_factors': obj.key_factors,
            'model_type': obj.model_type,
        })

    return Response({'detail': f'预测完成，共{len(saved)}条记录', 'results': saved})


@api_view(['GET'])
@permission_classes([IsAuthenticated])
def prediction_export(request):
    """导出预测结果为CSV"""
    start_month = request.query_params.get('start_month', '2026-03')
    end_month = request.query_params.get('end_month', '2027-02')

    qs = PredictionResult.objects.filter(
        month__gte=start_month,
        month__lte=end_month
    ).order_by('month')

    response = HttpResponse(content_type='text/csv; charset=utf-8-sig')
    response['Content-Disposition'] = 'attachment; filename="prediction_results.csv"'
    response.write('\ufeff')

    writer = csv.writer(response)
    writer.writerow(['月份', '预测销量(万支)', '环比变化(%)', '预测关键因素', '预测模型'])

    for item in qs:
        writer.writerow([
            item.month,
            item.predicted_quantity,
            item.mom_change_pct if item.mom_change_pct is not None else '–',
            item.key_factors,
            item.model_type,
        ])

    return response


@api_view(['POST'])
@permission_classes([IsAuthenticated])
def ai_analyze_view(request):
    """调用讯飞星火 AI 对预测结果进行分析"""
    prediction_data = request.data.get('predictions', [])
    if not prediction_data:
        return Response({'detail': '缺少预测数据'}, status=status.HTTP_400_BAD_REQUEST)
    try:
        result = analyze_predictions(prediction_data)
    except Exception as e:
        return Response({'detail': f'AI 分析失败：{str(e)}'}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
    return Response({'analysis': result})
