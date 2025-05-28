import json
from django.conf import settings
from django.core.management.base import BaseCommand
from django.db import transaction
from recipes.models import Ingredient


class Command(BaseCommand):
    help = 'Импорт ингредиентов из JSON файла'

    def handle(self, *args, **options):
        try:
            self.stdout.write(self.style.SUCCESS('Начался импорт ингредиентов.'))
            path = settings.BASE_DIR / "data" / "ingredients.json"
            
            with open(path, 'r', encoding='utf-8') as json_file:
                json_data = json.load(json_file)
                
                with transaction.atomic():

                    existing_ingredients = set(
                        Ingredient.objects.values_list('name', 'measurement_unit')
                    )
                    
                    new_ingredients = [
                        Ingredient(name=item['name'], measurement_unit=item['measurement_unit'])
                        for item in json_data
                        if (item['name'], item['measurement_unit']) not in existing_ingredients
                    ]
                    
                    created_count = len(new_ingredients)
                    Ingredient.objects.bulk_create(new_ingredients)
                    

                    total_in_file = len(json_data)
                    skipped = total_in_file - created_count
                    
                    self.stdout.write(self.style.SUCCESS(
                        f'Успешно загружено: {created_count} ингредиентов\n'
                        f'Пропущено дубликатов: {skipped}\n'
                        f'Всего в файле: {total_in_file}'
                    ))
                    
        except FileNotFoundError:
            self.stdout.write(self.style.ERROR('Файл ingredients.json не найден в директории data/'))
        except json.JSONDecodeError:
            self.stdout.write(self.style.ERROR('Ошибка парсинга JSON файла'))
        except KeyError as e:
            self.stdout.write(self.style.ERROR(f'В JSON файле отсутствует обязательное поле: {e}'))
        except Exception as e:
            self.stdout.write(self.style.ERROR(f'Неожиданная ошибка: {e}'))