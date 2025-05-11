from http import HTTPStatus
from io import BytesIO

from django.conf import settings
from django.core.files.storage import default_storage
from django.db.models import Sum
from django.http import FileResponse
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
from api.paginations import CustomPagination
from api.permissions import IsAuthorOrReadOnly
from api.serializers import (
    AuthTokenSerializer,
    AvatarSerializer,
    FavoriteRecipeSerializer,
    IngredientSerializer,
    RecipeSerializer,
    SetPasswordSerializer,
    ShoppingCartSerializer,
    SubscribeSerializer,
    UserDetailSerializer,
    UserRegistrationSerializer,
    UserSerializer,
)
from ingredients.models import Ingredient
from recipes.models import Favorite, Recipe, RecipeIngredient, ShoppingCart
from users.models import Subscription, User

hashids = Hashids(salt=settings.SECRET_KEY, min_length=6)


class IngredientViewSet(viewsets.ReadOnlyModelViewSet):
    queryset = Ingredient.objects.all().order_by(Lower('name'))
    serializer_class = IngredientSerializer
    pagination_class = None
    filter_backends = [DjangoFilterBackend, filters.SearchFilter]
    filterset_class = IngredientFilter


class RecipeViewSet(viewsets.ModelViewSet):
    queryset = Recipe.objects.all()
    serializer_class = RecipeSerializer
    permission_classes = [
        permissions.IsAuthenticatedOrReadOnly,
        IsAuthorOrReadOnly,
    ]
    pagination_class = CustomPagination
    filter_backends = [DjangoFilterBackend, filters.SearchFilter]
    filterset_class = RecipeFilter


    @decorators.action(detail=True, methods=["get"], url_path="get-link")
    def link(self, request, *args, **kwargs):
        recipe = self.get_object()
        short_code = hashids.encode(recipe.id)
        base_url = request.build_absolute_uri("/")[:-1]
        short_url = f"{base_url}/r/{short_code}"
        return response.Response(
            {"short-link": short_url}, status=status.HTTP_200_OK
        )

    @decorators.action(
        detail=True,
        methods=["post"],
        url_name="shopping_cart",
        permission_classes=[permissions.IsAuthenticated],
    )
    def shopping_cart(self, request, pk=None):
        recipe = generics.get_object_or_404(Recipe, id=pk)
        user = request.user

        instance, created = ShoppingCart.objects.get_or_create(
            user=user, recipe=recipe
        )
        serializer = ShoppingCartSerializer(instance)
        response_data = serializer.data
        return response.Response(
            response_data,
            status=(
                status.HTTP_201_CREATED if created else HTTPStatus.BAD_REQUEST
            ),
        )

    @shopping_cart.mapping.delete
    def remove_from_shopping_cart(self, request, pk=None):
        recipe = generics.get_object_or_404(Recipe, id=pk)
        user = request.user

        cart_item = user.recipes_shopping_cart.filter(recipe=recipe).first()

        if cart_item:
            cart_item.delete()
            return response.Response(status=status.HTTP_204_NO_CONTENT)
        return response.Response(
            {"detail": "Рецепт не найден"},
            status=HTTPStatus.BAD_REQUEST,
        )

    @decorators.action(
        detail=True,
        methods=["post"],
        url_name="favorite",
        permission_classes=[permissions.IsAuthenticated],
    )
    def favorite(self, request, pk=None):
        recipe = generics.get_object_or_404(Recipe, id=pk)
        user = request.user

        instance, created = Favorite.objects.get_or_create(
            user=user, recipe=recipe
        )
        serializer = FavoriteRecipeSerializer(instance)
        response_data = serializer.data
        return response.Response(
            response_data,
            status=(
                status.HTTP_201_CREATED if created else HTTPStatus.BAD_REQUEST
            ),
        )

    @favorite.mapping.delete
    def remove_from_favorite(self, request, pk=None):
        recipe = generics.get_object_or_404(Recipe, id=pk)
        user = request.user

        favorite = Favorite.objects.filter(user=user, recipe=recipe).first()

        if not favorite:
            return response.Response(
                {"detail": "Рецепт не был в избранном"},
                status=status.HTTP_400_BAD_REQUEST
            )

        favorite.delete()
        return response.Response(status=status.HTTP_204_NO_CONTENT)

    @decorators.action(
        detail=False,
        methods=["get"],
        url_path="download_shopping_cart",
        permission_classes=[permissions.IsAuthenticated],
    )
    def download_shopping_cart(self, request):
        document = Document()
        document.add_heading("Список покупок", level=1)
        recipes_shop = request.user.recipes_shopping_cart
        ingredients = (
            RecipeIngredient.objects.filter(
                recipe__in=recipes_shop.values_list("recipe", flat=True)
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
                row_cells[1].text = ing["ingredient__name"]
                row_cells[2].text = (
                    f"{ing['total_amount']} "
                    f"{ing['ingredient__measurement_unit']}"
                )
        else:
            document.add_paragraph("Список покупок пуст!")

        buffer = BytesIO()
        document.save(buffer)
        buffer.seek(0)

        сontent_type = (
            "application/vnd.openxmlformats-officedocument."
            "wordprocessingml.document"
        )
        return FileResponse(
            buffer,
            as_attachment=True,
            filename="shopping_list.docx",
            content_type=сontent_type,
        )


class ShoppingCartViewSet(viewsets.ModelViewSet):
    queryset = ShoppingCart.objects.all()
    serializer_class = ShoppingCartSerializer
    permission_classes = [permissions.IsAuthenticated]

    def get_queryset(self):
        return self.queryset.filter(user=self.request.user)

    def perform_create(self, serializer):
        serializer.save(user=self.request.user)

    @decorators.action(detail=False, methods=["delete"])
    def clear_cart(self, request):
        self.get_queryset().delete()
        return response.Response(status=status.HTTP_204_NO_CONTENT)


class UserViewSet(viewsets.ModelViewSet):
    queryset = User.objects.all()
    serializer_class = UserSerializer
    pagination_class = CustomPagination
    http_method_names = ["get", "post", "put", "patch", "delete"]

    def get_serializer_class(self):
        if self.action == "list":
            return UserSerializer
        if self.action == "retrieve":
            return UserDetailSerializer
        if self.action == "create":
            return UserRegistrationSerializer
        if self.action == "set_password":
            return SetPasswordSerializer
        if self.action in ["avatar"]:
            return UserDetailSerializer
        return UserSerializer

    def create(self, request, *args, **kwargs):
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        user = serializer.save()
        response_data = UserRegistrationSerializer(user).data
        return response.Response(response_data, status=status.HTTP_201_CREATED)

    @decorators.action(
        detail=False,
        methods=["get"],
        url_path="me",
        permission_classes=[permissions.IsAuthenticated],
    )
    def me(self, request, *args, **kwargs):
        serializer = UserDetailSerializer(
            request.user, context={"request": request}
        )
        return response.Response(serializer.data)

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
        return response.Response(status=status.HTTP_204_NO_CONTENT)

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
            return response.Response(
                {"avatar": user.avatar.url}, status=status.HTTP_200_OK
            )

        if request.method == "DELETE":
            if user.avatar:
                if default_storage.exists(user.avatar.name):
                    default_storage.delete(user.avatar.name)
                user.avatar = ""
                user.save()
            return response.Response(status=status.HTTP_204_NO_CONTENT)

    @decorators.action(
        detail=True,
        methods=["post", "delete"],
        permission_classes=[permissions.IsAuthenticated],
        url_path="subscribe",
    )
    def subscribe(self, request, pk=None):
        user = request.user
        author = generics.get_object_or_404(User, id=pk)

        if user == author:
            return response.Response(
                {"errors": "Нельзя подписаться на самого себя."},
                status=status.HTTP_400_BAD_REQUEST,
            )

        if request.method == "POST":
            data = {"subscribed_to": author.id}
            serializer = SubscribeSerializer(
                author, data=data, context={"request": request}
            )
            serializer.is_valid(raise_exception=True)
            Subscription.objects.create(user=user, subscribed_to=author)
            return response.Response(
                serializer.data, status=status.HTTP_201_CREATED
            )
        elif request.method == "DELETE":
            serializer = SubscribeSerializer(
                author, context={"request": request}
            )
            serializer.validate_for_delete(user=user, author=author)
            subscription = Subscription.objects.filter(
                user=user, subscribed_to=author
            ).first()
            if subscription:
                subscription.delete()
                return response.Response(status=status.HTTP_204_NO_CONTENT)
            return response.Response(
                {"errors": "Подписка не найдена."},
                status=status.HTTP_400_BAD_REQUEST,
            )

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
        serializer = SubscribeSerializer(
            pages, many=True, context={"request": request}
        )
        return self.get_paginated_response(serializer.data)


class ObtainAuthToken(views.APIView):
    serializer_class = AuthTokenSerializer

    def get_serializer_context(self):
        return {
            "request": self.request,
            "format": self.format_kwarg,
            "view": self,
        }

    def get_serializer(self, *args, **kwargs):
        kwargs["context"] = self.get_serializer_context()
        return self.serializer_class(*args, **kwargs)

    def post(self, request, *args, **kwargs):
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        user = serializer.validated_data["user"]
        token, created = authtoken.models.Token.objects.get_or_create(
            user=user
        )
        return response.Response({"auth_token": token.key})


class LogoutView(views.APIView):
    permission_classes = [permissions.IsAuthenticated]

    def post(self, request):
        request.user.auth_token.delete()
        return response.Response(status=status.HTTP_204_NO_CONTENT)
