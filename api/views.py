from rest_framework import generics, status
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from drf_yasg.utils import swagger_auto_schema
from drf_yasg import openapi

from rest_framework import generics
from user.models import Subscription, Company, SubscriptionHistory
from user.serializers import SubscriptionSerializer, CompanySerializer, SubscriptionHistorySerializer


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

