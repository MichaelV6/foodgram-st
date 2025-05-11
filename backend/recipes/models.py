import uuid
from os.path import splitext

from django.core.validators import MinValueValidator, MaxValueValidator
from django.db import models
from django.contrib.auth import get_user_model

from ingredients.models import Ingredient
from foodgram.constants import (
    MAX_RECIPE_NAME,
    MIN_COOKING_TIME,
    MAX_COOKING_TIME,
    MIN_AMOUNT,
    MAX_AMOUNT,
)

User = get_user_model()


class Recipe(models.Model):
    def upload_to(self, filename):
        recipe_title = self.name
        file_name, file_extension = splitext(filename)
        filename = f"{uuid.uuid4().hex}{file_extension}"
        return "recipes/{0}/{1}".format(recipe_title, filename)

    author = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        related_name="recipes",
        verbose_name="автор",
    )
    name = models.CharField(
        max_length=MAX_RECIPE_NAME,
        verbose_name="имя",
    )
    text = models.TextField(
        verbose_name="описание",
    )
    cooking_time = models.PositiveSmallIntegerField(
        verbose_name="время готовки",
        validators=[
            MinValueValidator(
                MIN_COOKING_TIME,
                message=f"Время приготовления не может быть меньше"
                f" {MIN_COOKING_TIME} минуты",
            ),
            MaxValueValidator(
                MAX_COOKING_TIME,
                message=f"Время приготовления не может превышать"
                f" {MAX_COOKING_TIME} минут",
            ),
        ],
    )
    ingredients = models.ManyToManyField(
        Ingredient,
        through="RecipeIngredient",
        related_name="recipes_used_in",
        verbose_name="ингредиенты",
    )

    class Meta:
        verbose_name = "Рецепт"
        verbose_name_plural = "Рецепты"
        ordering = (
            "name",
        )
    image = models.ImageField(
        upload_to=upload_to,
        verbose_name="картинка",
    )

    def __str__(self):
        return f"Рецепт {self.name}"


class RecipeIngredient(models.Model):
    recipe = models.ForeignKey(
        Recipe,
        on_delete=models.CASCADE,
        verbose_name="Рецепт",
        related_name="recipe_ingredients",
    )
    ingredient = models.ForeignKey(
        Ingredient,
        on_delete=models.CASCADE,
        related_name="recipe_usages",
        verbose_name="Ингредиент",
    )
    amount = models.PositiveSmallIntegerField(
        verbose_name="Кол-во",
        validators=[
            MinValueValidator(
                MIN_AMOUNT,
                message=f"Количество не может быть меньше {MIN_AMOUNT}",
            ),
            MaxValueValidator(
                MAX_AMOUNT,
                message=f"Количество не может превышать {MAX_AMOUNT}",
            ),
        ],
    )

    class Meta:
        verbose_name = "Ингридиент рецепта"
        verbose_name_plural = "Ингридиенты рецептов"
        ordering = (
            "recipe",
            "ingredient",
        )

    def __str__(self):
        return (
            f"{self.ingredient} - "
            f"{self.amount} {self.ingredient.measurement_unit}"
        )


class Favorite(models.Model):
    user = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        related_name="favorites",
        verbose_name="favorite_recipes",
    )
    recipe = models.ForeignKey(
        Recipe,
        on_delete=models.CASCADE,
        related_name="favorited_by_users",
        verbose_name="Рецепт",
    )

    class Meta:
        verbose_name = "Избранное"
        verbose_name_plural = "Избранные"
        ordering = (
            "user",
            "recipe"
        )

    def __str__(self):
        return f"Избраное {self.user} - {self.recipe}"


class ShoppingCart(models.Model):
    user = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        related_name="recipes_shopping_cart",
        verbose_name="Пользователь",
    )
    recipe = models.ForeignKey(
        "Recipe",
        on_delete=models.CASCADE,
        related_name="recipes_in_shopping_cart",
        verbose_name="Рецепт",
    )

    class Meta:
        constraints = [
            models.UniqueConstraint(
                fields=("user", "recipe"),
                name="unique_shopping_cart"
            )
        ]
        verbose_name = "Корзина"
        verbose_name_plural = "Корзины"
        ordering = (
            "user",
            "recipe"
        )

    def __str__(self):
        return f"Корзина {self.user} - {self.recipe}"
