from django.shortcuts import render

# Create your views here.
import time

from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status

from routing.services.route_service import get_route

from optimization.algorithm import (
    preprocess_route,
    assign_station_mile_markers,
    find_optimal_fuel_stops,
)

from stations.models import FuelStation

from .serializers import (
    OptimizationResponseSerializer
)

class RouteOptimizationView(APIView):

    def post(self, request):

        start = request.data.get("start")
        end = request.data.get("end")

        if not start or not end:
            return Response(
                {
                    "error": (
                        "start and end "
                        "are required"
                    )
                },
                status=status.HTTP_400_BAD_REQUEST,
            )
        route_data = get_route(
            start,
            end,
        )
        route_points = preprocess_route(
            route_data["route_coords"]
        )

        bounds = route_data["route_bounds"]

        stations = list(
            FuelStation.objects.filter(
                latitude__gte=bounds["min_lat"] - 1,
                latitude__lte=bounds["max_lat"] + 1,
                longitude__gte=bounds["min_lng"] - 1,
                longitude__lte=bounds["max_lng"] + 1,
                latitude__isnull=False,
                longitude__isnull=False,
                retail_price__isnull=False,
            ).values(
                "truckstop_name",
                "address",
                "city",
                "state",
                "latitude",
                "longitude",
                "retail_price",
            )
        )
        stations_with_markers = (
            assign_station_mile_markers(
                route_points,
                stations,
            )
        )
        optimization_result = (
            find_optimal_fuel_stops(
                route_distance=
                route_data[
                    "total_distance_miles"
                ],
                stations=
                stations_with_markers,
            )
        )

        response_data = {
            "start_location":
                route_data["start_address"],

            "end_location":
                route_data["end_address"],

            "total_distance_miles":
                route_data[
                    "total_distance_miles"
                ],

            "total_cost":
                optimization_result[
                    "total_cost"
                ],

            "total_gallons_purchased":
                optimization_result[
                    "total_gallons_purchased"
                ],

            "total_gallons_needed":
                optimization_result[
                    "total_gallons_needed"
                ],

            "stops":
                optimization_result[
                    "stops"
                ],
        }

        serializer = (
            OptimizationResponseSerializer(
                response_data
            )
        )

        return Response(
            serializer.data,
            status=status.HTTP_200_OK,
        )