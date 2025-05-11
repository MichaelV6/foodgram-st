from django.urls import path, include
from rest_framework.routers import DefaultRouter

from api.views import (
    UserViewSet,
    LogoutView,
    ObtainAuthToken,
    IngredientViewSet,
    RecipeViewSet,
    ShoppingCartViewSet,
)

router = DefaultRouter()
router.register("ingredients", IngredientViewSet)
router.register("recipes", RecipeViewSet)
router.register("shopping_cart", ShoppingCartViewSet, basename="shopping-cart")
router.register("users", UserViewSet)

urlpatterns = [
    path("", include(router.urls)),
    path("auth/token/login/", ObtainAuthToken.as_view(), name="login"),
    path("auth/token/logout/", LogoutView.as_view(), name="logout"),
]
