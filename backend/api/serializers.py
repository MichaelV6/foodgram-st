from django.contrib.auth import authenticate
from django.core.validators import MinValueValidator, MaxValueValidator
from rest_framework import serializers, generics
from drf_extra_fields.fields import Base64ImageField

from api.short_serializers import RecipeCustomSerializer
from foodgram.constants import (
    MIN_COOKING_TIME,
    MAX_COOKING_TIME,
    MIN_AMOUNT,
    MAX_AMOUNT,
)

from recipes.models import Recipe, RecipeIngredient, ShoppingCart, Favorite
from ingredients.models import Ingredient
from users.models import User, Subscription


class IngredientSerializer(serializers.ModelSerializer):
    class Meta:
        model = Ingredient
        fields = ["id", "name", "measurement_unit"]



class FavoriteRecipeSerializer(serializers.ModelSerializer):
    class Meta:
        model = Recipe
        fields = ("id",)

    def to_representation(self, instance):
        representation = super().to_representation(instance)
        favorite = generics.get_object_or_404(
            Favorite, pk=representation["id"]
        )
        return RecipeCustomSerializer(favorite.recipe).data


class ShoppingCartSerializer(serializers.ModelSerializer):
    class Meta:
        model = ShoppingCart
        fields = ["user", "recipe"]
        read_only_fields = ["user"]

    def validate(self, data):
        user = self.context["request"].user
        recipe = data["recipe"]

        if user.shopping_cart.filter(recipe=recipe).exists():
            raise serializers.ValidationError(
                "Этот рецепт уже добавлен в корзину"
            )
        return data

    def to_representation(self, instance):
        return RecipeCustomSerializer(instance.recipe).data


class BaseUserSerializer(serializers.ModelSerializer):
    is_subscribed = serializers.SerializerMethodField()
    avatar = Base64ImageField()

    class Meta:
        model = User
        fields = (
            "email",
            "id",
            "username",
            "first_name",
            "last_name",
            "is_subscribed",
            "avatar",
        )

    def get_is_subscribed(self, obj):
        request = self.context.get("request")
        if request and request.user.is_authenticated:
            return request.user.subscriptions.filter(
                subscribed_to=obj
            ).exists()
        return False


class UserSerializer(BaseUserSerializer):
    class Meta(BaseUserSerializer.Meta):
        read_only_fields = ("email",)


class UserDetailSerializer(BaseUserSerializer):
    pass


class UserRegistrationSerializer(serializers.ModelSerializer):
    password = serializers.CharField(write_only=True)

    class Meta:
        model = User
        fields = (
            "id",
            "username",
            "first_name",
            "last_name",
            "email",
            "password",
        )
        extra_kwargs = {"avatar": {"required": False}}

    def create(self, validated_data):
        return User.objects.create_user(
            username=validated_data["username"],
            first_name=validated_data["first_name"],
            last_name=validated_data["last_name"],
            email=validated_data["email"],
            password=validated_data["password"],
            avatar=validated_data.get("avatar"),
        )


class SetPasswordSerializer(serializers.Serializer):
    current_password = serializers.CharField(write_only=True)
    new_password = serializers.CharField(write_only=True)

    def validate(self, data):
        user = self.context["request"].user
        if not user.check_password(data["current_password"]):
            raise serializers.ValidationError(
                {"current_password": "Неверный пароль"}
            )
        if data["current_password"] == data["new_password"]:
            raise serializers.ValidationError(
                {"new_password": ("Новый пароль должен отличаться")}
            )
        return data

    def save(self):
        user = self.context["request"].user
        new_password = self.validated_data["new_password"]
        user.set_password(new_password)
        user.save()


class AvatarSerializer(serializers.Serializer):
    avatar = Base64ImageField(required=True)


