from pathlib import Path
import json

import pandas as pd
from django.conf import settings
from django.http import FileResponse, Http404, HttpResponse, JsonResponse
from django.templatetags.static import static
from django.views.decorators.csrf import csrf_exempt
from pyecharts import options as opts
from pyecharts.charts import Bar, Line
from pyecharts.globals import CurrentConfig

from .ai_service import analyze_predictions, build_prediction_payload
from . import forecast_jobs


DATA_ROOT = Path(settings.PROJECT_ROOT)
MONTHLY_DATA_FILE = DATA_ROOT / "冰柠销量数据.csv"
METRICS_FILE = DATA_ROOT / "模型评估结果.csv"
FORECAST_FILE = DATA_ROOT / "未来12个月预测结果.csv"
MONTHLY_COLUMNS = [
    "date",
    "sales",
    "last_month_sales",
    "last_year_same_month",
    "month",
    "is_holiday",
    "is_promo",
    "region",
    "product_series",
]

COLUMN_LABELS = {
    "date": "日期",
    "sales": "销售额(万支)",
    "last_month_sales": "上月销量(万支)",
    "last_year_same_month": "去年同月销量(万支)",
    "month": "月份",
    "is_holiday": "是否节假日",
    "is_promo": "是否促销",
    "region": "地区",
    "product_series": "产品系列",
}

# Reverse mapping: Chinese display name -> English field name (for Excel import)
COLUMN_LABELS_REVERSE = {v: k for k, v in COLUMN_LABELS.items()}


def records_labeled(df):
    """返回中文 key 的记录列表，用于前端展示。"""
    return [
        {COLUMN_LABELS.get(col, col): clean_value(row[col]) for col in df.columns}
        for _, row in df.iterrows()
    ]

IMAGE_CATALOG = [
    ("月度销量趋势与滚动均值图.png", "月度销量趋势"),
    ("月度季节性分析图.png", "月度季节性分析"),
    ("MAE指标对比图.png", "MAE 指标对比"),
    ("RMSE指标对比图.png", "RMSE 指标对比"),
    ("MAPE指标对比图.png", "MAPE 指标对比"),
    ("测试集多模型预测效果对比图.png", "测试集多模型预测"),
    ("关键特征重要性分析图.png", "关键特征重要性"),
    ("未来12个月多模型预测图.png", "未来 12 个月多模型预测"),
    ("历史与未来销量趋势图.png", "历史与未来销量趋势"),
    ("LSTM训练损失图.png", "LSTM 训练损失"),
]


def read_csv_or_empty(path):
    if not path.exists():
        return pd.DataFrame()
    return pd.read_csv(path)


def metrics_df():
    return read_csv_or_empty(METRICS_FILE)


def forecast_df():
    return read_csv_or_empty(FORECAST_FILE)


def monthly_df():
    data = read_csv_or_empty(MONTHLY_DATA_FILE)
    if data.empty:
        return pd.DataFrame(columns=MONTHLY_COLUMNS)
    return data


def save_monthly_df(dataframe):
    output = dataframe.copy()
    if "date" in output.columns:
        output["date"] = output["date"].astype(str)
    output.to_csv(MONTHLY_DATA_FILE, index=False, encoding="utf-8-sig")


def clean_value(value):
    if pd.isna(value):
        return None
    if hasattr(value, "item"):
        return value.item()
    return value


def parse_metric_value(value):
    raw = clean_value(value)
    if raw in (None, ""):
        return None
    if isinstance(raw, str):
        raw = raw.replace("%", "").strip()
    try:
        return float(raw)
    except (TypeError, ValueError):
        return None


def records(df):
    return [
        {column: clean_value(row[column]) for column in df.columns}
        for _, row in df.iterrows()
    ]


def parse_json_body(request):
    try:
        body = request.body.decode("utf-8") if request.body else "{}"
        return json.loads(body or "{}")
    except json.JSONDecodeError as exc:
        raise ValueError("请求体不是合法的 JSON 数据") from exc


def parse_optional_number(value, field_name):
    if value in (None, ""):
        return None
    try:
        return round(float(value), 4)
    except (TypeError, ValueError) as exc:
        raise ValueError(f"{field_name} 必须是数字") from exc


