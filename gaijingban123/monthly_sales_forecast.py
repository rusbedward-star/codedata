import os
import warnings
from pathlib import Path

import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
import torch
import torch.nn as nn
from sklearn.ensemble import (
    ExtraTreesRegressor,
    GradientBoostingRegressor,
    RandomForestRegressor,
)
from sklearn.linear_model import LinearRegression
from sklearn.metrics import mean_absolute_error, mean_squared_error
from sklearn.model_selection import GridSearchCV, TimeSeriesSplit
from sklearn.preprocessing import MinMaxScaler

try:
    from statsmodels.tsa.arima.model import ARIMA
    from statsmodels.tsa.stattools import adfuller

    STATSMODELS_AVAILABLE = True
    STATSMODELS_IMPORT_ERROR = ""
except Exception as exc:
    ARIMA = None
    adfuller = None
    STATSMODELS_AVAILABLE = False
    STATSMODELS_IMPORT_ERROR = str(exc)


warnings.filterwarnings("ignore")
plt.rcParams["font.sans-serif"] = [
    "PingFang SC",
    "Hiragino Sans GB",
    "Arial Unicode MS",
    "Microsoft YaHei",
    "DejaVu Sans",
]
plt.rcParams["axes.unicode_minus"] = False

BRAND_ALIAS = "牙膏"
CONFIDENCE_TOLERANCE = 0.20
np.random.seed(42)
torch.manual_seed(42)


def find_input_file():
    candidates = sorted(Path(".").glob("*.csv"))
    required_columns = {
        "date",
        "sales",
        "last_month_sales",
        "last_year_same_month",
        "month",
        "is_holiday",
        "is_promo",
        "region",
        "product_series",
    }

    for path in candidates:
        try:
            sample = pd.read_csv(path, nrows=3)
        except Exception:
            continue
        if required_columns.issubset(sample.columns):
            return str(path)

    raise FileNotFoundError("未找到符合月度预测结构的 CSV 数据文件。")


def safe_mape(y_true, y_pred):
    y_true = np.array(y_true, dtype=float)
    y_pred = np.array(y_pred, dtype=float)
    mask = y_true != 0
    if not np.any(mask):
        return np.nan
    return np.mean(np.abs((y_true[mask] - y_pred[mask]) / y_true[mask])) * 100


