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
from .models import APIKey, APIKey, Invoice, Withdrawal
from .serializers import InvoiceSerializer, WithdrawalSerializer


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

    def post(self, request):
        user = request.user
        api_key = APIKey.objects.create(user=user)
        return Response({
            'api_key': str(api_key.key),
        }, status=status.HTTP_201_CREATED)


class CheckKeyView(APIView):
    permission_classes = [IsAuthenticated]

    def post(self, request):
        key_value = request.data.get('key')
        try:
            key = APIKey.objects.get(key=key_value, user=request.user, is_active=True)
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



class PaymentHistoryView(APIView):
    def post(self, request):
        auth_login = request.data.get('auth_login')
        auth_secret = request.data.get('auth_secret')

        try:
            user = User.objects.get(email=auth_login)
            api_secret = APIKey.objects.get(user=user, secret=auth_secret, is_active=True)
        except (User.DoesNotExist, APIKey.DoesNotExist):
            return Response({'error': 'Invalid auth_login or auth_secret'}, status=status.HTTP_403_FORBIDDEN)

        payments = Invoice.objects.filter(user=user)
        serializer = InvoiceSerializer(payments, many=True)
        return Response(serializer.data, status=status.HTTP_200_OK)


class ChangeSubscriptionView(generics.UpdateAPIView):
    queryset = Company.objects.all()
    serializer_class = CompanySerializer
    permission_classes = [IsAuthenticated]

    @swagger_auto_schema(tags=["Subscription"])
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


class CreateInvoiceView(APIView):
    def post(self, request):
        auth_login = request.data.get('auth_login')
        auth_secret = request.data.get('auth_secret')

        try:
            user = User.objects.get(email=auth_login)
            api_secret = APIKey.objects.get(user=user, secret=auth_secret, is_active=True)
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
            user = User.objects.get(email=auth_login)
            api_secret = APIKey.objects.get(user=user, secret=auth_secret, is_active=True)
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
            user = User.objects.get(email=auth_login)
            api_secret = APIKey.objects.get(user=user, secret=auth_secret, is_active=True)
        except (User.DoesNotExist, APIKey.DoesNotExist):
            return Response({'error': 'Invalid auth_login or auth_secret'}, status=status.HTTP_403_FORBIDDEN)

        total_invoices = Invoice.objects.filter(user=user).aggregate(total=Sum('amount'))['total'] or 0
        total_withdrawals = Withdrawal.objects.filter(user=user).aggregate(total=Sum('amount'))['total'] or 0

        data = {
            'total_invoices': total_invoices,
            'total_withdrawals': total_withdrawals
        }

        return Response(data, status=status.HTTP_200_OK)