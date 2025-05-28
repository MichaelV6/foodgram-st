from http import HTTPStatus
from io import BytesIO
from datetime import *
from django.conf import settings
from django.core.files.storage import default_storage
from django.db.models import Sum
from django.http import FileResponse
from django.shortcuts import get_object_or_404
from django.urls import reverse
from django_filters.rest_framework import DjangoFilterBackend
from django.db.models.functions import Lower
from docx import Document
from hashids import Hashids
from rest_framework import (
    authtoken,
    decorators,
    filters,
    generics,
    permissions,
    response,
    status,
    views,
    viewsets,
)

from api.filters import IngredientFilter, RecipeFilter
from api.paginations import Pagination
from api.permissions import IsAuthorOrReadOnly
from api.serializers import (
    AvatarSerializer,
    FavoriteSerializer,
    IngredientSerializer,
    RecipeSerializer,
    SetPasswordSerializer,
    ShoppingCartSerializer,
    UserRegistrationSerializer,
    UserSerializer,
    RecipeShortSerializer,
    UserSubscriptionSerializer,
)

from recipes.models import (
    Recipe,
    RecipeIngredient,
    Favorite,
    Ingredient,
    User,
    Subscription,
    ShoppingCart
)

from rest_framework.response import Response
from rest_framework.views import APIView


class RecipeShortLinkView(APIView):
    def get(self, request, short_code):
        recipe = get_object_or_404(Recipe, short_code=short_code)
        serializer = RecipeShortSerializer(recipe, context={'request': request})
        return Response(serializer.data)


class IngredientViewSet(viewsets.ReadOnlyModelViewSet):
    queryset = Ingredient.objects.all().order_by(Lower('name'))
    serializer_class = IngredientSerializer
    pagination_class = None
    filter_backends = [DjangoFilterBackend, filters.SearchFilter]
    filterset_class = IngredientFilter


class RecipeViewSet(viewsets.ModelViewSet):
    queryset = Recipe.objects.all().order_by('-id')
    serializer_class = RecipeSerializer
    permission_classes = [
        permissions.IsAuthenticatedOrReadOnly,
        IsAuthorOrReadOnly,
    ]
    pagination_class = Pagination
    filter_backends = [DjangoFilterBackend, filters.SearchFilter]
    filterset_class = RecipeFilter

    @decorators.action(detail=True, methods=["get"], url_path="get-link")
    def link(self, request, pk=None):
        recipe = get_object_or_404(Recipe, id=pk)
        short_url = request.build_absolute_uri(
            reverse('recipe-short-link', kwargs={'short_code': recipe.short_code})
        )
        return Response({"short-link": short_url}, status=status.HTTP_200_OK)

    @decorators.action(
        detail=True,
        methods=["post"],
        url_name="favorite",
        permission_classes=[permissions.IsAuthenticated],
    )
    def favorite(self, request, pk=None):
        return self._add_to_relation(request, pk, Favorite, FavoriteSerializer)

    @decorators.action(
        detail=True,
        methods=["post"],
        url_name="shopping_cart",
        permission_classes=[permissions.IsAuthenticated],
    )
    def shopping_cart(self, request, pk=None):
        return self._add_to_relation(request, pk, ShoppingCart, ShoppingCartSerializer)

    def _add_to_relation(self, request, pk, model, serializer_class):
        """Универсальный метод для добавления в избранное/корзину"""
        recipe = get_object_or_404(Recipe, id=pk)
        user = request.user

        # Проверяем, существует ли уже связь
        if model.objects.filter(user=user, recipe=recipe).exists():
            error_messages = {
                Favorite: "Рецепт уже в избранном",
                ShoppingCart: "Рецепт уже в корзине покупок"
            }
            return Response(
                {"errors": error_messages[model]},
                status=status.HTTP_400_BAD_REQUEST
            )

        instance = model.objects.create(user=user, recipe=recipe)
        serializer = serializer_class(instance, context={'request': request})
        return Response(serializer.data, status=status.HTTP_201_CREATED)

    def _remove_from_relation(self, request, pk, model):
        """Универсальный метод для удаления из избранного/корзины"""
        recipe = get_object_or_404(Recipe, id=pk)
        user = request.user

        instance = model.objects.filter(user=user, recipe=recipe).first()
        if not instance:
            error_messages = {
                Favorite: "Рецепт не был в избранном",
                ShoppingCart: "Рецепт не был в корзине покупок"
            }
            return Response(
                {"errors": error_messages[model]},
                status=status.HTTP_400_BAD_REQUEST
            )

        instance.delete()
        return Response(status=status.HTTP_204_NO_CONTENT)

    @favorite.mapping.delete
    def remove_from_favorite(self, request, pk=None):
        return self._remove_from_relation(request, pk, Favorite)

    @shopping_cart.mapping.delete
    def remove_from_shopping_cart(self, request, pk=None):
        return self._remove_from_relation(request, pk, ShoppingCart)

    @decorators.action(
        detail=False,
        methods=["get"],
        url_path="download_shopping_cart",
        permission_classes=[permissions.IsAuthenticated],
    )
    def download_shopping_cart(self, request):
        document = Document()

        #Дата
        current_date = datetime.now().strftime("%d.%m.%Y %H:%M")
        document.add_heading(f"Список покупок ({current_date})", level=1)
        
        # Получаем рецепты пользователя из корзины
        user_shopping_cart = request.user.recipes_shopping_cart.all()
        
        # Добавляем список рецептов
        document.add_paragraph("Рецепты:")
        for item in user_shopping_cart:
            author_name = item.recipe.author.get_full_name() or item.recipe.author.username
            document.add_paragraph(
                f"- {item.recipe.name} (автор: {author_name})",
                style="ListBullet"
            )

        ingredients = (
            RecipeIngredient.objects.filter(
                recipe__in=user_shopping_cart.values_list("recipe", flat=True)
            )
            .values("ingredient__name", "ingredient__measurement_unit")
            .annotate(total_amount=Sum("amount"))
            .order_by("ingredient__name")
        )

        if ingredients:
            table = document.add_table(rows=1, cols=3)
            table.style = "Table Grid"
            hdr_cells = table.rows[0].cells
            hdr_cells[0].text = "№"
            hdr_cells[1].text = "Ингредиент"
            hdr_cells[2].text = "Количество"

            for idx, ing in enumerate(ingredients, start=1):
                row_cells = table.add_row().cells
                row_cells[0].text = str(idx)
                # Имя продукта с большой буквы
                name = ing["ingredient__name"].capitalize() if ing["ingredient__name"] else ""
                row_cells[1].text = name
                row_cells[2].text = (
                    f"{ing['total_amount']} "
                    f"{ing['ingredient__measurement_unit']}"
                )
        else:
            document.add_paragraph("Список покупок пуст!")

        buffer = BytesIO()
        document.save(buffer)
        buffer.seek(0)

        filename = f"shopping_list_{datetime.now().strftime('%Y%m%d')}.docx"
        
        return FileResponse(
            buffer,
            as_attachment=True,
            filename=filename,
            content_type=(
                "application/vnd.openxmlformats-officedocument."
                "wordprocessingml.document"
            ),
        )


