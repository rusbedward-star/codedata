import json
from urllib import error, request

from django.conf import settings


MONTH_FACTORS = {
    1: "春节前备货拉动需求",
    2: "节后渠道补货节奏放缓",
    3: "春季常规补货恢复",
    4: "市场进入平稳销售期",
    5: "节日促销带来短期拉升",
    6: "年中大促与渠道活动放量",
    7: "促销后需求阶段性回落",
    8: "暑期口腔护理需求回暖",
    9: "开学季与渠道铺货带动增长",
    10: "国庆节前后促销刺激销量",
    11: '双11活动放大线上销量',
    12: "年终备货与库存调整并行",
}


def _month_factor(month_text):
    try:
        month_num = int(str(month_text).split("-")[1])
    except (IndexError, ValueError, TypeError):
        return "结合历史销量走势与季节性波动形成预测"
    return MONTH_FACTORS.get(month_num, "结合历史销量走势与季节性波动形成预测")


def build_prediction_payload(forecast_data, model_name, months_filter=None):
    if model_name not in forecast_data.columns:
        raise ValueError("模型不存在")

    if months_filter:
        forecast_data = forecast_data[forecast_data["月份"].isin(months_filter)]

    prediction_data = []
    previous_value = None
    for _, row in forecast_data.iterrows():
        month = row["月份"]
        current_value = float(row[model_name])
        mom_change = None
        if previous_value not in (None, 0):
            mom_change = round((current_value - previous_value) / previous_value * 100, 2)

        prediction_data.append(
            {
                "month": month,
                "predicted_quantity": round(current_value, 4),
                "mom_change_pct": mom_change,
                "key_factors": _month_factor(month),
            }
        )
        previous_value = current_value

    return prediction_data


def analyze_predictions(prediction_data, model_name):
    auth_token = settings.SPARK_API_PASSWORD
    if not auth_token:
        if not settings.SPARK_API_KEY or not settings.SPARK_API_SECRET:
            raise ValueError("未配置讯飞星火 APIPassword 或 APIKey / APISecret")
        auth_token = f"{settings.SPARK_API_KEY}:{settings.SPARK_API_SECRET}"

    lines = []
    for item in prediction_data:
        mom_change = item.get("mom_change_pct")
        mom_text = f"{mom_change:+.2f}%" if mom_change is not None else "基准月"
        lines.append(
            f"- {item.get('month', '')}：预测销量 {item.get('predicted_quantity', '')}，"
            f"环比 {mom_text}，关键因素：{item.get('key_factors', '')}"
        )
    data_text = "\n".join(lines)

    prompt = (
        f"以下是牙膏 {model_name} 模型在所选月份范围内的未来销量预测数据。"
        "请基于所选月份的预测结果，从整体趋势、季节性波动、经营建议三个维度给出简明分析，"
        "适合直接展示在系统页面中，控制在300字以内：\n\n"
        f"{data_text}"
    )

    payload = json.dumps(
        {
            "model": settings.SPARK_MODEL,
            "messages": [{"role": "user", "content": prompt}],
            "stream": False,
        }
    ).encode("utf-8")

    req = request.Request(
        settings.SPARK_API_URL,
        data=payload,
        headers={
            "Authorization": f"Bearer {auth_token}",
            "Content-Type": "application/json",
        },
        method="POST",
    )

    try:
        with request.urlopen(req, timeout=30) as response:
            data = json.loads(response.read().decode("utf-8"))
    except error.HTTPError as exc:
        detail = exc.read().decode("utf-8", errors="ignore")
        raise ValueError(f"讯飞星火请求失败：HTTP {exc.code} {detail}") from exc
    except error.URLError as exc:
        raise ValueError(f"讯飞星火连接失败：{exc.reason}") from exc

    try:
        return data["choices"][0]["message"]["content"]
    except (KeyError, IndexError, TypeError) as exc:
        raise ValueError(f"讯飞星火返回格式异常：{data}") from exc
