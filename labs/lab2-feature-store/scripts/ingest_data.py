"""
Ingest batch data into Feature Groups.
"""

import os
import time

import pandas as pd
from sagemaker.feature_store.feature_group import FeatureGroup
from sagemaker.session import Session


def generate_sample_data():
    """Generate sample customer and order data."""
    t = int(time.time())
    customer_data = pd.DataFrame(
        {
            "customer_id": [101, 102, 103, 104, 105],
            "age": [34, 28, 45, 52, 31],
            "avg_monthly_spend": [149.99, 89.99, 299.99, 49.99, 199.99],
            "tenure_months": [12, 24, 6, 48, 18],
            "support_tickets": [2, 0, 5, 1, 3],
            "EventTime": [t] * 5,
        }
    )

    order_data = pd.DataFrame(
        {
            "customer_id": [101, 101, 102, 103, 104, 104, 105],
            "order_id": [1001, 1002, 1003, 1004, 1005, 1006, 1007],
            "order_amount": [
                199.99,
                49.99,
                399.99,
                45.00,
                899.99,
                29.99,
                75.00,
            ],
            "product_category": [
                "electronics",
                "books",
                "electronics",
                "clothing",
                "electronics",
                "books",
                "clothing",
            ],
            "order_date": [
                "2024-01-15",
                "2024-02-20",
                "2024-01-10",
                "2024-02-01",
                "2024-01-05",
                "2024-02-28",
                "2024-01-25",
            ],
            "EventTime": [t] * 7,
        }
    )

    return customer_data, order_data


def ingest_data(feature_group_name, data, sagemaker_session):
    """Ingest data into a feature group."""
    feature_group = FeatureGroup(
        name=feature_group_name, sagemaker_session=sagemaker_session
    )

    print(f"Ingesting {len(data)} records into {feature_group_name}...")
    feature_group.ingest(data_frame=data, max_workers=3, wait=True)
    print(f"✓ Ingestion complete for {feature_group_name}")


if __name__ == "__main__":
    bucket_name = os.environ.get("BUCKET_NAME")
    role_arn = os.environ.get("ROLE_ARN")

    if not bucket_name or not role_arn:
        print("ERROR: Set BUCKET_NAME and ROLE_ARN environment variables")
        raise SystemExit(1)

    with open("customer_fg_name.txt", "r", encoding="utf-8") as f:
        customer_fg_name = f.read().strip()
    with open("order_fg_name.txt", "r", encoding="utf-8") as f:
        order_fg_name = f.read().strip()

    session = Session()
    customer_data, order_data = generate_sample_data()

    print("=" * 50)
    print("Starting Feature Store Ingestion")
    print("=" * 50)

    ingest_data(customer_fg_name, customer_data, session)
    ingest_data(order_fg_name, order_data, session)

    print("\n✅ All data ingested successfully!")
