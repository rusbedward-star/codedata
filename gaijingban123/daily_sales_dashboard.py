import os
import warnings

import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
from statsmodels.tsa.holtwinters import ExponentialSmoothing


warnings.filterwarnings("ignore")
plt.style.use("seaborn-v0_8-whitegrid")
plt.rcParams["font.sans-serif"] = [
    "SimHei",
    "Microsoft YaHei",
    "Arial Unicode MS",
    "PingFang SC",
    "Heiti TC",
]
plt.rcParams["axes.unicode_minus"] = False


def pick_input_file():
    preferred_files = [
        "销售出库表.xlsx - Sheet1.csv",
        "销售出库表.xlsx",
    ]
    for path in preferred_files:
        if os.path.exists(path):
            return path

    candidates = [
        filename
        for filename in os.listdir(".")
        if "销售" in filename and filename.endswith((".csv", ".xlsx"))
    ]
    if not candidates:
        raise FileNotFoundError("当前目录下未找到包含“销售”的 CSV 或 Excel 文件。")
    return candidates[0]


def load_sales_data(file_path):
    if file_path.endswith(".csv"):
        for encoding in ("utf-8", "gb18030"):
            try:
                return pd.read_csv(
                    file_path,
                    encoding=encoding,
                    sep=",",
                    on_bad_lines="skip",
                )
            except Exception:
                continue
        raise ValueError(f"CSV 文件读取失败: {file_path}")

    if file_path.endswith(".xlsx"):
        return pd.read_excel(file_path)

    raise ValueError(f"不支持的文件格式: {file_path}")


def prepare_daily_data(df):
    df = df.copy()
    df.columns = [column.strip() for column in df.columns]

    required_columns = {"日期", "实发数量"}
    missing_columns = required_columns - set(df.columns)
    if missing_columns:
        missing_text = "、".join(sorted(missing_columns))
        raise KeyError(f"缺少必要字段: {missing_text}")

    df["日期"] = pd.to_datetime(df["日期"], errors="coerce")
    df = df.dropna(subset=["日期"]).sort_values("日期")

    daily_quantity = df.groupby("日期")["实发数量"].sum()
    daily_quantity = daily_quantity.asfreq("D").fillna(0)

    df_analysis = df.copy()
    df_analysis["Weekday"] = df_analysis["日期"].dt.day_name()
    week_map = {
        "Monday": "周一",
        "Tuesday": "周二",
        "Wednesday": "周三",
        "Thursday": "周四",
        "Friday": "周五",
        "Saturday": "周六",
        "Sunday": "周日",
    }
    df_analysis["Weekday_CN"] = df_analysis["Weekday"].map(week_map)
    week_order = ["周一", "周二", "周三", "周四", "周五", "周六", "周日"]
    weekday_avg = (
        df_analysis.groupby("Weekday_CN")["实发数量"].mean().reindex(week_order)
    )

    top_products = (
        df.groupby("产品名称")["实发数量"].sum().nlargest(5).sort_values(ascending=True)
    )
    top_customers = (
        df.groupby("购货单位")["实发数量"].sum().nlargest(5).sort_values(ascending=True)
    )

    return daily_quantity, weekday_avg, top_products, top_customers


def forecast_sales(daily_quantity, forecast_days=30):
    model = ExponentialSmoothing(
        daily_quantity,
        seasonal_periods=7,
        trend="add",
        seasonal="add",
        damped_trend=True,
    ).fit()

    forecast = model.forecast(forecast_days)

    # 保留原 notebook 的表现形式，给未来曲线加入少量随机扰动。
    std_dev = daily_quantity.std()
    noise = np.random.normal(0, std_dev * 0.15, forecast_days)
    forecast_adjusted = forecast + noise
    forecast_adjusted[forecast_adjusted < 0] = 0

    return forecast_adjusted


def truncate_labels(labels, max_len=12):
    output = []
    for label in labels:
        label_text = str(label)
        if len(label_text) > max_len:
            output.append(label_text[:max_len] + "...")
        else:
            output.append(label_text)
    return output


def plot_dashboard(daily_quantity, weekday_avg, top_products, top_customers, forecast):
    fig = plt.figure(figsize=(18, 12))

    ax1 = plt.subplot2grid((2, 3), (0, 0), colspan=3)
    ax2 = plt.subplot2grid((2, 3), (1, 0))
    ax3 = plt.subplot2grid((2, 3), (1, 1))
    ax4 = plt.subplot2grid((2, 3), (1, 2))

    display_start = daily_quantity.index.max() - pd.DateOffset(days=30)
    plot_hist = daily_quantity[display_start:]

    ax1.plot(
        plot_hist.index,
        plot_hist.values,
        label="历史销量 (近30天)",
        color="#2ca02c",
        marker="o",
        linewidth=2,
    )
    ax1.plot(
        forecast.index,
        forecast.values,
        label="未来30天预测",
        color="#d62728",
        linestyle="--",
        marker="x",
        linewidth=2,
    )
    ax1.set_title("销售趋势预测 (Holt-Winters 模型)", fontsize=16, fontweight="bold")
    ax1.set_ylabel("销售数量")
    ax1.legend(loc="upper left", fontsize=12)
    ax1.grid(True, linestyle="--", alpha=0.5)

    colors = plt.cm.Blues(np.linspace(0.4, 0.9, len(weekday_avg)))
    bars = ax2.bar(weekday_avg.index, weekday_avg.values, color=colors)
    ax2.set_title("周度销量规律 (平均每日)", fontsize=14, fontweight="bold")
    ax2.set_ylabel("平均销量")
    ax2.tick_params(axis="x", rotation=45)
    max_idx = int(np.argmax(weekday_avg.values))
    bars[max_idx].set_color("#ff7f0e")

    product_labels = truncate_labels(top_products.index)
    ax3.barh(product_labels, top_products.values, color="#17becf")
    ax3.set_title("Top 5 畅销商品", fontsize=14, fontweight="bold")
    ax3.set_xlabel("总销量")

    customer_labels = truncate_labels(top_customers.index)
    ax4.barh(customer_labels, top_customers.values, color="#9467bd")
    ax4.set_title("Top 5 核心客户", fontsize=14, fontweight="bold")
    ax4.set_xlabel("总采购量")

    plt.tight_layout()
    plt.show()


def main():
    file_path = pick_input_file()
    print(f"正在读取文件: {file_path}")

    df = load_sales_data(file_path)
    daily_quantity, weekday_avg, top_products, top_customers = prepare_daily_data(df)
    forecast = forecast_sales(daily_quantity)
    plot_dashboard(daily_quantity, weekday_avg, top_products, top_customers, forecast)
    print("数据分析看板已生成。")


if __name__ == "__main__":
    main()
