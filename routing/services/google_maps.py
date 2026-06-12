import requests

from django.conf import settings


GEOCODING_URL = "https://maps.googleapis.com/maps/api/geocode/json"


def geocode_address(address: str):

    response = requests.get(
        GEOCODING_URL,
        params={
            "address": address,
            "key": settings.GOOGLE_MAPS_API_KEY,
        },
        timeout=15,
    )

    response.raise_for_status()

    data = response.json()

    if data["status"] != "OK":
        return None

    location = data["results"][0]["geometry"]["location"]

    return {
        "lat": location["lat"],
        "lng": location["lng"],
    }