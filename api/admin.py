from django.contrib import admin

from .models import APIKey, Payment


@admin.register(APIKey)
class APIKeyAdmin(admin.ModelAdmin):
    list_display = ('key', 'user', 'created_at', 'is_active')
    search_fields = ('key', 'user__email')
    list_filter = ('is_active', 'created_at')


@admin.register(Payment)
class PaymentAdmin(admin.ModelAdmin):
    list_display = ('id', 'user', 'amount', 'currency', 'status', 'created_at')
    search_fields = ('id', 'user__email', 'description')
    list_filter = ('status', 'created_at', 'currency')
