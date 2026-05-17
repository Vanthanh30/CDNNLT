from __future__ import annotations

import hashlib
from datetime import date
from datetime import timedelta

import joblib
import numpy as np
import pandas as pd
from sklearn.ensemble import RandomForestRegressor
from sklearn.metrics import mean_absolute_error

from config import MIN_TRAINING_DAYS, MODEL_DIR
from database import fetch_active_diseases, fetch_daily_cases, fetch_disease_regions


MODEL_VERSION = 5
FEATURE_COLUMNS = [
    "day_index",
    "day_of_week",
    "observed",
    "days_since_observed",
    "lag_1",
    "lag_2",
    "lag_3",
    "lag_7",
    "rolling_3",
    "rolling_7",
    "rolling_14",
    "trend_7",
    "event_count_7",
]


def _model_key(disease_name: str | None, location: str | None) -> str:
    raw = f"v{MODEL_VERSION}::{disease_name or 'all'}::{location or 'all'}"
    return hashlib.sha1(raw.encode("utf-8")).hexdigest()[:16]


def _model_path(disease_name: str | None, location: str | None):
    MODEL_DIR.mkdir(parents=True, exist_ok=True)
    return MODEL_DIR / f"forecast_{_model_key(disease_name, location)}.joblib"


def _continuous_series(df: pd.DataFrame) -> pd.DataFrame:
    if df.empty:
        return pd.DataFrame(
            columns=[
                "event_date",
                "cases_infected",
                "event_count",
                "observed",
                "signal_cases",
            ]
        )

    start = min(df["event_date"])
    end = max(df["event_date"])
    calendar = pd.DataFrame({"event_date": pd.date_range(start, end, freq="D").date})
    series = calendar.merge(df, on="event_date", how="left")

    series["observed"] = series["cases_infected"].notna().astype(int)
    series["cases_infected"] = pd.to_numeric(series["cases_infected"], errors="coerce")
    series["event_count"] = pd.to_numeric(
        series.get("event_count", 0), errors="coerce"
    ).fillna(0)

    observed_cases = series["cases_infected"].clip(lower=0)
    positive_cases = observed_cases.where(observed_cases > 0)
    positive_count = int(positive_cases.notna().sum())

    if positive_count == 0:
        signal = pd.Series(0.0, index=series.index)
    elif positive_count == 1:
        first_idx = positive_cases.first_valid_index()
        signal = pd.Series(0.0, index=series.index)
        if first_idx is not None:
            first_value = float(positive_cases.loc[first_idx])
            days_after = np.arange(len(series) - first_idx)
            signal.iloc[first_idx:] = first_value * np.power(0.9, days_after)
    else:
        signal = positive_cases.interpolate(method="linear")
        first_idx = positive_cases.first_valid_index()
        last_idx = positive_cases.last_valid_index()
        if first_idx is not None:
            signal.iloc[:first_idx] = 0
        if last_idx is not None and last_idx + 1 < len(signal):
            last_value = float(positive_cases.loc[last_idx])
            days_after = np.arange(1, len(signal) - last_idx)
            signal.iloc[last_idx + 1 :] = last_value * np.power(0.9, days_after)
        signal = signal.fillna(0)

    series["signal_cases"] = signal.ewm(span=7, adjust=False).mean().clip(lower=0)
    series["cases_infected"] = observed_cases.fillna(0).clip(lower=0)
    return series


def _add_features(series: pd.DataFrame) -> pd.DataFrame:
    data = series.copy()
    y = data["signal_cases"].astype(float)
    observed = data.get("observed", pd.Series(1, index=data.index)).astype(int)

    data["day_index"] = np.arange(len(data))
    data["day_of_week"] = pd.to_datetime(data["event_date"]).dt.dayofweek
    data["observed"] = observed

    last_seen = []
    counter = 0
    for flag in observed:
        if flag:
            counter = 0
        else:
            counter += 1
        last_seen.append(counter)
    data["days_since_observed"] = last_seen

    data["lag_1"] = y.shift(1)
    data["lag_2"] = y.shift(2)
    data["lag_3"] = y.shift(3)
    data["lag_7"] = y.shift(7)
    data["rolling_3"] = y.shift(1).rolling(3, min_periods=1).mean()
    data["rolling_7"] = y.shift(1).rolling(7, min_periods=1).mean()
    data["rolling_14"] = y.shift(1).rolling(14, min_periods=1).mean()
    data["trend_7"] = data["rolling_3"] - data["rolling_7"]
    data["event_count_7"] = (
        data.get("event_count", 0).shift(1).rolling(7, min_periods=1).sum()
    )
    return data.fillna(0)


