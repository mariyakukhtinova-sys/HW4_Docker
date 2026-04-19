# Домашнее задание 4. Dockerfile по правилам

**Автор:** Мария Кухтинова  
**Группа:** ДС-25/26  
**Дата:** 2026-04-19  
**Репозиторий:** `https://github.com/mariyakukhtinova-sys/HW4_Docker`  
**Адрес работающего приложения:** `http://72.56.39.50:30080/`

## Краткое описание приложения

В качестве примера было использовано небольшое веб-приложение на `FastAPI`.
Приложение запускается через `uvicorn` и предоставляет HTTP-эндпоинты для проверки работоспособности сервиса и выполнения простых операций с данными.

## 1. Написать Dockerfile для ML-приложения

Для сборки контейнера был подготовлен файл [Dockerfile](https://github.com/mariyakukhtinova-sys/HW4_Docker/blob/master/Dockerfile).

В нем:

- используется фиксированная версия базового образа `ubuntu:24.04`;
- зависимости устанавливаются в отдельной стадии сборки;
- в финальный образ копируется только необходимое для запуска приложение;
- приложение запускается через `uvicorn`.

Текст файла [Dockerfile](https://github.com/mariyakukhtinova-sys/HW4_Docker/blob/master/Dockerfile):

```dockerfile
# syntax=docker/dockerfile:1.7
FROM ubuntu:24.04 AS builder

WORKDIR /app

RUN apt-get update && \
    apt-get install -y python3 python3-pip python3-venv && \
    rm -rf /var/lib/apt/lists/*

COPY requirements.txt .

RUN --mount=type=cache,target=/root/.cache/pip \
    python3 -m venv /opt/venv && \
    /opt/venv/bin/pip install -r requirements.txt

FROM ubuntu:24.04

WORKDIR /app

LABEL org.opencontainers.image.source="https://github.com/mariyakukhtinova-sys/HW4_Docker"

RUN apt-get update && \
    apt-get install -y python3 && \
    rm -rf /var/lib/apt/lists/*

COPY --from=builder /opt/venv /opt/venv
COPY app.py .

ENV PATH="/opt/venv/bin:$PATH"

EXPOSE 8000

CMD ["uvicorn", "app:app", "--host", "0.0.0.0", "--port", "8000"]
```

Сборка образа выполнялась командой:

```bash
DOCKER_BUILDKIT=1 docker build -t hw4-app:latest .
```

Скриншот сборки образа:

![Сборка Docker-образа](<../screenshots/Screenshot 2026-04-18 at 21.39.20.png>)

Краткий вывод по этапу:

Dockerfile успешно собирается без ошибок и формирует рабочий образ приложения.

## 2. Использовать многостадийные сборки docker-образов для ML-приложения

Многостадийная сборка реализована в том же файле [Dockerfile](https://github.com/mariyakukhtinova-sys/HW4_Docker/blob/master/Dockerfile).

Ключевой фрагмент из [Dockerfile](https://github.com/mariyakukhtinova-sys/HW4_Docker/blob/master/Dockerfile):

```dockerfile
FROM ubuntu:24.04 AS builder
...
RUN --mount=type=cache,target=/root/.cache/pip \
    python3 -m venv /opt/venv && \
    /opt/venv/bin/pip install -r requirements.txt

FROM ubuntu:24.04
...
COPY --from=builder /opt/venv /opt/venv
COPY app.py .
```

В первой стадии `builder` устанавливаются зависимости и создается виртуальное окружение.
Во второй стадии формируется финальный образ, в который копируются готовое окружение и файл приложения.
На этапе сборки используется кеширование `pip`-зависимостей через BuildKit.

Краткий вывод по этапу:

Требование по многостадийной сборке выполнено: зависимости собираются отдельно, а финальный образ содержит только необходимые для запуска компоненты.

## 3. Настроить внешние и внутренние сети, тома хранения (volumes) и рестарт в docker-compose файле

Для локального запуска был подготовлен файл [docker-compose.yml](https://github.com/mariyakukhtinova-sys/HW4_Docker/blob/master/docker-compose.yml).

Локальный файл `.env` создается отдельно и не хранится в репозитории. Шаблон переменных вынесен в [.env.example](https://github.com/mariyakukhtinova-sys/HW4_Docker/blob/master/.env.example).

Текст файла [docker-compose.yml](https://github.com/mariyakukhtinova-sys/HW4_Docker/blob/master/docker-compose.yml):

```yaml
services:
  app:
    build:
      context: .
      dockerfile: Dockerfile
    image: hw4-app:latest
    container_name: hw4_app
    env_file:
      - .env
    restart: unless-stopped
    ports:
      - "8000:8000"
    depends_on:
      db:
        condition: service_healthy
    networks:
      - external
      - internal
    profiles:
      - dev
      - prod
    mem_limit: 512m
    cpus: "0.50"
    deploy:
      resources:
        reservations:
          memory: 256m
          cpus: "0.25"

  db:
    image: postgres:16
    container_name: hw4_db
    env_file:
      - .env
    restart: unless-stopped
    networks:
      - internal
    volumes:
      - postgres_data:/var/lib/postgresql/data
    profiles:
      - dev
      - prod
    healthcheck:
      test: ["CMD-SHELL", "pg_isready -U ${POSTGRES_USER} -d ${POSTGRES_DB}"]
      interval: 10s
      timeout: 5s
      retries: 5
      start_period: 10s
    mem_limit: 512m
    cpus: "0.50"
    deploy:
      resources:
        reservations:
          memory: 256m
          cpus: "0.25"

networks:
  internal:
    driver: bridge
    internal: true
  external:
    driver: bridge

volumes:
  postgres_data:
```

В конфигурации:

- описаны сервисы `app` и `db`;
- настроены внутренняя и внешняя сети;
- для PostgreSQL подключен volume;
- задана политика перезапуска контейнеров `restart: unless-stopped`.

Основная команда запуска:

```bash
docker compose --profile dev up -d
```

Скриншот запуска сервисов через `docker compose`:

![Запуск сервисов через docker compose](<../screenshots/Screenshot 2026-04-18 at 13.36.14.png>)

Краткий вывод по этапу:

Сети, volume и политика рестарта настроены корректно, контейнеры запускаются без ошибок.

## 4. Настроить минимальные и максимальные границы памяти и ЦПУ в docker-compose файле

Ограничения CPU и памяти заданы в том же файле [docker-compose.yml](https://github.com/mariyakukhtinova-sys/HW4_Docker/blob/master/docker-compose.yml).

Фрагмент из [docker-compose.yml](https://github.com/mariyakukhtinova-sys/HW4_Docker/blob/master/docker-compose.yml), отвечающий за ресурсы:

```yaml
app:
  mem_limit: 512m
  cpus: "0.50"
  deploy:
    resources:
      reservations:
        memory: 256m
        cpus: "0.25"

db:
  mem_limit: 512m
  cpus: "0.50"
  deploy:
    resources:
      reservations:
        memory: 256m
        cpus: "0.25"
```

Для обоих сервисов указаны:

- верхняя граница памяти и CPU;
- резервирование части ресурсов через `deploy.resources.reservations`.

Краткий вывод по этапу:

Минимальные и максимальные границы потребления ресурсов в `docker-compose.yml` заданы.

## Публикация образа в GitHub Container Registry

После сборки контейнерный образ был опубликован в `GHCR`, чтобы затем использовать его в Kubernetes.

Использованные команды:

```bash
docker tag hw4-app:latest ghcr.io/mariyakukhtinova-sys/hw4-app:latest
docker push ghcr.io/mariyakukhtinova-sys/hw4-app:latest
```

Скриншот отправки образа в `GHCR`:

![Публикация образа в GHCR](<../screenshots/Screenshot 2026-04-18 at 14.32.30.png>)

Краткий вывод по этапу:

Образ успешно опубликован в контейнерный реестр GitHub и может использоваться при развертывании в Kubernetes.

## 5. Написать базовый деплой сервиса в Kubernetes, используя YAML-файлы

Для Kubernetes был подготовлен файл [k8s.yaml](https://github.com/mariyakukhtinova-sys/HW4_Docker/blob/master/k8s.yaml).

Секрет `hw4-db-secret` создается отдельно перед развертыванием и не хранится в репозитории.
Аналогично локальному `.env`, он содержит чувствительные значения, поэтому формируется вручную вне репозитория.

Пример создания секрета:

```bash
sudo k3s kubectl create secret generic hw4-db-secret \
  --from-literal=POSTGRES_USER=your_postgres_user \
  --from-literal=POSTGRES_PASSWORD=your_postgres_password \
  --from-literal=POSTGRES_DB=your_postgres_db
```

Текст файла [k8s.yaml](https://github.com/mariyakukhtinova-sys/HW4_Docker/blob/master/k8s.yaml):

```yaml
apiVersion: v1
kind: PersistentVolumeClaim
metadata:
  name: postgres-pvc
spec:
  accessModes:
    - ReadWriteOnce
  resources:
    requests:
      storage: 1Gi

---
apiVersion: apps/v1
kind: Deployment
metadata:
  name: hw4-db
spec:
  replicas: 1
  selector:
    matchLabels:
      app: hw4-db
  template:
    metadata:
      labels:
        app: hw4-db
    spec:
      containers:
        - name: postgres
          image: postgres:16
          ports:
            - containerPort: 5432
          envFrom:
            - secretRef:
                name: hw4-db-secret
          volumeMounts:
            - name: postgres-storage
              mountPath: /var/lib/postgresql/data
          resources:
            limits:
              memory: "512Mi"
              cpu: "500m"
      volumes:
        - name: postgres-storage
          persistentVolumeClaim:
            claimName: postgres-pvc

---
apiVersion: v1
kind: Service
metadata:
  name: hw4-db
spec:
  selector:
    app: hw4-db
  ports:
    - port: 5432
      targetPort: 5432
  type: ClusterIP

---
apiVersion: apps/v1
kind: Deployment
metadata:
  name: hw4-app
spec:
  replicas: 1
  selector:
    matchLabels:
      app: hw4-app
  template:
    metadata:
      labels:
        app: hw4-app
    spec:
      containers:
        - name: hw4-app
          image: ghcr.io/mariyakukhtinova-sys/hw4-app:latest
          ports:
            - containerPort: 8000
          env:
            - name: POSTGRES_DB
              valueFrom:
                secretKeyRef:
                  name: hw4-db-secret
                  key: POSTGRES_DB
            - name: POSTGRES_USER
              valueFrom:
                secretKeyRef:
                  name: hw4-db-secret
                  key: POSTGRES_USER
            - name: POSTGRES_PASSWORD
              valueFrom:
                secretKeyRef:
                  name: hw4-db-secret
                  key: POSTGRES_PASSWORD
            - name: DB_HOST
              value: hw4-db
            - name: DB_PORT
              value: "5432"
          resources:
            limits:
              memory: "512Mi"
              cpu: "500m"

---
apiVersion: v1
kind: Service
metadata:
  name: hw4-app-service
spec:
  selector:
    app: hw4-app
  ports:
    - port: 8000
      targetPort: 8000
      nodePort: 30080
  type: NodePort
```

Команды деплоя:

```bash
sudo k3s kubectl apply -f k8s.yaml
sudo k3s kubectl get pods
sudo k3s kubectl get svc
```

Скриншот списка pod'ов и сервисов:

![Pods и Services в Kubernetes](<../screenshots/Screenshot 2026-04-18 at 19.37.39.png>)

Краткий вывод по этапу:

Манифест успешно применился, pod'ы перешли в состояние `Running`, сервис приложения опубликован через `NodePort`.

## Проверка работоспособности сервиса

После запуска контейнеров и развертывания в Kubernetes была выполнена проверка работы API через `curl`.
Внутри контейнера приложение использует порт `8000`, а для внешнего доступа в Kubernetes используется `NodePort 30080`.

Примеры команд:

```bash
curl http://72.56.39.50:30080/

curl -X POST http://72.56.39.50:30080/items/1 \
  -H "Content-Type: application/json" \
  -d '{"name":"test item","description":"first item"}'

curl http://72.56.39.50:30080/items/1
```

Скриншот проверки API:

![Проверка API через curl](<../screenshots/Screenshot 2026-04-18 at 19.51.05.png>)

Краткий вывод по этапу:

Приложение отвечает на HTTP-запросы, создание и получение объекта выполняются без ошибок.

## 6. Итоговое оформление

### Пошаговая инструкция выполнения каждого этапа

1. Склонировать репозиторий `HW4_Docker`.
2. Подготовить локальный файл `.env` отдельно на основе [.env.example](https://github.com/mariyakukhtinova-sys/HW4_Docker/blob/master/.env.example), не коммитя реальные секреты в репозиторий.
3. Собрать Docker-образ приложения командой `DOCKER_BUILDKIT=1 docker build -t hw4-app:latest .`.
4. Поднять сервисы через `docker compose --profile dev up -d`.
5. Проверить локальную работоспособность контейнеров и API.
6. Присвоить образу тег `ghcr.io/mariyakukhtinova-sys/hw4-app:latest` и отправить его в `GHCR`.
7. Создать в Kubernetes секрет `hw4-db-secret` отдельно от репозитория, не сохраняя реальные значения в YAML-файлах.
8. Применить манифест [k8s.yaml](https://github.com/mariyakukhtinova-sys/HW4_Docker/blob/master/k8s.yaml) командой `kubectl apply -f k8s.yaml`.
9. Проверить состояние `pods` и `services`.
10. Проверить доступность приложения по внешнему адресу `http://72.56.39.50:30080/`.

### Выводы

В ходе выполнения работы я подготовила контейнеризированное веб-приложение и описала процесс его сборки в `Dockerfile`.
Использование многостадийной сборки позволило отделить установку зависимостей от финального образа приложения.
Также был настроен запуск нескольких сервисов через `docker-compose`, включая сети, volume, политику перезапуска и ограничения по ресурсам.
Затем контейнерный образ был опубликован в `GitHub Container Registry`, что позволило использовать его при развертывании в Kubernetes.
Для Kubernetes был подготовлен YAML-манифест, описывающий приложение и вспомогательные ресурсы.
Наиболее полезной частью работы стало понимание того, как связаны между собой Docker-образ, compose-конфигурация, контейнерный реестр и Kubernetes-манифесты.
Наибольшие трудности были связаны с правильной последовательностью пересборки образа, его публикации и обновления деплоя.
В результате я получила целостное представление о базовом процессе контейнеризации и развертывания приложения.
