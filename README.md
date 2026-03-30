Cryptocurrency Trigger Tracking API
A robust backend service designed to monitor cryptocurrency markets and execute custom price triggers. Built with performance and scalability in mind, utilizing asynchronous background tasks to handle real-time data processing without blocking the main application.


Tech Stack
Backend Framework: FastAPI (Python 3.x)
Database: PostgreSQL, SQLAlchemy (ORM)
Asynchronous Processing: Celery, Redis 
Infrastructure & Tools: Docker, Docker Compose, Alembic, python-dotenv


Features
RESTful API endpoints for managing cryptocurrency trackers.
Asynchronous background workers for continuous market monitoring.
Relational database architecture for efficient user and trigger data storage.
Fully containerized environment for easy deployment.


Local Setup

Prerequisites:

  Docker and Docker Compose installed on your machine.

Installation Steps:

  Clone the repository:
    git clone https://github.com/твоє-посилання/crypto-tracker.git
    cd crypto-tracker

Create a .env file in the root directory and add your environment variables (see .env.example for reference):
  SECRET_KEY=super_secret_key_change_me_please
  CELERY_BROKER_URL=redis://redis:6379/0
  DATABASE_URL=postgresql+asyncpg://user:password@db:5432/crypto_portfolio_db
  # Add other necessary API keys here

Build and start the containers:
  docker-compose up --build
  
The API will be available at http://localhost:8000.



API Documentation
Once the application is running, you can access the interactive API documentation (Swagger UI) at:
  http://localhost:8000/docs