def parse_flag(value, field_name):
    try:
        flag = int(value)
    except (TypeError, ValueError) as exc:
        raise ValueError(f"{field_name} 只能填写 0 或 1") from exc
    if flag not in (0, 1):
        raise ValueError(f"{field_name} 只能填写 0 或 1")
    return flag


def normalize_monthly_record(payload):
    required_fields = [
        "date",
        "sales",
        "last_month_sales",
        "last_year_same_month",
        "is_holiday",
        "is_promo",
        "region",
        "product_series",
    ]
    missing_fields = [field for field in required_fields if field not in payload]
    if missing_fields:
        raise ValueError(f"缺少字段: {'、'.join(missing_fields)}")

    try:
        parsed_date = pd.to_datetime(str(payload["date"]), format="%Y-%m")
    except (TypeError, ValueError) as exc:
        raise ValueError("date 必须是 YYYY-MM 格式") from exc

    region = str(payload.get("region", "")).strip()
    product_series = str(payload.get("product_series", "")).strip()
    if not region:
        raise ValueError("region 不能为空")
    if not product_series:
        raise ValueError("product_series 不能为空")

    return {
        "date": parsed_date.strftime("%Y-%m"),
        "sales": parse_optional_number(payload.get("sales"), "sales"),
        "last_month_sales": parse_optional_number(
            payload.get("last_month_sales"),
            "last_month_sales",
        ),
        "last_year_same_month": parse_optional_number(
            payload.get("last_year_same_month"),
            "last_year_same_month",
        ),
        "month": int(parsed_date.month),
        "is_holiday": parse_flag(payload.get("is_holiday"), "is_holiday"),
        "is_promo": parse_flag(payload.get("is_promo"), "is_promo"),
        "region": region,
        "product_series": product_series,
    }


def mutation_notice():
    return "月度样本已更新；若需同步模型评估、预测结果和图表，请重新运行预测脚本。"


def overview(request):
    monthly_data = monthly_df()
    metrics_data = metrics_df()
    forecast_data = forecast_df()

    best_model = None
    if not metrics_data.empty:
        best_row = metrics_data.iloc[0]
        best_model = {
            "name": clean_value(best_row["模型"]),
            "rmse": clean_value(best_row["RMSE"]),
            "mae": clean_value(best_row["MAE"]),
            "mape": clean_value(best_row["MAPE"]),
        }

    payload = {
        "project_name": "牙膏销量分析与预测系统",
        "tech_stack": ["Vue 3", "Vite", "Django", "PyTorch", "Scikit-learn"],
        "dataset_rows": int(len(monthly_data)),
        "forecast_months": int(len(forecast_data)),
        "model_count": int(len(metrics_data)),
        "chart_count": sum(1 for filename, _ in IMAGE_CATALOG if (DATA_ROOT / filename).exists()),
        "date_range": {
            "start": clean_value(monthly_data["date"].min()) if not monthly_data.empty else None,
            "end": clean_value(monthly_data["date"].max()) if not monthly_data.empty else None,
        },
        "best_model": best_model,
    }
    return JsonResponse(payload)


def metrics(request):
    metrics_data = metrics_df()
    best_model = None
    if not metrics_data.empty:
        best_model = clean_value(metrics_data.iloc[0]["模型"])
    return JsonResponse(
        {
            "best_model": best_model,
            "items": records(metrics_data),
        }
    )


def forecast(request):
    forecast_data = forecast_df()
    return JsonResponse(
        {
            "columns": [column for column in forecast_data.columns],
            "items": records(forecast_data),
        }
    )


@csrf_exempt
def sample_data(request):
    if request.method == "POST":
        try:
            payload = normalize_monthly_record(parse_json_body(request))
        except ValueError as exc:
            return JsonResponse({"error": str(exc)}, status=400)

        monthly_data = monthly_df()
        if not monthly_data.empty and payload["date"] in monthly_data["date"].astype(str).values:
            return JsonResponse({"error": "该月份数据已存在，请直接编辑原记录"}, status=409)

        updated = pd.concat([monthly_data, pd.DataFrame([payload])], ignore_index=True)
        updated["date_sort"] = pd.to_datetime(updated["date"], format="%Y-%m", errors="coerce")
        updated = updated.sort_values("date_sort").drop(columns=["date_sort"])
        updated = updated[MONTHLY_COLUMNS]
        save_monthly_df(updated)
        return JsonResponse(
            {"item": payload, "notice": mutation_notice()},
            status=201,
        )

    monthly_data = monthly_df()
    return JsonResponse(
        {
            "columns": [COLUMN_LABELS.get(c, c) for c in monthly_data.columns],
            "items": records_labeled(monthly_data),
        }
    )


