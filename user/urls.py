from django.urls import path

from .views import *

urlpatterns = [

    path('token/', MyTokenObtainPairView.as_view(), name='token_obtain_pair'),
    path('token/refresh/', UserTokenRefreshView.as_view(), name='token_refresh'),
    path('register/', RegisterView.as_view(), name='auth_register'),
    path('change-password/', ChangePasswordView.as_view(), name='change-password'),
    path('send-reset-email/', SendResetEmailView.as_view(), name='send_reset_email'),
    path('reset-password-confirm/<uuid:token>', ResetPasswordConfirmView.as_view(), name='password_reset_confirm'),
    path('start-registration/', StartRegistrationView.as_view(), name='start_registration'),
    path('change-email/', ChangeEmailView.as_view(), name='change_email'),
    path('confirm-registration/<uuid:token>/', ConfirmRegistrationView.as_view(), name='confirm_registration'),
    path('confirm-email/<uuid:token>', ConfirmEmailChangeView.as_view(), name='change-email'),
    path('auth/google/', GoogleLogin.as_view(), name='google_login'),

    path('user-statistics/', MonthlyUserStatisticsListView.as_view(), name='user-statistics-list'),

    path('business-types/', BusinessTypeListCreateView.as_view(), name='business-type-list-create'),
    path('companies/', CompanyListCreateView.as_view(), name='company-list-create'),
    path('user-companies/', UserCompanyRelationListView.as_view(), name='user-company-list'),
    path('user-statistics/', MonthlyUserStatisticsListView.as_view(), name='user-statistics-list'),
    path('company-statistics/', MonthlyCompanyStatisticsListView.as_view(), name='company-statistics-list'),

    path('topup', BalanceTopUpView.as_view(), name='balance_topup'),
]
