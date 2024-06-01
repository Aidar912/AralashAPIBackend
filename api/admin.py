from django.contrib import messages
from django.urls import path, reverse
from django.shortcuts import redirect
from django.utils.html import format_html
from django.contrib import admin
from user.models import User, BusinessType, Company, UserCompanyRelation, MonthlyUserStatistics, Subscription
from api.models import PaymentMethod, Invoice, Withdrawal, WithdrawalRequest


class WithdrawalRequestAdmin(admin.ModelAdmin):
    list_display = [ 'user', 'amount', 'status', 'process_withdrawal_button','id']

    def process_withdrawal_button(self, obj):
        if obj.status == 'processing':
            return format_html(
                '<a class="button" href="{}">Mark as Payed and Deduct Balance</a>',
                reverse('admin:process_withdrawal', args=[obj.id])
            )
        return '-'
    process_withdrawal_button.short_description = 'Actions'
    process_withdrawal_button.allow_tags = True

    def get_urls(self):
        urls = super().get_urls()
        custom_urls = [
            path(
                'process_withdrawal/<int:request_id>/',
                self.admin_site.admin_view(self.process_withdrawal),
                name='process_withdrawal',
            ),
        ]
        return custom_urls + urls

    def process_withdrawal(self, request, request_id, *args, **kwargs):
        withdrawal_request = self.get_object(request, request_id)
        try:
            withdrawal_request.set_payed_and_deduct_balance()
            self.message_user(request, f"Withdrawal request {withdrawal_request.id} marked as payed and balance deducted.", messages.SUCCESS)
        except ValueError as e:
            self.message_user(request, f"Error processing withdrawal request {withdrawal_request.id}: {e}", messages.ERROR)
        return redirect('admin:api_withdrawalrequest_changelist')

admin.site.register(WithdrawalRequest, WithdrawalRequestAdmin)

from .models import APIKey


@admin.register(APIKey)
class APIKeyAdmin(admin.ModelAdmin):
    list_display = ('key', 'company', 'created_at', 'is_active')
    search_fields = ('key', 'company__name')
    list_filter = ('is_active', 'created_at')




# Настройка админских классов для моделей

@admin.register(User)
class UserAdmin(admin.ModelAdmin):
    list_display = ('email', 'username', 'is_active', 'is_staff', 'date_joined', 'balance')
    search_fields = ('email', 'username')
    list_filter = ('is_active', 'is_staff', 'date_joined')
    ordering = ('-date_joined',)


@admin.register(BusinessType)
class BusinessTypeAdmin(admin.ModelAdmin):
    list_display = ('name', 'code')
    search_fields = ('name', 'code')


@admin.register(Company)
class CompanyAdmin(admin.ModelAdmin):
    list_display = ('name', 'business_type', 'registration_number', 'address', 'created_at', 'subscription')
    search_fields = ('name', 'registration_number', 'address')
    list_filter = ('business_type', 'created_at')
    ordering = ('-created_at',)


@admin.register(UserCompanyRelation)
class UserCompanyRelationAdmin(admin.ModelAdmin):
    list_display = ('user', 'company', 'is_verified', 'created_at')
    search_fields = ('user__email', 'company__name')
    list_filter = ('is_verified', 'created_at')
    ordering = ('-created_at',)


@admin.register(MonthlyUserStatistics)
class MonthlyUserStatisticsAdmin(admin.ModelAdmin):
    list_display = ('user', 'month', 'requests_made')
    search_fields = ('user__email',)
    list_filter = ('month',)
    ordering = ('-month',)


@admin.register(Subscription)
class SubscriptionAdmin(admin.ModelAdmin):
    list_display = ('name', 'max_requests_per_month', 'price', 'created_at')
    search_fields = ('name',)
    list_filter = ('created_at',)
    ordering = ('-created_at',)




@admin.register(PaymentMethod)
class PaymentMethodAdmin(admin.ModelAdmin):
    list_display = ('name', 'description', 'is_active')
    search_fields = ('name',)
    list_filter = ('is_active',)
    ordering = ('name',)


@admin.register(Invoice)
class InvoiceAdmin(admin.ModelAdmin):
    list_display = ('id', 'user', 'amount', 'amount_currency', 'status', 'created_at')
    search_fields = ('user__email', 'id', 'amount_currency')
    list_filter = ('status', 'created_at')
    ordering = ('-created_at',)


@admin.register(Withdrawal)
class WithdrawalAdmin(admin.ModelAdmin):
    list_display = ('id', 'user', 'amount', 'currency', 'status', 'created_at')
    search_fields = ('user__email', 'id', 'currency')
    list_filter = ('status', 'created_at')
    ordering = ('-created_at',)


# Зарегистрируйте ваши модели в админке
# admin.site.register(UserCompanyRelation, UserCompanyRelationAdmin)
# admin.site.register(MonthlyUserStatistics, MonthlyUserStatisticsAdmin)
# admin.site.register(Subscription, SubscriptionAdmin)
# admin.site.register(PaymentMethod, PaymentMethodAdmin)
# admin.site.register(Invoice, InvoiceAdmin)
# admin.site.register(Withdrawal, WithdrawalAdmin)
