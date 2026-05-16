from django.contrib import admin

from .models import UserProfile


@admin.register(UserProfile)
class UserProfileAdmin(admin.ModelAdmin):
    list_display = ('user', 'role', 'timezone', 'created_at')
    list_filter = ('role', 'timezone')
    search_fields = ('user__username', 'user__email')
