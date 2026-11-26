from datetime import datetime, timedelta
from pathlib import Path
import runpy

from airflow.decorators import dag, task

PROJECT_DIR = Path("/opt/airflow/project")
RAW_DIR = PROJECT_DIR / "data" / "raw"

REQUIRED_RAW_FILES = [
    "crm_cust_info.csv",
    "crm_prd_info.csv",
    "crm_sales_details.csv",
    "erp_cust_az12.csv",
    "erp_loc_a101.csv",
    "erp_px_cat_g1v2.csv",
]

default_args = {
    "owner": "ahmed_ashraf",
    "retries": 2,
    "retry_delay": timedelta(minutes=2),
}


def run_script(filename: str) -> None:
    script_path = PROJECT_DIR / filename
    if not script_path.exists():
        raise FileNotFoundError(f"Script not found: {script_path}")
    runpy.run_path(str(script_path), run_name="__main__")


@dag(
    dag_id="ecommerce_medallion_pipeline",
    default_args=default_args,
    description="Orchestrates E-Commerce Data Pipeline (with safe fallback when raw CSVs are not yet placed)",
    start_date=datetime(2026, 11, 1),
    schedule="@daily",
    catchup=False,
    tags=["ecommerce", "medallion", "airflow"],
)
def ecommerce_medallion_pipeline():

    @task
    def check_raw_files_status() -> dict:
        missing = [f for f in REQUIRED_RAW_FILES if not (RAW_DIR / f).exists()]
        has_all_raw = len(missing) == 0
        print(f"Raw directory: {RAW_DIR}")
        print(f"All raw files present: {has_all_raw}")
        if missing:
            print(f"Missing raw files (will skip raw steps for now): {missing}")
        return {"has_all_raw": has_all_raw, "missing": missing}

    @task
    def test_connection(raw_status: dict) -> None:
        if not raw_status["has_all_raw"]:
            print("[SKIP] test_connection skipped because raw CSV files are not in data/raw yet.")
            return
        run_script("test_connection.py")

    @task
    def load_bronze(raw_status: dict) -> None:
        if not raw_status["has_all_raw"]:
            print("[SKIP] load_bronze skipped because raw CSV files are not in data/raw yet.")
            return
        run_script("load_bronze.py")

    @task
    def validate_bronze(raw_status: dict) -> None:
        if not raw_status["has_all_raw"]:
            print("[SKIP] validate_bronze skipped because raw CSV files are not in data/raw yet.")
            return
        run_script("validate_bronze.py")

    @task
    def transform_data(raw_status: dict) -> None:
        if not raw_status["has_all_raw"]:
            print("[SKIP] transform_data skipped because raw CSV files are not in data/raw yet.")
            return
        run_script("transform.py")

    @task
    def validate_silver(raw_status: dict) -> None:
        if not raw_status["has_all_raw"]:
            print("[SKIP] validate_silver skipped because raw CSV files are not in data/raw yet.")
            return
        run_script("validate_silver.py")

    @task
    def check_local_data_quality() -> None:
        run_script("check_data.py")

    status = check_raw_files_status()
    conn_done = test_connection(status)
    bronze_done = load_bronze(status)
    val_bronze_done = validate_bronze(status)
    trans_done = transform_data(status)
    val_silver_done = validate_silver(status)
    quality_done = check_local_data_quality()

    status >> conn_done >> bronze_done >> val_bronze_done >> trans_done >> val_silver_done >> quality_done


dag = ecommerce_medallion_pipeline()
