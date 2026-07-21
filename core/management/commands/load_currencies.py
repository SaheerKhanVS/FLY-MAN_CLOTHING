from django.core.management.base import BaseCommand
from core.models import Currency
import pycountry
class Command(BaseCommand):
    help = "Load all ISO currencies into the database"
    def handle(self, *args, **kwargs):
        created = 0
        for currency in pycountry.currencies:
            Currency.objects.get_or_create(code=currency.alpha_3,defaults={ "name": currency.name,}, )
            created += 1
        self.stdout.write(self.style.SUCCESS( f"Successfully loaded {created} currencies."))