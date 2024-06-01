from decimal import Decimal

import requests
from rest_framework import generics, status
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from drf_yasg.utils import swagger_auto_schema
from drf_yasg import openapi

from rest_framework import generics
from user.models import Subscription, Company, SubscriptionHistory
from user.serializers import SubscriptionSerializer, CompanySerializer, SubscriptionHistorySerializer


from django.shortcuts import get_object_or_404
from rest_framework.pagination import PageNumberPagination
from rest_framework.views import APIView
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework import status

from .authentication import APIKeyAuthentication
from .models import APIKey, Payment, WithdrawalRequest
from .serializers import PaymentSerializer, WithdrawalRequestSerializer, ConfirmWithdrawalRequestSerializer, \
    CancelWithdrawalRequestSerializer, GetWithdrawalRequestSerializer
from .utils import verify_key


class SubscriptionCreateView(generics.CreateAPIView):
    queryset = Subscription.objects.all()
    serializer_class = SubscriptionSerializer


class SubscriptionListView(generics.ListAPIView):
    queryset = Subscription.objects.all()
    serializer_class = SubscriptionSerializer


class SubscriptionDetailView(generics.RetrieveAPIView):
    queryset = Subscription.objects.all()
    serializer_class = SubscriptionSerializer


class SubscriptionUpdateView(generics.UpdateAPIView):
    queryset = Subscription.objects.all()
    serializer_class = SubscriptionSerializer


class SubscriptionDeleteView(generics.DestroyAPIView):
    queryset = Subscription.objects.all()
    serializer_class = SubscriptionSerializer


class GenerateKeyView(APIView):
    permission_classes = [IsAuthenticated]

    @swagger_auto_schema(
        tags=["Key"],
        operation_description="Generate a new API key and secret key for the authenticated user",
        request_body=openapi.Schema(
            type=openapi.TYPE_OBJECT,
            properties={
                'company_name': openapi.Schema(type=openapi.TYPE_STRING, description='company_name')
            }
        ),
        responses={
            201: 'API key and secret key successfully generated',
            400: 'Company not found'
        }
    )
    def post(self, request):
        user = request.user
        company_name = request.data.get('company_name')

        if not company_name:
            return Response({
                'error': 'Company name is required'
            }, status=status.HTTP_400_BAD_REQUEST)

        try:
            company = Company.objects.get(name=company_name, usercompanyrelation__user=user)
        except Company.DoesNotExist:
            return Response({
                'error': 'Company not found or not associated with the user'
            }, status=status.HTTP_400_BAD_REQUEST)

        api_key = APIKey.objects.create(company=company)
        return Response({
            'api_key': str(api_key.key),
        }, status=status.HTTP_201_CREATED)

class CheckKeyView(APIView):
    permission_classes = [IsAuthenticated]

    @swagger_auto_schema(
        tags=["Key"],
        operation_description="Check if the provided API key and secret key are valid for the authenticated user",
        request_body=openapi.Schema(
            type=openapi.TYPE_OBJECT,
            properties={
                'key': openapi.Schema(type=openapi.TYPE_STRING, description='API key'),
            }
        ),
        responses={
            200: 'API key and secret key are valid',
            404: 'API key and secret key are invalid'
        }
    )
    def post(self, request):
        key_value = request.data.get('key')
        try:
            api_key = APIKey.objects.get(key=key_value, company__usercompanyrelation__user=request.user, is_active=True)
            return Response({'valid': True}, status=status.HTTP_200_OK)
        except APIKey.DoesNotExist:
            return Response({'valid': False}, status=status.HTTP_404_NOT_FOUND)

