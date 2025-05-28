import csv

from django.conf import settings
from django.core.management.base import BaseCommand
from django.db import transaction

from recipes.models import Ingredient


class Command(BaseCommand):
    help = 'Импорт ингредиентов из CSV файла'

    def handle(self, *args, **options):
        try:
            self.stdout.write(self.style.SUCCESS('Начался импорт ингредиентов.'))
            path = settings.BASE_DIR / "data" / "ingredients.csv"
            
            with open(path, newline='', encoding='utf-8') as csv_file:
                reader = csv.reader(csv_file, delimiter=",")
                

                with transaction.atomic():

                    existing_ingredients = set(Ingredient.objects.values_list('name', 'measurement_unit'))
                    new_ingredients = []
                    
                    for name, measurement_unit in reader:
                        if (name, measurement_unit) not in existing_ingredients:
                            new_ingredients.append(Ingredient(
                                name=name,
                                measurement_unit=measurement_unit,
                            ))
                    
                    Ingredient.objects.bulk_create(new_ingredients)
                    
            self.stdout.write(self.style.SUCCESS(
                f'Ингредиенты загружены, всего: {len(new_ingredients)} шт (пропущено дубликатов: {len(list(reader)) - len(new_ingredients)})'
            ))
        except Exception as e:
            self.stdout.write(self.style.ERROR(f"Ошибка: {e}"))