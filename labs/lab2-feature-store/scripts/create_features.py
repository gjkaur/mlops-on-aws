"""
Create Feature Groups in SageMaker Feature Store.
Run this script before ingesting data.
"""

import os
import time
import uuid

import pandas as pd
from sagemaker.feature_store.feature_group import FeatureGroup
from sagemaker.session import Session


def create_customer_feature_group(session, bucket_name, role_arn):
    """Create customer features feature group."""
    uniq = uuid.uuid4().hex[:8]
    now = int(time.time())

    sample_data = pd.DataFrame(
        {
            "customer_id": [101],
            "age": [34],
            "avg_monthly_spend": [149.99],
            "tenure_months": [12],
            "support_tickets": [2],
            "EventTime": [now],
        }
    )

    feature_group_name = f"customer-features-{uniq}-{now}"
    feature_group = FeatureGroup(name=feature_group_name, sagemaker_session=session)
    feature_group.load_feature_definitions(data_frame=sample_data)

    feature_group.create(
        s3_uri=f"s3://{bucket_name}/offline-store",
        record_identifier_name="customer_id",
        event_time_feature_name="EventTime",
        role_arn=role_arn,
        enable_online_store=True,
    )

    print(f"✓ Customer Feature Group created: {feature_group_name}")
    return feature_group_name, feature_group


def create_order_feature_group(session, bucket_name, role_arn):
    """Create order features feature group."""
    uniq = uuid.uuid4().hex[:8]
    now = int(time.time())

    sample_data = pd.DataFrame(
        {
            "customer_id": [101],
            "order_id": [1001],
            "order_amount": [199.99],
            "product_category": ["electronics"],
            "order_date": ["2024-01-15"],
            "EventTime": [now],
        }
    )

    feature_group_name = f"order-features-{uniq}-{now}"
    feature_group = FeatureGroup(name=feature_group_name, sagemaker_session=session)
    feature_group.load_feature_definitions(data_frame=sample_data)

    feature_group.create(
        s3_uri=f"s3://{bucket_name}/offline-store",
        record_identifier_name="order_id",
        event_time_feature_name="EventTime",
        role_arn=role_arn,
        enable_online_store=True,
    )

    print(f"✓ Order Feature Group created: {feature_group_name}")
    return feature_group_name, feature_group


def wait_for_feature_group_creation(feature_group):
    """Wait until feature group status is Created."""
    print("Waiting for feature group to be ready...")
    while True:
        status = feature_group.describe().get("FeatureGroupStatus")
        if status == "Created":
            print("✓ Feature group is ready!")
            break
        if status == "Failed":
            print("❌ Feature group creation failed!")
            break
        print(f"   Status: {status}... waiting")
        time.sleep(10)


if __name__ == "__main__":
    bucket_name = os.environ.get("BUCKET_NAME")
    role_arn = os.environ.get("ROLE_ARN")

    if not bucket_name or not role_arn:
        print("ERROR: Set BUCKET_NAME and ROLE_ARN environment variables")
        print("Run: export BUCKET_NAME=$(terraform output -raw s3_bucket_name)")
        print("      export ROLE_ARN=$(terraform output -raw feature_store_role_arn)")
        raise SystemExit(1)

    session = Session()
    print(f"Using bucket: {bucket_name}")
    print(f"Using role: {role_arn}")

    customer_fg_name, customer_fg = create_customer_feature_group(
        session, bucket_name, role_arn
    )
    wait_for_feature_group_creation(customer_fg)

    order_fg_name, order_fg = create_order_feature_group(session, bucket_name, role_arn)
    wait_for_feature_group_creation(order_fg)

    with open("customer_fg_name.txt", "w", encoding="utf-8") as f:
        f.write(customer_fg_name)
    with open("order_fg_name.txt", "w", encoding="utf-8") as f:
        f.write(order_fg_name)

    print("\n✅ All feature groups created successfully!")
    print(f"   Customer Feature Group: {customer_fg_name}")
    print(f"   Order Feature Group: {order_fg_name}")