class RegenerateKeyView(APIView):
    permission_classes = [IsAuthenticated]

    @swagger_auto_schema(
        tags=["Key"],
        operation_description="Regenerate a new API key and deactivate the old one",
        request_body=openapi.Schema(
            type=openapi.TYPE_OBJECT,
            properties={
                'key': openapi.Schema(type=openapi.TYPE_STRING, description='Old API key')
            }
        ),
        responses={
            201: 'New API key and secret key successfully generated',
            404: 'Old API key not found or inactive'
        }
    )
    def post(self, request):
        key_value = request.data.get('key')
        try:
            old_key = APIKey.objects.get(key=key_value, company__usercompanyrelation__user=request.user, is_active=True)
            old_key.is_active = False
            old_key.save()
            new_key = APIKey.objects.create(company=old_key.company)
            return Response({
                'new_api_key': str(new_key.key),
            }, status=status.HTTP_201_CREATED)
        except APIKey.DoesNotExist:
            return Response({'error': 'API key not found or inactive'}, status=status.HTTP_404_NOT_FOUND)


class DeactivateKeyView(APIView):
    permission_classes = [IsAuthenticated]

    @swagger_auto_schema(
        tags=["Key"],
        operation_description="Deactivate an existing API key",
        request_body=openapi.Schema(
            type=openapi.TYPE_OBJECT,
            properties={
                'key': openapi.Schema(type=openapi.TYPE_STRING, description='API key to be deactivated')
            }
        ),
        responses={
            200: 'API key successfully deactivated',
            404: 'API key not found'
        }
    )
    def post(self, request):
        key_value = request.data.get('key')
        try:
            api_key = APIKey.objects.get(key=key_value, company__usercompanyrelation__user=request.user)
            api_key.is_active = False
            api_key.save()
            return Response({'message': 'API key deactivated'}, status=status.HTTP_200_OK)
        except APIKey.DoesNotExist:
            return Response({'error': 'API key not found'}, status=status.HTTP_404_NOT_FOUND)


class CreatePaymentView(APIView):
    authentication_classes = [APIKeyAuthentication]
    permission_classes = [IsAuthenticated]

    @swagger_auto_schema(
        tags=["Payment"],
        operation_description="Create a new payment",
        request_body=PaymentSerializer,
        responses={
            201: openapi.Response('Payment created successfully', PaymentSerializer),
            400: 'Invalid data'
        }
    )
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

    @swagger_auto_schema(
        tags=["Payment"],
        operation_description="Get the status of a specific payment",
        responses={
            200: openapi.Response('Payment status retrieved successfully', PaymentSerializer),
            404: 'Payment not found'
        }
    )
    def get(self, request, payment_id):
        user = request.user
        payment = get_object_or_404(Payment, id=payment_id, user=user)
        return Response({'id': payment.id, 'status': payment.status})


class CancelPaymentView(APIView):
    authentication_classes = [APIKeyAuthentication]
    permission_classes = [IsAuthenticated]

    @swagger_auto_schema(
        tags=["Payment"],
        operation_description="Cancel a specific payment",
        responses={
            200: openapi.Response('Payment canceled successfully', PaymentSerializer),
            404: 'Payment not found'
        }
    )
    def post(self, request, payment_id):
        user = request.user
        payment = get_object_or_404(Payment, id=payment_id, user=user)
        payment.status = 'canceled'
        payment.save()
        return Response({'id': payment.id, 'status': payment.status})


class PaymentHistoryView(APIView):
    authentication_classes = [APIKeyAuthentication]
    permission_classes = [IsAuthenticated]

    @swagger_auto_schema(
        tags=["Payment"],
        operation_description="Get the payment history of the authenticated user",
        responses={
            200: openapi.Response('Payment history retrieved successfully', PaymentSerializer(many=True))
        }
    )
    def get(self, request):
        user = request.user
        payments = Payment.objects.filter(user=user).order_by('-created_at')
        paginator = PageNumberPagination()
        paginated_payments = paginator.paginate_queryset(payments, request)
        serializer = PaymentSerializer(paginated_payments, many=True)
        return paginator.get_paginated_response(serializer.data)

