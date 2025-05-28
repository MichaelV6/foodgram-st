from django.urls import path, include
from rest_framework.routers import DefaultRouter

from api.views import (
    UserViewSet,
    IngredientViewSet,
    RecipeShortLinkView,
    RecipeViewSet,
)

router = DefaultRouter()
router.register("ingredients", IngredientViewSet)
router.register("recipes", RecipeViewSet)
router.register("users", UserViewSet)

urlpatterns = [
    path("", include(router.urls)),
    path('s/<str:short_code>/', RecipeShortLinkView.as_view(), name='recipe-short-link'),
    path("auth/", include('djoser.urls')),  # Эндпоинты Djoser
    path("auth/", include('djoser.urls.authtoken')),  # Аутентификация по токену

]
