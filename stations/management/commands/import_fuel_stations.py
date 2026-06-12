from decimal import Decimal
from django.core.management.base import BaseCommand
from stations.models import FuelStation
import pandas as pd


class Command(BaseCommand):
    help = "Import fuel stations from CSV"

    def add_arguments(self, parser):
        parser.add_argument(
            "csv_file",
            type=str,
            help="Path to CSV file"
        )

    def handle(self, *args, **options):

        csv_file = options["csv_file"]

        self.stdout.write(
            self.style.WARNING(
                f"Reading {csv_file}"
            )
        )

        df = pd.read_csv(csv_file)

        stations_to_create = []

        for _, row in df.iterrows():

            station = FuelStation(
                opis_truckstop_id=str(
                    row["OPIS Truckstop ID"]
                ),
                truckstop_name=row["Truckstop Name"],
                address=row["Address"],
                city=row["City"],
                state=row["State"],
                rack_id=str(row["Rack ID"]),
                retail_price=Decimal(
                    str(row["Retail Price"])
                )
            )

            stations_to_create.append(station)

        FuelStation.objects.bulk_create(
            stations_to_create,
            batch_size=1000
        )

        self.stdout.write(
            self.style.SUCCESS(
                f"Imported {len(stations_to_create)} stations"
            )
        )