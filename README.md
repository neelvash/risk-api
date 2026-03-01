# Risk Alert & Transaction API

A production-ready, cloud-native REST API built with Python (FastAPI) and PostgreSQL. This microservice is designed to simulate enterprise financial transaction processing, enforcing strict business-logic rules, automated risk/fraud alerting, and comprehensive system observability.

![image](https://github.com/user-attachments/assets/c52c112e-5c80-4a58-ab97-978c33fe7aed)

## Overview

This project was developed to demonstrate practical capability in backend software engineering, specifically focusing on building reliable, scalable, and secure API integrations for business-critical financial services. 

It handles transaction payloads, validates them against relational database records, enforces risk controls (e.g. fraud limits, balance checks), and exposes real-time application monitoring metrics.

## Key Features (Risk & Controls)

* **Business Logic Validation:** Automatically declines transactions if an account has insufficient funds.
* **Automated Fraud Alerting:** Any transaction exceeding £10,000 is intercepted, prevented from deducting funds, and flagged as `flagged_for_fraud` in the database.
* **Secure API Integrations:** All endpoints are protected via an `X-API-Key` dependency injection.
* **Observability & Monitoring:** Fully instrumented with Prometheus to track API latency, request volume, and a custom `fraud_alerts_total` metric.
* **Automated Testing:** Comprehensive unit testing using `pytest` covering happy paths, exception handling, and security breaches.

## Tech Stack

* **Core Language:** Python 3.10
* **API Framework:** FastAPI (with Pydantic for data validation/serialisation)
* **Database:** PostgreSQL & SQLAlchemy (ORM for relational schema design)
* **Infrastructure / Cloud-Native:** Docker & Docker Compose
* **Observability:** Prometheus & Python `logging`
* **Testing:** Pytest & FastAPI `TestClient`

## Database Schema Design

The application uses a relational schema with two primary tables:
1. `accounts`: Stores `id`, `customer_name`, `balance`, and `status`.
2. `transactions`: Stores `id`, `account_id` (Foreign Key), `amount`, `timestamp`, and `status`.

*On startup, the application automatically seeds the database with a test user (Account ID: 1, Balance: £100,000) for seamless testing.*

## Getting Started (Local Deployment)

Because this application is fully containerised, you can spin up the API, PostgreSQL database, and Prometheus monitoring in seconds without installing local dependencies.

### Prerequisites
* Docker & Docker Compose installed on your machine.

### Run the Application
1. Clone the repository:
   ```bash
   git clone https://github.com/neelvash/risk-api.git
   cd risk-api
   ```
2. Start the services using Docker Compose:
   ```bash
   docker compose up --build -d
   ```
3. The API will now be running at `http://localhost:8000`.

### Teardown
To stop the application and wipe the ephemeral database clean:
```bash
docker compose down
```

## API Documentation & Usage

FastAPI automatically generates interactive API documentation. Once the Docker containers are running, navigate to:

**[http://localhost:8000/docs](http://localhost:8000/docs)**

### Available Endpoints
* `POST /transactions/` - Submit a new transaction payload.
* `GET /accounts/{id}/statement` - Retrieve account balance and a history of recent transactions.
* `GET /metrics` - Exposes system health and custom metrics for Prometheus scraping.

**Security:** To test the endpoints in the Swagger UI, click **"Authorize"** or "Try it out" and provide the required API Key: `super-secret-key`.

## Running Automated Tests

The project includes an isolated testing environment that utilises an ephemeral SQLite database to ensure the production database remains untouched.

To run the test suite locally:
```bash
# Create a virtual environment and install dependencies
python -m venv venv
source venv/bin/activate  # On Windows use: venv\Scripts\activate
pip install -r requirements.txt

# Run Pytest
pytest test_main.py -v
```

## Application Monitoring

Prometheus is configured to scrape the API every 5 seconds. Once the application is running, you can view the raw metrics at `http://localhost:8000/metrics`. 

To view the specific custom fraud metric, search the metrics page for:
```text
fraud_alerts_total
```
This counter increments automatically every time the risk-control logic intercepts a transaction over £10,000.
