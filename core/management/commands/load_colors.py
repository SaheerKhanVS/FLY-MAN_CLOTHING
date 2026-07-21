import csv
from pathlib import Path
from django.core.management.base import BaseCommand
from core.models import Color


class Command(BaseCommand):
    help = "Load colors from colors.csv"
    def handle(self, *args, **kwargs):
        csv_file = ( Path(__file__).resolve().parent.parent.parent.parent/"core" / "management" / "data" / "colors.csv")
        if not csv_file.exists():
            self.stdout.write(self.style.ERROR(f"CSV file not found: {csv_file}"))
            return
        created = 0
        updated = 0
        with open(csv_file, newline="", encoding="utf-8") as file:
            reader = csv.DictReader(file)
            for row in reader:
                color, is_created = Color.objects.update_or_create(name=row["name"].strip(),defaults={ "hex_code": row["hex_code"].strip(),"category": row.get("category", "").strip(),},)
                if is_created:created += 1
                else: updated += 1
        self.stdout.write(self.style.SUCCESS( f"Done!\nCreated: {created}\nUpdated: {updated}") )