@csrf_exempt
def sample_data_detail(request, date_key):
    monthly_data = monthly_df()
    if monthly_data.empty:
        return JsonResponse({"error": "数据不存在"}, status=404)

    date_column = monthly_data["date"].astype(str)
    if date_key not in date_column.values:
        return JsonResponse({"error": "记录不存在"}, status=404)

    row_index = monthly_data.index[date_column == date_key][0]

    if request.method == "DELETE":
        updated = monthly_data.drop(index=row_index).reset_index(drop=True)
        updated = updated[MONTHLY_COLUMNS]
        save_monthly_df(updated)
        return JsonResponse({"notice": mutation_notice()})

    if request.method != "PUT":
        return JsonResponse({"error": "不支持的请求方法"}, status=405)

    try:
        payload = normalize_monthly_record(parse_json_body(request))
    except ValueError as exc:
        return JsonResponse({"error": str(exc)}, status=400)

    duplicate_dates = set(date_column.values) - {date_key}
    if payload["date"] in duplicate_dates:
        return JsonResponse({"error": "新的月份与现有记录冲突"}, status=409)

    for column in MONTHLY_COLUMNS:
        monthly_data.at[row_index, column] = payload[column]

    monthly_data["date_sort"] = pd.to_datetime(
        monthly_data["date"],
        format="%Y-%m",
        errors="coerce",
    )
    monthly_data = monthly_data.sort_values("date_sort").drop(columns=["date_sort"])
    monthly_data = monthly_data[MONTHLY_COLUMNS].reset_index(drop=True)
    save_monthly_df(monthly_data)
    return JsonResponse({"item": payload, "notice": mutation_notice()})


def _detect_raw_ledger(df):
    """检测是否为销售流水格式（含"实发数量"列且无"date"/"sales"/"日期(月)"列）。"""
    cols = {str(c).strip() for c in df.columns}
    has_ledger_col = bool({"实发数量", "日期"} & cols)
    has_standard_col = bool({"date", "sales", "销售额(万支)"} & cols)
    return has_ledger_col and not has_standard_col


def _aggregate_raw_ledger(df):
    """
    将销售流水 DataFrame 聚合为月度样本记录列表。

    流水列映射：
      日期        -> 解析 YYYY-MM
      实发数量    -> 月度销量（取负值使正，单位：支 -> 万支）
      商品分类    -> product_series（取该月出现次数最多的值）
      部门        -> region（取该月出现次数最多的值）

    自动补全字段：
      last_month_sales       -> 同聚合数据中上一个月的销量
      last_year_same_month   -> 同聚合数据中去年同月的销量
      is_holiday / is_promo  -> 默认 0
    """
    df = df.copy()
    # 标准化列名（去除空格）
    df.columns = [str(c).strip() for c in df.columns]

    if "日期" not in df.columns:
        raise ValueError('流水 Excel 缺少"日期"列，无法解析月份')
    if "实发数量" not in df.columns:
        raise ValueError('流水 Excel 缺少"实发数量"列，无法计算销量')

    df["_parsed_date"] = pd.to_datetime(df["日期"], errors="coerce")
    df = df.dropna(subset=["_parsed_date"])
    if df.empty:
        raise ValueError("日期列无法解析，请确认格式（如 2024/10/28）")

    df["_month"] = df["_parsed_date"].dt.to_period("M").astype(str)  # YYYY-MM

    # 实发数量取数值，负值代表出库，转为正数销量
    df["_qty"] = pd.to_numeric(df["实发数量"], errors="coerce").fillna(0)
    # 销售流水出库通常为负，取绝对值；若本月净值为正（如退货多于出库）则算 0
    monthly_qty = df.groupby("_month")["_qty"].apply(
        lambda s: max(-s.sum(), 0) / 10000  # 转换为万支
    )

    def most_common(series):
        vals = series.dropna().astype(str).str.strip()
        vals = vals[vals != ""]
        return vals.mode().iloc[0] if len(vals) else ""

    monthly_series = (
        df.groupby("_month")["商品分类"].apply(most_common)
        if "商品分类" in df.columns
        else pd.Series("", index=monthly_qty.index, name="商品分类")
    )
    monthly_region = (
        df.groupby("_month")["部门"].apply(most_common)
        if "部门" in df.columns
        else pd.Series("", index=monthly_qty.index, name="部门")
    )

    months_sorted = sorted(monthly_qty.index.tolist())
    qty_map = monthly_qty.to_dict()

    records = []
    for month in months_sorted:
        sales_val = round(float(qty_map[month]), 4)

        # 上月销量
        prev_month = (pd.Period(month, "M") - 1).strftime("%Y-%m")
        last_month = round(float(qty_map.get(prev_month, 0)), 4)

        # 去年同月销量
        yr = int(month[:4])
        mo = month[4:]
        prev_year_month = f"{yr - 1}{mo}"
        last_year = qty_map.get(prev_year_month, None)
        last_year_val = round(float(last_year), 4) if last_year is not None else ""

        records.append(
            {
                "date": month,
                "sales": str(sales_val),
                "last_month_sales": str(last_month),
                "last_year_same_month": str(last_year_val) if last_year_val != "" else "",
                "is_holiday": "0",
                "is_promo": "0",
                "region": str(monthly_region.get(month, "")),
                "product_series": str(monthly_series.get(month, "")),
            }
        )
    return records


