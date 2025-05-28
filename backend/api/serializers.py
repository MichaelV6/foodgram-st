from django.contrib.auth import authenticate
from django.core.validators import MinValueValidator, MaxValueValidator
from rest_framework import serializers, generics

from foodgram.constants import (
    MIN_COOKING_TIME,
    MAX_COOKING_TIME,
    MIN_AMOUNT,
    MAX_AMOUNT,
)

from recipes.models import (
    Recipe,
    RecipeIngredient,
    Favorite,
    Ingredient,
    User,
    ShoppingCart
)

from drf_extra_fields.fields import Base64ImageField
from djoser.serializers import (
    UserSerializer as DjoserUserSerializer,
    UserCreateSerializer as DjoserRegistrationSerializer,
    SetPasswordSerializer as DjoserSetPasswordSerializer
)


class BaseUserMixin(serializers.ModelSerializer):
    avatar = Base64ImageField(required=False)
    is_subscribed = serializers.SerializerMethodField()

    def get_is_subscribed(self, obj):
        request = self.context.get("request")
        return (
            request and
            request.user.is_authenticated and
            request.user.subscriptions.filter(subscribed_to=obj).exists()
        )


class RecipeShortSerializer(serializers.ModelSerializer):
    image = Base64ImageField(read_only=True)

    class Meta:
        model = Recipe
        fields = ("id", "name", "image", "cooking_time")
        read_only_fields = fields

    def create(self, validated_data):
        raise NotImplementedError(
            "RecipeShortSerializer предназначен только для чтения"
        )

    def update(self, instance, validated_data):
        raise NotImplementedError(
            "RecipeShortSerializer предназначен только для чтения"
        )


class IngredientSerializer(serializers.ModelSerializer):
    class Meta:
        model = Ingredient
        fields = ["id", "name", "measurement_unit"]


class FavoriteSerializer(serializers.ModelSerializer):
    """Сериализатор для добавления/удаления из избранного"""
    class Meta:
        model = Favorite
        fields = ("user", "recipe")
        read_only_fields = ("user",)

    def validate(self, data):
        user = self.context["request"].user
        recipe = data["recipe"]

        if user.favorites.filter(recipe=recipe).exists():
            raise serializers.ValidationError(
                "Этот рецепт уже добавлен в избранное"
            )
        return data

    def to_representation(self, instance):
        
        return RecipeShortSerializer(instance.recipe, context=self.context).data


class ShoppingCartSerializer(serializers.ModelSerializer):
    class Meta:
        model = ShoppingCart
        fields = ["user", "recipe"]
        read_only_fields = ["user"]

    def validate(self, data):
        user = self.context["request"].user
        recipe = data["recipe"]

        if user.recipes_shopping_cart.filter(recipe=recipe).exists():
            raise serializers.ValidationError(
                "Этот рецепт уже добавлен в корзину"
            )
        return data

    def to_representation(self, instance):
        return RecipeShortSerializer(instance.recipe, context=self.context).data


class BaseUserSerializer(DjoserUserSerializer, BaseUserMixin):
    class Meta(DjoserUserSerializer.Meta):
        fields = tuple(
            field for field in DjoserUserSerializer.Meta.fields
            if field != 'password'
        ) + (
            'is_subscribed',
            'avatar',
        )
        read_only_fields = DjoserUserSerializer.Meta.read_only_fields + (
            'is_subscribed',
        )


class SetPasswordSerializer(DjoserSetPasswordSerializer):
    current_password = serializers.CharField(write_only=True)

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields['new_password'] = serializers.CharField(write_only=True)
        self.fields['current_password'] = serializers.CharField(write_only=True)

    def validate(self, attrs):
        attrs = super().validate(attrs)
        user = self.context.get("request").user
        current_password = attrs.get("current_password")

        if not user.check_password(current_password):
            raise serializers.ValidationError(
                {"current_password": "Неверный пароль"}
            )

        if current_password == attrs.get("new_password"):
            raise serializers.ValidationError(
                {"new_password": "Новый пароль должен отличаться"}
            )

        return attrs

    def save(self):
        user = self.context.get("request").user
        user.set_password(self.validated_data["new_password"])
        user.save()


# Алиасы для совместимости
UserSerializer = BaseUserSerializer
UserRegistrationSerializer = DjoserRegistrationSerializer


class AvatarSerializer(serializers.Serializer):
    avatar = Base64ImageField(required=True)


