from django.urls import path
from .views import *

urlpatterns = [
    path('subscriptions/', SubscriptionListView.as_view(), name='subscription-list'),
    path('subscriptions/create/', SubscriptionCreateView.as_view(), name='subscription-create'),
    path('subscriptions/<int:pk>/', SubscriptionDetailView.as_view(), name='subscription-detail'),
    path('subscriptions/<int:pk>/update/', SubscriptionUpdateView.as_view(), name='subscription-update'),
    path('subscriptions/<int:pk>/delete/', SubscriptionDeleteView.as_view(), name='subscription-delete'),
    path('change-subscription/<int:pk>/', ChangeSubscriptionView.as_view(), name='change-subscription'),
    path('subscription-history/', SubscriptionHistoryListView.as_view(), name='subscription-history-list'),
]