@csrf_exempt
def sample_data_import(request):
    if request.method != "POST":
        return JsonResponse({"error": "只支持 POST 请求"}, status=405)

    upload = request.FILES.get("file")
    if not upload:
        return JsonResponse({"error": "请上传 Excel 文件"}, status=400)

    suffix = Path(upload.name).suffix.lower()
    if suffix not in {".xlsx", ".xls"}:
        return JsonResponse({"error": "仅支持 .xlsx 或 .xls 文件"}, status=400)

    try:
        imported_df = pd.read_excel(upload)
    except ImportError:
        return JsonResponse(
            {"error": "缺少 Excel 读取依赖，请安装 openpyxl"},
            status=500,
        )
    except Exception as exc:
        return JsonResponse({"error": f"Excel 读取失败：{exc}"}, status=400)

    if imported_df.empty:
        return JsonResponse({"error": "Excel 文件内容为空"}, status=400)

    # ── 判断格式 ──────────────────────────────────────────────
    is_ledger_mode = _detect_raw_ledger(imported_df)
    if is_ledger_mode:
        # 流水格式：自动按月聚合
        try:
            raw_records = _aggregate_raw_ledger(imported_df)
        except ValueError as exc:
            return JsonResponse({"error": str(exc)}, status=400)
        total_rows = len(imported_df)
    else:
        # 标准格式：按列名映射
        renamed_columns = {}
        for column in imported_df.columns:
            normalized = str(column).strip()
            renamed_columns[column] = COLUMN_LABELS_REVERSE.get(normalized, normalized)
        imported_df = imported_df.rename(columns=renamed_columns)

        missing_fields = [
            field
            for field in [
                "date",
                "sales",
                "last_month_sales",
                "last_year_same_month",
                "is_holiday",
                "is_promo",
                "region",
                "product_series",
            ]
            if field not in imported_df.columns
        ]
        if missing_fields:
            return JsonResponse(
                {"error": f'Excel 缺少必要列: {"、".join(missing_fields)}。如需导入销售流水，请确保包含"日期"和"实发数量"列'},
                status=400,
            )

        raw_records = [
            {
                "date": clean_value(row.get("date")),
                "sales": clean_value(row.get("sales")),
                "last_month_sales": clean_value(row.get("last_month_sales")),
                "last_year_same_month": clean_value(row.get("last_year_same_month")),
                "is_holiday": clean_value(row.get("is_holiday")),
                "is_promo": clean_value(row.get("is_promo")),
                "region": clean_value(row.get("region")),
                "product_series": clean_value(row.get("product_series")),
            }
            for _, row in imported_df.iterrows()
        ]
        total_rows = len(imported_df)

    # ── 写入（跳过已有月份）────────────────────────────────────
    monthly_data = monthly_df()
    existing_dates = set(monthly_data["date"].astype(str).tolist()) if not monthly_data.empty else set()
    imported_records = []
    skipped_dates = []

    try:
        for raw in raw_records:
            if is_ledger_mode:
                # 流水聚合结果直接构造最终 record，允许 region/product_series 为空
                try:
                    parsed_date = pd.to_datetime(raw["date"], format="%Y-%m")
                except (TypeError, ValueError):
                    continue
                payload = {
                    "date": parsed_date.strftime("%Y-%m"),
                    "sales": parse_optional_number(raw.get("sales"), "sales"),
                    "last_month_sales": parse_optional_number(raw.get("last_month_sales"), "last_month_sales"),
                    "last_year_same_month": parse_optional_number(raw.get("last_year_same_month"), "last_year_same_month"),
                    "month": int(parsed_date.month),
                    "is_holiday": 0,
                    "is_promo": 0,
                    "region": str(raw.get("region", "") or ""),
                    "product_series": str(raw.get("product_series", "") or ""),
                }
            else:
                payload = normalize_monthly_record(raw)
            if payload["date"] in existing_dates:
                skipped_dates.append(payload["date"])
                continue
            imported_records.append(payload)
            existing_dates.add(payload["date"])
    except ValueError as exc:
        return JsonResponse({"error": str(exc)}, status=400)

    if imported_records:
        updated = pd.concat([monthly_data, pd.DataFrame(imported_records)], ignore_index=True)
        updated["date_sort"] = pd.to_datetime(updated["date"], format="%Y-%m", errors="coerce")
        updated = updated.sort_values("date_sort").drop(columns=["date_sort"])
        updated = updated[MONTHLY_COLUMNS].reset_index(drop=True)
        save_monthly_df(updated)

    return JsonResponse(
        {
            "notice": mutation_notice(),
            "total_rows": int(total_rows),
            "imported_count": len(imported_records),
            "skipped_count": len(skipped_dates),
            "skipped_dates": skipped_dates,
        }
    )