def load_and_preprocess_data(file_path):
    raw_df = pd.read_csv(file_path)
    raw_df["date"] = pd.to_datetime(raw_df["date"], format="%Y-%m")
    raw_df = raw_df.sort_values("date")

    raw_df["sales"] = raw_df["sales"].fillna(raw_df["sales"].mean())
    raw_df["last_month_sales"] = raw_df["last_month_sales"].fillna(
        raw_df["last_month_sales"].mean()
    )
    raw_df["last_year_same_month"] = raw_df["last_year_same_month"].fillna(
        raw_df["last_year_same_month"].mean()
    )
    raw_df["is_holiday"] = raw_df["is_holiday"].fillna(0)
    raw_df["is_promo"] = raw_df["is_promo"].fillna(0)

    encoded_df = raw_df.copy()

    # --- 新增时序衍生特征 ---
    encoded_df["sales_lag2"] = encoded_df["sales"].shift(2).fillna(encoded_df["sales"].mean())
    encoded_df["sales_lag3"] = encoded_df["sales"].shift(3).fillna(encoded_df["sales"].mean())
    encoded_df["sales_roll3"] = (
        encoded_df["sales"].shift(1).rolling(3, min_periods=1).mean()
        .fillna(encoded_df["sales"].mean())
    )
    encoded_df["sales_roll6"] = (
        encoded_df["sales"].shift(1).rolling(6, min_periods=1).mean()
        .fillna(encoded_df["sales"].mean())
    )
    encoded_df["mom_ratio"] = (
        encoded_df["sales"] / encoded_df["last_month_sales"].replace(0, np.nan)
    ).replace([np.inf, -np.inf], np.nan).fillna(1.0)
    encoded_df["yoy_diff"] = (
        encoded_df["sales"] - encoded_df["last_year_same_month"]
    ).fillna(0)
    encoded_df["yoy_ratio"] = (
        encoded_df["sales"] / encoded_df["last_year_same_month"].replace(0, np.nan)
    ).replace([np.inf, -np.inf], np.nan).fillna(1.0)
    encoded_df["promo_holiday"] = encoded_df["is_promo"] * encoded_df["is_holiday"]
    encoded_df["month_sin"] = np.sin(2 * np.pi * encoded_df["month"] / 12)
    encoded_df["month_cos"] = np.cos(2 * np.pi * encoded_df["month"] / 12)
    encoded_df["quarter"] = ((encoded_df["month"] - 1) // 3 + 1).astype(int)
    encoded_df["is_q1"] = (encoded_df["quarter"] == 1).astype(int)
    encoded_df["is_q2"] = (encoded_df["quarter"] == 2).astype(int)
    encoded_df["is_peak_month"] = encoded_df["month"].isin([1, 6, 11]).astype(int)

    encoded_df = pd.get_dummies(
        encoded_df,
        columns=["region", "product_series"],
        drop_first=True,
    )
    encoded_df = encoded_df.set_index("date")
    raw_df = raw_df.set_index("date")
    return raw_df, encoded_df


def split_features(encoded_df):
    X = encoded_df.drop("sales", axis=1)
    y = encoded_df["sales"]
    train_size = int(len(encoded_df) * 0.8)
    X_train, X_test = X[:train_size], X[train_size:]
    y_train, y_test = y[:train_size], y[train_size:]
    return X, y, X_train, X_test, y_train, y_test, train_size


def confidence_score(y_true, y_pred, tolerance=CONFIDENCE_TOLERANCE):
    """计算连续型置信度：偏差越小越接近 100，超出容差后逐步衰减。"""
    y_true = np.array(y_true, dtype=float)
    y_pred = np.array(y_pred, dtype=float)
    mask = y_true != 0
    if not np.any(mask):
        return np.nan

    ape = np.abs((y_pred[mask] - y_true[mask]) / y_true[mask])
    scores = np.clip(1 - ape / tolerance, 0, 1)
    return round(float(np.mean(scores) * 100), 2)


def timeseries_cv_confidence(model, X, y, n_splits=4, tolerance=CONFIDENCE_TOLERANCE):
    """
    使用 expanding-window 时序交叉验证计算平均置信度。
    对每个 fold 用 confidence_score() 评分，最终取均值。
    样本少于 n_splits*2 时自动降低折数。
    """
    n_splits = min(n_splits, max(2, len(X) // 3))
    tscv = TimeSeriesSplit(n_splits=n_splits)
    fold_scores = []
    for train_idx, test_idx in tscv.split(X):
        if len(test_idx) == 0:
            continue
        X_tr, X_te = X.iloc[train_idx], X.iloc[test_idx]
        y_tr, y_te = y.iloc[train_idx], y.iloc[test_idx]
        model.fit(X_tr, y_tr)
        y_pred = model.predict(X_te)
        score = confidence_score(y_te.values, y_pred, tolerance)
        if not np.isnan(score):
            fold_scores.append(score)
    return round(float(np.mean(fold_scores)), 2) if fold_scores else np.nan


def evaluate_predictions(model_name, y_true, y_pred):
    mae = round(mean_absolute_error(y_true, y_pred), 4)
    rmse = round(np.sqrt(mean_squared_error(y_true, y_pred)), 4)
    mape = round(safe_mape(y_true, y_pred), 4)
    confidence = confidence_score(y_true, y_pred)
    return {
        "模型": model_name,
        "MAE": mae,
        "RMSE": rmse,
        "MAPE": f"{mape:.2f}%",
        "置信度": f"{confidence:.2f}%",
        "MAE原始值": mae,
        "RMSE原始值": rmse,
        "MAPE原始值": mape,
        "置信度原始值": confidence,
    }


def create_lstm_sequences(values, look_back):
    X_data = []
    y_data = []
    for i in range(look_back, len(values)):
        X_data.append(values[i - look_back : i])
        y_data.append(values[i])
    X_data = np.array(X_data)
    y_data = np.array(y_data)
    return X_data, y_data


class TorchLSTMRegressor(nn.Module):
    def __init__(self, hidden_size=32):
        super().__init__()
        self.lstm = nn.LSTM(input_size=1, hidden_size=hidden_size, batch_first=True)
        self.fc1 = nn.Linear(hidden_size, 16)
        self.relu = nn.ReLU()
        self.fc2 = nn.Linear(16, 1)

    def forward(self, x):
        output, _ = self.lstm(x)
        output = output[:, -1, :]
        output = self.fc1(output)
        output = self.relu(output)
        output = self.fc2(output)
        return output


def plot_lstm_loss(train_losses, val_losses):
    plt.figure(figsize=(10, 5))
    plt.plot(train_losses, label="训练损失", linewidth=2)
    if val_losses:
        plt.plot(val_losses, label="验证损失", linewidth=2)
    plt.title("LSTM模型训练损失变化图", fontsize=14, pad=20)
    plt.xlabel("Epoch", fontsize=12)
    plt.ylabel("Loss", fontsize=12)
    plt.legend()
    plt.grid(True, alpha=0.3)
    plt.tight_layout()
    plt.savefig("LSTM训练损失图.png", dpi=300, bbox_inches="tight")
    plt.show()


def build_lstm_model(raw_df, train_size, predict_months=12, look_back=3):
    sales_values = raw_df["sales"].values.reshape(-1, 1)
    scaler = MinMaxScaler()
    scaled_values = scaler.fit_transform(sales_values)

    X_all, y_all = create_lstm_sequences(scaled_values, look_back)
    split_index = train_size - look_back
    X_train = X_all[:split_index]
    y_train = y_all[:split_index]

    if len(X_train) < 4:
        raise ValueError("LSTM训练样本过少，无法完成建模。")

    X_train = X_train.reshape((X_train.shape[0], X_train.shape[1], 1)).astype(np.float32)
    y_train = y_train.astype(np.float32)

    val_size = max(1, int(len(X_train) * 0.2))
    X_fit = X_train[:-val_size]
    y_fit = y_train[:-val_size]
    X_val = X_train[-val_size:]
    y_val = y_train[-val_size:]

    model = TorchLSTMRegressor(hidden_size=32)
    criterion = nn.MSELoss()
    optimizer = torch.optim.Adam(model.parameters(), lr=0.01)

    X_fit_tensor = torch.tensor(X_fit, dtype=torch.float32)
    y_fit_tensor = torch.tensor(y_fit, dtype=torch.float32).view(-1, 1)
    X_val_tensor = torch.tensor(X_val, dtype=torch.float32)
    y_val_tensor = torch.tensor(y_val, dtype=torch.float32).view(-1, 1)

    train_losses = []
    val_losses = []
    best_state = None
    best_val_loss = float("inf")
    patience = 30
    patience_counter = 0

    for _ in range(300):
        model.train()
        optimizer.zero_grad()
        fit_pred = model(X_fit_tensor)
        train_loss = criterion(fit_pred, y_fit_tensor)
        train_loss.backward()
        optimizer.step()

        model.eval()
        with torch.no_grad():
            val_pred = model(X_val_tensor)
            val_loss = criterion(val_pred, y_val_tensor)

        train_losses.append(float(train_loss.item()))
        val_losses.append(float(val_loss.item()))

        current_val_loss = float(val_loss.item())
        if current_val_loss < best_val_loss:
            best_val_loss = current_val_loss
            best_state = {k: v.detach().clone() for k, v in model.state_dict().items()}
            patience_counter = 0
        else:
            patience_counter += 1
            if patience_counter >= patience:
                break

    if best_state is not None:
        model.load_state_dict(best_state)

    plot_lstm_loss(train_losses, val_losses)

    test_predictions = []
    test_indices = raw_df.index[train_size:]
    model.eval()
    for idx in range(train_size, len(raw_df)):
        window = scaled_values[idx - look_back : idx]
        window = torch.tensor(window.reshape((1, look_back, 1)), dtype=torch.float32)
        with torch.no_grad():
            pred_scaled = float(model(window).item())
        pred_value = scaler.inverse_transform([[pred_scaled]])[0][0]
        test_predictions.append(pred_value)

    lstm_test_pred = pd.Series(test_predictions, index=test_indices)
    lstm_metrics = evaluate_predictions(
        "LSTM",
        raw_df["sales"].iloc[train_size:],
        lstm_test_pred,
    )

    history_scaled = scaled_values.flatten().tolist()
    future_dates = pd.date_range(
        start=raw_df.index[-1] + pd.DateOffset(months=1),
        periods=predict_months,
        freq="MS",
    )
    future_predictions = []
    for _ in range(predict_months):
        window = np.array(history_scaled[-look_back:]).reshape((1, look_back, 1))
        window_tensor = torch.tensor(window, dtype=torch.float32)
        with torch.no_grad():
            pred_scaled = float(model(window_tensor).item())
        pred_value = scaler.inverse_transform([[pred_scaled]])[0][0]
        pred_value = max(float(pred_value), 0.0)
        future_predictions.append(pred_value)
        history_scaled.append(pred_scaled)

    lstm_future = pd.Series(future_predictions, index=future_dates)
    print("\n===== LSTM模型评估指标 =====")
    for key, value in lstm_metrics.items():
        if key != "模型":
            print(f"{key}: {value}")

    return model, lstm_test_pred, lstm_metrics, lstm_future


def build_arima_model(raw_df, train_size, predict_months=12):
    if not STATSMODELS_AVAILABLE:
        print("\n===== ARIMA模型已跳过 =====")
        print(f"原因: 当前环境中的 statsmodels 不可用，错误信息: {STATSMODELS_IMPORT_ERROR}")
        return None, None, None

    sales_series = raw_df["sales"]

    adf_result = adfuller(sales_series)
    print("===== ARIMA模型 - ADF平稳性检验 =====")
    print(f"ADF统计量: {adf_result[0]:.4f}")
    print(f"p值: {adf_result[1]:.4f}")
    if adf_result[1] < 0.05:
        print("结论：序列平稳，无需差分")
        d = 0
    else:
        print("结论：序列非平稳，使用一阶差分")
        d = 1

    train_arima = sales_series[:train_size]
    test_arima = sales_series[train_size:]

    # 自动搜索最优 (p, q)
    best_aic = float("inf")
    best_order = (1, d, 1)
    for p in range(0, 4):
        for q in range(0, 4):
            try:
                candidate = ARIMA(train_arima, order=(p, d, q)).fit()
                if candidate.aic < best_aic:
                    best_aic = candidate.aic
                    best_order = (p, d, q)
            except Exception:
                continue
    print(f"ARIMA 最优阶数: {best_order}，AIC={best_aic:.2f}")

    arima_fit = ARIMA(train_arima, order=best_order).fit()
    arima_pred = arima_fit.forecast(steps=len(test_arima))

    metrics = evaluate_predictions("ARIMA", test_arima, arima_pred)
    print("\n===== ARIMA模型评估指标 =====")
    for key, value in metrics.items():
        if key != "模型":
            print(f"{key}: {value}")

    future_model = ARIMA(sales_series, order=best_order).fit()
    future_dates = pd.date_range(
        start=sales_series.index[-1] + pd.DateOffset(months=1),
        periods=predict_months,
        freq="MS",
    )
    future_pred = future_model.forecast(steps=predict_months)
    future_pred.index = future_dates

    return arima_pred, metrics, future_pred


def build_supervised_models(X_train, X_test, y_train, y_test, X_full=None, y_full=None):
    models = {}
    split_count = min(4, max(2, len(X_train) // 3))
    tscv = TimeSeriesSplit(n_splits=split_count)

    rf = RandomForestRegressor(random_state=42)
    rf_param_grid = {
        "n_estimators": [200, 400, 600],
        "max_depth": [3, 5, 8, None],
        "min_samples_leaf": [1, 2, 3],
        "max_features": ["sqrt", 0.7, 1.0],
    }
    rf_search = GridSearchCV(
        estimator=rf,
        param_grid=rf_param_grid,
        cv=tscv,
        scoring="neg_mean_squared_error",
        n_jobs=1,
    )
    rf_search.fit(X_train, y_train)
    best_rf = rf_search.best_estimator_
    print("\n===== 随机森林最优超参数 =====")
    print(rf_search.best_params_)

    gbr_param_grid = {
        "n_estimators": [200, 400],
        "learning_rate": [0.03, 0.05, 0.1],
        "max_depth": [2, 3, 4],
        "subsample": [0.8, 1.0],
    }
    gbr_search = GridSearchCV(
        estimator=GradientBoostingRegressor(random_state=42),
        param_grid=gbr_param_grid,
        cv=tscv,
        scoring="neg_mean_squared_error",
        n_jobs=1,
    )
    gbr_search.fit(X_train, y_train)
    best_gbr = gbr_search.best_estimator_
    print("\n===== 梯度提升最优超参数 =====")
    print(gbr_search.best_params_)

    lr = LinearRegression()
    lr.fit(X_train, y_train)

    et_param_grid = {
        "n_estimators": [200, 400],
        "max_depth": [5, 10, None],
        "min_samples_leaf": [1, 2],
    }
    et_search = GridSearchCV(
        estimator=ExtraTreesRegressor(random_state=42),
        param_grid=et_param_grid,
        cv=tscv,
        scoring="neg_mean_squared_error",
        n_jobs=1,
    )
    et_search.fit(X_train, y_train)
    best_et = et_search.best_estimator_
    print("\n===== 极端随机森林最优超参数 =====")
    print(et_search.best_params_)

    models["随机森林"] = best_rf
    models["梯度提升回归"] = best_gbr
    models["线性回归"] = lr
    models["极端随机森林"] = best_et

    predictions = {}
    metrics = []
    for model_name, model in models.items():
        pred = model.predict(X_test)
        predictions[model_name] = pred
        metric = evaluate_predictions(model_name, y_test, pred)
        if X_full is not None and y_full is not None and len(X_full) >= 9:
            cv_conf = timeseries_cv_confidence(model, X_full, y_full)
            if not np.isnan(cv_conf):
                metric["置信度原始值"] = cv_conf
                metric["置信度"] = f"{cv_conf:.2f}%"
        metrics.append(metric)

    metrics_df = pd.DataFrame(metrics).sort_values(
        ["置信度原始值", "RMSE原始值"],
        ascending=[False, True],
    ).reset_index(drop=True)
    print("\n===== 监督学习模型评估指标 =====")
    print(metrics_df.to_string(index=False))
    return models, predictions, metrics_df


def build_future_features(raw_df, feature_columns, predict_months=12):
    future_dates = pd.date_range(
        start=raw_df.index[-1] + pd.DateOffset(months=1),
        periods=predict_months,
        freq="MS",
    )
    default_values = {col: 0 for col in feature_columns}
    return future_dates, default_values


def recursive_future_predict(model, raw_df, feature_columns, predict_months=12):
    future_dates, default_values = build_future_features(
        raw_df, feature_columns, predict_months=predict_months
    )
    history = raw_df["sales"].copy()
    predictions = []

    for date in future_dates:
        row = {col: 0 for col in feature_columns}
        row.update(default_values)
        row["last_month_sales"] = float(history.iloc[-1])
        same_month_history = history[history.index.month == date.month]
        row["last_year_same_month"] = (
            float(same_month_history.mean())
            if not same_month_history.empty
            else float(history.mean())
        )
        row["month"] = date.month
        row["is_holiday"] = 1 if date.month in [1, 5, 10] else 0
        row["is_promo"] = 1 if date.month in [6, 11] else 0

        if "product_series_经典系列" in feature_columns:
            row["product_series_经典系列"] = 1

        row_df = pd.DataFrame([row], index=[date])[feature_columns]
        pred_value = float(model.predict(row_df)[0])
        predictions.append(pred_value)
        history.loc[date] = pred_value

    return pd.Series(predictions, index=future_dates)


def select_best_model(metrics_df):
    high_conf = metrics_df[metrics_df["置信度原始值"] >= 80]
    if not high_conf.empty:
        best_row = high_conf.sort_values("RMSE原始值").iloc[0]
        best_model_name = best_row["模型"]
        print(
            f"\n===== 最优模型 =====\n{best_model_name}"
            f"  (置信度={best_row['置信度']}，RMSE={best_row['RMSE']})"
        )
    else:
        best_row = metrics_df.sort_values(
            ["置信度原始值", "RMSE原始值"], ascending=[False, True]
        ).iloc[0]
        best_model_name = best_row["模型"]
        print(
            f"\n===== 最优模型 =====\n{best_model_name}"
            f"  (置信度={best_row['置信度']}，RMSE={best_row['RMSE']})"
            "\n  [警告] 所有模型置信度均未达到 80%，已选置信度最高者"
        )
    return best_model_name


def save_metrics(metrics_df, arima_metrics=None):
    all_metrics = metrics_df.copy()
    all_metrics = all_metrics.sort_values(
        ["置信度原始值", "RMSE原始值"], ascending=[False, True]
    )
    export_df = pd.DataFrame(
        {
            "模型": all_metrics["模型"],
            "MAE": all_metrics["MAE原始值"].map(lambda v: f"{v:.2f}%"),
            "RMSE": all_metrics["RMSE原始值"].map(lambda v: f"{v:.2f}%"),
            "MAPE": all_metrics["MAPE原始值"].map(lambda v: f"{v:.2f}%"),
            "置信度": all_metrics["置信度原始值"].map(lambda v: f"{v:.2f}%"),
        }
    )
    export_df.to_csv("模型评估结果.csv", index=False, encoding="utf-8-sig")
    return all_metrics


def save_future_results(future_predictions):
    future_df = pd.DataFrame(future_predictions)
    future_df.index.name = "月份"
    future_df = future_df.reset_index()
    future_df["月份"] = future_df["月份"].dt.strftime("%Y-%m")
    future_df.to_csv("未来12个月预测结果.csv", index=False, encoding="utf-8-sig")
    return future_df


def plot_sales_trend(raw_df):
    rolling_mean = raw_df["sales"].rolling(window=3, min_periods=1).mean()

    plt.figure(figsize=(14, 7))
    plt.plot(raw_df.index, raw_df["sales"], marker="o", linewidth=2, label="月销量")
    plt.plot(raw_df.index, rolling_mean, linestyle="--", linewidth=2, label="3个月滚动均值")
    plt.title(f"{BRAND_ALIAS}月度销量趋势与滚动均值", fontsize=14, pad=20)
    plt.xlabel("日期", fontsize=12)
    plt.ylabel("销量（万支）", fontsize=12)
    plt.legend()
    plt.grid(True, alpha=0.3)
    plt.tight_layout()
    plt.savefig("月度销量趋势与滚动均值图.png", dpi=300, bbox_inches="tight")
    plt.show()


def plot_seasonality(raw_df):
    seasonality_df = raw_df.copy()
    seasonality_df["月份"] = seasonality_df.index.month
    month_avg = seasonality_df.groupby("月份")["sales"].mean()

    plt.figure(figsize=(12, 6))
    plt.bar(month_avg.index, month_avg.values, color="#5B8FF9")
    plt.title(f"{BRAND_ALIAS}月度季节性分析图", fontsize=14, pad=20)
    plt.xlabel("月份", fontsize=12)
    plt.ylabel("平均销量（万支）", fontsize=12)
    plt.xticks(range(1, 13))
    plt.grid(axis="y", alpha=0.3)
    plt.tight_layout()
    plt.savefig("月度季节性分析图.png", dpi=300, bbox_inches="tight")
    plt.show()


def plot_model_comparison(all_metrics):
    metric_configs = [
        ("MAE原始值", "MAE", "MAE指标对比图.png"),
        ("RMSE原始值", "RMSE", "RMSE指标对比图.png"),
        ("MAPE原始值", "MAPE", "MAPE指标对比图.png"),
    ]
    base_colors = ["#5B8FF9", "#61DDAA", "#F6BD16", "#E8684A", "#9270CA", "#6DC8EC"]
    colors = [base_colors[i % len(base_colors)] for i in range(len(all_metrics))]

    for metric_key, metric_label, output_name in metric_configs:
        plt.figure(figsize=(10, 6))
        plt.bar(all_metrics["模型"], all_metrics[metric_key], color=colors[: len(all_metrics)])
        plt.title(f"{metric_label} 指标对比", fontsize=14, pad=20)
        plt.xlabel("模型", fontsize=12)
        plt.ylabel(metric_label, fontsize=12)
        plt.xticks(rotation=20)
        plt.grid(axis="y", alpha=0.3)
        plt.tight_layout()
        plt.savefig(output_name, dpi=300, bbox_inches="tight")
        plt.show()


def plot_test_predictions(raw_df, train_size, supervised_predictions):
    plt.figure(figsize=(14, 7))
    plt.plot(
        raw_df.index[:train_size],
        raw_df["sales"][:train_size],
        color="lightgray",
        label="训练集真实销量",
        alpha=0.7,
    )
    plt.plot(
        raw_df.index[train_size:],
        raw_df["sales"][train_size:],
        label="测试集真实销量",
        color="black",
        linewidth=2,
    )

    line_styles = {
        "随机森林": ("#5B8FF9", "-."),
        "梯度提升回归": ("#61DDAA", ":"),
        "线性回归": ("#9270CA", "--"),
        "极端随机森林": ("#F6BD16", "-"),
        "LSTM": ("#E8684A", "-"),
    }
    for model_name, pred in supervised_predictions.items():
        color, style = line_styles[model_name]
        plt.plot(
            raw_df.index[train_size:],
            pred,
            label=f"{model_name}预测",
            color=color,
            linestyle=style,
            linewidth=2,
        )

    plt.axvline(
        raw_df.index[train_size],
        color="gray",
        linestyle=":",
        label="训练/测试集分割线",
    )
    plt.title("测试集多模型预测效果对比", fontsize=14, pad=20)
    plt.xlabel("日期", fontsize=12)
    plt.ylabel("销量（万支）", fontsize=12)
    plt.legend(loc="best", fontsize=10)
    plt.grid(True, alpha=0.3)
    plt.tight_layout()
    plt.savefig("测试集多模型预测效果对比图.png", dpi=300, bbox_inches="tight")
    plt.show()


def plot_feature_importance(model, feature_columns):
    if not hasattr(model, "feature_importances_"):
        return

    importance_df = pd.DataFrame(
        {
            "feature": feature_columns,
            "importance": model.feature_importances_,
        }
    ).sort_values("importance", ascending=False)
    top_df = importance_df.head(8).sort_values("importance")

    plt.figure(figsize=(10, 6))
    plt.barh(top_df["feature"], top_df["importance"], color="#5AD8A6")
    plt.title("关键特征重要性分析", fontsize=14, pad=20)
    plt.xlabel("重要性", fontsize=12)
    plt.tight_layout()
    plt.savefig("关键特征重要性分析图.png", dpi=300, bbox_inches="tight")
    plt.show()


def pick_feature_model(models, metrics_df):
    tree_candidates = metrics_df[
        metrics_df["模型"].isin(["随机森林", "梯度提升回归", "极端随机森林"])
    ]
    if tree_candidates.empty:
        return models["随机森林"]
    best_tree_name = tree_candidates.sort_values("RMSE原始值").iloc[0]["模型"]
    return models[best_tree_name]


def plot_future_comparison(raw_df, future_predictions, best_model_name):
    plt.figure(figsize=(14, 7))
    plt.plot(raw_df.index, raw_df["sales"], label="历史真实销量", color="black", linewidth=2)

    future_df = pd.DataFrame(future_predictions)
    for column in future_df.columns:
        line_width = 3 if column == best_model_name else 1.8
        alpha = 1 if column == best_model_name else 0.8
        plt.plot(
            future_df.index,
            future_df[column],
            label=f"{column}未来预测",
            linewidth=line_width,
            alpha=alpha,
        )

    plt.axvline(raw_df.index[-1], color="gray", linestyle=":", label="预测起始点")
    plt.title(f"{BRAND_ALIAS}未来12个月多模型预测对比", fontsize=14, pad=20)
    plt.xlabel("日期", fontsize=12)
    plt.ylabel("销量（万支）", fontsize=12)
    plt.legend(loc="best", fontsize=10)
    plt.grid(True, alpha=0.3)
    plt.tight_layout()
    plt.savefig("未来12个月多模型预测图.png", dpi=300, bbox_inches="tight")
    plt.show()


def plot_best_future_trend(raw_df, future_predictions, best_model_name):
    best_future = future_predictions[best_model_name]

    plt.figure(figsize=(14, 7))
    plt.plot(raw_df.index, raw_df["sales"], label="历史真实销量", color="#5B8FF9", linewidth=2)
    plt.plot(
        best_future.index,
        best_future.values,
        label=f"{best_model_name}未来12个月预测",
        color="#F6BD16",
        linewidth=2.5,
        marker="o",
    )
    plt.axvline(raw_df.index[-1], color="black", linestyle=":", label="预测起始点")

    for date, value in best_future.items():
        plt.annotate(
            f"{value:.2f}",
            xy=(date, value),
            xytext=(0, 6),
            textcoords="offset points",
            fontsize=8,
            ha="center",
        )

    plt.title(f"{BRAND_ALIAS}历史与未来销量趋势图", fontsize=14, pad=20)
    plt.xlabel("日期", fontsize=12)
    plt.ylabel("销量（万支）", fontsize=12)
    plt.legend(loc="best", fontsize=10)
    plt.grid(True, alpha=0.3)
    plt.tight_layout()
    plt.savefig("历史与未来销量趋势图.png", dpi=300, bbox_inches="tight")
    plt.show()


def main():
    data_path = find_input_file()
    print(f"当前使用的数据文件: {data_path}")

    raw_df, encoded_df = load_and_preprocess_data(data_path)
    X, y, X_train, X_test, y_train, y_test, train_size = split_features(encoded_df)

    models, supervised_predictions, metrics_df = build_supervised_models(
        X_train, X_test, y_train, y_test, X_full=X, y_full=y
    )
    lstm_model, lstm_pred, lstm_metrics, lstm_future = build_lstm_model(raw_df, train_size)
    supervised_predictions["LSTM"] = lstm_pred.values
    metrics_df = pd.concat([metrics_df, pd.DataFrame([lstm_metrics])], ignore_index=True)
    metrics_df = metrics_df.sort_values(["置信度原始值", "RMSE原始值"], ascending=[False, True]).reset_index(drop=True)

    best_model_name = select_best_model(metrics_df)
    all_metrics = save_metrics(metrics_df)

    future_predictions = {}
    for model_name, model in models.items():
        model.fit(X, y)
        future_predictions[model_name] = recursive_future_predict(
            model,
            raw_df,
            X.columns,
        )
    future_predictions["LSTM"] = lstm_future

    save_future_results(future_predictions)

    plot_sales_trend(raw_df)
    plot_seasonality(raw_df)
    plot_model_comparison(all_metrics)
    plot_test_predictions(raw_df, train_size, supervised_predictions)
    feature_model = pick_feature_model(models, metrics_df)
    plot_feature_importance(feature_model, X.columns)
    plot_future_comparison(raw_df, future_predictions, best_model_name)
    plot_best_future_trend(raw_df, future_predictions, best_model_name)

    print("\n===== 全部结果已生成 =====")
    print("输出文件包括：")
    print("- 模型评估结果.csv")
    print("- 未来12个月预测结果.csv")
    print("- 月度销量趋势与滚动均值图.png")
    print("- 月度季节性分析图.png")
    print("- MAE指标对比图.png")
    print("- RMSE指标对比图.png")
    print("- MAPE指标对比图.png")
    print("- 测试集多模型预测效果对比图.png")
    print("- 关键特征重要性分析图.png")
    print("- 未来12个月多模型预测图.png")
    print("- 历史与未来销量趋势图.png")
    print("- LSTM训练损失图.png")


if __name__ == "__main__":
    main()
