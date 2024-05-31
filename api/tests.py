# tests.py
import uuid

from django.urls import reverse
from rest_framework.test import APITestCase, APIClient
from rest_framework import status
from .models import APIKey, User, Payment


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


class PaymentAPITests(APITestCase):
    def setUp(self):
        # Создаем пользователя и API ключ
        self.user = User.objects.create_user(username='testuser', email='testuser@example.com', password='password')
        self.api_key = APIKey.objects.create(user=self.user)

        self.client = APIClient()
        self.client.credentials(HTTP_API_KEY=self.api_key.key)

        self.payment_data = {
            'amount': '100.00',
            'currency': 'KGS',
            'description': 'Test Payment',
            'client_data': {'name': 'John Doe', 'email': 'john@example.com'}
        }

    def test_create_payment(self):
        url = reverse('create-payment')
        response = self.client.post(url, self.payment_data, format='json')
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertIn('id', response.data)
        self.assertEqual(response.data['status'], 'created')

    def test_get_payment_status(self):
        payment = Payment.objects.create(
            id=uuid.uuid4(),
            user=self.user,
            amount='100.00',
            currency='KGS',
            description='Test Payment',
            client_data={'name': 'John Doe', 'email': 'john@example.com'},
            status='created'
        )
        url = reverse('payment-status', args=[payment.id])
        response = self.client.get(url, format='json')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(str(response.data['id']), str(payment.id))  # Приведение к строке
        self.assertEqual(response.data['status'], 'created')

    def test_cancel_payment(self):
        payment = Payment.objects.create(
            id=uuid.uuid4(),
            user=self.user,
            amount='100.00',
            currency='KGS',
            description='Test Payment',
            client_data={'name': 'John Doe', 'email': 'john@example.com'},
            status='created'
        )
        url = reverse('cancel-payment', args=[payment.id])
        response = self.client.post(url, format='json')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        payment.refresh_from_db()
        self.assertEqual(payment.status, 'canceled')