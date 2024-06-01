import random
import secrets
import uuid
from decimal import Decimal
from django.core.management.base import BaseCommand
from django.utils import timezone
from user.models import User, Company, BusinessType, UserCompanyRelation, Subscription
from api.models import APIKey, PaymentMethod, Invoice, Withdrawal, WithdrawalRequest

class Command(BaseCommand):
    help = 'Populate database with additional test data'

    def handle(self, *args, **kwargs):
        self.stdout.write(self.style.SUCCESS('Starting additional data population...'))

        # Создание методов оплаты
        payment_methods = [
            ('LZTMARKET', 'LZTMARKET description'),
            ('BITCOIN', 'BITCOIN description'),
            ('ETHEREUM', 'ETHEREUM description')
        ]
        for name, description in payment_methods:
            if not PaymentMethod.objects.filter(name=name).exists():
                PaymentMethod.objects.create(name=name, description=description)
        self.stdout.write(self.style.SUCCESS('Payment methods created.'))

        # Создание бизнес типов, если еще не создано
        business_types = ['IT', 'Finance', 'Healthcare', 'Education', 'Retail']
        for name in business_types:
            if not BusinessType.objects.filter(name=name).exists():
                code = uuid.uuid4().hex[:6].upper()  # Генерация уникального кода
                BusinessType.objects.create(name=name, code=code)
        self.stdout.write(self.style.SUCCESS('Business types created.'))

        # Создание подписок, если еще не создано
        subscriptions = [
            ('FREE', 1000, 0.00),
            ('BASIC', 5000, 9.99),
            ('PREMIUM', 10000, 19.99)
        ]
        for name, max_requests, price in subscriptions:
            if not Subscription.objects.filter(name=name).exists():
                Subscription.objects.create(name=name, max_requests_per_month=max_requests, price=price)
        self.stdout.write(self.style.SUCCESS('Subscriptions created.'))

        # Создание пользователей, если еще не создано
        users = []
        for i in range(5):
            email = f'user{i}@example.com'
            if not User.objects.filter(email=email).exists():
                user = User.objects.create_user(
                    email=email,
                    password='password123',
                    username=f'user{i}',
                    is_active=True,
                    balance=random.uniform(1000, 5000),
                )
                users.append(user)
        self.stdout.write(self.style.SUCCESS('Users created.'))

        # Создание компаний и связей между пользователями и компаниями
        for i in range(5):
            company_name = f'Company {i}'
            if not Company.objects.filter(name=company_name).exists():
                registration_number = uuid.uuid4().hex[:8].upper()  # Генерация уникального регистрационного номера
                company = Company.objects.create(
                    name=company_name,
                    business_type=BusinessType.objects.order_by('?').first(),
                    registration_number=registration_number,
                    address=f'Address {i}',
                    subscription=Subscription.objects.order_by('?').first()
                )
                for user in users:
                    UserCompanyRelation.objects.create(
                        user=user,
                        company=company,
                        is_verified=True,
                    )
        self.stdout.write(self.style.SUCCESS('Companies and relations created.'))

        # Создание API ключей
        companies = Company.objects.all()
        for company in companies:
            if not APIKey.objects.filter(company=company).exists():
                APIKey.objects.create(company=company)
        self.stdout.write(self.style.SUCCESS('API keys created.'))

        # Создание инвойсов
        for user in users:
            for _ in range(5):
                Invoice.objects.create(
                    user=user,
                    amount=Decimal(random.uniform(100, 1000)).quantize(Decimal('0.00000001')),
                    amount_currency='USD',
                    required_method='BITCOIN',
                    type='invoice',
                    description='Test invoice',
                    lifetime=3600,
                    status='created'
                )
        self.stdout.write(self.style.SUCCESS('Invoices created.'))

        # Создание запросов на вывод средств
        for user in users:
            for _ in range(5):
                WithdrawalRequest.objects.create(
                    user=user,
                    company=companies.order_by('?').first(),
                    auth_login=user.email,
                    auth_secret=secrets.token_hex(16),
                    signature=secrets.token_hex(32),
                    amount=Decimal(random.uniform(50, 500)).quantize(Decimal('0.00')),
                    amount_currency='USD',
                    method='BITCOIN',
                    wallet='1A1zP1eP5QGefi2DMPTfTL5SLmv7DivfNa',
                    subtract_from='balance',
                    callback_url='https://example.com/callback',
                    extra='Some extra data',
                    commission=Decimal('0.0001'),
                    rub_amount=Decimal(random.uniform(3000, 50000)).quantize(Decimal('0.00')),
                    receive_amount=Decimal(random.uniform(50, 500)).quantize(Decimal('0.00000001')),
                    deduction_amount=Decimal(random.uniform(50, 500)).quantize(Decimal('0.00000001')),
                    currency='USD',
                    status='created'
                )
        self.stdout.write(self.style.SUCCESS('Withdrawal requests created.'))

        self.stdout.write(self.style.SUCCESS('Database additional population complete.'))
