from datetime import datetime
from django.contrib.auth.base_user import BaseUserManager
from django.contrib.auth.models import AbstractUser
from django.db import models
from django.utils import timezone
from django.utils.timezone import now
from django.db.models.signals import pre_save
from django.dispatch import receiver

from AralashAPI import settings  # Update to your app name
from .enum import Role


class UserManager(BaseUserManager):
    use_in_migrations = True

    def create_user(self, email, password=None, **kwargs):
        if not email:
            raise ValueError("Email is required")
        email = self.normalize_email(email)
        user = self.model(email=email, **kwargs)
        user.set_password(password)
        user.save(using=self._db)
        return user

    def create_superuser(self, email, password=None, **kwargs):
        if not email:
            raise ValueError("Email is required")
        kwargs['is_staff'] = True
        kwargs['is_superuser'] = True
        email = self.normalize_email(email)
        user = self.model(email=email, **kwargs)
        user.set_password(password)
        user.type = Role.ADMIN.value
        user.save(using=self._db)
        return user


class User(AbstractUser):
    username = models.CharField(max_length=256, null=True)
    email = models.EmailField(unique=True)
    phone = models.CharField(max_length=50, null=True)
    photo = models.ImageField(upload_to='user_photos/', null=True, blank=True, verbose_name="Фото")
    type = models.CharField(
        verbose_name="Тип пользователя",
        choices=Role.choices(),
        max_length=32,
        default=Role.USER.value,
        null=True
    )
    is_active = models.BooleanField(default=True)
    is_staff = models.BooleanField(default=False)
    is_email = models.BooleanField(default=False)
    balance = models.DecimalField(max_digits=10, decimal_places=2, default=0.0)
    date_joined = models.DateTimeField(default=timezone.now)
    requests_made_this_month = models.IntegerField(default=0)
    USERNAME_FIELD = 'email'
    REQUIRED_FIELDS = ['phone', 'username']
    objects = UserManager()

    def get_current_month(self):
        return datetime(now().year, now().month, 1)

    def get_or_create_monthly_statistics(self):
        current_month = self.get_current_month()
        stats, created = MonthlyUserStatistics.objects.get_or_create(user=self, month=current_month)
        return stats

    def reset_request_count(self):
        current_month = self.get_current_month()
        MonthlyUserStatistics.objects.filter(user=self, month=current_month).update(requests_made=0)

    def increment_request_count(self):
        stats = self.get_or_create_monthly_statistics()
        stats.requests_made += 1
        stats.save()

    def can_make_request(self):
        stats = self.get_or_create_monthly_statistics()
        return stats.requests_remaining() > 0

    def __str__(self):
        return self.email


@receiver(pre_save, sender=User)
def set_default_photo(sender, instance, **kwargs):
    if not instance.photo:
        instance.photo = f'http://{settings.SERVER_IP}/{settings.MEDIA_URL}DEFAULTS/DEFAULT_IMAGE.png'


class Subscription(models.Model):
    PLAN_CHOICES = [
        ('FREE', 'Free'),
        ('BASIC', 'Basic'),
        ('PREMIUM', 'Premium'),
    ]

    name = models.CharField(max_length=50, choices=PLAN_CHOICES, default='FREE')
    max_requests_per_month = models.IntegerField(default=1000)
    price = models.DecimalField(max_digits=10, decimal_places=2, default=0.00)
    created_at = models.DateTimeField(default=timezone.now)

    def __str__(self):
        return self.name


class MonthlyUserStatistics(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    month = models.DateField()
    requests_made = models.IntegerField(default=0)

    class Meta:
        unique_together = ('user', 'month')

    def requests_remaining(self):
        return self.requests_made

    def __str__(self):
        return f"Statistics for {self.user.email} - {self.month.strftime('%B %Y')}"


class BusinessType(models.Model):
    name = models.CharField(max_length=255, unique=True)
    code = models.CharField(max_length=10, unique=True)
    description = models.TextField(null=True, blank=True)

    def __str__(self):
        return self.name


class Company(models.Model):
    name = models.CharField(max_length=255)
    business_type = models.ForeignKey(BusinessType, on_delete=models.PROTECT)
    registration_number = models.CharField(max_length=100, unique=True)
    address = models.CharField(max_length=255)
    created_at = models.DateTimeField(default=timezone.now)
    updated_at = models.DateTimeField(auto_now=True)
    subscription = models.ForeignKey(Subscription, on_delete=models.SET_NULL, null=True, blank=True)
    requests_made_this_month = models.IntegerField(default=0)

    def get_current_month(self):
        now = timezone.now()
        return datetime(now.year, now.month, 1, tzinfo=now.tzinfo)

    def get_or_create_monthly_statistics(self):
        current_month = self.get_current_month()
        stats, created = MonthlyCompanyStatistics.objects.get_or_create(company=self, month=current_month)
        return stats

    def reset_request_count(self):
        current_month = self.get_current_month()
        MonthlyCompanyStatistics.objects.filter(company=self, month=current_month).update(requests_made=0)

    def increment_request_count(self):
        stats = self.get_or_create_monthly_statistics()
        stats.requests_made += 1
        stats.save()

    def can_make_request(self):
        stats = self.get_or_create_monthly_statistics()
        if self.subscription:
            return stats.requests_remaining() > 0
        return False

    def __str__(self):
        return self.name


class UserCompanyRelation(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    company = models.ForeignKey(Company, on_delete=models.CASCADE)
    is_verified = models.BooleanField(default=False)
    verified_at = models.DateTimeField(null=True, blank=True)
    created_at = models.DateTimeField(default=timezone.now)

    class Meta:
        unique_together = ('user', 'company')

    def __str__(self):
        return f"{self.user.email} - {self.company.name}"


class MonthlyCompanyStatistics(models.Model):
    company = models.ForeignKey(Company, on_delete=models.CASCADE)
    month = models.DateField()
    requests_made = models.IntegerField(default=0)

    def requests_remaining(self):
        return self.company.subscription.max_requests_per_month - self.requests_made

    def __str__(self):
        return f"{self.company.name} - {self.month.strftime('%B %Y')}"


class SubscriptionHistory(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    company = models.ForeignKey('Company', on_delete=models.CASCADE)
    subscription = models.ForeignKey('Subscription', on_delete=models.CASCADE)
    amount = models.DecimalField(max_digits=10, decimal_places=2)
    date = models.DateTimeField(default=timezone.now)

    def __str__(self):
        return f"{self.user.email} - {self.company.name} - {self.subscription.name} - {self.amount}"

