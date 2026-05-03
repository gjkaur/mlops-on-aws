"""
Retrieve features from online store for real-time inference patterns.
"""

import boto3


def get_online_record(feature_group_name, record_id):
    """Get a single record from online store."""
    runtime = boto3.client(
        "sagemaker-featurestore-runtime", region_name="us-east-1"
    )

    response = runtime.get_record(
        FeatureGroupName=feature_group_name,
        RecordIdentifierValueAsString=str(record_id),
    )

    return response.get("Record", [])


def batch_get_records(feature_group_name, record_ids):
    """Get multiple records from online store."""
    runtime = boto3.client(
        "sagemaker-featurestore-runtime", region_name="us-east-1"
    )

    response = runtime.batch_get_record(
        Identifiers=[
            {
                "FeatureGroupName": feature_group_name,
                "RecordIdentifiersValueAsString": [str(i) for i in record_ids],
            }
        ]
    )

    return response.get("Records", [])


if __name__ == "__main__":
    with open("customer_fg_name.txt", "r", encoding="utf-8") as f:
        customer_fg_name = f.read().strip()

    print("=" * 50)
    print("Online Store Feature Retrieval")
    print("=" * 50)

    print("\n1. Single Record Lookup (Customer 101):")
    record = get_online_record(customer_fg_name, 101)
    for feature in record:
        print(f"   {feature['FeatureName']}: {feature['ValueAsString']}")

    print("\n2. Batch Record Lookup (Customers 101, 103, 105):")
    records = batch_get_records(customer_fg_name, [101, 103, 105])

    for item in records:
        customer_id = None
        age = None
        for feature in item.get("Record", []):
            fn = feature.get("FeatureName")
            fv = feature.get("ValueAsString")
            if fn == "customer_id":
                customer_id = fv
            if fn == "age":
                age = fv
        print(f"   Customer {customer_id}: Age {age}")

    print("\n✅ Feature retrieval complete!")
