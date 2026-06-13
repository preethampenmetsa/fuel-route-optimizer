from rest_framework import serializers


class FuelStopSerializer(serializers.Serializer):
    truckstop_name = serializers.CharField()
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

    stops = FuelStopSerializer(many=True)
    