def insights(request):
    metrics_data = metrics_df()
    forecast_data = forecast_df()

    best_rmse_model = None
    best_mape_model = None
    peak_forecast = None

    if not metrics_data.empty:
        best_rmse_row = metrics_data.assign(
            _rmse=metrics_data["RMSE"].map(parse_metric_value),
            _mape=metrics_data["MAPE"].map(parse_metric_value),
        ).sort_values("_rmse").iloc[0]
        best_mape_row = metrics_data.assign(
            _rmse=metrics_data["RMSE"].map(parse_metric_value),
            _mape=metrics_data["MAPE"].map(parse_metric_value),
        ).sort_values("_mape").iloc[0]
        best_rmse_model = clean_value(best_rmse_row["模型"])
        best_mape_model = clean_value(best_mape_row["模型"])

    if not forecast_data.empty:
        model_columns = [column for column in forecast_data.columns if column != "月份"]
        peak_value = None
        peak_month = None
        peak_model = None
        for _, row in forecast_data.iterrows():
            for column in model_columns:
                current_value = clean_value(row[column])
                if current_value is None:
                    continue
                if peak_value is None or current_value > peak_value:
                    peak_value = current_value
                    peak_month = clean_value(row["月份"])
                    peak_model = column
        peak_forecast = {
            "month": peak_month,
            "model": peak_model,
            "value": peak_value,
        }

    return JsonResponse(
        {
            "best_rmse_model": best_rmse_model,
            "best_mape_model": best_mape_model,
            "peak_forecast": peak_forecast,
            "recommendations": [
                "优先采用随机森林作为系统默认展示模型，用于主结果页面展示。",
                "将梯度提升回归作为辅助对照模型，用于说明不同算法下的误差差异。",
                "在深度学习扩展模块中保留 PyTorch LSTM，作为后续扩展和论文对比分析依据。",
            ],
        }
    )


