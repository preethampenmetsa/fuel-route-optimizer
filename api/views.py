import time
from django.core.cache import cache
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
from routing.services.route_service import get_route
from stations.models import FuelStation
from optimization.algorithm import (
    preprocess_route,
    assign_station_mile_markers,
    find_optimal_fuel_stops,
)
from .serializers import (
    OptimizationResponseSerializer,
    RouteOptimizationRequestSerializer
)
from drf_spectacular.utils import (
    extend_schema,
    OpenApiExample,
)


class RouteOptimizationView(APIView):

    @extend_schema(
        summary="Optimize Fuel Stops",
        description=(
            "Find the cheapest fuel stops "
            "along a route while respecting "
            "the truck's 500-mile range."
        ),
        request=RouteOptimizationRequestSerializer,
        responses=OptimizationResponseSerializer,
        examples=[
            OpenApiExample(
                "Sample Request",
                value={
                    "start":
                        "New York, NY",
                    "end":
                        "Chicago, IL"
                }
            )
        ],
    )
    
    def post(self, request):

        request_start_time = time.time()

        request_serializer = (RouteOptimizationRequestSerializer(data=request.data))
        request_serializer.is_valid(raise_exception=True)
        start = request_serializer.validated_data["start"]
        end = request_serializer.validated_data["end"]

        cache_key = (
            f"route_opt:"
            f"{start.lower().strip()}:"
            f"{end.lower().strip()}"
        )

        cached_response = cache.get(
            cache_key
        )

        if cached_response:
            cached_response = cached_response.copy()
            cached_response["is_cached"] = True

            return Response(
                cached_response,
                status=status.HTTP_200_OK,
            )

        try:
            route_data = get_route(
                start,
                end,
            )

        except ValueError as exc:
            return Response(
                {
                    "error": str(exc)
                },
                status=status.HTTP_400_BAD_REQUEST,
            )

        except Exception:
            return Response(
                {
                    "error":
                    "Failed to retrieve route"
                },
                status=status.HTTP_500_INTERNAL_SERVER_ERROR,
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

        if not stations:
            return Response(
                {
                    "error":
                    "No fuel stations found"
                },
                status=status.HTTP_404_NOT_FOUND,
            )

        try:
            stations_with_markers = (
                assign_station_mile_markers(
                    route_points,
                    stations,
                )
            )

        except Exception:
            return Response(
                {
                    "error":
                    "Failed to process route stations"
                },
                status=status.HTTP_500_INTERNAL_SERVER_ERROR,
            )
        
        try:
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

        except ValueError as exc:
            return Response(
                {
                    "error": str(exc)
                },
                status=status.HTTP_400_BAD_REQUEST,
            )

        except Exception:
            return Response(
                {
                    "error":
                    "Fuel optimization failed"
                },
                status=status.HTTP_500_INTERNAL_SERVER_ERROR,
            )
        
        response_time_ms = round((time.time() - request_start_time) * 1000, 2)

        response_data = {
            "start_location":
                route_data["start_address"],

            "end_location":
                route_data["end_address"],

            "total_distance_miles":
                route_data["total_distance_miles"],

            "total_cost":
                optimization_result["total_cost"],

            "total_gallons_purchased":
                optimization_result[
                    "total_gallons_purchased"
                ],

            "total_gallons_needed":
                optimization_result[
                    "total_gallons_needed"
                ],

            "fuel_stop_count":
                len(
                    optimization_result["stops"]
                ),

            "route_polyline":
                    route_data["route_polyline"],

            "stops":
                optimization_result["stops"],

            "response_time_ms":
                response_time_ms,

            "is_cached":
                False,
        }

        serializer = (
            OptimizationResponseSerializer(
                response_data
            )
        )

        cache.set(
            cache_key,
            serializer.data,
            timeout=3600,
        )

        return Response(
            serializer.data,
            status=status.HTTP_200_OK,
        )