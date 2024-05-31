from abc import ABC

from django.contrib.auth.password_validation import validate_password
from django.shortcuts import get_object_or_404
from rest_framework import serializers
from rest_framework.validators import UniqueValidator
from rest_framework_simplejwt.serializers import TokenObtainPairSerializer
from rest_framework_simplejwt.tokens import RefreshToken

from user.enum import Role
from user.models import User


class MyTokenObtainPairSerializer(TokenObtainPairSerializer):
    @classmethod
    def get_token(cls, user):
        token = super().get_token(user)

        # Add custom claims
        token['username'] = user.username
        token['email'] = user.email
        # ...

        return token


class RegisterSerializer(serializers.ModelSerializer):
    password = serializers.CharField(
        write_only=True, required=True,
        help_text="Пароль для нового пользователя."
    )
    email = serializers.EmailField(
        required=True,
        validators=[UniqueValidator(queryset=User.objects.all())],
        help_text="Адрес электронной почты нового пользователя."
    )
    username = serializers.CharField(
        help_text="Имя пользователя."
    )
    phone = serializers.CharField(
        help_text="Номер телефона пользователя."
    )

    class Meta:
        model = User
        fields = ('username', 'email', 'phone', 'password')

    def create(self, validated_data):
        """
        Создать нового пользователя.

        Параметры:
        - username (str): Имя пользователя.
        - email (str): Адрес электронной почты.
        - phone (str): Номер телефона.
        - password (str): Пароль.

        Пример запроса:
        POST /register/
        {
            "username": "john_doe",
            "email": "johndoe@example.com",
            "phone": "+1234567890",
            "password": "securepassword"
        }

        Пример ответа:
        {
            "username": "john_doe",
            "email": "johndoe@example.com",
            "phone": "+1234567890"
        }
        """
        user = User.objects.create_user(
            username=validated_data['username'],
            email=validated_data['email'],
            phone=validated_data['phone']
        )

        user.set_password(validated_data['password'])
        user.type = Role.USER
        user.save()

        refresh = RefreshToken.for_user(user)
        self.tokens = {

            'refresh': str(refresh),
            'access': str(refresh.access_token),
        }

        return user

    #Метод для возврата только токенов
    def to_representation(self, instance):
        return self.tokens

class EmailSerializer(serializers.Serializer):
    email = serializers.EmailField()

class ChangePasswordSerializer(serializers.Serializer):
    old_password = serializers.CharField(required=True)
    new_password = serializers.CharField(required=True)

class ResetPasswordSerializer(serializers.Serializer):
    new_password = serializers.CharField(write_only=True)