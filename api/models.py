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


class Payment(models.Model):
    STATUS_CHOICES = [
        ('created', 'Created'),
        ('processed', 'Processed'),
        ('canceled', 'Canceled'),
        ('completed', 'Completed'),
    ]

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    user = models.ForeignKey(User, on_delete=models.CASCADE)  # Добавляем это поле
    amount = models.DecimalField(max_digits=10, decimal_places=2)
    currency = models.CharField(max_length=10, default="KGS")
    description = models.TextField()
    client_data = models.JSONField(default={})
    status = models.CharField(max_length=10, choices=STATUS_CHOICES, default='created')
    created_at = models.DateTimeField(default=timezone.now)

    def __str__(self):
        return f"Payment {self.id} - {self.status}"


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