def model_detail(request):
    model_name = request.GET.get("model")
    metrics_data = metrics_df()
    forecast_data = forecast_df()

    if not model_name:
        if metrics_data.empty:
            return JsonResponse({"error": "模型不存在"}, status=404)
        model_name = clean_value(metrics_data.iloc[0]["模型"])

    metric_row = metrics_data[metrics_data["模型"] == model_name]
    if metric_row.empty or model_name not in forecast_data.columns:
        return JsonResponse({"error": "模型不存在"}, status=404)

    metric_info = records(metric_row)[0]
    series_items = [
        {"month": clean_value(row["月份"]), "value": clean_value(row[model_name])}
        for _, row in forecast_data.iterrows()
    ]
    return JsonResponse(
        {
            "model": model_name,
            "metrics": metric_info,
            "series": series_items,
        }
    )


def ai_analysis(request):
    model_name = request.GET.get("model")
    metrics_data = metrics_df()
    forecast_data = forecast_df()

    if forecast_data.empty:
        return JsonResponse({"error": "预测数据不存在"}, status=404)

    if not model_name:
        if not metrics_data.empty:
            model_name = clean_value(metrics_data.iloc[0]["模型"])
        else:
            model_columns = [column for column in forecast_data.columns if column != "月份"]
            model_name = model_columns[0] if model_columns else None

    if not model_name:
        return JsonResponse({"error": "模型不存在"}, status=404)

    try:
        months_filter = request.GET.getlist("months") or None
        prediction_data = build_prediction_payload(forecast_data, model_name, months_filter)
        if not prediction_data:
            return JsonResponse({"error": "所选月份范围内无预测数据"}, status=400)
        analysis = analyze_predictions(prediction_data, model_name)
    except ValueError as exc:
        return JsonResponse({"error": str(exc)}, status=502)

    return JsonResponse(
        {
            "model": model_name,
            "analysis": analysis,
            "items": prediction_data,
        }
    )


def render_chart_page(chart):
    dependency_urls = []
    for dependency in chart.js_dependencies.items:
        if dependency == "echarts":
            dependency_urls.append(static("dashboard/echarts.min.js"))
        else:
            dependency_urls.append(f"{CurrentConfig.ONLINE_HOST}{dependency}.js")

    scripts = "\n".join(
        f'<script src="{dependency_url}"></script>'
        for dependency_url in dependency_urls
    )
    html = f"""
    <!DOCTYPE html>
    <html lang="zh-CN">
    <head>
      <meta charset="utf-8" />
      <meta name="viewport" content="width=device-width, initial-scale=1.0" />
      <style>
        html, body {{
          margin: 0;
          padding: 0;
          background: #ffffff;
          font-family: "PingFang SC", "Microsoft YaHei", sans-serif;
        }}
      </style>
      {scripts}
    </head>
    <body>
      {chart.render_embed()}
    </body>
    </html>
    """
    return HttpResponse(html)


def build_metric_chart(metric_name):
    data = metrics_df().copy()
    data["_metric_value"] = data[metric_name].map(parse_metric_value)
    data = data.sort_values("_metric_value")
    chart = (
        Bar(init_opts=opts.InitOpts(width="1000px", height="360px"))
        .add_xaxis([clean_value(item) for item in data["模型"].tolist()])
        .add_yaxis(metric_name, [round(float(item), 4) for item in data["_metric_value"].tolist()])
        .set_global_opts(
            title_opts=opts.TitleOpts(title=f"{metric_name} 模型对比"),
            legend_opts=opts.LegendOpts(is_show=False),
            xaxis_opts=opts.AxisOpts(axislabel_opts=opts.LabelOpts(rotate=-15)),
            yaxis_opts=opts.AxisOpts(splitline_opts=opts.SplitLineOpts(is_show=True)),
        )
        .set_series_opts(label_opts=opts.LabelOpts(is_show=True, position="top"))
    )
    return chart


def build_multi_forecast_chart():
    data = forecast_df()
    chart = Line(init_opts=opts.InitOpts(width="1000px", height="400px"))
    x_axis = [clean_value(item) for item in data["月份"].tolist()]
    chart.add_xaxis(x_axis)
    for column in data.columns:
        if column == "月份":
            continue
        chart.add_yaxis(
            column,
            [round(float(item), 4) for item in data[column].tolist()],
            is_smooth=False,
            label_opts=opts.LabelOpts(is_show=False),
        )
    chart.set_global_opts(
        title_opts=opts.TitleOpts(title="未来 12 个月多模型预测"),
        tooltip_opts=opts.TooltipOpts(trigger="axis"),
        datazoom_opts=[opts.DataZoomOpts()],
        yaxis_opts=opts.AxisOpts(splitline_opts=opts.SplitLineOpts(is_show=True)),
    )
    return chart