class UserSubscriptionSerializer(BaseUserMixin, serializers.ModelSerializer):
    recipes = serializers.SerializerMethodField()
    recipes_count = serializers.ReadOnlyField(source="recipes.count")

    class Meta:
        model = User
        fields = (
            "email",
            "id",
            "username",
            "first_name",
            "last_name",
            "is_subscribed",
            "recipes",
            "recipes_count",
            "avatar",
        )
        read_only_fields = fields

    def get_recipes(self, obj):
        request = self.context.get("request")
        recipes = obj.recipes.all()
        try:
            limit = int(request.GET.get("recipes_limit", 10 ** 10))
            recipes = recipes[:limit] if limit > 0 else recipes.none()
        except (ValueError, TypeError):
            pass

        serializer = RecipeShortSerializer(
            recipes, many=True, read_only=True, context=self.context
        )
        return serializer.data


class RecipeIngredientSerializer(serializers.ModelSerializer):
    id = serializers.PrimaryKeyRelatedField(
        queryset=Ingredient.objects.all(), source="ingredient.id"
    )
    name = serializers.CharField(source="ingredient.name", read_only=True)
    measurement_unit = serializers.CharField(
        source="ingredient.measurement_unit", read_only=True
    )
    amount = serializers.IntegerField()

    class Meta:
        model = RecipeIngredient
        fields = ("id", "name", "measurement_unit", "amount")


class RecipeSerializer(serializers.ModelSerializer):
    author = UserSerializer(read_only=True)

    ingredients = RecipeIngredientSerializer(
        many=True, source="recipe_ingredients"
    )
    image = Base64ImageField(required=True)
    is_favorited = serializers.SerializerMethodField()
    is_in_shopping_cart = serializers.SerializerMethodField()
    cooking_time = serializers.IntegerField(
    )

    class Meta:
        model = Recipe
        fields = [
            "id",
            "author",
            "ingredients",
            "name",
            "image",
            "text",
            "cooking_time",
            "is_favorited",
            "is_in_shopping_cart",
        ]

    def validate(self, data):
        ingredients = data.get("recipe_ingredients", [])
        image = data.get("image")
        cooking_time = data.get("cooking_time")

        if self.context['request'].method == 'POST' and (
                image is None or image == ""):
            raise serializers.ValidationError(
                {"image": "Изображение нельзя оставить пустым"}
            )

        if not ingredients:
            raise serializers.ValidationError(
                {"ingredient": "Поле Ингридиент не может быть пустым."}
            )
        for ingredient in ingredients:
            amount = ingredient.get("amount")
            if amount is None:
                raise serializers.ValidationError(
                    {
                        "amount": "Количество обязательно "
                        "для каждого ингредиента."
                    }
                )
            if not (MIN_AMOUNT <= amount <= MAX_AMOUNT):
                raise serializers.ValidationError(
                    {
                        "amount": f"Количество должно "
                        f"быть между {MIN_AMOUNT} и {MAX_AMOUNT}."
                    }
                )

        if len(ingredients) != len(
            {ingredient["ingredient"]["id"] for ingredient in ingredients}
        ):
            raise serializers.ValidationError(
                {"ingredients": "Ингредиенты не должны повторяться."}
            )
        if cooking_time is None:
            raise serializers.ValidationError(
                {"cooking_time": "Время приготовления обязательно."}
            )
        if not (MIN_COOKING_TIME <= cooking_time <= MAX_COOKING_TIME):
            raise serializers.ValidationError(
                {
                    "cooking_time": f"Время приготовления "
                    f"должно быть между {MIN_COOKING_TIME} "
                    f"и {MAX_COOKING_TIME} минутами."
                }
            )

        if image is None or image == "":
            raise serializers.ValidationError(
                {"image": "Изображение нельзя оставить пустым"}
            )

        return data

    def get_is_favorited(self, obj):
        request = self.context.get("request")
        return (
            request and
            request.user.is_authenticated and
            obj.favorited_by_users.filter(user=request.user).exists()
        )

    def get_is_in_shopping_cart(self, obj):
        request = self.context.get("request")
        if request and request.user.is_authenticated:
            return obj.recipes_in_shopping_cart.filter(
                user=request.user
            ).exists()
        return False

    def _create_or_update_ingredients(self, recipe, ingredients_data):
        RecipeIngredient.objects.bulk_create([
            RecipeIngredient(
                recipe=recipe,
                ingredient_id=ingredient_data["ingredient"]["id"].id,
                amount=ingredient_data["amount"],
            )
            for ingredient_data in ingredients_data
        ])

    def create(self, validated_data):
        ingredients_data = validated_data.pop("recipe_ingredients", [])
        author = self.context["request"].user
        recipe = super().create({**validated_data, "author": author})
        self._create_or_update_ingredients(recipe, ingredients_data)
        return recipe

    def update(self, instance, validated_data):
        ingredients_data = validated_data.pop("recipe_ingredients", [])

        if 'image' not in validated_data:
            validated_data['image'] = instance.image

        instance = super().update(instance, validated_data)

        instance.recipe_ingredients.all().delete()
        self._create_or_update_ingredients(instance, ingredients_data)

        return instance

    def to_representation(self, instance):
        rep = super().to_representation(instance)
        return rep
