# tests.py
import uuid

from django.urls import reverse
from rest_framework.test import APITestCase, APIClient
from rest_framework import status
from .models import APIKey, User, APIKey, Invoice, Withdrawal


class APITests(APITestCase):
    def setUp(self):
        self.user = User.objects.create_user(email='test@example.com', password='testpassword', phone='+1234567890',
                                             username='testuser')
        self.client = APIClient()
        self.login_url = reverse('token_obtain_pair')
        self.generate_key_url = reverse('generate_key')
        self.check_key_url = reverse('check_key')
        self.regenerate_key_url = reverse('regenerate_key')
        self.deactivate_key_url = reverse('deactivate_key')

        # Получение токена
        response = self.client.post(self.login_url, {'email': 'test@example.com', 'password': 'testpassword'})
        self.token = response.data['access']
        self.client.credentials(HTTP_AUTHORIZATION='Bearer ' + self.token)

    def test_generate_key(self):
        response = self.client.post(self.generate_key_url)
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertIn('api_key', response.data)

    def test_check_key_valid(self):
        api_key = APIKey.objects.create(user=self.user)
        response = self.client.post(self.check_key_url, {'key': str(api_key.key)})
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertTrue(response.data['valid'])

    def test_check_key_invalid(self):
        response = self.client.post(self.check_key_url, {'key': 'invalid_key'})
        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)
        self.assertFalse(response.data['valid'])

    def test_regenerate_key(self):
        api_key = APIKey.objects.create(user=self.user)
        response = self.client.post(self.regenerate_key_url, {'key': str(api_key.key)})
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertIn('new_api_key', response.data)

    def test_deactivate_key(self):
        api_key = APIKey.objects.create(user=self.user)
        response = self.client.post(self.deactivate_key_url, {'key': str(api_key.key)})
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data['message'], 'API key deactivated')

    # def test_protected_view(self):
    #     api_key = APIKey.objects.create(user=self.user)
    #     url = reverse('some_protected_view')  # Убедитесь, что это имя маршрута существует
    #     self.client.credentials(HTTP_X_API_KEY=str(api_key.key))
    #     response = self.client.get(url)
    #     self.assertEqual(response.status_code, status.HTTP_200_OK)
    #
    # def test_protected_view_no_key(self):
    #     url = reverse('some_protected_view')  # Убедитесь, что это имя маршрута существует
    #     response = self.client.get(url)
    #     self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)
    #
    # def test_protected_view_invalid_key(self):
    #     url = reverse('some_protected_view')  # Убедитесь, что это имя маршрута существует
    #     self.client.credentials(HTTP_X_API_KEY='invalid_key')
    #     response = self.client.get(url)
    #     self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)


class InvoiceAPITests(APITestCase):
    def setUp(self):
        self.user = User.objects.create_user(username='testuser', email='testuser@example.com', password='password')
        self.api_secret = APIKey.objects.create(user=self.user)
        self.client = APIClient()

    def test_create_invoice_success(self):
        url = reverse('create-invoice')
        data = {
            'auth_login': self.user.email,
            'auth_secret': str(self.api_secret.secret),
            'amount': 100.00,
            'currency': 'USD',
            'type': 'purchase',
            'description': 'Payment for services',
            'redirect_url': 'https://example.com/redirect',
            'callback_url': 'https://example.com/callback',
            'extra': 'Internal payment ID',
            'payer_details': 'payer@example.com',
            'lifetime': 60
        }
        response = self.client.post(url, data, format='json')
        if response.status_code != status.HTTP_201_CREATED:
            print(response.data)
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertIn('id', response.data)
        self.assertEqual(response.data['status'], 'created')

    def test_create_invoice_invalid_auth(self):
        url = reverse('create-invoice')
        data = {
            'auth_login': self.user.email,
            'auth_secret': str(uuid.uuid4()),  # Используем неверный secret
            'amount': 100.00,
            'currency': 'USD',
            'type': 'purchase',
            'description': 'Payment for services',
            'redirect_url': 'https://example.com/redirect',
            'callback_url': 'https://example.com/callback',
            'extra': 'Internal payment ID',
            'payer_details': 'payer@example.com',
            'lifetime': 60
        }
        response = self.client.post(url, data, format='json')
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)
        self.assertIn('error', response.data)
        self.assertEqual(response.data['error'], 'Invalid auth_login or auth_secret')

    def test_create_invoice_missing_fields(self):
        url = reverse('create-invoice')
        data = {
            'auth_login': self.user.email,
            'auth_secret': str(self.api_secret.secret),
            # Пропущены обязательные поля
            'amount': 100.00,
            'currency': 'USD',
            'type': 'purchase',
            # 'lifetime': 60
        }
        response = self.client.post(url, data, format='json')
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn('lifetime', response.data)



class InvoiceGETAPITests(APITestCase):
    def setUp(self):
        self.user = User.objects.create_user(username='testuser', email='testuser@example.com', password='password')
        self.api_secret = APIKey.objects.create(user=self.user)
        self.client = APIClient()

        self.invoice = Invoice.objects.create(
            user=self.user,
            amount=100.00,
            amount_currency='USD',
            type='purchase',
            description='Payment for services',
            redirect_url='https://example.com/redirect',
            callback_url='https://example.com/callback',
            extra='Internal payment ID',
            payer_details='payer@example.com',
            lifetime=60
        )

    def test_get_invoice_info_success(self):
        url = reverse('invoice-info')
        data = {
            'auth_login': self.user.email,
            'auth_secret': str(self.api_secret.secret),
            'id': str(self.invoice.id)
        }
        response = self.client.post(url, data, format='json')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data['id'], str(self.invoice.id))
        self.assertEqual(float(response.data['amount']), 100.00)
        self.assertEqual(response.data['amount_currency'], 'USD')
        self.assertEqual(response.data['type'], 'purchase')

    def test_get_invoice_info_invalid_auth(self):
        url = reverse('invoice-info')
        data = {
            'auth_login': self.user.email,
            'auth_secret': str(uuid.uuid4()),  # Неверный secret
            'id': str(self.invoice.id)
        }
        response = self.client.post(url, data, format='json')
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)
        self.assertIn('error', response.data)
        self.assertEqual(response.data['error'], 'Invalid auth_login or auth_secret')

    def test_get_invoice_info_not_found(self):
        url = reverse('invoice-info')
        data = {
            'auth_login': self.user.email,
            'auth_secret': str(self.api_secret.secret),
            'id': str(uuid.uuid4())  # Неверный ID инвойса
        }
        response = self.client.post(url, data, format='json')
        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)