def build_model_forecast_chart(model_name):
    data = forecast_df()
    if model_name not in data.columns:
        raise Http404("模型不存在")

    chart = (
        Line(init_opts=opts.InitOpts(width="1000px", height="360px"))
        .add_xaxis([clean_value(item) for item in data["月份"].tolist()])
        .add_yaxis(
            model_name,
            [round(float(item), 4) for item in data[model_name].tolist()],
            is_smooth=True,
            label_opts=opts.LabelOpts(is_show=True),
        )
        .set_global_opts(
            title_opts=opts.TitleOpts(title=f"{model_name} 预测曲线"),
            tooltip_opts=opts.TooltipOpts(trigger="axis"),
            yaxis_opts=opts.AxisOpts(splitline_opts=opts.SplitLineOpts(is_show=True)),
        )
    )
    return chart


def build_sales_trend_chart():
    data = monthly_df()
    chart = (
        Line(init_opts=opts.InitOpts(width="1000px", height="360px"))
        .add_xaxis([clean_value(item) for item in data["date"].tolist()])
        .add_yaxis(
            "销量",
            [round(float(item), 4) for item in data["sales"].tolist()],
            is_smooth=True,
            label_opts=opts.LabelOpts(is_show=False),
        )
        .set_global_opts(
            title_opts=opts.TitleOpts(title="历史销量趋势"),
            tooltip_opts=opts.TooltipOpts(trigger="axis"),
            yaxis_opts=opts.AxisOpts(splitline_opts=opts.SplitLineOpts(is_show=True)),
        )
    )
    return chart


def build_series_forecast_chart(model_name=None, series_name=None):
    forecast_data = forecast_df()
    monthly_data = monthly_df()
    metrics_data = metrics_df()

    if forecast_data.empty or monthly_data.empty:
        raise Http404("预测数据不存在")

    if not model_name:
        if not metrics_data.empty:
            model_name = clean_value(metrics_data.iloc[0]["模型"])
        else:
            model_columns = [column for column in forecast_data.columns if column != "月份"]
            model_name = model_columns[0] if model_columns else None

    if not model_name or model_name not in forecast_data.columns:
        raise Http404("模型不存在")

    series_sales = (
        monthly_data.groupby("product_series", dropna=False)["sales"]
        .sum()
        .reset_index()
    )
    series_sales = series_sales[series_sales["product_series"].notna()]
    series_sales["product_series"] = series_sales["product_series"].astype(str).str.strip()
    series_sales = series_sales[series_sales["product_series"] != ""]
    if series_sales.empty:
        raise Http404("产品系列数据不存在")

    total_sales = float(series_sales["sales"].sum())
    if total_sales <= 0:
        raise Http404("产品系列销量占比无效")

    series_sales["ratio"] = series_sales["sales"] / total_sales
    months = [clean_value(item) for item in forecast_data["月份"].tolist()]

    chart = Line(init_opts=opts.InitOpts(width="1000px", height="400px"))
    chart.add_xaxis(months)

    selected_rows = series_sales
    title = f"各系列未来销量预测（{model_name}）"
    if series_name:
        selected_rows = series_sales[series_sales["product_series"] == series_name]
        if selected_rows.empty:
            raise Http404("产品系列不存在")
        title = f"{series_name} 未来销量预测（{model_name}）"

    base_values = forecast_data[model_name].astype(float).tolist()
    for _, row in selected_rows.iterrows():
        chart.add_yaxis(
            clean_value(row["product_series"]),
            [round(value * float(row["ratio"]), 4) for value in base_values],
            is_smooth=True,
            label_opts=opts.LabelOpts(is_show=False),
        )

    chart.set_global_opts(
        title_opts=opts.TitleOpts(title=title),
        tooltip_opts=opts.TooltipOpts(trigger="axis"),
        datazoom_opts=[opts.DataZoomOpts()],
        yaxis_opts=opts.AxisOpts(splitline_opts=opts.SplitLineOpts(is_show=True)),
    )
    return chart