def _metrics(y_true: pd.Series, y_pred: np.ndarray) -> dict:
    if len(y_true) == 0:
        return {"mae": None, "wape": None}

    y_true_arr = np.asarray(y_true, dtype=float)
    y_pred_arr = np.asarray(y_pred, dtype=float)
    mae = float(mean_absolute_error(y_true_arr, y_pred_arr))
    denominator = float(np.sum(np.abs(y_true_arr)))
    wape = (
        float(np.sum(np.abs(y_true_arr - y_pred_arr)) / denominator)
        if denominator
        else None
    )
    return {
        "mae": mae,
        "wape": wape,
    }


def _fallback_forecast(series: pd.DataFrame, forecast_days: int) -> list[dict]:
    if series.empty:
        baseline = 0.0
        trend = 0.0
        last_date = pd.Timestamp.today().date()
    else:
        signal = series["signal_cases"].astype(float)
        recent = signal.tail(7)
        previous = signal.tail(14).head(7)
        baseline = float(recent.mean()) if len(recent) else 0.0
        trend = float(recent.mean() - previous.mean()) / 7 if len(previous) else 0.0
        last_date = max(series["event_date"])

    output = []
    for day in range(1, forecast_days + 1):
        predicted = max(0, round(baseline + trend * day))
        output.append(
            {
                "date": (last_date + timedelta(days=day)).isoformat(),
                "predicted_cases": int(predicted),
            }
        )
    return output


def _pad_series_to_today(series: pd.DataFrame) -> pd.DataFrame:
    if series.empty:
        return series

    today = date.today()
    last_date = max(series["event_date"])
    if last_date >= today:
        return series

    rows = []
    signal = float(series["signal_cases"].iloc[-1])
    for next_date in pd.date_range(last_date + timedelta(days=1), today, freq="D").date:
        signal *= 0.88
        rows.append(
            {
                "event_date": next_date,
                "cases_infected": 0,
                "event_count": 0,
                "observed": 0,
                "signal_cases": signal,
            }
        )

    if not rows:
        return series
    return pd.concat([series, pd.DataFrame(rows)], ignore_index=True)


def train_forecast_model(
    disease_name: str | None = None,
    location: str | None = None,
    history_days: int = 180,
) -> dict:
    raw = fetch_daily_cases(
        disease_name=disease_name, location=location, history_days=history_days
    )
    series = _continuous_series(raw)
    observed_days = int(series["observed"].sum()) if not series.empty else 0

    if len(series) < MIN_TRAINING_DAYS or observed_days < 3:
        model_data = {
            "model_version": MODEL_VERSION,
            "method": "signal_moving_average_fallback",
            "series": series,
            "metrics": {"mae": None, "wape": None},
            "disease_name": disease_name,
            "location": location,
            "history_days": history_days,
        }
        joblib.dump(model_data, _model_path(disease_name, location))
        return {
            "method": model_data["method"],
            "training_days": len(series),
            "observed_days": observed_days,
            "mae": None,
            "wape": None,
            "message": "Not enough observed days; using signal moving average fallback.",
        }

    featured = _add_features(series)
    X = featured[FEATURE_COLUMNS]
    y = featured["signal_cases"].astype(float)

    split_index = max(1, int(len(featured) * 0.8))
    X_train, y_train = X.iloc[:split_index], y.iloc[:split_index]
    X_test, y_test = X.iloc[split_index:], y.iloc[split_index:]

    model = RandomForestRegressor(
        n_estimators=240,
        min_samples_leaf=2,
        random_state=42,
    )
    model.fit(X_train, y_train)

    metrics = {"mae": None, "wape": None}
    if len(X_test):
        pred = np.clip(model.predict(X_test), 0, None)
        metrics = _metrics(y_test, pred)

    model_data = {
        "model_version": MODEL_VERSION,
        "method": "random_forest_signal_v5",
        "model": model,
        "series": series,
        "metrics": metrics,
        "disease_name": disease_name,
        "location": location,
        "history_days": history_days,
    }
    joblib.dump(model_data, _model_path(disease_name, location))

    return {
        "method": model_data["method"],
        "training_days": len(series),
        "observed_days": observed_days,
        "mae": metrics["mae"],
        "wape": metrics["wape"],
        "message": "Model trained on smoothed reporting signal.",
    }


def _next_feature_row(series: pd.DataFrame) -> pd.DataFrame:
    next_date = max(series["event_date"]) + timedelta(days=1)
    next_seed = pd.concat(
        [
            series,
            pd.DataFrame(
                [
                    {
                        "event_date": next_date,
                        "cases_infected": 0,
                        "event_count": 0,
                        "observed": 0,
                        "signal_cases": float(series["signal_cases"].iloc[-1])
                        if len(series)
                        else 0,
                    }
                ]
            ),
        ],
        ignore_index=True,
    )
    return _add_features(next_seed).iloc[-1:]


