import uuid
from os.path import splitext

from django.contrib.auth.models import AbstractUser
from django.core.validators import RegexValidator
from django.db import models

from foodgram.constants import MAX_USER_NAME
from foodgram.utils import image_compress


class User(AbstractUser):
    def upload_to(self, filename):
        user_username = self.username
        file_name, file_extension = splitext(filename)
        filename = f"{uuid.uuid4().hex}{file_extension}"
        return "users/{0}/{1}".format(user_username, filename)

    username = models.CharField(
        verbose_name="имя пользователя",
        max_length=MAX_USER_NAME,
        unique=True,
        validators=[RegexValidator(r"^[\w.@+-]+$")],
    )
    email = models.EmailField(
        unique=True,
        verbose_name="почта"
    )
    first_name = models.CharField(
        max_length=MAX_USER_NAME,
        verbose_name="имя",
    )
    last_name = models.CharField(
        max_length=MAX_USER_NAME,
        verbose_name="фамилия",
    )
    avatar = models.ImageField(
        upload_to=upload_to,
        null=True,
        blank=True,
        verbose_name="аватар",
    )

    REQUIRED_FIELDS = (
        "username", "first_name", "last_name", "password"
    )
    USERNAME_FIELD = "email"

    class Meta:
        verbose_name = "Пользователь"
        verbose_name_plural = "Пользователи"
        ordering = (
            "email",
        )

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.__original_avatar = self.avatar if self.pk else None

    def save(self, *args, **kwargs):
        """Переопределение метода сохранения с обработкой аватара"""
        super().save(*args, **kwargs)

        if self.__original_avatar != self.avatar and self.avatar:
            image_compress(self.avatar.path)

    def __str__(self):
        return f"Пользователь {self.email}"


class Subscription(models.Model):
    user = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        related_name="subscriptions",
        verbose_name="кто подписался",
    )
    subscribed_to = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        related_name="users_subscribers",
        verbose_name="на кого подписались",
    )

    class Meta:
        constraints = [
            models.UniqueConstraint(
                fields=["user", "subscribed_to"],
                name="unique_subscription_users",
            )
        ]
        verbose_name = "Подписка"
        verbose_name_plural = "Подписки"
        ordering = (
            "user",
            "subscribed_to",
        )

    def __str__(self):
        return f"{self.user} -> {self.subscribed_to}"
