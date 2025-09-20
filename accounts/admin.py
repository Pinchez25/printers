from django.contrib import admin
from django.contrib.auth.admin import GroupAdmin, UserAdmin
from django.contrib.auth.models import Group
from django.utils.html import format_html
from unfold.admin import ModelAdmin
from unfold.forms import AdminPasswordChangeForm, UserChangeForm, UserCreationForm

from .models import CustomUser

admin.site.unregister(Group)


@admin.register(Group)
class GroupAdmin(GroupAdmin, ModelAdmin):
    pass



@admin.register(CustomUser)
class CustomUserAdmin(UserAdmin, ModelAdmin):
    form = UserChangeForm
    add_form = UserCreationForm
    change_password_form = AdminPasswordChangeForm

    def profile_thumbnail(self, obj):
        if obj.profile_photo:
            return format_html(
                '<img src="{}" style="width:40px;height:40px;border-radius:50%;" />',
                obj.profile_photo.url
            )
        return "—"

    profile_thumbnail.short_description = "Photo"

    list_display = (
        "username", "email", "first_name", "last_name",
        "role", "is_staff", "profile_thumbnail"
    )
    list_filter = ("is_staff", "is_superuser", "is_active", "groups")
    search_fields = ("username", "first_name", "last_name", "email", "role")
    ordering = ("username",)

    fieldsets = UserAdmin.fieldsets + (
        ("Profile", {"fields": ("profile_photo", "role", "description")}),
    )
    add_fieldsets = UserAdmin.add_fieldsets + (
        ("Profile", {"fields": ("profile_photo", "role", "description")}),
    )
