from django.contrib import admin

from .models import APIKey


@admin.register(APIKey)
class APIKeyAdmin(admin.ModelAdmin):
    list_display = ('secret', 'user', 'created_at', 'is_active')
    search_fields = ('secret', 'user__email')
    list_filter = ('is_active', 'created_at')


