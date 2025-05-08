from rest_framework import serializers
from drf_extra_fields.fields import Base64ImageField

from recipes.models import Recipe


class RecipeCustomSerializer(serializers.ModelSerializer):
    image = Base64ImageField()

    class Meta:
        model = Recipe
        fields = ("id", "name", "image", "cooking_time")
