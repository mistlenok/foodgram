## Foodgram

Фудграм - сервис, на котором пользователи могут публиковать свои рецепты, добавлять чужие рецепты в избранное и подписываться на публикации других авторов. Зарегистрированным пользователям также доступен сервис «Список покупок». Он позволяет создавать список продуктов, которые нужно купить для приготовления выбранных блюд.

## Стек технологий

- **Django**
- **Django REST Framework**
- **PostgreSQL**
- **Docker**
- **Nginx**

## Как развернуть проект

1. Клонируйте репозиторий и перейдите в директорию проекта:

   ```bash
   git clone https://github.com/mistlenok/foodgram.git
   cd foodgram
   ```

2. Создайте и активируйте виртуальное окружение:

   ```bash
   python -m venv venv
   source venv/Scripts/activate  # для Windows
   source venv/bin/activate      # для Linux/MacOS
   ```

3. Установите зависимости:

   ```bash
   pip install -r requirements.txt
   ```

4. Создайте пустой файл для переменных окружения, откройте его и заполните по аналогии с .env.example в корневой директории проекта:

   ```bash
   touch .env
   nano .env
   ```

## Как создать Docker образы

1. Замените DOCKERHUB_USERNAME на свой логин в DockerHub:

   ```
   cd frontend
   docker build -t DOCKERHUB_USERNAME/foodgram_frontend .
   cd ../backend
   docker build -t DOCKERHUB_USERNAME/foodgram_backend .
   cd ../nginx
   docker build -t DOCKERHUB_USERNAME/foodgram_gateway .
   ```

2. Загрузите созданные образы на свой DockerHub:

   ```bash
   docker push DOCKERHUB_USERNAME/foodgram_frontend
   docker push DOCKERHUB_USERNAME/foodgram_backend
   docker push DOCKERHUB_USERNAME/foodgram_gateway
   ```

## Как запустить проект на сервере
 
1. Подключитесь к своему серверу:

   ```bash
   ssh -i PATH_TO_SSH_KEY/SSH_KEY_NAME YOUR_USERNAME@SERVER_IP_ADDRESS 
   ```

2. Создайте на сервере директорию foodgram:

   ```bash
   mkdir foodgram 
   ```

3. Установите на своем сервере Docker Compose:

   ```bash
   sudo apt update
   sudo apt install curl
   curl -fsSL https://get.docker.com -o get-docker.sh
   sudo sh get-docker.sh
   sudo apt install docker-compose
   ```

4. Скопируйте docker-compose.production.yml и .env в директорию foodgram/ на своем сервере:
   ```bash
   scp -i PATH_TO_SSH_KEY/SSH_KEY_NAME docker-compose.production.yml YOUR_USERNAME@SERVER_IP_ADDRESS:/home/YOUR_USERNAME/foodgram/docker-compose.production.yml
   ```

5. Запустите Docker Compose:

   ```bash
   sudo docker-compose -f /home/YOUR_USERNAME/foodgram/docker-compose.production.yml up -d
   ```

6. Выполните миграцию и сборку статических файлов, а также их копирование в директорию /backend_static/static/

   ```bash
   sudo docker-compose -f /home/YOUR_USERNAME/foodgram/docker-compose.production.yml exec backend python manage.py migrate
   sudo docker-compose -f /home/YOUR_USERNAME/foodgram/docker-compose.production.yml exec backend python manage.py collectstatic
   sudo docker-compose -f /home/YOUR_USERNAME/foodgram/docker-compose.production.yml exec backend cp -r /app/collected_static/. /backend_static/static/
   ```
6.1. Можно добавить данные по ингредиентам из заранее подготовленного json файла. Для этого нужно выполнить команду:
   ```bash
   sudo docker-compose -f /home/YOUR_USERNAME/foodgram/docker-compose.production.yml exec backend python manage.py load_data
   ```

7. Откройте файл конфигурации Nginx:

   ```bash
   sudo nano /etc/nginx/sites-enabled/default
   ```

8. В разделе server измените настройки location:

   ```
   location / {
    proxy_set_header Host $http_host;
    proxy_pass http://127.0.0.1:8013;
   }
   ```

9. Запустите проверку конфигурации Nginx:

   ```bash
   sudo nginx -t
   ```

10. Перезапустите Nginx:

   ```bash
   sudo service nginx reload
   ```

## Автор

[Татьяна Харченко](https://github.com/mistlenok)
