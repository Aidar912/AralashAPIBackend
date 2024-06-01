from rest_framework import serializers

from .models import PaymentMethod, Invoice, Withdrawal,WithdrawalRequest




class PaymentMethodSerializer(serializers.ModelSerializer):
    class Meta:
        model = PaymentMethod
        fields = '__all__'


class InvoiceSerializer(serializers.ModelSerializer):
    class Meta:
        model = Invoice
        fields = '__all__'


class WithdrawalRequestSerializer(serializers.ModelSerializer):
    amount = serializers.DecimalField(max_digits=10, decimal_places=2)
    callback_url = serializers.CharField(required=False, allow_blank=True)

    class Meta:
        model = WithdrawalRequest
        fields = [
            'auth_login', 'auth_secret', 'amount',
            'amount_currency', 'method', 'wallet', 'subtract_from',
            'callback_url', 'extra', 'commission', 'rub_amount',
            'receive_amount', 'deduction_amount', 'currency'
        ]
        read_only_fields = ['commission', 'rub_amount', 'receive_amount', 'deduction_amount', 'currency']

class ConfirmWithdrawalRequestSerializer(serializers.Serializer):
    auth_login = serializers.CharField()
    auth_secret = serializers.CharField()
    id = serializers.CharField()

class CancelWithdrawalRequestSerializer(serializers.Serializer):
    auth_login = serializers.CharField()
    auth_secret = serializers.CharField()
    id = serializers.CharField()


class GetWithdrawalRequestSerializer(serializers.Serializer):
    auth_login = serializers.CharField()
    auth_secret = serializers.CharField()
    id = serializers.CharField()


class WithdrawalSerializer(serializers.ModelSerializer):
    class Meta:
        model = Withdrawal
        fields = '__all__'

