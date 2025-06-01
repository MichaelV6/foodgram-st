import uuid
from os.path import splitext

from django.conf import settings
from django.contrib.auth.models import AbstractUser
from django.core.validators import (
    MinValueValidator, MaxValueValidator, RegexValidator,
)
from django.db import models
from foodgram.constants import (
    MAX_RECIPE_NAME, MIN_COOKING_TIME,
    MIN_AMOUNT, MAX_USER_NAME,
    MAX_INGREDIENT_NAME, MAX_MEASUREMENT_NAME,
)
from foodgram.utils import image_compress


class User(AbstractUser):

    def upload_to(self, filename: str) -> str:
        file_name, file_ext = splitext(filename)
        return f"users/{self.username}/{uuid.uuid4().hex}{file_ext}"

    username = models.CharField(
        "ник",
        max_length=MAX_USER_NAME,
        unique=True,
        validators=[RegexValidator(r"^[\w.@+-]+$")],
    )
    email = models.EmailField("почта", unique=True, max_length=254,)
    first_name = models.CharField("имя", max_length=MAX_USER_NAME)
    last_name = models.CharField("фамилия", max_length=MAX_USER_NAME)
    avatar = models.ImageField(
        "аватар",
        upload_to=upload_to,
        blank=True,
        null=True
    )

    USERNAME_FIELD = "email"
    REQUIRED_FIELDS = ("username", "first_name", "last_name")

    class Meta:
        verbose_name = "Пользователь"
        verbose_name_plural = "Пользователи"
        ordering = ("email",)

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.__original_avatar = self.avatar if self.pk else None

    def save(self, *args, **kwargs):
        super().save(*args, **kwargs)
        if self.__original_avatar != self.avatar and self.avatar:
            image_compress(self.avatar.path)

    def __str__(self):
        return self.email


class Subscription(models.Model):
    """Подписка одного пользователя на другого."""

    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="subscriptions",
        verbose_name="кто подписался",
    )
    subscribed_to = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="users_subscribers",
        verbose_name="на кого подписались",
    )

    class Meta:
        constraints = [
            models.UniqueConstraint(
                fields=("user", "subscribed_to"),
                name="unique_subscription_users",
            ),
            models.CheckConstraint(
                check=~models.Q(user=models.F("subscribed_to")),
                name="no_self_subscription",
            ),
        ]
        verbose_name = "Подписка"
        verbose_name_plural = "Подписки"
        ordering = ("user", "subscribed_to")

    def __str__(self):
        return f"{self.user} -> {self.subscribed_to}"


class Ingredient(models.Model):
    name = models.CharField("название", max_length=MAX_INGREDIENT_NAME)
    measurement_unit = models.CharField(
        "единицы измерения", max_length=MAX_MEASUREMENT_NAME
    )

    class Meta:
        verbose_name = "Ингредиент"
        verbose_name_plural = "Ингредиенты"
        ordering = ("name",)

    def __str__(self):
        return self.name


class Recipe(models.Model):
    """Рецепт: текст, фото, ингредиенты и т. д."""

    def upload_to(self, filename: str) -> str:
        _, file_ext = splitext(filename)
        return f"recipes/{self.name}/{uuid.uuid4().hex}{file_ext}"

    author = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        verbose_name="автор",
    )
    name = models.CharField("имя", max_length=MAX_RECIPE_NAME)
    text = models.TextField("описание")
    cooking_time = models.PositiveSmallIntegerField(
        "время готовки",
        validators=[
            MinValueValidator(MIN_COOKING_TIME),
        ],
    )
    ingredients = models.ManyToManyField(
        Ingredient,
        through="RecipeIngredient",
        related_name="recipes",
        verbose_name="ингредиенты",
    )
    image = models.ImageField("картинка", upload_to=upload_to)

    class Meta:
        verbose_name = "Рецепт"
        verbose_name_plural = "Рецепты"
        ordering = ("name",)
        default_related_name = "recipes"

    def __str__(self):
        return self.name


class RecipeIngredient(models.Model):
    recipe = models.ForeignKey(
        Recipe,
        on_delete=models.CASCADE,
        verbose_name="рецепт",
    )
    ingredient = models.ForeignKey(
        Ingredient,
        on_delete=models.CASCADE,
        related_name="recipe_usages",
        verbose_name="ингредиент",
    )
    amount = models.PositiveSmallIntegerField(
        "кол-во",
        validators=[
            MinValueValidator(MIN_AMOUNT),
        ],
    )

    class Meta:
        constraints = [
            models.UniqueConstraint(
                fields=("recipe", "ingredient"),
                name="unique_recipe_ingredient",
            )
        ]
        verbose_name = "Продукт рецепта"
        verbose_name_plural = "Продукты рецептов"
        ordering = ("recipe", "ingredient")
        default_related_name = "recipe_ingredients"

    def __str__(self):
        return (
            f"{self.ingredient} – {self.amount} "
            f"{self.ingredient.measurement_unit}"
        )


class Favorite(models.Model):
    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        verbose_name="пользователь",
    )
    recipe = models.ForeignKey(
        Recipe,
        on_delete=models.CASCADE,
        related_name="favorites",
        verbose_name="рецепт",
    )

    class Meta:
        constraints = [
            models.UniqueConstraint(
                fields=("user", "recipe"),
                name="unique_favorite",
            )
        ]
        verbose_name = "Избранное"
        verbose_name_plural = "Избранные"
        ordering = ("user", "recipe")
        default_related_name = "favorites"

    def __str__(self):
        return f"{self.user} -> {self.recipe}"


class ShoppingCart(models.Model):
    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="recipes_shopping_cart", 
        verbose_name="пользователь",
    )
    recipe = models.ForeignKey(
        Recipe,
        on_delete=models.CASCADE,
        related_name="recipes_in_shopping_cart",
        verbose_name="рецепт",
    )

    class Meta:
        constraints = [
            models.UniqueConstraint(
                fields=("user", "recipe"),
                name="unique_shopping_cart",
            )
        ]
        verbose_name = "Корзина"
        verbose_name_plural = "Корзины"
        ordering = ("user", "recipe")

    def __str__(self):
        return f"{self.user} -> {self.recipe}"
