# Credit System

## Demo

[![Demo Video](https://img.youtube.com/vi/Lr6vd0VW8DU/0.jpg)](https://youtu.be/Lr6vd0VW8DU)

[Watch the demo video on YouTube](https://youtu.be/Lr6vd0VW8DU)

A Django REST API for a Credit Approval System, built with Django, Django REST Framework, Celery, Redis, and PostgreSQL. The system ingests customer and loan data from Excel files and provides endpoints for customer registration, loan eligibility checks, loan creation, and loan viewing.

---

## Features
- Customer and loan data ingestion from Excel files
- RESTful API endpoints for registration, eligibility, loan creation, and loan viewing
- Credit score and eligibility logic as per assignment
- Dockerized for easy setup
- Asynchronous data ingestion with Celery and Redis

---

## Tech Stack
- Python 3.10
- Django 5+
- Django REST Framework
- PostgreSQL 17
- Celery + Redis
- Docker & Docker Compose

---

## Setup Instructions

### 1. Clone the Repository
```sh
git clone https://github.com/Nalwa-Jayesh/credit-system.git
cd credit-system
```

### 2. Build and Start the Services
```sh
docker compose up --build
```
This will start the web server, PostgreSQL, Redis, and Celery worker.

### 3. Run Migrations
```sh
docker compose exec web python manage.py makemigrations

docker compose exec web python manage.py migrate
```

### 4. Ingest Data from Excel Files
```sh
docker compose exec web python manage.py load_data
```
This will load data from `data/customer_data.xlsx` and `data/loan_data.xlsx`.

### 5. (Optional) Create a Superuser
```sh
docker compose exec web python manage.py createsuperuser
```

---

## API Endpoints

### 1. Register Customer
`POST /register`
- Request: `{ "first_name", "last_name", "age", "monthly_income", "phone_number" }`
- Response: Customer details with approved limit

### 2. Check Loan Eligibility
`POST /check-eligibility`
- Request: `{ "customer_id", "loan_amount", "interest_rate", "tenure" }`
- Response: Approval status, corrected interest rate, monthly installment

### 3. Create Loan
`POST /create-loan`
- Request: `{ "customer_id", "loan_amount", "interest_rate", "tenure" }`
- Response: Loan approval, loan ID, message, monthly installment

### 4. View Loan
`GET /view-loan/<loan_id>`
- Response: Loan details and nested customer details

### 5. View Loans by Customer
`GET /view-loans/<customer_id>`
- Response: List of all loans for the customer, with repayments left

---

## Data Model

### Customer
- `customer_id` (int, primary key)
- `first_name` (str)
- `last_name` (str)
- `phone_number` (str)
- `age` (int)
- `monthly_salary` (float)
- `approved_limit` (float)
- `current_debt` (float)

### Loan
- `loan_id` (int, primary key)
- `customer` (FK to Customer)
- `loan_amount` (float)
- `tenure` (int)
- `interest_rate` (float)
- `monthly_installment` (float)
- `emis_paid_on_time` (int)
- `start_date` (date)
- `end_date` (date)

---

## Data Files
- Place your Excel files in the `data/` folder:
  - `customer_data.xlsx`
  - `loan_data.xlsx`
- **Note:** `.xlsx` files in the `data/` folder are now tracked by git. Do not place sensitive or private data here if you plan to share the repository.
- If you want to keep the folder structure but not share data, add a `data/README.md` or `data/.gitkeep` file instead.

---

## Environment Variables
- See `docker-compose.yml` and `credit_system/settings.py` for all environment variables and settings.

---

## Running Tests
You can add and run tests using Django’s test framework:
```sh
docker compose exec web python manage.py test
```

---

## Notes
- All endpoints return JSON.
- The project is fully dockerized and can be run with a single command.
- For any issues, check the logs with:
  - `docker compose logs web`
  - `docker compose logs celery`
  - `docker compose logs db`

---

## Author
- [Your Name]

---

## License
[MIT License or as appropriate] 