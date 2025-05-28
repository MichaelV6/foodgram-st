from django.core.management.base import BaseCommand
from django.contrib.auth import get_user_model
from django.db.utils import IntegrityError
from recipes.models import Recipe, Ingredient, RecipeIngredient
import random

User = get_user_model()

class Command(BaseCommand):
    help = "Создаёт тестовых пользователей и рецепты (если их ещё нет)"

    def handle(self, *args, **options):
        # Создаем пользователей
        users_data = [
            {
                "username": "user1",
                "email": "user1@example.com",
                "first_name": "Иван",
                "last_name": "Иванов",
                "password": "password123",
            },
            {
                "username": "user2",
                "email": "user2@example.com",
                "first_name": "Пётр",
                "last_name": "Петров",
                "password": "password123",
            },
            {
                "username": "user3",
                "email": "user3@example.com",
                "first_name": "Сергей",
                "last_name": "Сергеев",
                "password": "password123",
            },
        ]

        users_created = 0
        users_existed = 0

        for user_data in users_data:
            try:
                user, created = User.objects.get_or_create(
                    username=user_data["username"],
                    defaults={
                        "email": user_data["email"],
                        "first_name": user_data["first_name"],
                        "last_name": user_data["last_name"]
                    }
                )
                if created:
                    user.set_password(user_data["password"])
                    user.save()
                    users_created += 1
                    self.stdout.write(f"Создан пользователь: {user.username}")
                else:
                    users_existed += 1
            except IntegrityError as e:
                self.stdout.write(self.style.ERROR(
                    f"Ошибка при создании пользователя {user_data['username']}: {e}"
                ))

        self.stdout.write(self.style.SUCCESS(
            f"Пользователи: создано {users_created}, уже существовало {users_existed}"
        ))

        # Проверяем наличие ингредиентов перед созданием рецептов
        ingredients = Ingredient.objects.all()
        if not ingredients.exists():
            self.stdout.write(self.style.WARNING(
                "Ингредиенты не найдены. Сначала загрузите ингредиенты!"
            ))
            return

        # Создаем рецепты для пользователей
        recipes_created = 0
        recipes_skipped = 0

        for user in User.objects.all():
            # Пропускаем пользователей, у которых уже есть рецепты
            if user.recipes.exists():
                recipes_skipped += 1
                continue

            for i in range(1, 5):  # 4 рецепта на пользователя
                try:
                    recipe, created = Recipe.objects.get_or_create(
                        author=user,
                        name=f"Рецепт {i} от {user.username}",
                        defaults={
                            'text': f"Подробное описание рецепта {i}...",
                            'cooking_time': random.randint(10, 120)
                        }
                    )

                    if created:
                        # Добавляем 3 случайных ингредиента к рецепту
                        selected_ingredients = random.sample(list(ingredients), min(3, len(ingredients)))
                        for ingredient in selected_ingredients:
                            RecipeIngredient.objects.create(
                                recipe=recipe,
                                ingredient=ingredient,
                                amount=random.randint(1, 500)
                            )
                        recipes_created += 1
                        self.stdout.write(f"Создан рецепт: {recipe.name}")

                except IntegrityError as e:
                    self.stdout.write(self.style.ERROR(
                        f"Ошибка при создании рецепта для {user.username}: {e}"
                    ))

        self.stdout.write(self.style.SUCCESS(
            f"Рецепты: создано {recipes_created}, пропущено пользователей с рецептами {recipes_skipped}"
        ))
        self.stdout.write(self.style.SUCCESS(
            "Тестовые данные успешно созданы!"
        ))