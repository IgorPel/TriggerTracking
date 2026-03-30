# Cryptocurrency Trigger Tracking API

A robust backend service designed to monitor cryptocurrency markets and execute custom price triggers. Built with performance and scalability in mind, this API utilizes asynchronous background tasks to handle real-time data processing without blocking the main application.

## 🚀 Tech Stack

* **Backend Framework:** FastAPI (Python 3.x)
* **Database:** PostgreSQL, SQLAlchemy (ORM), asyncpg
* **Asynchronous Processing:** Celery, Redis
* **Infrastructure & Tools:** Docker, Docker Compose, Alembic, python-dotenv

## ✨ Features

* RESTful API endpoints for managing cryptocurrency trackers.
* Asynchronous background workers for continuous market monitoring.
* Relational database architecture for efficient user and trigger data storage.
* Automated database migrations using Alembic.
* Fully containerized environment for easy and consistent deployment.

## ⚙️ Local Setup

### Prerequisites
* [Docker](https://www.docker.com/) and Docker Compose installed on your machine.

### Installation Steps

1. **Clone the repository:**
   ```bash
   git clone [[https://github.com/yourusername/TriggerTracking.git](https://github.com/yourusername/TriggerTracking.git)]
   cd crypto-tracker
2. **Environment Variables:**
   *Create a .env file in the root directory and add your environment variables (see .env.example for reference):
    ```Фрагмент коду
    SECRET_KEY=super_secret_key_change_me_please
    CELERY_BROKER_URL=redis://redis:6379/0
    DATABASE_URL=postgresql+asyncpg://user:password@db:5432/crypto_portfolio_db
3. **Build and start the containers:**
    ```bash
    docker-compose up --build

  The API will be available at http://localhost:8000.


## 📚 API Documentation

### FastAPI automatically generates interactive documentation. Once the application is running, you can explore and test the endpoints at:

  * Swagger UI: http://localhost:8000/docs
  * ReDoc: http://localhost:8000/redoc

## 📂 Project Structure
```Plaintext
  app/
  ├── api/          # API routers and endpoints
  ├── core/         # Configuration, security, and settings
  ├── db/           # Database sessions and migrations
  ├── schemas/      # Pydantic models for validation
  ├── services/     # Business logic and Celery tasks
  └── main.py       # FastAPI application instance
