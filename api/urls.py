from django.urls import path
from .views import GenerateKeyView, CheckKeyView, RegenerateKeyView, DeactivateKeyView, CreatePaymentView, \
    PaymentStatusView, CancelPaymentView

urlpatterns = [
    path('generate-key', GenerateKeyView.as_view(), name='generate_key'),
    path('check-key', CheckKeyView.as_view(), name='check_key'),
    path('regenerate-key', RegenerateKeyView.as_view(), name='regenerate_key'),
    path('deactivate-key', DeactivateKeyView.as_view(), name='deactivate_key'),

    path('create/', CreatePaymentView.as_view(), name='create-payment'),
    path('status/<uuid:payment_id>/', PaymentStatusView.as_view(), name='payment-status'),
    path('cancel/<uuid:payment_id>/', CancelPaymentView.as_view(), name='cancel-payment'),

]