def _forecast_context(series: pd.DataFrame) -> dict:
    signal = series["signal_cases"].astype(float)
    if signal.empty:
        return {
            "last_signal": 0.0,
            "recent_avg": 0.0,
            "previous_avg": 0.0,
            "trend_per_day": 0.0,
        }

    recent = signal.tail(7)
    previous = signal.tail(14).head(7)
    recent_avg = float(recent.mean()) if len(recent) else 0.0
    previous_avg = float(previous.mean()) if len(previous) else recent_avg
    return {
        "last_signal": float(signal.iloc[-1]),
        "recent_avg": recent_avg,
        "previous_avg": previous_avg,
        "trend_per_day": (recent_avg - previous_avg) / 7,
    }


def _baseline_next_signal(context: dict, step: int) -> float:
    last_signal = float(context["last_signal"])
    recent_avg = float(context["recent_avg"])
    trend_per_day = float(context["trend_per_day"])

    min_decay = max(last_signal, recent_avg * 0.7) * np.power(0.93, step)
    trend_projection = last_signal + trend_per_day * step
    return max(0.0, min_decay, trend_projection)


def _predict_with_model(model_data: dict, forecast_days: int) -> list[dict]:
    series = _pad_series_to_today(model_data["series"].copy())
    model = model_data.get("model")
    if model is None:
        return _fallback_forecast(series, forecast_days)

    future = []
    context = _forecast_context(series)
    previous_prediction = float(context["last_signal"])
    for step in range(1, forecast_days + 1):
        next_row = _next_feature_row(series)
        next_date = next_row["event_date"].iloc[0]
        model_signal = max(0.0, float(model.predict(next_row[FEATURE_COLUMNS])[0]))
        baseline_signal = _baseline_next_signal(context, step)

        if baseline_signal > 1 and model_signal < baseline_signal * 0.35:
            predicted_signal = baseline_signal * 0.75 + model_signal * 0.25
        else:
            predicted_signal = baseline_signal * 0.45 + model_signal * 0.55

        if previous_prediction > 10:
            predicted_signal = max(predicted_signal, previous_prediction * 0.82)

        predicted = int(round(predicted_signal))
        previous_prediction = predicted_signal

        future.append({"date": next_date.isoformat(), "predicted_cases": predicted})
        series = pd.concat(
            [
                series,
                pd.DataFrame(
                    [
                        {
                            "event_date": next_date,
                            "cases_infected": predicted,
                            "event_count": 0,
                            "observed": 0,
                            "signal_cases": predicted_signal,
                        }
                    ]
                ),
            ],
            ignore_index=True,
        )
    return future


def _risk_alert(history: list[dict], forecast: list[dict]) -> dict:
    history_signal = [
        item.get("signal_cases", item["cases_infected"]) for item in history[-14:]
    ]
    forecast_cases = [item["predicted_cases"] for item in forecast]

    recent_avg = float(np.mean(history_signal[-7:])) if history_signal else 0.0
    previous_avg = (
        float(np.mean(history_signal[:7])) if len(history_signal) >= 14 else recent_avg
    )
    forecast_peak = max(forecast_cases) if forecast_cases else 0
    forecast_avg = float(np.mean(forecast_cases)) if forecast_cases else 0.0

    baseline = max(recent_avg, 1.0)
    growth_ratio = (forecast_avg - baseline) / baseline
    peak_ratio = forecast_peak / baseline
    recent_growth = (recent_avg - previous_avg) / max(previous_avg, 1.0)
    risk_score = min(
        1.0,
        max(
            0.0,
            growth_ratio * 0.45
            + max(0.0, peak_ratio - 1) * 0.35
            + max(0.0, recent_growth) * 0.2,
        ),
    )

    if recent_avg >= 150 and forecast_peak >= 50:
        level = "MEDIUM"
        message = "Cảnh báo trung bình: tín hiệu gần đây vẫn ở mức cao, cần tiếp tục giám sát dù dự báo đang giảm."
    elif forecast_peak >= max(10, recent_avg * 1.8) or risk_score >= 0.65:
        level = "HIGH"
        message = "Cảnh báo cao: tín hiệu dự báo tăng mạnh, cần theo dõi và chuẩn bị phản ứng sớm."
    elif forecast_peak >= max(5, recent_avg * 1.25) or risk_score >= 0.35:
        level = "MEDIUM"
        message = "Cảnh báo trung bình: xu hướng có dấu hiệu tăng, nên tăng tần suất giám sát."
    else:
        level = "LOW"
        message = "Nguy cơ thấp: chưa thấy tín hiệu bùng phát rõ trong kỳ dự báo."

    return {
        "risk_level": level,
        "risk_score": round(risk_score, 3),
        "recent_avg": round(recent_avg, 2),
        "forecast_avg": round(forecast_avg, 2),
        "forecast_peak": int(forecast_peak),
        "message": message,
    }