class SubscribeSerializer(serializers.ModelSerializer):
    is_subscribed = serializers.SerializerMethodField()
    recipes = serializers.SerializerMethodField()
    recipes_count = serializers.ReadOnlyField(source="recipes.count")
    avatar = Base64ImageField(required=False)

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
        read_only_fields = ("email", "username", "first_name", "last_name")

    def get_is_subscribed(self, obj):
        request = self.context.get("request")
        if request and request.user.is_authenticated:
            return request.user.users_subscribers.filter(
                subscribed_to=obj
            ).exists()
        return False

    def get_recipes(self, obj):
        request = self.context.get("request")
        limit = request.GET.get("recipes_limit")
        recipes = obj.recipes.all()

        if limit:
            try:
                limit = int(limit)
                recipes = recipes[:limit] if limit > 0 else recipes.none()
            except (ValueError, TypeError):
                pass  # Или можно вернуть ошибку, если нужно

        serializer = RecipeCustomSerializer(recipes, many=True, read_only=True)
        return serializer.data

    def validate(self, data):
        request = self.context.get("request")
        user = request.user
        author = self.instance
        if user == author:
            raise serializers.ValidationError(
                "Нельзя подписаться на самого себя."
            )

        if user.subscriptions.filter(subscribed_to=author).exists():
            raise serializers.ValidationError(
                "Вы уже подписаны на этого пользователя."
            )

        return data

    def validate_for_delete(self, user, author):
        if not user.subscriptions.filter(subscribed_to=author).exists():
            raise serializers.ValidationError("Подписка не найдена.")

    def create(self, validated_data):
        user = self.context["request"].user
        subscription = Subscription.objects.create(
            user=user, subscribed_to=self.instance
        )
        return subscription


class AuthTokenSerializer(serializers.Serializer):
    email = serializers.CharField(write_only=True)
    password = serializers.CharField(
        style={"input_type": "password"},
        trim_whitespace=False,
        write_only=True,
    )
    token = serializers.CharField(read_only=True)

    def validate(self, attrs):
        email = attrs.get("email")
        password = attrs.get("password")

        if email and password:
            user = authenticate(
                request=self.context.get("request"),
                username=email,
                password=password,
            )

            if not user:
                msg = "Нет такого пользователя"
                raise serializers.ValidationError(msg, code="authorization")
        else:
            msg = "Должна включать email и пароль"
            raise serializers.ValidationError(msg, code="authorization")

        attrs["user"] = user
        return attrs


class RecipeIngredientSerializer(serializers.ModelSerializer):
    id = serializers.PrimaryKeyRelatedField(
        queryset=Ingredient.objects.all(), source="ingredient.id"
    )
    name = serializers.CharField(source="ingredient.name", read_only=True)
    measurement_unit = serializers.CharField(
        source="ingredient.measurement_unit", read_only=True
    )
    amount = serializers.IntegerField(
        min_value=MIN_AMOUNT,
        max_value=MAX_AMOUNT,
        validators=[
            MinValueValidator(
                MIN_AMOUNT,
                message=f"Количество не может быть меньше {MIN_AMOUNT}",
            ),
            MaxValueValidator(
                MAX_AMOUNT,
                message=f"Количество не может превышать {MAX_AMOUNT}",
            ),
        ],
    )

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
        min_value=MIN_COOKING_TIME,
        max_value=MAX_COOKING_TIME,
        validators=[
            MinValueValidator(
                MIN_COOKING_TIME,
                message=f"Время приготовления не "
                f"может быть меньше {MIN_COOKING_TIME} минуты",
            ),
            MaxValueValidator(
                MAX_COOKING_TIME,
                message=f"Время приготовления не "
                f"может превышать {MAX_COOKING_TIME} минут",
            ),
        ],
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
        if request and request.user.is_authenticated:
            return obj.favorited_by_users.filter(user=request.user).exists()
        return False

    def get_is_in_shopping_cart(self, obj):
        request = self.context.get("request")
        if request and request.user.is_authenticated:
            return obj.recipes_in_shopping_cart.filter(
                user=request.user
            ).exists()
        return False

    def _create_or_update_ingredients(self, recipe, ingredients_data):
        recipe_ingredients = [
            RecipeIngredient(
                recipe=recipe,
                ingredient_id=ingredient_data["ingredient"]["id"].id,
                amount=ingredient_data["amount"],
            )
            for ingredient_data in ingredients_data
        ]
        RecipeIngredient.objects.bulk_create(recipe_ingredients)
        return recipe_ingredients

    def create(self, validated_data):
        ingredients_data = validated_data.pop("recipe_ingredients", [])
        author = self.context["request"].user

        recipe = Recipe.objects.create(author=author, **validated_data)

        self._create_or_update_ingredients(recipe, ingredients_data)
        return recipe

    def update(self, instance, validated_data):
        if 'image' not in validated_data:
            validated_data['image'] = instance.image

        ingredients_data = validated_data.pop("recipe_ingredients", [])

        for attr, value in validated_data.items():
            setattr(instance, attr, value)
        instance.save()

        instance.recipe_ingredients.all().delete()

        self._create_or_update_ingredients(instance, ingredients_data)
        return instance

    def to_representation(self, instance):
        rep = super().to_representation(instance)
        return rep
