from django.core.management.base import BaseCommand

from stations.models import FuelStation
from routing.services.google_maps import geocode_address


class Command(BaseCommand):
    help = "Geocode fuel stations using Google Maps"

    def handle(self, *args, **kwargs):

        stations = FuelStation.objects.filter(
            latitude__isnull=True,
            longitude__isnull=True
        )

        total = stations.count()

        self.stdout.write(
            self.style.SUCCESS(
                f"Found {total} stations to geocode"
            )
        )

        failed_count = 0

        for index, station in enumerate(stations, start=1):

            address = (
                f"{station.address}, "
                f"{station.city}, "
                f"{station.state}"
            )

            coordinates = geocode_address(address)

            if coordinates:

                station.latitude = coordinates["lat"]
                station.longitude = coordinates["lng"]

                station.save(
                    update_fields=[
                        "latitude",
                        "longitude",
                    ]
                )

            else:

                failed_count += 1

                self.stdout.write(
                    self.style.ERROR(
                        f"FAILED: {station.truckstop_name}"
                    )
                )

            if index % 100 == 0:

                self.stdout.write(
                    self.style.SUCCESS(
                        f"Processed {index}/{total}"
                    )
                )

        self.stdout.write("\n" + "=" * 50)

        self.stdout.write(
            self.style.SUCCESS(
                "Geocoding completed"
            )
        )

        self.stdout.write(
            self.style.ERROR(
                f"Failed records: {failed_count}"
            )
        )