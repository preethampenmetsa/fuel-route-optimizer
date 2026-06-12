from django.db import models


class FuelStation(models.Model):
    opis_truckstop_id = models.CharField(max_length=50)

    truckstop_name = models.CharField(max_length=255)

    address = models.CharField(max_length=255)

    city = models.CharField(max_length=100)

    state = models.CharField(max_length=50)

    rack_id = models.CharField(max_length=50)

    retail_price = models.DecimalField(
        max_digits=8,
        decimal_places=7
    )

    latitude = models.FloatField(
        null=True,
        blank=True
    )

    longitude = models.FloatField(
        null=True,
        blank=True
    )

    def __str__(self):
        return self.truckstop_name
