from stations.models import FuelStation

from routing.services.route_service import get_route

from optimization.algorithm import (
    preprocess_route,
    assign_station_mile_markers,
    find_optimal_fuel_stops,
)


def get_candidate_stations(route_bounds):
    """
    Get stations inside route bounding box.
    """

    return list(
        FuelStation.objects.filter(
            latitude__isnull=False,
            longitude__isnull=False,
        )
        .filter(
            latitude__gte=route_bounds["min_lat"] - 1,
            latitude__lte=route_bounds["max_lat"] + 1,
            longitude__gte=route_bounds["min_lng"] - 1,
            longitude__lte=route_bounds["max_lng"] + 1,
        )
        .values(
            "truckstop_name",
            "retail_price",
            "latitude",
            "longitude",
        )
    )


def optimize_route(start, end):
    """
    Complete optimization workflow.
    """

    route = get_route(start, end)

    route_points = preprocess_route(
        route["route_coords"]
    )

    stations = get_candidate_stations(
        route["route_bounds"]
    )

    stations = assign_station_mile_markers(
        route_points,
        stations,
    )

    stations = [
        station
        for station in stations
        if station["distance_to_route"] <= 10
    ]

    optimization_result = find_optimal_fuel_stops(
        route_distance=route["total_distance_miles"],
        stations=stations,
    )

    return {
        "start": route["start_address"],
        "end": route["end_address"],
        "total_distance_miles":
            route["total_distance_miles"],
        **optimization_result,
    }