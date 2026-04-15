import json
from urllib import request, error
from django.conf import settings


def analyze_predictions(prediction_data: list) -> str:
    """调用讯飞星火 Lite 对预测结果进行 AI 分析"""
    if not settings.SPARK_API_KEY or not settings.SPARK_API_SECRET:
        raise ValueError('未配置讯飞星火 APIKey / APISecret')

    lines = []
    for item in prediction_data:
        mom_change = item.get('mom_change_pct')
        mom = f'{mom_change:+.2f}%' if mom_change is not None else '基准月'
        lines.append(
            f"- {item.get('month', '')}：预测销量 {item.get('predicted_quantity', '')} 万支，"
            f"环比 {mom}，关键因素：{item.get('key_factors', '')}"
        )
    data_text = '\n'.join(lines)

    prompt = (
        '以下是牙膏销售未来销量预测数据，'
        '请从趋势、季节性规律、重点月份风险与机会三个维度给出简明分析建议，'
        '语言简洁、适合业务汇报，控制在300字以内：\n\n'
        + data_text
    )

    payload = json.dumps({
        'model': settings.SPARK_MODEL,
        'messages': [{'role': 'user', 'content': prompt}],
        'stream': False,
    }).encode('utf-8')

    req = request.Request(
        settings.SPARK_API_URL,
        data=payload,
        headers={
            'Authorization': f'Bearer {settings.SPARK_API_KEY}:{settings.SPARK_API_SECRET}',
            'Content-Type': 'application/json',
        },
        method='POST',
    )

    try:
        with request.urlopen(req, timeout=30) as response:
            data = json.loads(response.read().decode('utf-8'))
    except error.HTTPError as e:
        detail = e.read().decode('utf-8', errors='ignore')
        raise ValueError(f'讯飞星火请求失败：HTTP {e.code} {detail}')
    except error.URLError as e:
        raise ValueError(f'讯飞星火连接失败：{e.reason}')

    try:
        return data['choices'][0]['message']['content']
    except (KeyError, IndexError, TypeError):
        raise ValueError(f'讯飞星火返回格式异常：{data}')
