from config import API_PARAMS


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