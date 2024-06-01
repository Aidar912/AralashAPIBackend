from django.urls import reverse
from rest_framework.test import APITestCase
from rest_framework import status
from django.contrib.auth import get_user_model

User = get_user_model()

class BalanceTopUpTests(APITestCase):
    def setUp(self):
        self.user = User.objects.create_user(username='awesth', email='a@a.com', password='1234')
        self.url = reverse('balance_topup')
        self.client.login(username='testuser', password='testpassword')

    def test_balance_top_up_success(self):
        data = {'amount': '10000.00'}
        response = self.client.post(self.url, data, format='json')
        self.user.refresh_from_db()
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(self.user.balance, 100.00)
        self.assertEqual(response.data['status'], 'success')
        self.assertEqual(response.data['new_balance'], 100.00)

    def test_balance_top_up_invalid_amount(self):
        data = {'amount': 'invalid_amount'}
        response = self.client.post(self.url, data, format='json')
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
