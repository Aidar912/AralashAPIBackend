from django.shortcuts import get_object_or_404
from rest_framework.pagination import PageNumberPagination
from rest_framework.views import APIView
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework import status

from .authentication import APIKeyAuthentication
from .models import APIKey, Payment
from .serializers import PaymentSerializer


class GenerateKeyView(APIView):
    permission_classes = [IsAuthenticated]

    def post(self, request):
        user = request.user
        api_key = APIKey.objects.create(user=user)
        return Response({
            'api_key': str(api_key.key),
            'secret_key': api_key.secret_key
        }, status=status.HTTP_201_CREATED)


class CheckKeyView(APIView):
    permission_classes = [IsAuthenticated]

    def post(self, request):
        key_value = request.data.get('key')
        secret_value = request.data.get('secret_key')
        try:
            key = APIKey.objects.get(key=key_value, secret_key=secret_value, user=request.user, is_active=True)
            return Response({'valid': True}, status=status.HTTP_200_OK)
        except APIKey.DoesNotExist:
            return Response({'valid': False}, status=status.HTTP_404_NOT_FOUND)


class RegenerateKeyView(APIView):
    permission_classes = [IsAuthenticated]

    def post(self, request):
        key_value = request.data.get('key')
        try:
            old_key = APIKey.objects.get(key=key_value, user=request.user, is_active=True)
            old_key.is_active = False
            old_key.save()
            new_key = APIKey.objects.create(user=request.user)
            return Response({
                'new_api_key': str(new_key.key),
                'secret_key': new_key.secret_key
            }, status=status.HTTP_201_CREATED)
        except APIKey.DoesNotExist:
            return Response({'error': 'API key not found or inactive'}, status=status.HTTP_404_NOT_FOUND)


class DeactivateKeyView(APIView):
    permission_classes = [IsAuthenticated]

    def post(self, request):
        key_value = request.data.get('key')
        try:
            key = APIKey.objects.get(key=key_value, user=request.user)
            key.is_active = False
            key.save()
            return Response({'message': 'API key deactivated'}, status=status.HTTP_200_OK)
        except APIKey.DoesNotExist:
            return Response({'error': 'API key not found'}, status=status.HTTP_404_NOT_FOUND)


class CreatePaymentView(APIView):
    authentication_classes = [APIKeyAuthentication]
    permission_classes = [IsAuthenticated]

    def post(self, request):
        user = request.user
        data = request.data
        data['user'] = user.id  # Устанавливаем пользователя
        serializer = PaymentSerializer(data=data)
        if serializer.is_valid():
            payment = serializer.save()
            return Response({'id': payment.id, 'status': payment.status}, status=status.HTTP_201_CREATED)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


class PaymentStatusView(APIView):
    authentication_classes = [APIKeyAuthentication]
    permission_classes = [IsAuthenticated]

    def get(self, request, payment_id):
        user = request.user
        payment = get_object_or_404(Payment, id=payment_id, user=user)
        return Response({'id': payment.id, 'status': payment.status})


class CancelPaymentView(APIView):
    authentication_classes = [APIKeyAuthentication]
    permission_classes = [IsAuthenticated]

    def post(self, request, payment_id):
        user = request.user
        payment = get_object_or_404(Payment, id=payment_id, user=user)
        payment.status = 'canceled'
        payment.save()
        return Response({'id': payment.id, 'status': payment.status})


class PaymentHistoryView(APIView):
    authentication_classes = [APIKeyAuthentication]
    permission_classes = [IsAuthenticated]

    def get(self, request):
        user = request.user
        payments = Payment.objects.filter(user=user).order_by('-created_at')
        paginator = PageNumberPagination()
        paginated_payments = paginator.paginate_queryset(payments, request)
        serializer = PaymentSerializer(paginated_payments, many=True)
        return paginator.get_paginated_response(serializer.data)
