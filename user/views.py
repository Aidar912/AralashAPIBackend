import uuid

from django.core.cache import cache
from django.core.exceptions import ValidationError
from django.core.mail import send_mail
from django.shortcuts import render, redirect
from django.urls import reverse
from drf_yasg import openapi
from drf_yasg.utils import swagger_auto_schema
from rest_framework import generics, status
from rest_framework.permissions import AllowAny, IsAuthenticated
from rest_framework.response import Response
from rest_framework.views import APIView
from rest_framework_simplejwt.tokens import RefreshToken
from rest_framework_simplejwt.views import TokenObtainPairView, TokenRefreshView

from AralashAPI.settings import FRONTEND_BASE_URL, EMAIL_HOST_USER
from user.models import User
from user.serializers import MyTokenObtainPairSerializer, RegisterSerializer, ChangePasswordSerializer, \
    EmailSerializer, ResetPasswordSerializer


# Create your views here.



class MyTokenObtainPairView(TokenObtainPairView):
    serializer_class = MyTokenObtainPairSerializer

    @swagger_auto_schema(
        operation_description="Get JWT token pair",
        responses={200: 'JWT Token'},
        tags=["Authentication"]
    )
    def post(self, request, *args, **kwargs):
        return super().post(request, *args, **kwargs)

# Register User
class RegisterView(generics.CreateAPIView):
    queryset = User.objects.all()
    permission_classes = (AllowAny,)
    serializer_class = RegisterSerializer
    pagination_class = None

    @swagger_auto_schema(
        operation_description="Register a new user",
        tags=["Registration"]
    )
    def post(self, request, *args, **kwargs):
        return super().post(request, *args, **kwargs)


class UserTokenRefreshView(TokenRefreshView):
    @swagger_auto_schema(
        operation_description="Refresh JWT token",
        tags=["Authentication"],
        responses={200: 'Token refreshed'}
    )
    def post(self, request, *args, **kwargs):
        """
        This endpoint allows users to refresh their JWT token.
        """
        return super().post(request, *args, **kwargs)

class StartRegistrationView(APIView):
    """
    Представление для начала регистрации пользователя.
    Отправляет письмо с подтверждением на указанный email.
    """

    @swagger_auto_schema(tags=["User"],request_body=EmailSerializer)
    def post(self, request):
        # Извлечение email из тела запроса
        email = request.data.get('email')

        # Проверка, указан ли email
        if not email:
            return Response({'error': 'Email address is required.'}, status=status.HTTP_400_BAD_REQUEST)

        # Проверка, существует ли пользователь с таким email и верифицирован ли он
        existing_user = User.objects.filter(email=email).first()
        if existing_user and existing_user.is_email:
            return Response({'error': 'A user with that email already exists and is verified.'},
                            status=status.HTTP_400_BAD_REQUEST)

        # Создание уникального токена для подтверждения регистрации
        token = str(uuid.uuid4())

        # Генерация URL для подтверждения регистрации
        confirm_url = request.build_absolute_uri(reverse('confirm_registration', args=[token]))

        # Сохранение токена и email в кэше с таймаутом 1800 секунд (30 минут)
        cache.set(token, email, timeout=1800)

        # Отправка письма с ссылкой для подтверждения email
        send_mail(
            'Confirm Your Email Address',
            f'Please follow this link to confirm your email address: {confirm_url}',
            EMAIL_HOST_USER,
            [email],
            fail_silently=False,
        )

        # Возврат успешного ответа
        return Response({'message': 'A confirmation email has been sent. Please check your inbox to continue'},
                        status=status.HTTP_200_OK)

class ConfirmRegistrationView(APIView):
    """
    Представление для подтверждения регистрации пользователя.
    Проверяет токен, активирует учетную запись пользователя и перенаправляет на соответствующую страницу.
    """

    @swagger_auto_schema(tags=["User"],manual_parameters=[
        openapi.Parameter('token', openapi.IN_PATH, description="Токен подтверждения", type=openapi.TYPE_STRING)
    ])
    def get(self, request, token):
        # Получение email из кэша по токену
        email = cache.get(token)

        # Проверка, существует ли email в кэше
        if email:
            try:
                # Поиск пользователя по email
                user = User.objects.get(email=email)
                user.is_email = True  # Установка флага подтверждения email

                try:
                    # Сохранение изменений пользователя
                    user.save()

                    # Перенаправление на страницу успешной регистрации
                    redirect_url = f"{FRONTEND_BASE_URL}/registration-success"
                    return redirect(redirect_url)
                except Exception as e:
                    # В случае ошибки сохранения, перенаправление на страницу ошибки
                    error_url = f"{FRONTEND_BASE_URL}/error?message={str(e)}"
                    return redirect(error_url)
            except User.DoesNotExist:
                # Если пользователь с таким email не существует, перенаправление на страницу ошибки
                error_url = f"{FRONTEND_BASE_URL}/error?message=User does not exist."
                return redirect(error_url)
        else:
            # Если токен недействителен или истек, перенаправление на страницу ошибки
            error_url = f"{FRONTEND_BASE_URL}/error?message=Invalid or expired link."
            return redirect(error_url)

