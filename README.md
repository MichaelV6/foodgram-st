# Foodgram — Продуктовый помощник

**Учебный проект по курсу «Интеграция и управление приложениями на удалённом сервере»**

## Содержимое

* [Описание](#описание)
* [Автор](#автор)
* [Технологии](#технологии)
* [Системные требования](#системные-требования)
* [Установка и запуск](#установка-и-запуск)

  * [Локальный (разработка)](#локальный-разработка)
  * [Docker (продакшен)](#docker-продакшен)
* [Переменные окружения](#переменные-окружения)
* [Контейнеры и порты](#контейнеры-и-порты)
* [API и документация](#api-и-документация)
* [CI/CD](#cicd)
---

## Описание

Foodgram — веб-приложение для публикации и потребления рецептов:

* Создание, редактирование и удаление собственных рецептов
* Добавление рецептов в избранное и список покупок
* Подписка на авторов и лента новых рецептов
* Формирование и скачивание списка покупок

Проект разрабатывался с целью обучения деплою и управлению Docker-контейнерами на удалённом сервере.

## Автор

**Михаил В.**

* Email: [michaelv063@yandex.com](mailto:michaelv063@yandex.com)
* GitHub: [https://github.com/MichaelV6](https://github.com/MichaelV6)

## Технологии

**Backend:**

* Python 3.10
* Django 4.2
* Django REST Framework
* PostgreSQL 13
* Gunicorn
* Nginx

**Frontend:**

* React
* JavaScript (ES6+)
* HTML5, CSS3

**Инфраструктура:**

* Docker, Docker Compose
* GitHub Actions (CI/CD)

## Системные требования

* Docker ≥ 20.10
* Docker Compose ≥ 2.x
* Git

## Установка и запуск

### Локальный запуск (разработка)

```bash

git clone https://github.com/MichaelV6/foodgram.git


cd foodgram/


python -m venv venv
source venv/bin/activate 
venv\\Scripts\\activate 


pip install -r backend/requirements.txt



cd backend
python manage.py migrate
python manage.py load_ingredients_from_json


python manage.py runserver


cd ../frontend
npm install
npm start
```

### Запуск через Docker Compose (продакшен)

```bash

cd infra


docker compose up -d --build


docker compose exec backend python manage.py migrate


docker compose exec backend python manage.py createsuperuser
```

Также предусмотрены предподготовленные данные для проверки с юзерами и рецептами.

Для их загрузки следуйте указаниям:

!!Примечание: перед созданием рецептов убедитесь, что база ингредиентов загружена.!!

```bash
cd infra


docker compose exec backend python manage.py create_test_data
```


После запуска сервисы будут доступны по следующим адресам:

* [http://localhost](http://localhost) — фронтенд веб-приложения
* [http://localhost/api/docs/](http://localhost/api/) — документация
* [http://localhost/admin/](http://localhost/admin/) — панель администратора Django

## Переменные окружения

В файле `backend/.env` укажите:

```dotenv
POSTGRES_DB=foodgram
POSTGRES_USER=postgres
POSTGRES_PASSWORD=db_password
DB_HOST=db
DB_PORT=5432

DJANGO_SECRET_KEY=your_secret_key
DJANGO_DEBUG=False
DJANGO_ALLOWED_HOSTS=localhost,127.0.0.1
```

## Контейнеры и порты

| Сервис            | Контейнер          | Порт     |
| ----------------- | ------------------ | -------- |
| PostgreSQL        | `foodgram_db`      | 5432/tcp |
| Django + Gunicorn | `foodgram_backend` | 8000/tcp |
| Nginx (gateway)   | `foodgram_gateway` | 80/tcp   |

Статика (`/static`) и медиа-файлы (`/media`) хранятся в volume:

* `static_volume`
* `media_volume`

Данные PostgreSQL — в volume `pg_data`.

## CI/CD

GitHub Actions (`.github/workflows/main.yaml`) автоматически:

1. Прогоняет тесты Django в контейнере Postgres
2. Собирает Docker-образы для backend, frontend и gateway
3. Пушит их в Docker Hub 
