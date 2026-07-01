import logging

import pandas as pd

from config import API_PARAMS

logger = logging.getLogger(__name__)

NUMERIC_COLUMNS = [
    "temperature_2m",
    "relative_humidity_2m",
    "precipitation",
    "wind_speed_10m",
    "weather_code",
]

VALID_RANGES = {
    "temperature_2m": (-20, 60),
    "relative_humidity_2m": (0, 100),
    "precipitation": (0, None),     
    "wind_speed_10m": (0, None),    
}


def flatten_city(city_name: str, data: dict) -> list[dict]:
    hourly = data["hourly"]

    rows = []
    for i, timestamp in enumerate(hourly["time"]):
        row = {
            "city": city_name,
            "time": timestamp,
            "latitude": data.get("latitude"),
            "longitude": data.get("longitude"),
            "timezone": data.get("timezone"),
            "elevation": data.get("elevation"),
        }

        for var in API_PARAMS["hourly"]:
            row[var] = hourly[var][i]

        rows.append(row)

    return rows


def flatten_all(raw_data: dict[str, dict]) -> list[dict]:
    rows = []

    for city_name, data in raw_data.items():
        rows.extend(flatten_city(city_name, data))

    return rows


def clean_data(rows: list[dict]) -> pd.DataFrame:
    """
    بتاخد الـ rows الناتجة من flatten_all وترجع DataFrame نضيف.

    خطوات التنظيف:
    1. تحويل عمود الوقت لـ datetime حقيقي
    2. حذف أي صفوف مكررة تمامًا
    3. حذف التكرار على مستوى (city, time) والاحتفاظ بأول ظهور
    4. تحويل الأعمدة الرقمية لأرقام فعلية (أي قيمة غير رقمية تتحول لـ NaN)
    5. استبدال القيم الخارجة عن النطاق المنطقي (VALID_RANGES) بـ NaN
    6. ملء القيم الناقصة (NaN) بالـ interpolation الزمني لكل مدينة على حدة
    7. ترتيب النتيجة حسب المدينة ثم الوقت
    """
    if not rows:
        logger.warning("No rows to clean — returning empty DataFrame")
        return pd.DataFrame()

    df = pd.DataFrame(rows)

    # 1. تحويل الوقت
    df["time"] = pd.to_datetime(df["time"], errors="coerce")

    before = len(df)

    df = df.dropna(subset=["time"])

    df = df.drop_duplicates()

    df = df.drop_duplicates(subset=["city", "time"], keep="first")

    dropped = before - len(df)
    if dropped:
        logger.info(f"Dropped {dropped} duplicate/invalid-time rows")

    for col in NUMERIC_COLUMNS:
        if col in df.columns:
            df[col] = pd.to_numeric(df[col], errors="coerce")

    
    for col, (low, high) in VALID_RANGES.items():
        if col not in df.columns:
            continue
        mask = pd.Series(False, index=df.index)
        if low is not None:
            mask |= df[col] < low
        if high is not None:
            mask |= df[col] > high
        n_invalid = mask.sum()
        if n_invalid:
            logger.warning(f"[{col}] {n_invalid} out-of-range values set to NaN")
            df.loc[mask, col] = pd.NA

    df = df.sort_values(["city", "time"])
    numeric_cols_present = [c for c in NUMERIC_COLUMNS if c in df.columns]

    df[numeric_cols_present] = df.groupby("city")[numeric_cols_present].transform(
        lambda s: s.interpolate(method="linear", limit_direction="both")
    )

    remaining_na = df[numeric_cols_present].isna().sum()
    remaining_na = remaining_na[remaining_na > 0]
    if not remaining_na.empty:
        logger.warning(f"Remaining NaNs after interpolation:\n{remaining_na}")


    return df