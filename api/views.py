
from decimal import Decimal

import requests

from django.db.models import Sum

from rest_framework import generics, status
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from drf_yasg.utils import swagger_auto_schema
from drf_yasg import openapi

from rest_framework import generics
from user.models import Subscription, Company, SubscriptionHistory, User
from user.serializers import SubscriptionSerializer, CompanySerializer, SubscriptionHistorySerializer

from django.shortcuts import get_object_or_404
from rest_framework.pagination import PageNumberPagination
from rest_framework.views import APIView
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework import status

from .authentication import APIKeyAuthentication

from .utils import verify_key

from .models import APIKey, APIKey, Invoice, Withdrawal,WithdrawalRequest
from .serializers import InvoiceSerializer, WithdrawalSerializer,WithdrawalRequestSerializer, ConfirmWithdrawalRequestSerializer, \
    CancelWithdrawalRequestSerializer, GetWithdrawalRequestSerializer



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





class PaymentHistoryView(APIView):
    def post(self, request):
        auth_login = request.data.get('auth_login')
        auth_secret = request.data.get('auth_secret')

        try:
            is_valid, user, company = verify_key(auth_login, auth_secret)
        except (User.DoesNotExist, APIKey.DoesNotExist):
            return Response({'error': 'Invalid auth_login or auth_secret'}, status=status.HTTP_403_FORBIDDEN)

        payments = Invoice.objects.filter(user=user)
        serializer = InvoiceSerializer(payments, many=True)
        return Response(serializer.data, status=status.HTTP_200_OK)


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






class CreateInvoiceView(APIView):
    def post(self, request):
        auth_login = request.data.get('auth_login')
        auth_secret = request.data.get('auth_secret')

        try:
            is_valid, user, company = verify_key(auth_login, auth_secret)
        except (User.DoesNotExist, APIKey.DoesNotExist):
            return Response({'error': 'Invalid auth_login or auth_secret'}, status=status.HTTP_403_FORBIDDEN)

        data = request.data.copy()
        data['user'] = user.id
        data.pop('auth_login')
        data.pop('auth_secret')

        serializer = InvoiceSerializer(data=data)
        if serializer.is_valid():
            invoice = serializer.save()
            return Response({'id': invoice.id, 'status': invoice.status}, status=status.HTTP_201_CREATED)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


class InvoiceDetailView(APIView):
    def post(self, request):
        auth_login = request.data.get('auth_login')
        auth_secret = request.data.get('auth_secret')
        invoice_id = request.data.get('id')

        try:
             is_valid, user, company = verify_key(auth_login, auth_secret)
        except (User.DoesNotExist, APIKey.DoesNotExist):
            return Response({'error': 'Invalid auth_login or auth_secret'}, status=status.HTTP_403_FORBIDDEN)

        invoice = get_object_or_404(Invoice, id=invoice_id, user=user)
        serializer = InvoiceSerializer(invoice)
        return Response(serializer.data, status=status.HTTP_200_OK)


class WithdrawalHistoryView(APIView):
    def post(self, request):
        auth_login = request.data.get('auth_login')
        auth_secret = request.data.get('auth_secret')

        try:
            user = User.objects.get(email=auth_login)
            api_secret = APIKey.objects.get(user=user, secret=auth_secret, is_active=True)
        except (User.DoesNotExist, APIKey.DoesNotExist):
            return Response({'error': 'Invalid auth_login or auth_secret'}, status=status.HTTP_403_FORBIDDEN)

        withdrawals = Withdrawal.objects.filter(user=user)
        serializer = WithdrawalSerializer(withdrawals, many=True)
        return Response(serializer.data, status=status.HTTP_200_OK)


class GeneralStatisticsView(APIView):
    def post(self, request):
        auth_login = request.data.get('auth_login')
        auth_secret = request.data.get('auth_secret')

        try:
             is_valid, user, company = verify_key(auth_login, auth_secret)
        except (User.DoesNotExist, APIKey.DoesNotExist):
            return Response({'error': 'Invalid auth_login or auth_secret'}, status=status.HTTP_403_FORBIDDEN)

        total_invoices = Invoice.objects.filter(user=user).aggregate(total=Sum('amount'))['total'] or 0
        total_withdrawals = Withdrawal.objects.filter(user=user).aggregate(total=Sum('amount'))['total'] or 0

        data = {
            'total_invoices': total_invoices,
            'total_withdrawals': total_withdrawals
        }

        return Response(data, status=status.HTTP_200_OK)

