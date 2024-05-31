from django.contrib.auth.base_user import BaseUserManager
from django.contrib.auth.models import AbstractUser
from django.db import models
from django.utils import timezone
from .enum import Role

class UserManager(BaseUserManager):
    use_in_migrations = True

    def create_user(self, email, password=None, **kwargs):
        if not email:
            raise ValueError("Email is required")
        email = self.normalize_email(email)
        user = self.model(email=email, **kwargs)
        user.set_password(password)
        user.type = Role.USER.value
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
    username = models.CharField(max_length=256)
    email = models.EmailField(unique=True)
    phone = models.CharField(max_length=50)
    # photo = models.ImageField(upload_to='user_photos/', null=True, blank=True, verbose_name="Фото",
    #                           default='DEFAULTS/DEFAULT_IMAGE.png')
    type = models.CharField(
        verbose_name="Тип пользователя",
        choices=Role.choices(),
        max_length=32,
        null=True
    )
    is_active = models.BooleanField(default=True)
    is_staff = models.BooleanField(default=False)
    is_email = models.BooleanField(default=False)
    date_joined = models.DateTimeField(default=timezone.now)
    USERNAME_FIELD = 'email'
    REQUIRED_FIELDS = ['phone', 'username']
    objects = UserManager()

    def __str__(self):
        return self.email
