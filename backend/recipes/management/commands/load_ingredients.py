import csv

from django.conf import settings
from django.core.management.base import BaseCommand

from recipes.models import Ingredient


class Command(BaseCommand):
    def handle(self, *args, **options):
        self.stdout.write(self.style.SUCCESS('Начался импорт ингредиентов.'))
        path = settings.BASE_DIR / "data" / "ingredients.csv"
        with open(
                path,
                newline='',
                encoding='utf-8'
        ) as csv_file:
            reader = csv.reader(csv_file, delimiter=",")
            total_ingredients = []
            for name, measurement_unit in reader:
                if name:
                    ingredient = Ingredient(
                        name=name,
                        measurement_unit=measurement_unit,
                    )
                    total_ingredients.append(ingredient)
            Ingredient.objects.bulk_create(total_ingredients)
        self.stdout.write(self.style.SUCCESS('Ингридиенты загружены'))