class ChangeSubscriptionView(generics.UpdateAPIView):
    queryset = Company.objects.all()
    serializer_class = CompanySerializer
    permission_classes = [IsAuthenticated]

    @swagger_auto_schema(tags=["subscriptions"])
    def patch(self, request, *args, **kwargs):
        company = self.get_object()
        serializer = self.get_serializer(company, data=request.data, partial=True)
        serializer.is_valid(raise_exception=True)
        serializer.save()

        subscription = company.subscription

        # Create subscription history record
        SubscriptionHistory.objects.create(
            user=request.user,
            company=company,
            subscription=subscription,
            amount=subscription.price
        )

        return Response({"message": "Subscription updated successfully"}, status=status.HTTP_200_OK)

    @swagger_auto_schema(tags=["subscriptions"])
    def put(self, request, *args, **kwargs):
        return super().put(request,*args,**kwargs)

class SubscriptionHistoryListView(generics.ListAPIView):
    serializer_class = SubscriptionHistorySerializer
    permission_classes = [IsAuthenticated]

    @swagger_auto_schema(tags=["Subscription History"])
    def get(self, request, *args, **kwargs):
        return super().get(request, *args, **kwargs)

    def get_queryset(self):
        return SubscriptionHistory.objects.filter(user=self.request.user).order_by('-date')



class WithdrawalRequestView(APIView):
    permission_classes = [IsAuthenticated]

    @swagger_auto_schema(tags=["Conclusion"], request_body=WithdrawalRequestSerializer)
    def post(self, request):

        auth_login = request.data.get('auth_login')
        auth_secret = request.data.get('auth_secret')

        is_valid, user, company = verify_key(auth_login, auth_secret)

        company.increment_request_count()
        user.increment_request_count()
        if not is_valid:

            return Response(
                {
                    "status": "failed",
                    "message": "Invalid credentials"
                },
                status=status.HTTP_400_BAD_REQUEST
            )

        if not company.can_make_request():
            return Response(
                {
                    "status": "failed",
                    "message": "Request limit reached for this month"
                },
                status=status.HTTP_400_BAD_REQUEST
            )

        amount = Decimal(request.data.get('amount'))
        subtract_from = request.data.get('subtract_from')
        commission_percentage = Decimal('0.015')  # Пример комиссии 1.5%, можете заменить на вашу логику расчета
        commission = amount * commission_percentage

        serializer = WithdrawalRequestSerializer(data=request.data)
        if serializer.is_valid():
            withdrawal_request = serializer.save(
                user=user,
                company=company,
                commission=commission,
                deduction_amount=amount + commission if subtract_from == 'balance' else amount
            )

            # Отправка callback запроса
            callback_url = withdrawal_request.callback_url
            if callback_url:
                callback_data = {
                    "status": "created",
                    "id": withdrawal_request.id,
                    "method": withdrawal_request.method,
                    "amount": float(withdrawal_request.amount),
                    "deduction_amount": float(withdrawal_request.deduction_amount),
                    "subtract_from": withdrawal_request.subtract_from,
                    "currency": withdrawal_request.currency
                }
                try:
                    response = requests.post(callback_url, json=callback_data)
                    response.raise_for_status()
                except requests.RequestException as e:
                    return Response(
                        {
                            "status": "failed",
                            "message": f"Callback request failed: {e}"
                        },
                        status=status.HTTP_400_BAD_REQUEST
                    )

            response_data = {
                "status": "created",
                "id": withdrawal_request.id,
                "method": withdrawal_request.method,
                "amount": float(withdrawal_request.amount),
                "deduction_amount": float(withdrawal_request.deduction_amount),
                "subtract_from": withdrawal_request.subtract_from,
                "currency": withdrawal_request.currency
            }
            return Response(response_data, status=status.HTTP_201_CREATED)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


