import requests
import polyline

from django.conf import settings


DIRECTIONS_URL = "https://maps.googleapis.com/maps/api/directions/json"


def _extract_route_points(route):
    """
    Decode all step polylines and combine them into a single route.
    This gives significantly higher route resolution than using
    overview_polyline alone.
    """
    coordinates = []

    for leg in route.get("legs", []):
        for step in leg.get("steps", []):
            encoded = step.get("polyline", {}).get("points")

            if not encoded:
                continue

            decoded_points = polyline.decode(encoded)

            # Avoid duplicate points between consecutive steps
            if coordinates and decoded_points:
                decoded_points = decoded_points[1:]

            coordinates.extend(decoded_points)

    return coordinates


def get_route(start: str, end: str) -> dict:
    """
    Fetch route from Google Directions API.

    Returns:
    {
        "route_coords": [(lat, lng), ...],
        "total_distance_miles": float,
        "start_address": str,
        "end_address": str,
        "route_bounds": {
            "min_lat": float,
            "max_lat": float,
            "min_lng": float,
            "max_lng": float
        }
    }

    Raises:
        ValueError
    """

    api_key = settings.GOOGLE_MAPS_API_KEY

    if not api_key:
        raise ValueError("Google Maps API key not configured")

    params = {
        "origin": start,
        "destination": end,
        "mode": "driving",
        "key": api_key,
    }

    try:
        response = requests.get(
            DIRECTIONS_URL,
            params=params,
            timeout=30,
        )
        response.raise_for_status()

    except requests.RequestException as exc:
        raise ValueError(
            f"Unable to contact Google Directions API: {exc}"
        )

    data = response.json()

    status = data.get("status")

    if status != "OK":
        error_message = data.get(
            "error_message",
            "Unknown Google Directions API error"
        )

        raise ValueError(
            f"Google Directions API error: {status}. {error_message}"
        )

    routes = data.get("routes", [])

    if not routes:
        raise ValueError("No driving route found")

    route = routes[0]

    route_coords = _extract_route_points(route)

    if not route_coords:
        raise ValueError("Route polyline could not be decoded")

    total_distance_meters = 0

    for leg in route.get("legs", []):
        total_distance_meters += leg["distance"]["value"]

    total_distance_miles = round(
        total_distance_meters * 0.000621371,
        2
    )

    first_leg = route["legs"][0]
    last_leg = route["legs"][-1]

    start_address = first_leg["start_address"]
    end_address = last_leg["end_address"]

    # USA validation (requirement)
    if ", USA" not in start_address:
        raise ValueError(
            "Start location must be within the USA"
        )

    if ", USA" not in end_address:
        raise ValueError(
            "End location must be within the USA"
        )

    latitudes = [lat for lat, _ in route_coords]
    longitudes = [lng for _, lng in route_coords]

    route_bounds = {
        "min_lat": min(latitudes),
        "max_lat": max(latitudes),
        "min_lng": min(longitudes),
        "max_lng": max(longitudes),
    }

    return {
        "route_coords": route_coords,
        "total_distance_miles": total_distance_miles,
        "start_address": start_address,
        "end_address": end_address,
        "route_bounds": route_bounds,
    }