class UserViewSet(viewsets.ModelViewSet):
    queryset = User.objects.all()
    serializer_class = UserSerializer
    pagination_class = Pagination
    http_method_names = ["get", "post", "put", "patch", "delete"]

    def get_serializer_class(self):
        if self.action == "list":
            return UserSerializer
        if self.action == "retrieve":
            return UserSerializer
        if self.action == "create":
            return UserRegistrationSerializer
        if self.action == "set_password":
            return SetPasswordSerializer
        if self.action in ["avatar"]:
            return UserSerializer
        return UserSerializer

    def create(self, request, *args, **kwargs):
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        user = serializer.save()
        response_data = UserRegistrationSerializer(user).data
        return Response(response_data, status=status.HTTP_201_CREATED)

    @decorators.action(
        detail=False,
        methods=["get"],
        url_path="me",
        permission_classes=[permissions.IsAuthenticated],
    )
    def me(self, request, *args, **kwargs):
        serializer = UserSerializer(
            request.user, context={"request": request}
        )
        return Response(serializer.data)

    @decorators.action(
        detail=False,
        methods=["post"],
        permission_classes=[permissions.IsAuthenticated],
        url_path="set_password",
    )
    def set_password(self, request, *args, **kwargs):
        serializer = self.get_serializer(
            data=request.data, context={"request": request}
        )
        serializer.is_valid(raise_exception=True)
        serializer.save()
        return Response(status=status.HTTP_204_NO_CONTENT)

    @decorators.action(
        detail=False,
        methods=["put", "delete"],
        permission_classes=[permissions.IsAuthenticated],
        url_path="me/avatar",
    )
    def avatar(self, request, *args, **kwargs):
        user = request.user

        if request.method in ["PUT", "PATCH"]:
            serializer = AvatarSerializer(data=request.data)
            serializer.is_valid(raise_exception=True)
            avatar = serializer.validated_data["avatar"]
            user.avatar = avatar
            user.save()
            return Response(
                {"avatar": user.avatar.url}, status=status.HTTP_200_OK
            )

        if request.method == "DELETE":
            if user.avatar:
                if default_storage.exists(user.avatar.name):
                    default_storage.delete(user.avatar.name)
                user.avatar = ""
                user.save()
            return Response(status=status.HTTP_204_NO_CONTENT)

    @decorators.action(
        detail=True,
        methods=["post", "delete"],
        permission_classes=[permissions.IsAuthenticated],
        url_path="subscribe",
    )
    def subscribe(self, request, pk=None):
        user = request.user
        author = get_object_or_404(User, id=pk)

        if user == author:
            return Response(
                {"errors": "Нельзя подписаться на самого себя."},
                status=status.HTTP_400_BAD_REQUEST,
            )

        if request.method == "POST":
            if user.subscriptions.filter(subscribed_to=author).exists():
                return Response(
                    {"errors": "Вы уже подписаны на этого пользователя."},
                    status=status.HTTP_400_BAD_REQUEST,
                )

            Subscription.objects.create(user=user, subscribed_to=author)
            serializer = UserSubscriptionSerializer(
                author, context={"request": request}
            )
            return Response(
                serializer.data, status=status.HTTP_201_CREATED
            )
        # DELETE method
        subscription = user.subscriptions.filter(subscribed_to=author).first()
        if not subscription:
            return Response(
                {"errors": "Подписка не найдена."},
                status=status.HTTP_400_BAD_REQUEST,
            )

        subscription.delete()
        return Response(status=status.HTTP_204_NO_CONTENT)

    @decorators.action(
        detail=False,
        methods=["get"],
        permission_classes=[permissions.IsAuthenticated],
        url_path="subscriptions",
    )
    def subscriptions(self, request, *args, **kwargs):
        user = request.user
        queryset = User.objects.filter(users_subscribers__user=user)
        pages = self.paginate_queryset(queryset)
        serializer = UserSubscriptionSerializer(
            pages, many=True, context={"request": request}
        )
        return self.get_paginated_response(serializer.data)