class ConfirmWithdrawalRequestView(APIView):
    permission_classes = [IsAuthenticated]

    @swagger_auto_schema(tags=["Conclusion"], request_body=ConfirmWithdrawalRequestSerializer)
    def post(self, request):
        serializer = ConfirmWithdrawalRequestSerializer(data=request.data)
        if serializer.is_valid():
            auth_login = serializer.validated_data.get('auth_login')
            auth_secret = serializer.validated_data.get('auth_secret')
            request_id = serializer.validated_data.get('id')
            signature = serializer.validated_data.get('signature')

            is_valid, user, company = verify_key(auth_login, auth_secret)
            if not is_valid:
                return Response(
                    {
                        "status": "failed",
                        "message": "Invalid credentials"
                    },
                    status=status.HTTP_400_BAD_REQUEST
                )

            try:
                withdrawal_request = WithdrawalRequest.objects.get(id=request_id, company=company)
            except WithdrawalRequest.DoesNotExist:

                return Response(
                    {
                        "status": "failed",
                        "message": "Withdrawal request not found"
                    },
                    status=status.HTTP_404_NOT_FOUND
                )

            if withdrawal_request.status != 'created':
                return Response(
                    {
                        "status": "failed",
                        "message": "Withdrawal request cannot be confirmed"
                    },
                    status=status.HTTP_400_BAD_REQUEST
                )

            withdrawal_request.status = 'processing'
            withdrawal_request.save()

            return Response(
                {
                    "status": "success",
                    "message": "Withdrawal request confirmed"
                },
                status=status.HTTP_200_OK
            )
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


class CancelWithdrawalRequestView(APIView):
    permission_classes = [IsAuthenticated]

    @swagger_auto_schema(tags=["Conclusion"], request_body=CancelWithdrawalRequestSerializer)
    def post(self, request):
        serializer = CancelWithdrawalRequestSerializer(data=request.data)
        if serializer.is_valid():
            auth_login = serializer.validated_data.get('auth_login')
            auth_secret = serializer.validated_data.get('auth_secret')
            request_id = serializer.validated_data.get('id')
            signature = serializer.validated_data.get('signature')

            is_valid, user, company = verify_key(auth_login, auth_secret)
            if not is_valid:
                return Response(
                    {
                        "status": "failed",
                        "message": "Invalid credentials"
                    },
                    status=status.HTTP_400_BAD_REQUEST
                )

            try:
                withdrawal_request = WithdrawalRequest.objects.get(id=request_id, company=company)
            except WithdrawalRequest.DoesNotExist:
                return Response(
                    {
                        "status": "failed",
                        "message": "Withdrawal request not found"
                    },
                    status=status.HTTP_404_NOT_FOUND
                )

            if withdrawal_request.status != 'created':
                return Response(
                    {
                        "status": "failed",
                        "message": "Withdrawal request cannot be cancelled"
                    },
                    status=status.HTTP_400_BAD_REQUEST
                )

            withdrawal_request.status = 'cancelled'
            withdrawal_request.save()

            return Response(
                {
                    "status": "success",
                    "message": "Withdrawal request cancelled"
                },
                status=status.HTTP_200_OK
            )
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


class GetWithdrawalRequestView(APIView):
    permission_classes = [IsAuthenticated]

    @swagger_auto_schema(tags=["Conclusion"], request_body=GetWithdrawalRequestSerializer)
    def post(self, request):
        serializer = GetWithdrawalRequestSerializer(data=request.data)
        if serializer.is_valid():
            auth_login = serializer.validated_data.get('auth_login')
            auth_secret = serializer.validated_data.get('auth_secret')
            request_id = serializer.validated_data.get('id')

            is_valid, user, company = verify_key(auth_login, auth_secret)
            if not is_valid:
                return Response(
                    {
                        "status": "failed",
                        "message": "Invalid credentials"
                    },
                    status=status.HTTP_400_BAD_REQUEST
                )

            try:
                withdrawal_request = WithdrawalRequest.objects.get(id=request_id, company=company)
            except WithdrawalRequest.DoesNotExist:
                return Response(
                    {
                        "status": "failed",
                        "message": "Withdrawal request not found"
                    },
                    status=status.HTTP_404_NOT_FOUND
                )

            response_data = {
                "status": "success",
                "id": withdrawal_request.id,
                "method": withdrawal_request.method,
                "amount": float(withdrawal_request.amount),
                "deduction_amount": float(withdrawal_request.deduction_amount),
                "subtract_from": withdrawal_request.subtract_from,
                "currency": withdrawal_request.currency,
                "status": withdrawal_request.status
            }
            return Response(response_data, status=status.HTTP_200_OK)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)





