from django.db import models

from foodgram.constants import MAX_INGREDIENT_NAME, MAX_MEASUREMENT_NAME


class Ingredient(models.Model):
    name = models.CharField(
        max_length=MAX_INGREDIENT_NAME,
        verbose_name="название",
    )
    measurement_unit = models.CharField(
        max_length=MAX_MEASUREMENT_NAME,
        verbose_name="единицы измерения",
    )

    class Meta:
        verbose_name = "Ингредиент"
        verbose_name_plural = "Ингредиенты"
        ordering = (
            "name",
        )

    def __str__(self):
        return f"Ингредиент {self.name}"