class PaymentHistoryAPITests(APITestCase):
    def setUp(self):
        self.user = User.objects.create_user(username='testuser', email='testuser@example.com', password='password')
        self.api_secret = APIKey.objects.create(user=self.user)
        self.client = APIClient()

        self.invoice1 = Invoice.objects.create(
            user=self.user,
            amount=100.00,
            amount_currency='USD',
            type='purchase',
            description='Payment for services',
            redirect_url='https://example.com/redirect',
            callback_url='https://example.com/callback',
            extra='Internal payment ID 1',
            payer_details='payer1@example.com',
            lifetime=60
        )

        self.invoice2 = Invoice.objects.create(
            user=self.user,
            amount=200.00,
            amount_currency='EUR',
            type='topup',
            description='Top up account',
            redirect_url='https://example.com/redirect',
            callback_url='https://example.com/callback',
            extra='Internal payment ID 2',
            payer_details='payer2@example.com',
            lifetime=60
        )

    def test_get_payment_history_success(self):
        url = reverse('payment-history')
        data = {
            'auth_login': self.user.email,
            'auth_secret': str(self.api_secret.secret)
        }
        response = self.client.post(url, data, format='json')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data), 2)
        self.assertEqual(float(response.data[0]['amount']), 100.00)
        self.assertEqual(float(response.data[1]['amount']), 200.00)

    def test_get_payment_history_invalid_auth(self):
        url = reverse('payment-history')
        data = {
            'auth_login': self.user.email,
            'auth_secret': str(uuid.uuid4())  # Неверный secret
        }
        response = self.client.post(url, data, format='json')
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)
        self.assertIn('error', response.data)
        self.assertEqual(response.data['error'], 'Invalid auth_login or auth_secret')


class WithdrawalHistoryAPITests(APITestCase):
    def setUp(self):
        self.user = User.objects.create_user(username='testuser', email='testuser@example.com', password='password')
        self.api_secret = APIKey.objects.create(user=self.user)
        self.client = APIClient()

        self.withdrawal1 = Withdrawal.objects.create(
            user=self.user,
            amount=100.00,
            currency='USD',
            method='BITCOIN',
            status='completed'
        )

        self.withdrawal2 = Withdrawal.objects.create(
            user=self.user,
            amount=200.00,
            currency='EUR',
            method='ETHEREUM',
            status='pending'
        )

    def test_get_withdrawal_history_success(self):
        url = reverse('withdrawal-history')
        data = {
            'auth_login': self.user.email,
            'auth_secret': str(self.api_secret.secret)
        }
        response = self.client.post(url, data, format='json')
        print("Request Data:", data)
        print("Response Data:", response.data)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data), 2)
        self.assertEqual(float(response.data[0]['amount']), 100.00)
        self.assertEqual(float(response.data[1]['amount']), 200.00)

    def test_get_withdrawal_history_invalid_auth(self):
        url = reverse('withdrawal-history')
        data = {
            'auth_login': self.user.email,
            'auth_secret': str(uuid.uuid4())  # Неверный secret
        }
        response = self.client.post(url, data, format='json')
        print("Request Data:", data)
        print("Response Data:", response.data)
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)
        self.assertIn('error', response.data)
        self.assertEqual(response.data['error'], 'Invalid auth_login or auth_secret')


class GeneralStatisticsAPITests(APITestCase):
    def setUp(self):
        self.user = User.objects.create_user(username='testuser', email='testuser@example.com', password='password')
        self.api_secret = APIKey.objects.create(user=self.user)
        self.client = APIClient()

        Invoice.objects.create(
            user=self.user,
            amount=100.00,
            amount_currency='USD',
            type='purchase',
            status='completed',
            lifetime=60  # Добавляем значение для lifetime
        )

        Invoice.objects.create(
            user=self.user,
            amount=200.00,
            amount_currency='USD',
            type='topup',
            status='completed',
            lifetime=60  # Добавляем значение для lifetime
        )

        Withdrawal.objects.create(
            user=self.user,
            amount=50.00,
            currency='USD',
            method='BITCOIN',
            status='completed'
        )

    def test_get_general_statistics_success(self):
        url = reverse('general-statistics')
        data = {
            'auth_login': self.user.email,
            'auth_secret': str(self.api_secret.secret)
        }
        response = self.client.post(url, data, format='json')
        print("Request Data:", data)
        print("Response Data:", response.data)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(float(response.data['total_invoices']), 300.00)
        self.assertEqual(float(response.data['total_withdrawals']), 50.00)

    def test_get_general_statistics_invalid_auth(self):
        url = reverse('general-statistics')
        data = {
            'auth_login': self.user.email,
            'auth_secret': str(uuid.uuid4())  # Неверный secret
        }
        response = self.client.post(url, data, format='json')
        print("Request Data:", data)
        print("Response Data:", response.data)
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)
        self.assertIn('error', response.data)
        self.assertEqual(response.data['error'], 'Invalid auth_login or auth_secret')