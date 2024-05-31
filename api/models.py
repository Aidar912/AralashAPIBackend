import secrets
import uuid
from django.db import models
from django.utils import timezone

from user.models import User


class APIKey(models.Model):
    key = models.UUIDField(default=uuid.uuid4, unique=True, editable=False)
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    created_at = models.DateTimeField(auto_now_add=True)
    is_active = models.BooleanField(default=True)

    def __str__(self):
        return f'APIKey {self.key} for {self.user.email}'


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
    client_data = models.JSONField(default=dict)
    status = models.CharField(max_length=10, choices=STATUS_CHOICES, default='created')
    created_at = models.DateTimeField(default=timezone.now)

    def __str__(self):
        return f"Payment {self.id} - {self.status}"