def pyecharts_chart(request, chart_key):
    metric_map = {"mae": "MAE", "rmse": "RMSE", "mape": "MAPE"}
    if chart_key in metric_map:
        return render_chart_page(build_metric_chart(metric_map[chart_key]))
    if chart_key == "forecast-multi":
        return render_chart_page(build_multi_forecast_chart())
    if chart_key == "sales-trend":
        return render_chart_page(build_sales_trend_chart())
    if chart_key == "series-forecast":
        model_name = request.GET.get("model")
        series_name = request.GET.get("series") or None
        return render_chart_page(build_series_forecast_chart(model_name, series_name))
    raise Http404("图表不存在")


def pyecharts_model_chart(request):
    model_name = request.GET.get("model")
    if not model_name:
        raise Http404("模型不存在")
    return render_chart_page(build_model_forecast_chart(model_name))


def images(request):
    items = []
    for filename, title in IMAGE_CATALOG:
        file_path = DATA_ROOT / filename
        if file_path.exists():
            items.append(
                {
                    "filename": filename,
                    "title": title,
                    "url": f"/api/media/results/{filename}/",
                }
            )
    return JsonResponse({"items": items})


def modules(request):
    payload = {
        "frontend_modules": [
            {
                "name": "系统总览模块",
                "description": "展示数据规模、最佳模型、图表数量和技术栈，帮助用户快速掌握系统状态。",
            },
            {
                "name": "模型评估模块",
                "description": "集中展示 MAE、RMSE、MAPE 评估结果，支持横向比较不同模型表现。",
            },
            {
                "name": "预测结果模块",
                "description": "按月份展示未来销量预测表，为业务人员查看趋势变化提供统一入口。",
            },
            {
                "name": "图表中心模块",
                "description": "汇总趋势图、季节性图、损失图与多模型对比图，支持论文截图与结果展示。",
            },
        ],
        "backend_modules": [
            {
                "name": "数据文件服务",
                "description": "负责读取月度数据、模型评估结果与未来预测文件，降低前端直接处理文件的复杂度。",
            },
            {
                "name": "结果聚合服务",
                "description": "统一封装概览、指标、预测和图片资源接口，便于前端模块化调用。",
            },
            {
                "name": "图像资源服务",
                "description": "通过后端统一输出结果图路径，使系统具备更稳定的资源访问方式。",
            },
            {
                "name": "分析展示接口",
                "description": "对外提供标准 JSON 接口，为后续扩展用户管理、上传任务和模型重训预留空间。",
            },
        ],
        "optimizations": [
            "采用前后端分离架构，前端只负责展示，后端统一管理分析结果接口。",
            "将模型评估指标拆分为 MAE、RMSE、MAPE 三类单独图表，提高论文结果展示清晰度。",
            "通过图片资源中心统一管理结果图，减少页面静态资源耦合。",
            "保留 PyTorch LSTM 与传统机器学习模型并行对比，为系统扩展深度学习模块提供基础。",
        ],
    }
    return JsonResponse(payload)


def result_image(request, filename):
    file_path = DATA_ROOT / filename
    if not file_path.exists() or not file_path.is_file():
        raise Http404("图片不存在")
    return FileResponse(file_path.open("rb"), content_type="image/png")


@csrf_exempt
def forecast_job_create(request):
    if request.method != "POST":
        return JsonResponse({"error": "只支持 POST 请求"}, status=405)

    # Check if any job is already running
    if forecast_jobs.is_any_job_running():
        return JsonResponse(
            {"error": "已有预测任务正在运行，请等待完成后再试"},
            status=409,
        )

    # Create and start job
    job_id = forecast_jobs.create_job()
    forecast_jobs.start_job(job_id)

    return JsonResponse(
        {
            "job_id": job_id,
            "message": "预测任务已启动",
        },
        status=202,
    )


def forecast_job_detail(request, job_id):
    if request.method != "GET":
        return JsonResponse({"error": "只支持 GET 请求"}, status=405)

    job = forecast_jobs.get_job(job_id)
    if not job:
        return JsonResponse({"error": "任务不存在"}, status=404)

    return JsonResponse(job)
