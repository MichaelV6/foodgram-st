from django.shortcuts import get_object_or_404
from django.http import JsonResponse
from .models import Recipe
from api.serializers import RecipeShortSerializer


def recipe_short_link(request, recipe_id):
    recipe = get_object_or_404(Recipe, id=recipe_id)
    serializer = RecipeShortSerializer(recipe, context={'request': request})
    return JsonResponse(serializer.data)