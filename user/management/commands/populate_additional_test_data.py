import random
import uuid
from datetime import datetime
from django.core.management.base import BaseCommand
from django.utils import timezone
from django.contrib.auth import get_user_model
from user.models import BusinessType, Company, UserCompanyRelation, MonthlyUserStatistics, MonthlyCompanyStatistics, Subscription

User = get_user_model()

class Command(BaseCommand):
    help = 'Populate database with test data'

    def handle(self, *args, **kwargs):
        self.stdout.write(self.style.SUCCESS('Starting data population...'))

        # Создание бизнес типов
        business_types = ['IT', 'Finance', 'Healthcare', 'Education', 'Retail']
        for name in business_types:
            if not BusinessType.objects.filter(name=name).exists():
                code = uuid.uuid4().hex[:6].upper()  # Генерация уникального кода
                BusinessType.objects.create(name=name, code=code)
        self.stdout.write(self.style.SUCCESS('Business types created.'))

        # Создание подписок
        subscriptions = [
            ('FREE', 1000, 0.00),
            ('BASIC', 5000, 9.99),
            ('PREMIUM', 10000, 19.99)
        ]
        for name, max_requests, price in subscriptions:
            if not Subscription.objects.filter(name=name).exists():
                Subscription.objects.create(name=name, max_requests_per_month=max_requests, price=price)
        self.stdout.write(self.style.SUCCESS('Subscriptions created.'))

        # Создание пользователей
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

        # Создание статистики пользователей
        for user in users:
            for month in range(1, 13):
                month_start = datetime(datetime.now().year, month, 1)
                MonthlyUserStatistics.objects.create(
                    user=user,
                    month=month_start,
                    requests_made=random.randint(10, 100),
                )
        self.stdout.write(self.style.SUCCESS('Monthly user statistics created.'))

        # Создание статистики компаний
        companies = Company.objects.all()
        for company in companies:
            for month in range(1, 13):
                month_start = datetime(datetime.now().year, month, 1)
                MonthlyCompanyStatistics.objects.create(
                    company=company,
                    month=month_start,
                    requests_made=random.randint(100, 1000),
                )
        self.stdout.write(self.style.SUCCESS('Monthly company statistics created.'))

        self.stdout.write(self.style.SUCCESS('Database population complete.'))