class ChangeEmailView(APIView):
    """
    Представление для изменения электронной почты пользователя.
    Отправляет письмо с подтверждением на новый email.
    """

    # Ограничение доступа только для аутентифицированных пользователей
    permission_classes = [IsAuthenticated]

    @swagger_auto_schema(tags=["User"],request_body=EmailSerializer)
    def post(self, request):
        # Извлечение нового email из тела запроса
        email = request.data.get('email')

        # Проверка, указан ли email
        if not email:
            return Response({'error': 'Email address is required.'}, status=status.HTTP_400_BAD_REQUEST)

        # Создание уникального токена для подтверждения изменения email
        token = str(uuid.uuid4())

        # Генерация URL для подтверждения изменения email
        confirm_url = f"{FRONTEND_BASE_URL}/confirm-email?token={token}"

        # Сохранение токена и нового email в кэше с таймаутом 1800 секунд (30 минут)
        cache.set(token, email, timeout=1800)

        # Отправка письма с ссылкой для подтверждения нового email
        send_mail(
            'Confirm Your Email Address',
            f'Please follow this link to confirm your email address and continue registration: {confirm_url}',
            EMAIL_HOST_USER,
            [email],
            fail_silently=False,
        )

        # Возврат успешного ответа
        return Response(
            {'message': 'A confirmation email has been sent. Please check your inbox to continue registration.'},
            status=status.HTTP_200_OK)

class ChangePasswordView(APIView):
    """
      Представление для смены пароля.
      Отправляет письмо с подтверждением на указанный email.
      """

    permission_classes = (IsAuthenticated,)

    @swagger_auto_schema(tags=["User"],
        request_body=ChangePasswordSerializer,
        responses={200: 'Password updated successfully'}
    )
    def post(self, request, *args, **kwargs):
        """
        Change user password

        An endpoint for changing password.

        Parameters:
        - old_password: string
        - new_password: string
        """
        serializer = ChangePasswordSerializer(data=request.data)
        if serializer.is_valid():
            user = request.user
            if not user.check_password(serializer.data.get("old_password")):
                return Response({"old_password": ["Wrong password."]},
                                status=status.HTTP_400_BAD_REQUEST)
            user.set_password(serializer.data.get("new_password"))
            user.save()
            return Response(status=status.HTTP_204_NO_CONTENT)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

class SendResetEmailView(APIView):

    @swagger_auto_schema(tags=["User"],request_body=EmailSerializer)
    def post(self, request):
        email = request.data.get('email')
        if not email:
            return Response({'error': 'Email address is required.'}, status=status.HTTP_400_BAD_REQUEST)

        user = User.objects.filter(email=email).first()
        if user is None:
            return Response({'error': 'User with this email does not exist.'}, status=status.HTTP_404_NOT_FOUND)

        token = str(uuid.uuid4())
        reset_url = f"{FRONTEND_BASE_URL}/new-password?token={token}"
        cache.set(token, email, timeout=1800)

        try:
            send_mail(
                'Password Reset',
                f'Follow this link to reset your password: {reset_url}',
                EMAIL_HOST_USER,
                [email],
                fail_silently=False,
            )
        except Exception as e:
            return Response({'error': str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

        return Response({'message': 'Password reset email sent.'}, status=status.HTTP_200_OK)

class ResetPasswordConfirmView(APIView):
    """
    Представление для сброса пароля пользователя.
    Проверяет токен, обновляет пароль пользователя.
    """

    @swagger_auto_schema(tags=["User"],request_body=ResetPasswordSerializer, manual_parameters=[
        openapi.Parameter('token', openapi.IN_PATH, description="Токен сброса пароля", type=openapi.TYPE_STRING)
    ])
    def post(self, request, token):
        email = cache.get(token)
        new_password = request.data.get('new_password')

        if not email:
            return Response({'error': 'Invalid or expired token.'}, status=status.HTTP_400_BAD_REQUEST)
        if not new_password:
            return Response({'error': 'Password required.'}, status=status.HTTP_400_BAD_REQUEST)

        try:
            user = User.objects.get(email=email)
        except User.DoesNotExist:
            return Response({'error': 'User with this email does not exist.'}, status=status.HTTP_404_NOT_FOUND)

        try:
            user.set_password(new_password)
            user.save()
        except ValidationError as e:
            return Response({'error': e.messages}, status=status.HTTP_400_BAD_REQUEST)

        return Response({'message': 'Password has been reset.'}, status=status.HTTP_200_OK)


class ConfirmEmailChangeView(APIView):
    permission_classes = [IsAuthenticated]

    @swagger_auto_schema(tags=["User"],request_body=EmailSerializer)
    def post(self, request, token):
        try:
            user = User.objects.get(email=request.data.get('email'))
        except User.DoesNotExist:
            return Response({'error': 'User not found.'}, status=status.HTTP_404_NOT_FOUND)

        cache_token = cache.get(token)
        if cache_token:
            user.email = request.data.get('new_email')
            try:
                user.save()
                refresh = RefreshToken.for_user(user)
                return Response({
                    'message': 'Email address has been successfully updated.',
                    'refresh': str(refresh),
                    'access': str(refresh.access_token),
                }, status=status.HTTP_200_OK)
            except Exception as e:
                return Response({'error': str(e)}, status=status.HTTP_400_BAD_REQUEST)
        else:
            return Response({'error': 'Invalid or expired link'}, status=status.HTTP_400_BAD_REQUEST)