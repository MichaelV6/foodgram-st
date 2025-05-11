from django.contrib import admin

from recipes.models import Recipe, RecipeIngredient, Favorite
from foodgram.utils import admin_thumbnail


@admin.register(Recipe)
class RecipeAdmin(admin.ModelAdmin):
    list_display = (
        "name",
        "id",
        "author",
        "get_image_preview",
    )
    search_fields = (
        "name",
        "author__username",
        "author__email",
    )
    list_filter = (
        "author",
        "name",
    )
    readonly_fields = (
        "get_image_preview",
    )

    def get_image_preview(self, obj):
        return admin_thumbnail(obj.image)

    get_image_preview.short_description = "Превью рецепта"



@admin.register(RecipeIngredient)
class RecipeIngredientAdmin(admin.ModelAdmin):
    list_display = (
        "recipe",
        "ingredient",
        "amount",
    )


@admin.register(Favorite)
class FavoriteAdmin(admin.ModelAdmin):
    list_display = (
        "id",
        "user",
        "recipe",
    )
    list_filter = (
        "user",
        "recipe",
    )
    search_fields = (
        "user__username",
        "recipe__name",
    )
    list_per_page = 20

    def get_queryset(self, request):
        return super().get_queryset(request).select_related("user", "recipe")
