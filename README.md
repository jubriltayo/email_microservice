# 📨 Distributed Notification System

A scalable, microservices-based notification platform that handles email and push notifications through asynchronous message queues.
Built for enterprise-grade reliability with:
- High Throughput: 1,000+ notifications/minute
- Delivery Success Rate: 99.5%+
- API Gateway Response Time: <100ms

---

## Table of contents

- [Project Overview](#-project-overview)
- [System Architecture](#-system-architecture)
- [Features](#-features)
- [Tech Stack](#-tech-stack)
- [Setup Instructions](#-setup-instructions)
- [Microservices & Responsibilities](#-microservices--responsibilities)
- [API Documentation](#-api-documentation)
- [Message Queue Setup](#-message-queue-setup)
- [Idempotency & Deduplication](#-idempotency--deduplication)
- [Retry Strategy & Dead-letter Queue](#-retry-strategy--dead-letter-queue)
- [Circuit Breaker & Failure Handling](#-circuit-breaker--failure-handling)
- [Service Discovery & Health Checks](#-service-discovery--health-checks)
- [Databases](#-databases)
- [Security & Auth](#-security--auth)
- [Local Dev (docker-compose)](#-local-dev-docker-compose)
- [CI/CD (GitHub Actions)](#-cicd-github-actions)
- [Contributing](#-contributing)

---

## 🧩 Project Overview
This project implements a distributed notification system where independent microservices handle specific responsibilities:
- **API Gateway Service:** Auth, validation, routing to queues, and status tracking
- **User Service:** Manages user contact info (emails, push tokens, preferences)
- **Email Service:** Sends transactional and bulk emails
- **Push Service:** Sends push notifications to devices
- **Template Service:** Stores and manages notification templates (multi-language & versioned)

**Shared Infrastructure:**
- RabbitMQ (message queue)
- Redis (caching/idempotency).

---

## 🏗️ System Architecture
```pgsql

┌─────────────┐
│   Client    │
└──────┬──────┘
       │
       ▼
┌─────────────────┐
│  API Gateway    │◄────┐
│   (Port 3000)   │     │
└────────┬────────┘     │
         │              │
         ▼              │
┌─────────────────┐     │
│   RabbitMQ      │     │
│   Exchange      │     │
└────┬───────┬────┘     │
     │       │          │
     ▼       ▼          │
┌────────┐ ┌────────┐   │
│ Email  │ │  Push  │   │
│ Queue  │ │ Queue  │   │
└───┬────┘ └───┬────┘   │
    │          │        │
    ▼          ▼        │
┌────────┐ ┌────────┐   │
│ Email  │ │  Push  │   │
│Service │ │Service │   │
└───┬────┘ └───┬────┘   │
    │          │        │
    └──────┬───┘        │
           │            │
    ┌──────▼─────┐      │
    │  Template  │      │
    │  Service   │      │
    └──────┬─────┘      │
           │            │
    ┌──────▼─────┐      │
    │   User     │      │
    │  Service   │──────┘
    └────────────┘

┌─────────────────────────────────────┐
│  Shared Infrastructure              │
│  • PostgreSQL (User, Template DB)   │
│  • Redis (Cache, Idempotency)       │
│  • RabbitMQ (Message Queue)         │
└─────────────────────────────────────┘
```

---

## 🚀 Features
Core Capabilities

- **Multi-Channel Notifications:** Email and Push notifications
- **Asynchronous Processing:** RabbitMQ message queue for scalability
- **Template Management:** Dynamic templates with variable substitution
- **User Preferences:** Per-user notification settings
- **Idempotency:** Prevent duplicate notifications
- **Circuit Breaker:** Fault tolerance and resilience
- **Retry Mechanism:** Exponential backoff for failed deliveries
- **Dead Letter Queue:** Handle permanently failed messages
- **Health Monitoring:** Service health checks and metrics
- **Correlation Tracking:** End-to-end request tracing

**Enterprise Features**
- 🔒 JWT Authentication
- 📊 Real-time Metrics
- 🔄 Horizontal Scaling
- 📝 Comprehensive Logging
- 🎯 99.5%+ Delivery Success Rate
- ⚡ <100ms API Gateway Response Time

---

## 🛠️ Tech Stack

| Component            | Technology                      |
| -------------------- | ------------------------------- |
| **Languages**        | Node.js (Fastify), Java, Python |
| **Message Queue**    | RabbitMQ                        |
| **Databases**        | PostgreSQL, Redis               |
| **Containerization** | Docker, Docker Compose          |
| **CI/CD**            | GitHub Actions                  |
| **Monitoring**       | Prometheus, Grafana             |
| **Docs**             | OpenAPI / Swagger               |

---

## ⚙️ Setup Instructions

### Prerequisites
- Node.js >= 20
- Python >= 3.11
- Java 17+
- Docker & Docker Compose
- RabbitMQ (for messaging)
- Redis (for caching)
- PostgreSQL 

---

### 🚦 Quick Start

1. **Clone Repository**
```bash
git clone https://github.com/NecheRose/distributed-notification-system.git
cd distributed-notification-system
```

2. **Configure Environment Variables**

`API Gateway Service`
```bash
PORT=
NODE_ENV=development
JWT_SECRET=your_jwt_secret_key_here
REDIS_URL=
RABBITMQ_URL=
USER_SERVICE_URL=
TEMPLATE_SERVICE_URL=
CORRELATION_ID_HEADER=x-correlation-id
RATE_LIMIT_WINDOW=
RATE_LIMIT_MAX_REQUESTS=
```

`User Service`
```bash
PORT=
NODE_ENV=development
DATABASE_URL=
REDIS_URL=
JWT_SECRET=your_jwt_secret_key_here
JWT_EXPIRY=
CACHE_TTL=
```

`Email Service`
```bash
PORT=
NODE_ENV=development
RABBITMQ_URL=
SMTP_HOST=smtp.gmail.com
SMTP_PORT=587
SMTP_USER=your_email@gmail.com
SMTP_PASSWORD=your_app_password
SMTP_FROM=noreply@yourapp.com
TEMPLATE_SERVICE_URL=
MAX_RETRY_ATTEMPTS=
RETRY_DELAY_MS=
```

`Push Service`
```bash
PORT=
NODE_ENV=development
RABBITMQ_URL=
FCM_SERVER_KEY=your_fcm_server_key
FCM_PROJECT_ID=your_fcm_project_id
TEMPLATE_SERVICE_URL=
MAX_RETRY_ATTEMPTS=3
RETRY_DELAY_MS=1000
```

`Template Service`
```bash
PORT=
NODE_ENV=development
DATABASE_URL=
REDIS_URL=
CACHE_TTL=
DEFAULT_LANGUAGE=en
```

---

### Running Locally
Each service lives under the `services/` directory.
You can run them individually or with Docker Compose.

**Start all services:**

```bash
docker-compose up --build
```

**Run a single service:**

```bash
# Example: Push Service
cd services/push-service
npm install
npm run dev
```

---

### 🧪 Testing
Each service includes unit and integration tests.

**Run tests per service:**

```bash
# Node
npm test

# Python
pytest

# Java
mvn test
```

**Note:** Integration tests require RabbitMQ and Redis to be running.

---

## 📦 Microservices & Responsibilities

### 1. API Gateway Service

- Entry point for all notification requests
- Request validation and authentication
- Routes messages to the correct queue (email or push)
- Tracks notification status
- Implements idempotency checks

### 2. User Service 

- Manages user contact information (email, push tokens)
- Stores notification preferences
- Handles authentication and authorization
- Provides REST APIs for user management

### 3. Email Service 

- Reads messages from the email queue
- Fills email templates with variables (e.g., {{name}})
- Sends emails via SMTP/SendGrid/Mailgun
- Handles delivery confirmations and bounces

### 4. Push Service 

- Reads messages from the push queue
- Sends mobile/web push notifications via Free Push Options: Firebase Cloud Messaging (FCM), OneSignal or Web Push with VAPID
- Validates device tokens
- Supports rich notifications (images, links etc)

### 5. Template Service 

- Stores and manages notification templates
- Handles variable substitution ({{name}}, {{email}})
- Supports multiple languages
- Keeps version history for templates

**Tech Stack per Service**

| Service          | Language | Framework      |
|------------------|----------|----------------|
| API Gateway      | Python   | Django         |
| Email Service    | Python   | Django         |
| Push Service     | Node.js  | Fastify        |
| Template Service | Java     | Spring Boot    |
| User Service     | Java     | Spring Boot    |

--- 

## 📘 API Documentation

See detailed API reference → [API docs]()

---

## 🧵 Message Queue Setup
The RabbitMQ broker is the backbone of the system’s asynchronous processing.

**Exchanges**

| Exchange                | Type    | Purpose                                                   |
|-------------------------|---------|---------------------------------------------------------- |
| `notifications.direct`  | `topic` | Routes messages to the correct service queue (email/push) |

**Queues**

| Queue         | Bound Key     | Consumer Service      |
| --------------|---------------|-----------------------|
| `email.queue` | `email.send`  | Email Service         |
| `push.queue`  | `push.send`   | Push Service          |
| `failed.queue`| `dead.letter` | Dead Letter Queue     |

**Bindings**

```less
notifications.direct -> email.queue (routing key: email.send)
notifications.direct -> push.queue (routing key: push.send)
```

**Each message includes:**
- correlationId
- retryCount
- timestamp
- payload (data specific to notification type)

---

## 🧠 Idempotency & Deduplication
To ensure the same notification isn’t processed twice:

- Each request includes a unique correlationId
- The API Gateway checks Redis for an existing key before enqueueing
- Redis TTL defines how long correlation IDs are stored (e.g., 24 hours)
- Duplicate requests return:

```json
{
  "status": "duplicate",
  "correlationId": "abc-123"
}
```

---

## 🔁 Retry Strategy & Dead-letter Queue

**When message delivery fails:**
- Message is retried using exponential backoff

- Retry count is incremented in message metadata

- After max retries, it moves to the Dead Letter Queue (DLQ)

**Retry logic example:**

```nginx
Attempt 1 → Delay 1s  
Attempt 2 → Delay 2s  
Attempt 3 → Delay 4s  
Attempt 4 → DLQ
```

**Note:** The DLQ is monitored via RabbitMQ Prometheus Plugin and Grafana dashboard.

---

## ⚡ Circuit Breaker & Failure Handling

Each service uses a circuit breaker (e.g., opossum in Node, resilience4j in Java) to:
- Detect downstream service failures (e.g., Template or SMTP)
- Temporarily halt requests to avoid cascading failures
- Automatically reset after cooldown

When open:
```json
{
  "status": "unavailable",
  "message": "Email service temporarily unavailable"
}
```

Circuit breaker state changes are published to Prometheus for alerting.

---

## 🔍 Service Discovery & Health Checks

Services register and monitor each other through REST endpoints or container networking.

**Health endpoint example:**
```bash
GET /health
```

**Response:**
```json
{
  "status": "healthy",
  "dependencies": {
    "rabbitmq": "ok",
    "redis": "ok",
    "db": "ok"
  }
}
```

In Docker, service discovery happens via **Docker internal DNS.**
Each service is accessible using its container name, e.g. http://user-service:5000.

---

🗄️ Databases

| Component      | Technology      | Purpose                                                                |
| ---------------|-----------------|------------------------------------------------------------------------|
| **PostgreSQL** | Relational DB   | Stores user data, templates, preferences                               |
| **Redis**      | In-memory cache | Used for caching templates, user preferences, managing rate limits etc |
| **RabbitMQ**   | Broker          | Handles message queuing                                                |

**Caching Strategy**
- Frequently accessed templates and user preferences are cached in Redis.
- Cache TTL = 1 hour (configurable per service).
- Cache invalidation occurs on template updates or preference changes.

```md
Each service maintains its own schema (database-per-service pattern).
```
This reinforces microservice isolation.

---

## 🔒 Security & Auth

- All endpoints protected via JWT authentication
- JWTs are validated at the API Gateway layer
- Sensitive environment variables are stored in `.env` file

**Example request header:**

```makefile
Authorization: Bearer <jwt_token>
```

---

## 🧰 Local Dev (Docker Compose)

Local setup uses Docker Compose for consistent environments.

**Compose Services**
- `api-gateway`
- `user-service`
- `email-service`
- `push-service`
- `template-service`
- `rabbitmq`
- `redis`
- `postgres`

**Start all:**
```bash
docker-compose up --build
```

**Stop all**
```bash
docker-compose down
```

Ports and environment variables are configurable via .env files per service.

---

## ⚙️ CI/CD (GitHub Actions)
Each microservice includes a workflow in .github/workflows.

**Pipeline Stages:**
1. **Build:** Install dependencies and compile code
2. **Test:** Run unit and integration tests
3. **Dockerize:** Build Docker images
4. **Deploy:** Push image to registry and deploy to server

**Example job snippet:**

```yaml
jobs:
  build:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4
      - run: npm ci
      - run: npm test
```

---

## 🤝 Contributing
1. Fork the repository.
2. Create a feature branch: 

```bash
git checkout -b feature/my-feature
```

3. Commit changes: 

```bash
git commit -m "Add new feature"
```

4. Push to branch: 

```bash
git push origin feature/my-feature
```

5. Open a Pull Request.
