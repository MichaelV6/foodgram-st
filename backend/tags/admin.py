from django.contrib import admin

from tags.models import Tag


@admin.register(Tag)
class TagAdmin(admin.ModelAdmin):
    list_display = (
        "name",
        "slug",
    )
    list_filter = (
        "name",
    )
    search_fields = (
        "name",
        "slug",
    )
