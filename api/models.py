import secrets
import uuid
from django.db import models
from django.utils import timezone

from user.models import User


class APIKey(models.Model):
    secret = models.UUIDField(default=uuid.uuid4, unique=True, editable=False)
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    created_at = models.DateTimeField(auto_now_add=True)
    is_active = models.BooleanField(default=True)

    def __str__(self):
        return f'APIKey {self.secret} for {self.user.email}'


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
