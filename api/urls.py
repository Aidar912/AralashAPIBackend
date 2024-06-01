from django.urls import path
from .views import *

urlpatterns = [
    path('subscriptions/', SubscriptionListView.as_view(), name='subscription-list'),
    path('subscriptions/create/', SubscriptionCreateView.as_view(), name='subscription-create'),
    path('subscriptions/<int:pk>/', SubscriptionDetailView.as_view(), name='subscription-detail'),
    path('subscriptions/<int:pk>/update/', SubscriptionUpdateView.as_view(), name='subscription-update'),
    path('subscriptions/<int:pk>/delete/', SubscriptionDeleteView.as_view(), name='subscription-delete'),

    path('generate-key', GenerateKeyView.as_view(), name='generate_key'),
    path('check-key', CheckKeyView.as_view(), name='check_key'),
    path('regenerate-key', RegenerateKeyView.as_view(), name='regenerate_key'),
    path('deactivate-key', DeactivateKeyView.as_view(), name='deactivate_key'),

    path('create/', CreatePaymentView.as_view(), name='create-payment'),
    path('status/<uuid:payment_id>/', PaymentStatusView.as_view(), name='payment-status'),
    path('cancel/<uuid:payment_id>/', CancelPaymentView.as_view(), name='cancel-payment'),

    path('change-subscription/<int:pk>/', ChangeSubscriptionView.as_view(), name='change-subscription'),
    path('subscription-history/', SubscriptionHistoryListView.as_view(), name='subscription-history-list'),


    path('payoff/vyvod', WithdrawalRequestView.as_view(), name='withdrawal_request'),
    path('payoff/confirm_withdrawal', ConfirmWithdrawalRequestView.as_view(), name='confirm_withdrawal'),
    path('payoff/cancel_withdrawal', CancelWithdrawalRequestView.as_view(), name='cancel_withdrawal'),
    path('payoff/get_withdrawal_info', GetWithdrawalRequestView.as_view(), name='get_withdrawal_info'),
]
