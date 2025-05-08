from django.db import models

from foodgram.constants import MAX_TAG_NAME


class Tag(models.Model):
    name = models.CharField(
        max_length=MAX_TAG_NAME,
        unique=True,
        verbose_name="название",
    )
    slug = models.SlugField(
        max_length=MAX_TAG_NAME,
        unique=True,
        verbose_name="слаг",
    )

    class Meta:
        verbose_name = "Тег"
        verbose_name_plural = "Теги"
        ordering = (
            "name",
        )

    def __str__(self):
        return f"Тег {self.name}"
