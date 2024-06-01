from django.contrib import admin
from django.contrib import messages
from django.urls import path, reverse
from django.shortcuts import redirect
from django.utils.html import format_html
from .models import WithdrawalRequest


from .models import APIKey


@admin.register(APIKey)
class APIKeyAdmin(admin.ModelAdmin):
    list_display = ('secret', 'user', 'created_at', 'is_active')
    search_fields = ('secret', 'user__email')
    list_filter = ('is_active', 'created_at')


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

