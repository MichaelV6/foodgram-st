from django.contrib import admin
from django.contrib.auth.admin import UserAdmin
from django.contrib.auth.models import Group

from users.models import User, Subscription
from foodgram.utils import admin_thumbnail


@admin.register(User)
class UserAdmin(UserAdmin):
    list_display = (
        "username",
        "email",
        "first_name",
        "last_name",
        "get_avatar_preview",
    )
    search_fields = (
        "username",
        "email",
        "first_name",
        "last_name"
    )
    ordering = (
        "username",
    )
    readonly_fields = (
        "get_avatar_preview",
    )
    fieldsets = (
        (
            None, {"fields":
                (
                    "username",
                    "password"
                )
            }
        ),
        (
            "Personal Info", {"fields":
                (
                    "first_name",
                    "last_name",
                    "email",
                    "avatar",
                )
            }),
        (
            "Permissions", {"fields":
                (
                    "is_active",
                    "is_staff",
                    "is_superuser"
                )
            }),
        (
            "Important dates", {"fields":
                (
                    "last_login",
                    "date_joined"
                )
            }),
    )
    add_fieldsets = (
        (
            None, {"classes":
                (
                    "wide",
                ),
                "fields": (
                    "username",
                    "email",
                    "password1",
                    "password2",
                    "is_staff",
                    "is_superuser",
                ),
            },
        ),
    )
    filter_horizontal = ()

    def get_avatar_preview(self, obj):
        return admin_thumbnail(obj.avatar)

    get_avatar_preview.short_description = "Превью аватара"


@admin.register(Subscription)
class SubscribeAdmin(admin.ModelAdmin):
    list_display = (
        "user",
        "subscribed_to",
    )


admin.site.unregister(Group)
