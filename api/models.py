import secrets
import uuid
from decimal import Decimal

from django.db import models
from django.utils import timezone

from user.models import User, Company


class APIKey(models.Model):

    key = models.UUIDField(default=uuid.uuid4, unique=True, editable=False)
    company = models.ForeignKey(Company, on_delete=models.CASCADE)
    created_at = models.DateTimeField(auto_now_add=True)
    is_active = models.BooleanField(default=True)

    def __str__(self):

        return f'APIKey {self.key} for {self.company.name}'



class PaymentMethod(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    name = models.CharField(max_length=100)
    description = models.TextField()
    is_active = models.BooleanField(default=True)

    def __str__(self):
        return self.name


class Invoice(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    amount = models.DecimalField(max_digits=20, decimal_places=8)
    amount_currency = models.CharField(max_length=10, blank=True, null=True)
    required_method = models.CharField(max_length=50, blank=True, null=True)
    type = models.CharField(max_length=20)
    description = models.TextField(blank=True, null=True)
    redirect_url = models.URLField(blank=True, null=True)
    callback_url = models.URLField(blank=True, null=True)
    extra = models.TextField(blank=True, null=True)
    payer_details = models.CharField(max_length=100, blank=True, null=True)
    lifetime = models.IntegerField()
    created_at = models.DateTimeField(auto_now_add=True)
    status = models.CharField(max_length=20, default='created')

    def __str__(self):
        return f"Invoice {self.id} - {self.status}"


class Withdrawal(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    amount = models.DecimalField(max_digits=20, decimal_places=8)
    currency = models.CharField(max_length=10)
    method = models.CharField(max_length=50)
    created_at = models.DateTimeField(auto_now_add=True)
    status = models.CharField(max_length=20)

    def __str__(self):

        return f"Withdrawal {self.id} - {self.status}"



class WithdrawalRequest(models.Model):
    PAYMENT_METHOD_CHOICES = [
        ('LZTMARKET', 'LZTMARKET'),
        ('BITCOIN', 'BITCOIN'),
        ('ETHEREUM', 'ETHEREUM'),
        # Добавьте другие методы, если необходимо
    ]

    SUBTRACT_FROM_CHOICES = [
        ('balance', 'Balance'),
        ('amount', 'Amount'),
    ]

    user = models.ForeignKey(User, on_delete=models.CASCADE)
    company = models.ForeignKey(Company, on_delete=models.CASCADE)
    auth_login = models.CharField(max_length=255)
    auth_secret = models.CharField(max_length=255)
    signature = models.CharField(max_length=255)
    amount = models.DecimalField(max_digits=20, decimal_places=2)
    amount_currency = models.CharField(max_length=10, null=True, blank=True)
    method = models.CharField(max_length=50, choices=PAYMENT_METHOD_CHOICES)
    wallet = models.CharField(max_length=255)
    subtract_from = models.CharField(max_length=10, choices=SUBTRACT_FROM_CHOICES)
    callback_url = models.URLField(null=True, blank=True)
    extra = models.CharField(max_length=255, null=True, blank=True)
    commission = models.DecimalField(max_digits=20, decimal_places=8, default=0.0)
    rub_amount = models.DecimalField(max_digits=20, decimal_places=2, null=True, blank=True)
    receive_amount = models.DecimalField(max_digits=20, decimal_places=8, null=True, blank=True)
    deduction_amount = models.DecimalField(max_digits=20, decimal_places=8, null=True, blank=True)
    currency = models.CharField(max_length=10, null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    status = models.CharField(max_length=50, default='created')

    def set_payed_and_deduct_balance(self):
        if self.status == 'created':
            total_deduction = self.deduction_amount + (self.commission / Decimal('100'))
            if self.user.balance >= total_deduction:
                self.user.balance -= total_deduction
                self.user.save()
                self.status = 'payed'
                self.save()
            else:
                raise ValueError("Insufficient balance to pay the withdrawal request")

    def __str__(self):
        return f"{self.user.email} - {self.amount} {self.amount_currency} - {self.method}"

