from rest_framework import serializers


class RouteOptimizationRequestSerializer(serializers.Serializer):

    start = serializers.CharField(
        max_length=255
    )

    end = serializers.CharField(
        max_length=255
    )


class FuelStopSerializer(serializers.Serializer):

    truckstop_name = serializers.CharField()

    address = serializers.CharField(
        allow_null=True
    )

    city = serializers.CharField(
        allow_null=True
    )

    state = serializers.CharField(
        allow_null=True
    )

    latitude = serializers.FloatField()

    longitude = serializers.FloatField()

    route_mile = serializers.FloatField()

    price = serializers.FloatField()

    gallons_purchased = serializers.FloatField()

    cost = serializers.FloatField()


class OptimizationResponseSerializer(serializers.Serializer):

    start_location = serializers.CharField()

    end_location = serializers.CharField()

    total_distance_miles = serializers.FloatField()

    total_cost = serializers.FloatField()

    total_gallons_purchased = serializers.FloatField()

    total_gallons_needed = serializers.FloatField()

    fuel_stop_count = serializers.IntegerField()

    route_polyline = serializers.CharField()

    stops = FuelStopSerializer(
        many=True
    )

    response_time_ms = serializers.FloatField()

    is_cached = serializers.BooleanField()