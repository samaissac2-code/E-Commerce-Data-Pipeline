# E-Commerce Medallion Pipeline (Airflow + Docker)

## Requirements
- Docker Desktop (with WSL2 enabled on Windows)
- Set Docker Memory limit to at least 4GB

## How to Run

1. Clone the repository:
   git clone <YOUR_REPOSITORY_URL>
   cd airflow_ecommerce_no_raw_needed

2. Start the environment:
   docker compose up -d

3. Open Airflow Webserver:
   Go to http://localhost:8080
   - Username: `airflow`
   - Password: `airflow`

4. Trigger the DAG:
   Unpause and trigger `ecommerce_medallion_pipeline`.

## Troubleshooting
If `airflow-webserver` shows unhealthy or connection refused:
run: `docker compose up -d --force-recreate airflow-webserver`