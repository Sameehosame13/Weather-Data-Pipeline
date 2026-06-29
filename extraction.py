import json
import logging
import requests
from datetime import datetime
from config import API_BASE_URL, API_PARAMS
from cities import CITIES

logger = logging.getLogger(__name__)


def fetch_city(city_name: str, coords: dict) -> dict | None:
    params = {
        "latitude":  coords["latitude"],
        "longitude": coords["longitude"],
        "hourly":    ",".join(API_PARAMS["hourly"]),
        "timezone":  API_PARAMS["timezone"],
        "past_days": API_PARAMS["past_days"],
    }
    try:
        response = requests.get(API_BASE_URL, params=params, timeout=10)
        response.raise_for_status()
        logger.info(f"[{city_name}] Fetched successfully")
        return response.json()

    except requests.exceptions.ConnectionError:
        logger.error(f"[{city_name}] Network error — could not reach API")
    except requests.exceptions.Timeout:
        logger.error(f"[{city_name}] Request timed out")
    except requests.exceptions.HTTPError as e:
        logger.error(f"[{city_name}] API returned error: {e}")

    return None


def fetch_all() -> dict[str, dict]:
    results = {}
    for city_name, coords in CITIES.items():
        data = fetch_city(city_name, coords)
        if data:
            results[city_name] = data
    return results


if __name__ == "__main__":
    raw_data = fetch_all()

    filename = f"raw_sample_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
    with open(filename, "w", encoding="utf-8") as f:
        json.dump(raw_data, f, indent=2, ensure_ascii=False)

    print(f"\nSaved {len(raw_data)} cities → {filename}")