def get_forecast(
    disease_name: str | None = None,
    location: str | None = None,
    forecast_days: int = 14,
    history_days: int = 180,
) -> dict:
    forecast_days = min(14, max(7, int(forecast_days)))
    path = _model_path(disease_name, location)
    if not path.exists():
        train_forecast_model(
            disease_name=disease_name, location=location, history_days=history_days
        )

    model_data = joblib.load(path)
    if (
        model_data.get("model_version") != MODEL_VERSION
        or model_data.get("history_days") != history_days
    ):
        train_forecast_model(
            disease_name=disease_name, location=location, history_days=history_days
        )
        model_data = joblib.load(path)

    series = _pad_series_to_today(model_data["series"])
    forecast = _predict_with_model(model_data, forecast_days)
    history = [
        {
            "date": row.event_date.isoformat(),
            "cases_infected": int(row.cases_infected),
            "signal_cases": round(float(row.signal_cases), 2),
            "observed": bool(row.observed),
        }
        for row in series.tail(30).itertuples(index=False)
    ]
    metrics = model_data.get("metrics") or {"mae": model_data.get("mae"), "wape": None}

    return {
        "disease_name": disease_name,
        "location": location,
        "forecast_days": forecast_days,
        "method": model_data["method"],
        "observed_days": int(series["observed"].sum()) if not series.empty else 0,
        "mae": metrics.get("mae"),
        "wape": metrics.get("wape"),
        "history": history,
        "forecast": forecast,
        "alert": _risk_alert(history, forecast),
        "notes": [
            "Model v5 trains on positive-case reporting signal because article dates are sparse observations.",
            "cases_infected is raw article-derived data; signal_cases is the smoothed series used for forecasting.",
            "0 extracted cases means no explicit count was found in the article, not confirmed zero infections.",
            "Forecast starts from the current date; old signals decay through days without new observations.",
        ],
    }


def get_disease_forecast_summary(
    location: str | None = None,
    history_days: int = 180,
    limit: int = 12,
    top_n: int = 3,
) -> dict:
    days = 7
    diseases = fetch_active_diseases(history_days=history_days, limit=limit)
    items = []

    for disease in diseases:
        name = disease["disease_name"]
        forecast_result = get_forecast(
            disease_name=name,
            location=location,
            forecast_days=days,
            history_days=history_days,
        )
        forecast_days = forecast_result.get("forecast", [])
        total_predicted = int(
            sum(day.get("predicted_cases", 0) for day in forecast_days)
        )
        peak_predicted = int(
            max([day.get("predicted_cases", 0) for day in forecast_days] or [0])
        )
        alert = forecast_result.get("alert", {})

        if total_predicted <= 0 and peak_predicted <= 0:
            continue

        items.append(
            {
                "disease_name": name,
                "location": location,
                "forecast_days": days,
                "predicted_total_7d": total_predicted,
                "predicted_peak": peak_predicted,
                "daily_forecast": forecast_days,
                "risk_level": alert.get("risk_level", "LOW"),
                "risk_score": alert.get("risk_score", 0),
                "risk_message": alert.get("message", ""),
                "recent_avg": alert.get("recent_avg", 0),
                "forecast_avg": alert.get("forecast_avg", 0),
                "history_total_cases": disease.get("total_cases", 0),
                "event_count": disease.get("event_count", 0),
                "last_event_date": disease.get("last_event_date"),
                "regions": fetch_disease_regions(
                    name, history_days=history_days, limit=5
                ),
                "method": forecast_result.get("method"),
                "observed_days": forecast_result.get("observed_days", 0),
                "confidence": (
                    "LOW"
                    if forecast_result.get("observed_days", 0) < 3
                    else "MEDIUM"
                    if forecast_result.get("observed_days", 0) < 7
                    else "HIGH"
                ),
                "mae": forecast_result.get("mae"),
                "wape": forecast_result.get("wape"),
            }
        )

    severity_order = {"HIGH": 3, "MEDIUM": 2, "LOW": 1}
    items.sort(
        key=lambda item: (
            severity_order.get(item["risk_level"], 0),
            item["predicted_total_7d"],
            item["recent_avg"],
        ),
        reverse=True,
    )
    items = items[: max(1, int(top_n))]

    highest = items[0]["risk_level"] if items else "LOW"
    total_predicted = sum(item["predicted_total_7d"] for item in items)
    return {
        "forecast_days": days,
        "location": location,
        "total_predicted_7d": int(total_predicted),
        "highest_risk_level": highest,
        "diseases": items,
        "message": "Dự báo 7 ngày tới theo từng bệnh dựa trên tín hiệu ca bệnh trích xuất từ báo chí.",
    }
