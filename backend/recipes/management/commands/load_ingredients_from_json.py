import json
from django.conf import settings
from django.core.management.base import BaseCommand
from recipes.models import Ingredient


class Command(BaseCommand):
    help = 'Импорт ингредиентов из JSON файла'
    def handle(self, *args, **options):
        try:
            self.stdout.write(self.style.SUCCESS('Начался импорт ингредиентов.'))
            path = settings.BASE_DIR / "data" / "ingredients.json"
            with open(path, 'r', encoding='utf-8') as json_file:
                existing_ingredients = set(Ingredient.objects.values_list('name', 'measurement_unit'))
                new_ingredients = [
                    Ingredient(**item) for item in json.load(json_file) if (item['name'], item['measurement_unit']) not in existing_ingredients
                ]
                Ingredient.objects.bulk_create(new_ingredients, ignore_conflicts=True)
                self.stdout.write(self.style.SUCCESS(
                    f'Успешно загружено: {len(new_ingredients)} ингредиентов'
                ))     
        except Exception as e:
            self.stdout.write(self.style.ERROR(f'Ошибка при импорте из ingredients.json: {e}'))