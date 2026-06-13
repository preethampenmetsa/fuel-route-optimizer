import math

from scipy.spatial import KDTree


EARTH_RADIUS_MILES = 3958.8
MAX_RANGE_MILES = 500
MPG = 10
TANK_CAPACITY_GALLONS = 50
MAX_DISTANCE_FROM_ROUTE = 10


def haversine(lat1, lon1, lat2, lon2):
    """
    Calculate great-circle distance between two coordinates.

    Returns:
        Distance in miles
    """

    lat1 = math.radians(lat1)
    lon1 = math.radians(lon1)
    lat2 = math.radians(lat2)
    lon2 = math.radians(lon2)

    dlat = lat2 - lat1
    dlon = lon2 - lon1

    a = (
        math.sin(dlat / 2) ** 2
        + math.cos(lat1)
        * math.cos(lat2)
        * math.sin(dlon / 2) ** 2
    )

    c = 2 * math.atan2(
        math.sqrt(a),
        math.sqrt(1 - a)
    )

    return EARTH_RADIUS_MILES * c


def preprocess_route(route_coords):
    """
    Convert route coordinates into route points with
    cumulative mile markers.

    Input:
        [
            (lat, lng),
            ...
        ]

    Output:
        [
            {
                "lat": ...,
                "lng": ...,
                "mile_marker": ...
            }
        ]
    """

    if not route_coords:
        return []

    route_points = []

    cumulative_miles = 0.0

    first_lat, first_lng = route_coords[0]

    route_points.append(
        {
            "lat": first_lat,
            "lng": first_lng,
            "mile_marker": 0.0,
        }
    )

    for i in range(1, len(route_coords)):
        prev_lat, prev_lng = route_coords[i - 1]
        curr_lat, curr_lng = route_coords[i]

        segment_distance = haversine(
            prev_lat,
            prev_lng,
            curr_lat,
            curr_lng,
        )

        cumulative_miles += segment_distance

        route_points.append(
            {
                "lat": curr_lat,
                "lng": curr_lng,
                "mile_marker": cumulative_miles,
            }
        )

    return route_points


def build_station_kdtree(stations):
    """
    Build KDTree from station coordinates.

    Returns:
        (
            kdtree,
            stations
        )
    """

    if not stations:
        return None, []

    coordinates = [
        (
            station["latitude"],
            station["longitude"]
        )
        for station in stations
        if station["latitude"] is not None
        and station["longitude"] is not None
    ]

    valid_stations = [
        station
        for station in stations
        if station["latitude"] is not None
        and station["longitude"] is not None
    ]

    if not coordinates:
        return None, []

    tree = KDTree(coordinates)

    return tree, valid_stations


def assign_station_mile_markers(
    route_points,
    stations,
):
    """
    Snap stations to nearest route point and assign
    route mile marker.

    Adds:
        station["route_mile"]
        station["distance_to_route"]
    """

    if not route_points:
        return []

    route_coordinates = [
        (
            point["lat"],
            point["lng"]
        )
        for point in route_points
    ]

    route_tree = KDTree(route_coordinates)

    enriched_stations = []

    for station in stations:
        lat = station.get("latitude")
        lng = station.get("longitude")

        if lat is None or lng is None:
            continue

        distance, idx = route_tree.query(
            (lat, lng)
        )

        snapped_point = route_points[idx]

        station_copy = station.copy()

        station_copy["route_mile"] = snapped_point[
            "mile_marker"
        ]

        station_copy["distance_to_route"] = haversine(
            lat,
            lng,
            snapped_point["lat"],
            snapped_point["lng"],
        )

        enriched_stations.append(
            station_copy
        )

    return enriched_stations

def get_stations_in_window(
    stations,
    current_mile,
    max_range=MAX_RANGE_MILES,
):
    """
    Return stations reachable from current position.

    Uses exact 500-mile range per requirements.
    """

    window_end = current_mile + max_range

    reachable = [
        station
        for station in stations
        if (
            current_mile < station["route_mile"] <= window_end
        )
    ]

    return sorted(
        reachable,
        key=lambda s: s["route_mile"]
    )

def find_optimal_fuel_stops(
    route_distance,
    stations,
):
    """
    Main optimization algorithm.
exi
        {
            "stops": [],
            "total_cost": float,
            "total_gallons_purchased": float,
            "total_gallons_needed": float
        }
    """

    stations = [
        station
        for station in stations
        if station["distance_to_route"]
        <= MAX_DISTANCE_FROM_ROUTE
    ]

    stations.sort(
        key=lambda s: s["route_mile"]
    )

    current_mile = 0.0

    fuel_in_tank = TANK_CAPACITY_GALLONS

    total_cost = 0.0
    total_gallons_purchased = 0.0

    stops = []

    while True:

        remaining_range = fuel_in_tank * MPG

        # destination reachable
        if current_mile + remaining_range >= route_distance:
            break

        reachable = get_stations_in_window(
            stations,
            current_mile,
            remaining_range,
        )

        if not reachable:
            raise ValueError(
                "No reachable fuel station found"
            )

        # WHERE TO STOP
        stop_station = min(
            reachable,
            key=lambda s: s["retail_price"]
        )

        distance_to_station = (
            stop_station["route_mile"]
            - current_mile
        )

        gallons_used = (
            distance_to_station / MPG
        )

        fuel_in_tank -= gallons_used

        current_mile = stop_station[
            "route_mile"
        ]

        # HOW MUCH TO BUY

        future_stations = [
            s
            for s in stations
            if (
                current_mile
                < s["route_mile"]
                <= current_mile + MAX_RANGE_MILES
            )
        ]

        cheaper_future_station = None

        for station in future_stations:

            if (
                station["retail_price"]
                < stop_station["retail_price"]
            ):
                cheaper_future_station = station
                break

        if cheaper_future_station:

            miles_needed = (
                cheaper_future_station["route_mile"]
                - current_mile
            )

            gallons_needed = (
                miles_needed / MPG
            )

            gallons_to_buy = max(
                0,
                gallons_needed - fuel_in_tank
            )

        else:

            gallons_to_buy = (
                TANK_CAPACITY_GALLONS
                - fuel_in_tank
            )

        price = float(stop_station["retail_price"])

        cost = gallons_to_buy * price

        fuel_in_tank += gallons_to_buy

        total_cost += cost

        total_gallons_purchased += (
            gallons_to_buy
        )

        stops.append(
        {
            "truckstop_name":
                stop_station["truckstop_name"],

            "address":
                stop_station.get("address"),

            "city":
                stop_station.get("city"),

            "state":
                stop_station.get("state"),

            "latitude":
                stop_station.get("latitude"),

            "longitude":
                stop_station.get("longitude"),

            "route_mile":
                round(
                    stop_station["route_mile"],
                    2
                ),

            "price":
                float(
                    stop_station["retail_price"]
                ),

            "gallons_purchased":
                round(
                    gallons_to_buy,
                    2
                ),

            "cost":
                round(
                    cost,
                    2
                ),
        }
    )

    total_gallons_needed = (
        route_distance / MPG
    )

    return {
        "stops": stops,
        "total_cost":
            round(total_cost, 2),
        "total_gallons_purchased":
            round(
                total_gallons_purchased,
                2
            ),
        "total_gallons_needed":
            round(
                total_gallons_needed,
                2
            ),
    }