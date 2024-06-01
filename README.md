# AralashAPIBackend

## О проекте

AralashAPIBackend - это функциональная система онлайн-платежей, позволяющая принимать оплату через API на веб-сайтах и в мобильных приложениях. 

## Запуск проекта

1. **Клонирование репозитория**:
   ```bash
   git clone https://github.com/Aidar912/AralashAPIBackend.git
   cd AralashAPIBackend

    
2. **Создание виртуального окружения и установка зависимостей**:
   ```bash
   Копировать код
   python -m venv venv
   source venv/bin/activate  # Для Windows используйте `venv\Scripts\activate`
   pip install -r requirements.txt

3. **Создание файла .env и добавление конфигурации:
Создайте файл .env в корне проекта и добавьте следующую информацию**:
    ```bash
    EMAIL_BACKEND=django.core.mail.backends.smtp.EmailBackend
    EMAIL_HOST=smtp.gmail.com
    EMAIL_PORT=587
    EMAIL_HOST_USER=your_email@gmail.com
    EMAIL_HOST_PASSWORD=your_password
    EMAIL_USE_TLS=True
    DEFAULT_FROM_EMAIL=your_email@gmail.com
    SERVER_EMAIL=your_email@gmail.com
    EMAIL_ADMIN=your_email@gmail.com
    SECRET_KEY='your_secret_key'
    
    DB_LOGIN=postgres
    DB_PASSWORD=root
    
    SOCIAL_AUTH_GOOGLE_OAUTH2_KEY=
    SOCIAL_AUTH_GOOGLE_OAUTH2_SECRET=


4. **Применение миграций и запуск сервера**:
    ```bash
    python manage.py migrate
    python manage.py runserver  

## Функционал

### Аутентификация и управление пользователями
- Получение JWT токена: `POST /token/`
- Обновление JWT токена: `POST /token/refresh/`
- Регистрация пользователя: `POST /register/`
- Смена пароля: `POST /change-password/`
- Отправка письма для сброса пароля: `POST /send-reset-email/`
- Подтверждение сброса пароля: `POST /reset-password-confirm/<uuid:token>/`
- Начало регистрации: `POST /start-registration/`
- Изменение email: `POST /change-email/`
- Подтверждение регистрации: `GET /confirm-registration/<uuid:token>/`
- Подтверждение изменения email: `POST /confirm-email/<uuid:token>/`
- Вход через Google: `POST /auth/google/`

### Управление статистикой
- Статистика пользователей: `GET /user-statistics/`
- Статистика компаний: `GET /company-statistics/`

### Управление бизнесом
- Типы бизнеса: `GET, POST /business-types/`
- Компании: `GET, POST /companies/`
- Связи пользователей с компаниями: `GET /user-companies/`

### Управление балансом
- Пополнение баланса: `POST /topup`

### Управление подписками

1. **Список подписок**: `GET /subscriptions/`
2. **Создание подписки**: `POST /subscriptions/create/`
3. **Просмотр подписки**: `GET /subscriptions/{id}/`
4. **Обновление подписки**: `PUT /subscriptions/{id}/update/`
5. **Удаление подписки**: `DELETE /subscriptions/{id}/delete/`

### Управление API ключами

1. **Создание ключа**: `POST /generate-key`
2. **Проверка ключа**: `POST /check-key`
3. **Перегенерация ключа**: `POST /regenerate-key`
4. **Деактивация ключа**: `POST /deactivate-key`

### Управление транзакциями

1. **Запрос на вывод средств**: `POST /payoff/vyvod`
2. **Подтверждение вывода**: `POST /payoff/confirm_withdrawal`
3. **Отмена вывода**: `POST /payoff/cancel_withdrawal`
4. **Получение информации о выводе**: `POST /payoff/get_withdrawal_info`

### Управление счетами

1. **Создание счета**: `POST /create_invoice/`
2. **Получение информации о счете**: `POST /invoice_info/`

### История платежей и выводов

1. **История платежей**: `POST /payment_history/`
2. **История выводов**: `POST /withdrawal_history/`

### Общая статистика

1. **Общая статистика**: `POST /general_statistics/`


